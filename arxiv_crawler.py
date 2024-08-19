from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
import asyncio
import aiohttp
from datetime import datetime
from paper import PaperResult, PaperFiltered, Paper


class ArxivScraper(object):
    def __init__(
        self,
        date_from,
        date_until,
        category_blacklist=[],
        category_whitelist=["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.IR"],
        optional_keywords=[
            "LLM",
            "LLMs",
            "language model",
            "language models",
            "multimodal",
            "finetuning",
            "GPT",
        ],
    ):
        """
        一个抓取指定日期范围内的arxiv文章的类,
        搜索基于https://arxiv.org/search/advanced,
        翻译基于google-translate

        Args:
            date_from (str): 开始日期(含当天)
            date_until (str): 结束日期(不含当天)
            category_blacklist (list, optional): 黑名单. Defaults to [].
            category_whitelist (list, optional): 白名单. Defaults to ["cs.CV", "cs.AI", "cs.LG", "cs.CL"].
                                                如果一个文章的分类在黑名单中，且没有任何一个分类在白名单中，则被过滤掉
            optional_keywords (list, optional): 关键词, 各词之间关系为OR, 在标题/摘要中至少要出现一个关键词才会被爬取.
                                                Defaults to ["LLM", "language model", "multimodal", "finetuning", "GPT"].
        """
        self.date_from = date_from
        self.date_until = date_until
        self.filter_date_by = "submitted_date_first"  # 默认按首次提交日期过滤
        self.order = "submitted_date"  # 结果默认按首次提交日期的升序排列
        self.total = None
        self.step = 50
        self.paper_result = PaperResult(date_from, date_until)
        self.category_blacklist = category_blacklist
        self.category_whitelist = category_whitelist
        self.oprional_keywords = [
            kw.replace(" ", "+") for kw in optional_keywords
        ]  # url转义
        self.console = Console()

    @staticmethod
    def convert_date(date_str, dateformat="%Y-%m-%d"):
        # 解析输入的日期字符串,形如"21 July, 2024"
        date_obj = datetime.strptime(date_str, "%d %B, %Y")
        # 将日期对象转换为所需的格式
        formatted_date = date_obj.strftime(dateformat)
        return formatted_date

    def get_url(self, start):
        """
        获取用于搜索的url

        Args:
            start (int): 返回结果的起始序号, 每个页面只会包含序号为[start, start+50)的文章
        """
        # https://arxiv.org/search/advanced?terms-0-operator=AND&terms-0-term=LLM&terms-0-field=all&terms-1-operator=OR&terms-1-term=language+model&terms-1-field=all&terms-2-operator=OR&terms-2-term=multimodal&terms-2-field=all&terms-3-operator=OR&terms-3-term=finetuning&terms-3-field=all&terms-4-operator=AND&terms-4-term=GPT&terms-4-field=all&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-year=&date-filter_by=date_range&date-from_date=2024-08-08&date-to_date=2024-08-15&date-date_type=submitted_date_first&abstracts=show&size=50&order=submitted_date
        kwargs = "".join(
            f"&terms-{i}-operator=OR&terms-{i}-term={kw}&terms-{i}-field=all"
            for i, kw in enumerate(self.oprional_keywords)
        )
        return (
            f"https://arxiv.org/search/advanced?advanced={kwargs}"
            + f"&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-year=&date-filter_by=date_range&date-from_date={self.date_from}&date-to_date={self.date_until}&date-date_type={self.filter_date_by}&abstracts=show&size={self.step}&order={self.order}&start={start}"
        )

    async def fetch_all(self):
        """
        (aio)获取所有文章
        """
        # 获取前50篇文章并记录总数
        self.console.log("[bold green]Fetching for the first time...")
        self.console.print(f"[grey] {self.get_url(0)}")
        content = await self.request(0)
        self.parse_search_html(content)

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
                self.parse_search_html(content)
                p.update(task, advance=self.step)

            # 创建异步任务
            fetch_tasks = []
            for start in range(self.step, self.total, self.step):
                fetch_tasks.append(wrapper(start))
            await asyncio.gather(*fetch_tasks)

        self.console.log(
            f"[bold green]Fetching completed. Papers: {self.paper_result.chosen_cnt} "
            f"({self.paper_result.filtered_cnt} filtered)"
        )

    async def request(self, start):
        """
        异步请求网页，重试至多3次
        """
        error = 0
        url = self.get_url(start)
        while error <= 3:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        content = await response.text()
                        return content
            except Exception as e:
                error += 1
                self.console.log(f"[bold red]Request {start} cause error: {e}")
                self.console.log(f"[bold red]Retrying {start}... {error}/3")

    def parse_search_html(self, content):
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
            total = soup.select(
                "#main-container > div.level.is-marginless > div.level-left > h1"
            )[0].text
            # "Showing 1–50 of 2,542,002 results"
            total = int(
                total[total.find("of") + 3 : total.find("results")].replace(",", "")
            )
            self.total = total

        papers = []
        filtered_papers = []
        results = soup.find_all("li", {"class": "arxiv-result"})
        for result in results:

            url_tag = result.find("a")
            url = url_tag["href"] if url_tag else "No link"

            title_tag = result.find("p", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else "No title"

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
            categories = [category.get_text(strip=True) for category in category_tag if "tooltip" in category.get("class")]
            filtered = False
            for category in categories:
                if category in self.category_blacklist:
                    self.paper_result.add_filtered(
                        PaperFiltered(
                            date=date,
                            title=title,
                            categories=categories,
                            url=url,
                            reason=f"cat:{category} in blacklist",
                        )
                    )
                    filtered = True
                    break
            if filtered:
                continue
            if not any(
                [category in self.category_whitelist for category in categories]
            ):
                self.paper_result.add_filtered(
                    PaperFiltered(
                        date=date,
                        title=title,
                        categories=categories,
                        url=url,
                        reason=f"cat:none of {categories} in whitelist",
                    )
                )
                continue

            authors_tag = result.find("p", class_="authors")
            authors = (
                authors_tag.get_text(strip=True)[len("Authors:") :]
                if authors_tag
                else "No authors"
            )

            summary_tag = result.find("span", class_="abstract-full")
            abstract = (
                summary_tag.get_text(strip=True)[: -len("△ Less")]
                if summary_tag
                else "No summary"
            )

            self.paper_result.add_chosen(
                Paper(
                    date=date,
                    title=title,
                    categories=categories,
                    url=url,
                    authors=authors,
                    abstract=abstract,
                )
            )

    async def translate(self):
        """
        异步翻译论文的标题和摘要
        """
        await self.paper_result.translate()

    def output(self, output_dir="./output_llms", filename_format="%Y-%m-%d"):
        self.paper_result.output(output_dir, filename_format)


if __name__ == "__main__":
    from datetime import date, timedelta

    today = date.today()
    recent = today - timedelta(days=3)

    date_from = recent.strftime("%Y-%m-%d")
    data_until = today.strftime("%Y-%m-%d")

    scraper = ArxivScraper(
        date_from=date_from,
        date_until=data_until,
    )
    asyncio.run(scraper.fetch_all())
    asyncio.run(scraper.translate())
    scraper.output()
