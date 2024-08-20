import sqlite3
from datetime import datetime, timedelta
from async_translator import async_translate
from collections import defaultdict
from pathlib import Path
from categories import parse_categories
from dataclasses import dataclass
from rich.console import Console
import csv


@dataclass
class Paper:
    first_submitted_date: datetime
    title: str
    categories: list
    url: str
    authors: str
    abstract: str
    title_translated: str | None = None
    abstract_translated: str | None = None

    @classmethod
    def from_row(cls, cursor, row):
        row = sqlite3.Row(cursor, row)
        return cls(
            first_submitted_date=datetime.strptime(row["first_submitted_date"], "%Y-%m-%d"),
            title=row["title"],
            categories=row["categories"].split(","),
            url=row["url"],
            authors=row["authors"],
            abstract=row["abstract"],
            title_translated=row["title_translated"],
            abstract_translated=row["abstract_translated"],
        )

    def to_markdown(
        self,
    ):
        """
        将文章信息转换为markdown格式
        """
        categories = ",".join(parse_categories(self.categories))
        abstract = (
            f"- **摘要**: {self.abstract_translated}"
            if self.abstract_translated
            else f"- **Abstract**: {self.abstract}"
        )
        return f"""### [{self.title}]({self.url})
> **Authors**: {self.authors}
> **First submission**: {self.first_submitted_date}
- **标题**: {self.title_translated}
- **领域**: {categories}
{abstract}

"""

    async def translate(self, langto="zh-CN"):
        self.title_translated = await async_translate(self.title, langto=langto)
        self.abstract_translated = await async_translate(self.abstract, langto=langto)


@dataclass
class PaperRecord:
    paper: Paper
    comment: str

    def to_markdown(self):
        """
        将文章信息转换为markdown格式
        """
        if self.comment != "-":
            return f"""- [{self.paper.title}]({self.paper.url})
  - **标题**: {self.paper.title_translated}
  - **Filtered Reason**: {self.comment}
"""
        else:
            return self.paper.to_markdown()


class PaperDatabase:

    def __init__(
        self,
        date_from: str,
        date_until: str,
        categories_blacklist: list[str] = [],
        categories_whitelist: list[str] = [
            "cs.CV",
            "cs.AI",
            "cs.LG",
            "cs.CL",
            "cs.IR",
            "cs.MA",
        ],
    ):
        self.date_from = datetime.strptime(date_from, "%Y-%m-%d")
        self.date_until = datetime.strptime(date_until, "%Y-%m-%d")
        self.date_range_days = (self.date_until - self.date_from).days
        self.categories_blacklist = set(categories_blacklist)
        self.categories_whitelist = set(categories_whitelist)
        self.conn = sqlite3.connect("papers.db")
        self.conn.row_factory = Paper.from_row
        self.console = Console()
        self.new_papers: list[Paper] = []
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    url TEXT PRIMARY KEY,
                    authors TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    title TEXT NOT NULL,
                    categories TEXT NOT NULL,
                    first_submitted_date DATE NOT NULL,
                    title_translated TEXT,
                    abstract_translated TEXT,
                    update_time DATETIME NOT NULL
                )
            """
            )

    def add_papers(self, papers: list[Paper]):
        """
        向数据库中插入所有论文信息，如果数据库中已经存在相同的url，则会被覆盖

        Args:
            papers (list[Paper]): 论文列表
        """
        with self.conn:
            # 创建一个要插入的数据列表
            data_to_insert = [
                (
                    paper.url,
                    paper.authors,
                    paper.abstract,
                    paper.title,
                    ",".join(paper.categories),
                    paper.first_submitted_date.strftime("%Y-%m-%d"),
                    paper.title_translated,
                    paper.abstract_translated,
                    datetime.now(),
                )
                for paper in papers
            ]

            # 使用 executemany 一次性插入所有数据
            self.conn.executemany(
                """
                INSERT OR REPLACE INTO papers 
                (url, authors, abstract, title, categories, first_submitted_date, title_translated, abstract_translated, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                data_to_insert,
            )

    def update_papers(self, papers: list[Paper])-> bool:
        """
        尝试向数据库中插入新的论文信息，如果遇到了已有的论文，在此之前的论文会被插入，剩余的都不会被插入。
        返回是否全部插入成功。

        Args:
            papers (list[Paper]): 论文列表

        Returns:
            bool: 是否全部插入成功，可用于增量更新的flag
        """
        new_papers = []
        continue_update = True
        for paper in papers:
            with self.conn:
                cursor = self.conn.execute(
                    """
                    SELECT * FROM papers WHERE url = ?
                    """,
                    (paper.url,),
                )
                if cursor.fetchone():
                    continue_update = False
                    break
                else:
                    new_papers.append(paper)
        self.add_papers(new_papers)
        return continue_update

    def fetch_papers_on_date(self, date: datetime) -> tuple[list[PaperRecord], list[PaperRecord]]:
        """
        获取某一天提交的所有论文信息，以初次提交日期为准。返回PaperRecord列表构成的元组，第一个元素为选中的论文，第二个元素为被过滤的论文

        Args:
            date (datetime): 日期

        Returns:
            tuple[list[PaperRecord], list[PaperRecord]]: 选中的论文和被过滤的论文
        """
        with self.conn:
            cursor = self.conn.execute(
                """
                SELECT * FROM papers WHERE first_submitted_date = ?
                """,
                (date.strftime("%Y-%m-%d"),),
            )
            papers = cursor.fetchall()

        filtered_paper_records = []
        chosen_paper_records = []
        for paper in papers:
            categories = set(paper.categories)
            # 没有任何一个领域在白名单中
            if not (self.categories_whitelist & categories):
                categories_str = ",".join(categories)
                filtered_paper_records.append(PaperRecord(paper, f"none of {categories_str} in whitelist"))
            # 至少有一个领域在黑名单中
            elif black := self.categories_blacklist & categories:
                black_str = ",".join(black)
                filtered_paper_records.append(PaperRecord(paper, f"cat:{black_str} in blacklist"))
            else:
                chosen_paper_records.append(PaperRecord(paper, "-"))
        return chosen_paper_records, filtered_paper_records

    def to_markdown(self, output_dir="./output_llms", filename_format="%Y-%m-%d", metadata=None):
        """
        将数据库中的论文信息输出为markdown格式
        
        Args:
            output_dir (str, optional): 输出目录. Defaults to "./output_llms".
            filename_format (str, optional): 文件名格式. Defaults to "%Y-%m-%d".
            metadata (dict, optional): 一些元数据，用于生成文章前言. Defaults to None.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        if metadata:
            repo_url = metadata["repo_url"]
            categories = ",".join(metadata["category_whitelist"])
            optional_keywords = ", ".join(metadata["optional_keywords"])
            preface_str = f"""
> 本文由 [{repo_url}]({repo_url}) 自动生成
>
> 领域白名单：{categories}
> 关键词： {optional_keywords}

""".lstrip()
        else:
            preface_str = ""

        for i in range(self.date_range_days):
            current = self.date_from + timedelta(days=i)
            current_filename = current.strftime(filename_format)

            with open(output_dir / f"{current_filename}.md", "w", encoding="utf-8") as file:
                chosen_records, filtered_records = self.fetch_papers_on_date(current)
                preface_str += f"# 论文全览：{current_filename}\n\n共有{len(chosen_records)}篇相关领域论文, 另有{len(filtered_records)}篇其他\n\n"

                papers_str = ""
                chosen_dict = defaultdict(list)
                for record in chosen_records:
                    chosen_dict[record.paper.categories[0]].append(record)
                for category in sorted(chosen_dict.keys()):
                    category_en = parse_categories([category], lang="en")[0]
                    category_zh = parse_categories([category], lang="zh-CN")[0]
                    papers_str += f"## {category_zh}({category}:{category_en})\n\n"
                    for record in chosen_dict[category]:
                        papers_str += record.to_markdown()

                papers_str += "## 其他论文\n\n"
                for record in filtered_records:
                    papers_str += record.to_markdown()

                file.write(preface_str + papers_str)

            self.console.log(
                f"[bold green]Output {current_filename}.md completed. {len(chosen_records)} papers chosen, {len(filtered_records)} papers filtered"
            )

    def to_csv(self, output_dir="./output_llms", filename_format="%Y-%m-%d", csv_config={}):
        """将数据库中的论文信息输出为csv格式

        Args:
            output_dir (str, optional): 输出文件夹. Defaults to "./output_llms".
            filename_format (str, optional): 日期转换为文件名字符串的格式. Defaults to "%Y-%m-%d".
            csv_config (dict, optional): csv的格式. Defaults to {}.
                其中，header (bool): 是否输出表头
                剩余的参数原样传递给csv.writer
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        csv_table = {
            "Title": lambda record: record.paper.title,
            "Interest": lambda record: ("chosen" if record.comment == "-" else "filtered"),
            "Title Translated": lambda record: (
                record.paper.title_translated if record.paper.title_translated else "-"
            ),
            "Categories": lambda record: ",".join(record.paper.categories),
            "Authors": lambda record: record.paper.authors,
            "URL": lambda record: record.paper.url,
            "First Submitted Date": lambda record: record.paper.first_submitted_date.strftime("%Y-%m-%d"),
            "Abstract": lambda record: record.paper.abstract,
            "Abstract Translated": lambda record: (
                record.paper.abstract_translated if record.paper.abstract_translated else "-"
            ),
            "comment": lambda record: record.comment,
        }

        headers = list(csv_table.keys())

        for i in range(self.date_range_days):
            current = self.date_from + timedelta(days=i)
            current_filename = current.strftime(filename_format)

            with open(output_dir / f"{current_filename}.csv", "w", encoding="utf-8") as file:
                header = csv_config.pop("header", True)
                if "lineterminator" not in csv_config:
                    csv_config["lineterminator"] = "\n"
                writer = csv.writer(file, **csv_config)
                if header:
                    writer.writerow(headers)

                chosen_records, filtered_records = self.fetch_papers_on_date(current)
                for record in chosen_records + filtered_records:
                    writer.writerow([fn(record) for fn in csv_table.values()])

                self.console.log(
                    f"[bold green]Output {current_filename}.csv completed. {len(chosen_records)} papers chosen, {len(filtered_records)} papers filtered"
                )


if __name__ == "__main__":
    from datetime import date, timedelta

    today = date.today()
    recent = today - timedelta(days=1)

    date_from = recent.strftime("%Y-%m-%d")
    date_until = today.strftime("%Y-%m-%d")

    db = PaperDatabase(date_from, date_until)
    db.to_markdown()
    db.to_csv(csv_config=dict(delimiter="\t", header=False))
