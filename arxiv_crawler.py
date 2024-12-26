import asyncio
import re
from datetime import datetime, timedelta, UTC
from itertools import chain

import aiohttp
from bs4 import BeautifulSoup, NavigableString, Tag
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from arxiv_time import next_arxiv_update_day
from paper import Paper, PaperDatabase, PaperExporter


class ArxivScraper(object):
    def __init__(
        self,
        date_from,
        date_until,
        subject_list=["computer_science", "physics", "economics", "eess", "mathematics", "q_biology", "q_finance", "statistics"],
        category_blacklist=[],
        category_whitelist=["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.IR", "cs.MA"],
        optional_keywords=["LLM", "LLMs", "language model", "language models", "multimodal", "finetuning", "GPT"],
        trans_to="zh-CN",
        proxy=None,
    ):
        """
        一个抓取指定日期范围内的arxiv文章的类,
        搜索基于https://arxiv.org/search/advanced,
        一个文件被爬取到的条件是：首次提交时间在`date_from`和`date_until`之间，并且包含至少一个关键词。
        一个文章被详细展示（不被过滤）的条件是：至少有一个领域在白名单中，并且没有任何一个领域在黑名单中。
        翻译基于google-translate

        Args:
            date_from (str): 开始日期(含当天)
            date_until (str): 结束日期(含当天)
            subject_list (list, optional): 领域. Defaults to ["computer_science", "physics", "economics", "eess", "mathematics", "q_biology", "q_finance", "statistics"]
            category_blacklist (list, optional): 黑名单. Defaults to [].
            category_whitelist (list, optional): 白名单. Defaults to ["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.IR", "cs.MA"].
            optional_keywords (list, optional): 关键词, 各词之间关系为OR, 在标题/摘要中至少要出现一个关键词才会被爬取.
                Defaults to [ "LLM", "LLMs", "language model", "language models", "multimodal", "finetuning", "GPT"]
            trans_to: 翻译的目标语言, 若设为可转换为False的值则不会翻译
            proxy (str | None, optional): 用于翻译和爬取arxiv时要使用的代理, 通常是http://127.0.0.1:7890. Defaults to None
        """
        # announced_date_first 日期处理为年月，从from到until的所有月份都会被爬取
        # 如果from和until是同一个月，则until设置为下个月(from+31)
        self.search_from_date = datetime.strptime(date_from[:-3], "%Y-%m")
        self.search_until_date = datetime.strptime(date_until[:-3], "%Y-%m")
        if self.search_from_date.month == self.search_until_date.month:
            self.search_until_date = (self.search_from_date + timedelta(days=31)).replace(day=1)
        # 由于arxiv的奇怪机制，每个月的第一天公布的文章总会被视作上个月的文章, 所以需要将月初文章的首次公布日期往后推一天
        self.fisrt_announced_date = next_arxiv_update_day(next_arxiv_update_day(self.search_from_date) + timedelta(days=1))

        self.subject_list = subject_list
        self.category_blacklist = category_blacklist  # used as metadata
        self.category_whitelist = category_whitelist  # used as metadata
        self.optional_keywords = [kw.replace(" ", "+") for kw in optional_keywords]  # url转义

        self.trans_to = trans_to  # translate
        self.proxy = proxy

        self.filt_date_by = "announced_date_first"  # url
        self.order = "-announced_date_first"  # url(结果默认按首次公布日期的降序排列，这样最新公布的会在前面)
        self.total = None  # fetch_all
        self.step = 50  # url, fetch_all
        self.papers: list[Paper] = []  # fetch_all

        self.paper_db = PaperDatabase()
        self.paper_exporter = PaperExporter(date_from, date_until, category_blacklist, category_whitelist)
        self.console = Console()

    @property
    def meta_data(self):
        """
        返回搜索的元数据
        """
        return dict(repo_url="https://github.com/huiyeruzhou/arxiv_crawler", **self.__dict__)

    def get_url(self, start):
        """
        获取用于搜索的url

        Args:
            start (int): 返回结果的起始序号, 每个页面只会包含序号为[start, start+50)的文章
            filter_date_by (str, optional): 日期筛选方式. Defaults to "submitted_date_first".
        """
        # https://arxiv.org/search/advanced?terms-0-operator=AND&terms-0-term=LLM&terms-0-field=all&terms-1-operator=OR&terms-1-term=language+model&terms-1-field=all&terms-2-operator=OR&terms-2-term=multimodal&terms-2-field=all&terms-3-operator=OR&terms-3-term=finetuning&terms-3-field=all&terms-4-operator=AND&terms-4-term=GPT&terms-4-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-year=&date-filter_by=date_range&date-from_date=2024-08-08&date-to_date=2024-08-15&date-date_type=submitted_date_first&abstracts=show&size=50&order=submitted_date
        kwargs = "".join(
            f"&terms-{i}-operator=OR&terms-{i}-term={kw}&terms-{i}-field=all"
            for i, kw in enumerate(self.optional_keywords)
        )
        date_from = self.search_from_date.strftime("%Y-%m")
        date_until = self.search_until_date.strftime("%Y-%m")
        subjects_query = '&classification-{}=y'.format('=y&classification-'.join(self.subject_list))
        return (
            f"https://arxiv.org/search/advanced?advanced={kwargs}"
            f"{subjects_query}&classification-physics_archives=all&"
            f"classification-include_cross_list=include&"
            f"date-year=&date-filter_by=date_range&date-from_date={date_from}&date-to_date={date_until}&"
            f"date-date_type={self.filt_date_by}&abstracts=show&size={self.step}&order={self.order}&start={start}"
        )
    async def request(self, start):
        """
        异步请求网页，重试至多3次
        """
        error = 0
        url = self.get_url(start)
        while error <= 3:
            try:
                async with aiohttp.ClientSession(trust_env=True, read_timeout=10) as session:
                    async with session.get(url, proxy=self.proxy) as response:
                        response.raise_for_status()
                        content = await response.text()
                        return content
            except Exception as e:
                error += 1
                self.console.log(f"[bold red]Request {start} cause error: ")
                self.console.print_exception()
                self.console.log(f"[bold red]Retrying {start}... {error}/3")

    async def fetch_all(self):
        """
        (aio)获取所有文章
        """
        # 获取前50篇文章并记录总数
        self.console.log(f"[bold green]Fetching the first {self.step} papers...")
        self.console.print(f"[grey] {self.get_url(0)}")
        content = await self.request(0)
        self.papers.extend(self.parse_search_html(content))

        # 获取剩余的内容
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        ) as p:  # rich进度条
            task = p.add_task(
                description=f"[bold green]Fetching {self.total} results",
                total=self.total,
            )
            p.update(task, advance=self.step)

            async def wrapper(start):  # wrapper用于显示进度
                # 异步请求网页，并解析其中的内容
                content = await self.request(start)
                papers = self.parse_search_html(content)
                p.update(task, advance=self.step)
                return papers

            # 创建异步任务
            fetch_tasks = []
            for start in range(self.step, self.total, self.step):
                fetch_tasks.append(wrapper(start))
            papers_list = await asyncio.gather(*fetch_tasks)
            self.papers.extend(chain(*papers_list))

        self.console.log(f"[bold green]Fetching completed. ")
        if self.trans_to:
            await self.translate()
        self.process_papers()

    def fetch_update(self):
        """
        更新文章, 这会从最新公布的文章开始更新, 直到遇到已经爬取过的文章为止。
        为了效率，建议在运行fetch_all后再运行fetch_update
        """
        # 当前时间
        utc_now = datetime.now(UTC).replace(tzinfo=None)
        # 上一次更新最新文章的UTC时间. 除了更新新文章外也可能重新爬取了老文章, 数据库只看最新文章的时间戳。
        last_update = self.paper_db.newest_update_time()
        # 检查一下上次之后的最近一个arxiv更新日期
        self.search_from_date = next_arxiv_update_day(last_update)
        self.console.log(f"[bold yellow]last update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}, "
                         f"next arxiv update: {self.search_from_date.strftime('%Y-%m-%d')}" 
                         )
        self.console.log(f"[bold yellow]UTC now: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}")
        # 如果还没到更新时间就不更新了
        if self.search_from_date >= utc_now:
            self.console.log(f"[bold red]Your database is already up to date.")
            return
        # 如果这一次的更新时间恰好是这个月的第一个更新日，那么当日更新的文章都会出现在上个月的搜索结果中
        # 为了正确获得这天的文章，我们上推一个月的搜索时间
        self.fisrt_announced_date = self.search_from_date
        if self.search_from_date == next_arxiv_update_day(self.search_from_date.replace(day=1)):
            self.search_from_date = self.search_from_date - timedelta(days=31)
            self.console.log(f"[bold yellow]The update in {self.fisrt_announced_date.strftime('%Y-%m-%d')} can only be found in the previous month.")
        else:
            self.console.log(
                f"[bold green]Searching from {self.search_from_date.strftime('%Y-%m-%d')} "
                f"to {self.search_until_date.strftime('%Y-%m-%d')}, fetch the first {self.step} papers..."
            )
        self.console.print(f"[grey] {self.get_url(0)}")

        continue_update = self.update(0)
        for start in range(self.step, self.total, self.step):
            if not continue_update:
                break

            continue_update = self.update(start)
        self.console.log(f"[bold green]Fetching completed. {len(self.papers)} new papers.")
        if self.trans_to:
            asyncio.run(self.translate())
        self.process_papers()

    def process_papers(self):
        """
        推断文章的首次公布日期, 并将文章添加到数据库中
        """
        # 从下一个可能的公布日期开始
        announced_date = next_arxiv_update_day(self.fisrt_announced_date)   
        self.console.log(f"fisrt announced date: {announced_date.strftime('%Y-%m-%d')}")
        # 按照从前到后的时间顺序梳理文章
        for paper in reversed(self.papers):
            # 文章于T日美东时间14:00(T UTC+0 18:00)前提交，将于T日美东时间20:00(T+1 UTC+0 00:00)公布，T始终为工作日。
            # 因此可知美东 T日的文章至少在UTC+0 T+1日公布，如果超过14:00甚至会在UTC+0 T+2日公布
            next_possible_annouced_date = next_arxiv_update_day(paper.first_submitted_date + timedelta(days=1))
            if announced_date < next_possible_annouced_date:
                announced_date = next_possible_annouced_date
            paper.first_announced_date = announced_date
        self.paper_db.add_papers(self.papers)
    
    def reprocess_papers(self):
        """
        这会从数据库中获取所有文章, 并重新推断文章的首次公布日期，并打印调试信息
        """
        self.papers = self.paper_db.fetch_all()
        self.process_papers()
        with open("announced_date.csv", "w") as f:
            f.write("url,title,announced_date,submitted_date\n")
            for paper in self.papers:
                f.write(
                    f"{paper.url},{paper.title},{paper.first_announced_date.strftime('%Y-%m-%d')},{paper.first_submitted_date.strftime('%Y-%m-%d')}\n"
                )

    def update(self, start) -> bool:
        content = asyncio.run(self.request(start))
        self.papers.extend(self.parse_search_html(content))
        cnt_new = self.paper_db.count_new_papers(self.papers[start : start + self.step])
        if cnt_new < self.step:
            self.papers = self.papers[: start + cnt_new]
            return False
        else:
            return True

    def parse_search_html(self, content) -> list[Paper]:
        """
        解析搜索结果页面, 并将结果保存到self.paper_result中
        初次调用时, 会解析self.total

        Args:
            content (str): 网页内容
        """

        """下面是一个搜索结果的例子
        <li class="arxiv-result">
            <div class="is-marginless">
                <p class="list-title is-inline-block">
                    <a href="https://arxiv.org/abs/physics/9403001">arXiv:physics/9403001</a>
                    <span>&nbsp;[<a href="https://arxiv.org/pdf/physics/9403001">pdf</a>, <a
                            href="https://arxiv.org/ps/physics/9403001">ps</a>, <a
                            href="https://arxiv.org/format/physics/9403001">other</a>]&nbsp;</span>
                </p>
                <div class="tags is-inline-block">
                    <span class="tag is-small is-link tooltip is-tooltip-top" data-tooltip="Popular Physics">
                        physics.pop-ph</span>
                    <span class="tag is-small is-grey tooltip is-tooltip-top"
                        data-tooltip="High Energy Physics - Theory">hep-th</span>
                </div>
                <div class="is-inline-block" style="margin-left: 0.5rem">
                    <div class="tags has-addons">
                        <span class="tag is-dark is-size-7">doi</span>
                        <span class="tag is-light is-size-7">
                            <a class="" href="https://doi.org/10.1063/1.2814991">10.1063/1.2814991 <i
                                    class="fa fa-external-link" aria-hidden="true"></i></a>
                        </span>
                    </div>
                </div> 
            </div>
            <p class="title is-5 mathjax">
                Desperately Seeking Superstrings
            </p>
            <p class="authors">
                <span class="has-text-black-bis has-text-weight-semibold">Authors:</span>
                    <a href="/search/?searchtype=author&amp;query=Ginsparg%2C+P">Paul Ginsparg</a>, <a href="/search/?searchtype=author&amp;query=Glashow%2C+S">Sheldon Glashow</a> 
            </p> 
            <p class="abstract mathjax">
                <span class="has-text-black-bis has-text-weight-semibold">Abstract</span>: 
                
                <span class="abstract-short has-text-grey-dark mathjax" id="physics/9403001v1-abstract-short"
                    style="display: inline;"> We provide a detailed analysis of the problems and prospects of superstring theory c.
                1986, anticipating much of the progress of the decades to follow. </span>

                <span class="abstract-full has-text-grey-dark mathjax" id="physics/9403001v1-abstract-full"
                    style="display: none;"> We provide a detailed analysis of the problems and prospects of
                superstring theory c. 1986, anticipating much of the progress of the decades to follow. 
                <a class="is-size-7" style="white-space: nowrap;"
                        onclick="document.getElementById('physics/9403001v1-abstract-full').style.display = 'none'; document.getElementById('physics/9403001v1-abstract-short').style.display = 'inline';">△ Less</a>
                </span>
            </p> 
            <p class="is-size-7"><span class="has-text-black-bis has-text-weight-semibold">Submitted</span>
                25 April, 1986; <span class="has-text-black-bis has-text-weight-semibold">originally
                announced</span> March 1994. </p> 
            <p class="comments is-size-7">
                <span class="has-text-black-bis has-text-weight-semibold">Comments:</span>
                <span class="has-text-grey-dark mathjax">originally appeared as a Reference Frame in Physics
                    Today, May 1986</span>
            </p> 
            <p class="comments is-size-7">
                <span class="has-text-black-bis has-text-weight-semibold">Journal ref:</span> Phys.Today
                86N5 (1986) 7-9 </p> 
        </li>
        """

        soup = BeautifulSoup(content, "html.parser")
        if not self.total:
            total = soup.select("#main-container > div.level.is-marginless > div.level-left > h1")[0].text
            # "Showing 1–50 of 2,542,002 results" or "Sorry, your query returned no results"
            if "Sorry" in total:
                self.total = 0
                return []
            total = int(total[total.find("of") + 3 : total.find("results")].replace(",", ""))
            self.total = total

        results = soup.find_all("li", {"class": "arxiv-result"})
        papers = []
        for result in results:

            url_tag = result.find("a")
            url = url_tag["href"] if url_tag else "No link"

            title_tag = result.find("p", class_="title")
            title = self.parse_search_text(title_tag) if title_tag else "No title"
            title = title.strip()

            date_tag = result.find("p", class_="is-size-7")
            date = date_tag.get_text(strip=True) if date_tag else "No date"
            if "v1" in date:
                # Submitted9 August, 2024; v1submitted 8 August, 2024; originally announced August 2024.
                # 注意空格会被吞掉，这里我们要找最早的提交日期
                v1 = date.find("v1submitted")
                date = date[v1 + 12 : date.find(";", v1)]
            else:
                # Submitted8 August, 2024; originally announced August 2024.
                # 注意空格会被吞掉
                submit_date = date.find("Submitted")
                date = date[submit_date + 9 : date.find(";", submit_date)]

            category_tag = result.find_all("span", class_="tag")
            categories = [
                category.get_text(strip=True) for category in category_tag if "tooltip" in category.get("class")
            ]

            authors_tag = result.find("p", class_="authors")
            authors = authors_tag.get_text(strip=True)[len("Authors:") :] if authors_tag else "No authors"

            summary_tag = result.find("span", class_="abstract-full")
            abstract = self.parse_search_text(summary_tag) if summary_tag else "No summary"
            abstract = abstract.strip()

            comments_tag = result.find("p", class_="comments")
            comments = comments_tag.get_text(strip=True)[len("Comments:") :] if comments_tag else "No comments"

            papers.append(
                Paper(
                    url=url,
                    title=title,
                    first_submitted_date=datetime.strptime(date, "%d %B, %Y"),
                    categories=categories,
                    authors=authors,
                    abstract=abstract,
                    comments=comments,
                )
            )
        return papers

    def parse_search_text(self, tag):
        string = ""
        for child in tag.children:
            if isinstance(child, NavigableString):
                string += re.sub(r"\s+", " ", child)
            elif isinstance(child, Tag):
                if child.name == "span" and "search-hit" in child.get("class"):
                    string += re.sub(r"\s+", " ", child.get_text(strip=False))
                elif child.name == "a" and ".style.display" in child.get("onclick"):
                    pass
                else:
                    import pdb

                    pdb.set_trace()
        return string

    async def translate(self):
        if not self.trans_to:
            raise ValueError("No target language specified.")
        self.console.log("[bold green]Translating...")
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        ) as p:
            total = len(self.papers)
            task = p.add_task(
                description=f"[bold green]Translating {total} papers",
                total=total,
            )

            async def worker(paper):
                await paper.translate(langto=self.trans_to)
                p.update(task, advance=1)

            await asyncio.gather(*[worker(paper) for paper in self.papers])

    def to_markdown(self, output_dir="./output_llms", filename_format="%Y-%m-%d", meta=False):
        self.paper_exporter.to_markdown(output_dir, filename_format, self.meta_data if meta else None)

    def to_csv(self, output_dir="./output_llms", filename_format="%Y-%m-%d",  header=False, csv_config={},):
        self.paper_exporter.to_csv(output_dir, filename_format, header, csv_config)


if __name__ == "__main__":
    from datetime import date, timedelta

    today = date.today()

    scraper = ArxivScraper(
        date_from=today.strftime("%Y-%m-%d"),
        date_until=today.strftime("%Y-%m-%d"),
    )
    asyncio.run(scraper.fetch_all())
    scraper.to_markdown(meta=True)
