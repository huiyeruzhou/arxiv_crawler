from pathlib import Path
from async_translator import async_translate
from collections import defaultdict
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from categories import parse_categories

@dataclass
class PaperFiltered:
    date: str
    title: str
    categories: list
    url: str
    reason: str
    title_translated: str | None = None

    def to_markdown(self):
        """
        将文章信息转换为markdown格式
        """
        return f"""
- [{self.title}]({self.url})
  - **标题**: {self.title_translated}
  - **Filtered Reason**: {self.reason}
""".lstrip()

    async def translate(self, langto="zh-CN"):
        """
        翻译文章的标题
        """
        self.title_translated = await async_translate(self.title, langto=langto)


@dataclass
class Paper:
    date: str
    title: str
    categories: list
    url: str
    authors: str
    abstract: str
    title_translated: str | None = None
    abstract_translated: str | None = None

    def to_markdown(self):
        """
        将文章信息转换为markdown格式
        """
        categories = ";".join(parse_categories(self.categories))
        return f"""
### [{self.title}]({self.url})
> **Authors**: {self.authors}
> **First submission**: {self.date}
- **标题**: {self.title_translated}
- **领域**: {categories}
- **摘要**: {self.abstract_translated}

""".lstrip()

    async def translate(self, langto="zh-CN"):
        """
        翻译文章的标题和摘要
        """
        self.title_translated = await async_translate(self.title, langto=langto)
        self.abstract_translated = await async_translate(self.abstract, langto=langto)


class PaperResult(object):
    def __init__(self, date_from, date_until) -> None:
        self.date_from = datetime.strptime(date_from, "%Y-%m-%d")
        self.date_until = datetime.strptime(date_until, "%Y-%m-%d")
        self.days = (self.date_until - self.date_from).days
        self.chosen_dict = defaultdict(lambda: defaultdict(list[Paper]))
        self.filtered_dict = defaultdict(list[PaperFiltered])
        self.chosen_cnt = 0
        self.filtered_cnt = 0
        self.console = Console()

    def add_chosen(self, paper: Paper):
        """
        将文章添加到chosen_dict中
        """
        self.chosen_dict[paper.date][paper.categories[0]].append(paper)
        self.chosen_cnt += 1

    def add_filtered(self, paper: PaperFiltered):
        """
        将文章添加到filtered_dict中
        """
        self.filtered_dict[paper.date].append(paper)
        self.filtered_cnt += 1

    async def translate(self, langto="zh-CN"):
        """
        翻译文章的标题和摘要
        """
        self.console.log("[bold green]Translating...")
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        ) as p:
            total = self.chosen_cnt + self.filtered_cnt
            task = p.add_task(
                description=f"[bold green]Translating {total} papers",
                total=total,
            )

            async def worker(paper):
                await paper.translate(langto=langto)
                p.update(task, advance=1)

            translates = [
                worker(paper)
                for cat in self.chosen_dict.values()
                for papers in cat.values()
                for paper in papers
            ]
            translates += [
                worker(paper)
                for papers in self.filtered_dict.values()
                for paper in papers
            ]
            await asyncio.gather(*translates)

        self.console.log(f"[bold green]Translating completed.")

    def output(self, output_dir, filename_format):
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True, parents=True)

        for i in range(self.days):
            current = self.date_from + i * timedelta(days=1)
            current_filename = current.strftime(filename_format)
            current_key = current.strftime("%d %B, %Y")

            with open(output_dir / f"{current_filename}.md", "w") as file:
                chosen = self.chosen_dict[current_key]
                filtered = self.filtered_dict[current_key]
                chosen_cnt = sum(len(papers) for papers in chosen.values())
                preface_str = f"# 论文全览：{current_filename}\n\n共有{chosen_cnt}篇相关领域论文，另有{len(filtered)}篇其他论文\n\n"

                papers_str = ""
                for category in sorted(chosen.keys()):
                    papers = chosen[category]
                    category_en = parse_categories([category], lang="en")[0]
                    category_zh = parse_categories([category], lang="zh-CN")[0]
                    papers_str += f"## {category_zh}({category}:{category_en})\n\n"
                    for paper in papers:
                        papers_str += paper.to_markdown()

                filtered_str = f"## 其他论文\n\n"
                for filtered in filtered:
                    filtered_str += filtered.to_markdown()

                file.write(preface_str + papers_str + filtered_str)
        self.console.log(
            f"[bold green]Output markdown files completed. {self.days} files in total."
        )
