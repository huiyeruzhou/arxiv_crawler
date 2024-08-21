# ARXIV_CRAWLER

这是一个高效，快捷的 arXiv 论文爬虫，它可以将指定主题，包含指定关键词的论文信息爬取到本地，并且将其中的标题和摘要翻译成中文。

主要特点包括：

- 高速：通过进行异步网络请求，这个爬虫能够在两分钟之内爬取并翻译 2000 篇文章的标题和摘要信息，并且将其输出为精美的 markdown 文件（取决于您的网络带宽，在一个能高速链接arxiv和google的环境下只需要十几秒）。
- 完备：通过以**最新公布时间**为索引，这个爬虫可以做到按天为单位更新且无漏召，无重复。
- 增量更新：这个爬虫会维护一个本地数据库，每次爬取时只需要将新提交的文章插入到数据库中。但它也支持你补充过去某段时间的文章。
- 可视化：爬取的结果可以导出为csv文件，配合飞书实现的精美可视化界面更加方便阅读和筛选，详情见[配合飞书的进阶用法](#进阶用法-配合飞书使用)

![alt text](readme/lark_demo.png)

下列示意中，系统用 4s 爬取并翻译了 2024 年 8 月 19 日的全部 70 篇文章，并根据其领域过滤了其中的 6 篇。并将结果输出到`output_llms/2024-08-19.md`中。
![alt text](readme/cli_demo.png)

markdown 示意：

<div style="text-align: center;">
    <img src="readme/markdown_demo.png" alt="markdown demo" style="width: 60%; height: auto;" />
</div>

论文的数据将被持久化在一个本地数据库`papers.db`中，这是为了便于进行[基于公布时间的增量更新](#进阶用法-基于公布时间的增量更新)。

## 基本用法：爬取当天提交的论文为 markdown

1. 克隆本仓库到本地

```bash
git clone https://github.com/huiyeruzhou/arxiv_crawler.git
```

2. 安装依赖

```bash
pip install BeautifulSoup4
pip install rich
pip install aiohttp
pip install requests
```

3. 运行

- 建立基础数据库

```bash
python arxiv_crawler.py
```

这段代码会将最近**一个月**内大模型相关的论文信息爬取到本地的`papers.db`中，并且将最近**一天**内公布的文章输出为带有元信息的 markdown 文件。

- 增量更新

由于更新过程需要逐个检查论文是否已经存在，因此增量更新时不再使用异步爬取而是使用同步爬取，这会导致一定的速度下降，对于少量论文来说无所谓。如果很久没有更新，建议直接用`fetch_all`方法爬整月论文，这样更快。

增量更新的原理请见[进阶用法-基于公布时间的增量更新](#进阶用法-基于公布时间的增量更新)。

```py
from datetime import date, timedelta
from arxiv_crawler import ArxivScraper
today = date.today()
recent = today - timedelta(days=1)

scraper = ArxivScraper(
    date_from=recent.strftime("%Y-%m-%d"),
    date_until=today.strftime("%Y-%m-%d"),
)
scraper.fetch_update()
scraper.to_markdown()
scraper.to_csv(csv_config=dict(delimiter="\t", header=False))
```

日常使用时只需要修改这部分代码中的内容即可。你可以将代码复制到`run.py`中，它不会被 git 跟踪。

- 从数据库中生成markdown/csv

```bash
python paper.py
```

这段代码会将`papers.db`中最近**一天**内提交的论文信息输出为 markdown 文件和 csv 文件，如果你只是需要重新获得已经爬取的论文中的信息，可以基于这里的代码修改。

1. 用法说明

- 要修改爬取的时间范围，领域，关键字，请参考`arxiv_crawler.py`中`ArxivScraper`类的注释：
  一个文件被爬取到的条件是：首次提交时间在`date_from`和`date_until`之间，并且包含至少一个关键词。
  一个文章被详细展示（不被过滤）的条件是：至少有一个领域在白名单中，并且没有任何一个领域在黑名单中。
  Args:

  - date_from (str): 开始日期(含当天)
  - date_until (str): 结束日期(不含当天)
  - category_blacklist (list, optional): 黑名单. Defaults to [].
  - category_whitelist (list, optional): 白名单. Defaults to ["cs.CV", "cs.AI", "cs.LG", "cs.CL", "cs.IR", "cs.MA"].
  - optional_keywords (list, optional): 关键词, 各词之间关系为OR, 在标题/摘要中至少要出现一个关键词才会被爬取.
        Defaults to [ "LLM", "LLMs", "language model", "language models", "multimodal", "finetuning", "GPT"]
  - trans_to: 翻译的目标语言, 若设为可转换为False的值则不会翻译
  - proxy (str | None, optional): 用于翻译和爬取arxiv时要使用的代理, 通常是http://127.0.0.1:7890. Defaults to None

- 输出文件名是根据日期生成的，可以使用`output`方法的`filename_format`参数修改日期格式，默认为`%Y-%m-%d`即形如`2024-08-08.md`。

```py
scraper.to_markdown(filename_format='%Y-%m-%d')
```

- 如果你希望将一条元信息添加到输出文件中，可以使用`output`方法的`meta`参数。

```py
scraper.to_markdown(meta=True)
```

元信息形如：

> 本文由 [https://github.com/huiyeruzhou/arxiv_crawler](https://github.com/huiyeruzhou/arxiv_crawler) 自动生成
>
> 领域白名单: cs.CV;cs.AI;cs.LG;cs.CL;cs.IR
> 关键词： LLM, LLMs, language+model, language+models, multimodal, finetuning, GPT

## 结果示例

假设爬取了七天的论文，那么结果可能形如：

```bash
output_llms
├── 2024-08-08.md
├── 2024-08-09.md
├── 2024-08-10.md
├── 2024-08-11.md
├── 2024-08-12.md
├── 2024-08-13.md
└── 2024-08-14.md
```

其中被保留的内容形如：

```md
# 论文全览：2024-08-16

共有 57 篇相关领域论文，另有 6 篇其他论文

## 人工智能(cs.AI:Artificial Intelligence)

### [Fine-tuningLLMsfor Autonomous Spacecraft Control: A Case Study Using Kerbal Space Program](https://arxiv.org/abs/2408.08676)

> **Authors**: Alejandro Carrasco,Victor Rodriguez-Fernandez,Richard Linares
> **First submission**: 16 August, 2024

- **标题**: 用于自主航天器控制的微调 LLM：使用坎巴拉太空计划的案例研究
- **领域**: 人工智能,天体物理学仪器和方法
- **摘要**: 最近出现的趋势是使用大型语言模型（LLM）作为自主代理，根据用户文本提示的内容采取行动。本研究探索使用微调大型语言模型 (LLM) 进行自主航天器控制，并使用坎巴拉太空计划微分游戏套件 (KSPDG) 作为测试环境。由于模拟能力和数据不足，传统的强化学习（RL）方法在该领域面临局限性。通过利用 LLM，特别是 GPT-3.5 和 LLaMA 等微调模型，我们演示了这些模型如何使用基于语言的输入和输出有效地控制航天器。我们的方法将实时任务遥测集成到 LLM 处理的文本提示中，然后通过代理生成控制操作。结果引发了一场关于法学硕士在空间操作方面的潜力的讨论，超出了其名义上用于文本相关任务的范围。未来的工作旨在将这种方法扩展到其他空间控制任务，并评估不同法学硕士系列的表现。该代码可通过以下 URL 获取：\texttt{https://github.com/ARCLab-MIT/kspdg}。

...(Some other content)
```

然后是被过滤掉的内容，会显示它被过滤的原因（命中了哪个黑名单领域/所有领域都不在白名单当中）

```md
- [Vulnerability Handling of AI-Generated Code -- Existing Solutions and Open Challenges](https://arxiv.org/abs/2408.08549)
  - **标题**: 人工智能生成代码的漏洞处理——现有解决方案和开放挑战
  - **Filtered Reason**: cat:none of ['cs.SE'] in whitelist
```

## 进阶用法-配合飞书使用

得益于飞书文档提供的[多维表格](https://www.feishu.cn/hc/zh-CN/category/6933474572494716956-%E5%A4%9A%E7%BB%B4%E8%A1%A8%E6%A0%BC)功能，我们可以将论文信息转换为看板视图，以获得极尽丝滑的体验：

![alt text](readme/lark_demo.png)

文章的信息一览无余，我们还可以根据自己的兴趣对文章进行粗筛，然后阅读自己最感兴趣的文章，如此大大提升了我们的科研效率。

### 1.输出为 csv

下面这段代码将不会输出 markdown，而是输出一个 csv 文件。通过参数指定不输出表头，并且以制表符分隔，我们可以直接复制这个 csv 的内容到飞书云文档中。

```py
from arxiv_crawler import ArxivScraper
import asyncio
from datetime import date, timedelta

today = date.today()
recent = today - timedelta(days=1)

date_from = recent.strftime("%Y-%m-%d")
data_until = today.strftime("%Y-%m-%d")

scraper = ArxivScraper(
    date_from=date_from,
    date_until=data_until,
)
asyncio.run(scraper.fetch_all())
scraper.to_csv(csv_config=dict(delimiter="\t"), header=False)
```

### 2.建立飞书多维表格

可以使用这个[模板](https://sx43gev8evy.feishu.cn/wiki/YLM1weiT3iaDNqkwL3NcnAO0nUb?from=from_copylink)

表格视图就是我们 csv 文件的内容，其中 title 作为索引，interest 列是一个单选列，初始的 interest 只有两种，一种是 chosen，另一种是 filtered，分别对应于被保留和被过滤的文章。在阅读的过程中，可以根据自己的研究方向和兴趣进行筛选。categories 是文章在 arxiv 上的领域 tag，是一个多选列，飞书表格会自动将以逗号分隔的多选内容拆解开，实现自动识别。

![alt text](readme/lark_table_view.png)

切换到看板视图之后，就可以开始阅读和过滤文章了，这里我预设了 5 个等级的文章：

- CORE：表示 scaling law 这种经典文章，小同行的文章
- PEER：表示大同行的文章，相关领域的文章
- RELATED：表示相关领域的文章，或者相关内容的其他方法
- INTERESTING：和自己的科研领域方向较远，但比较有趣
- IRRELEVANT：比较 trival 的其他领域文章

![alt text](readme/lark_card_view.png)

### 3.复制 csv 内容

首先找到输出的文件，比如`output_llms/2024-08-19.csv`，记录一下它一共有多少行，全选并复制
![alt text](readme/csv_demo.png)

接下来复制一份数据表，但是只复制其结构

<div style="display: flex; justify-content: space-between;">
    <img src="readme/lark_copy_datasheet.png" alt="Image 1" style="width: 48%;height: auto"/>
    <img src="readme/lark_copy_datasheet2.png" alt="Image 2" style="width: 48%;height: auto"/>
</div>

在副本里插入和 csv 文件相等行数的内容。
![alt text](readme/lark_new_datasheet.png)

然后`ctrl+a`全选再`ctrl+v`粘贴到表格中即可！

接下来切换到看板视图开始阅读论文吧！

## 进阶用法-基于公布时间的增量更新

爬取论文的目的是为了获取第一手的学术视野，因漏召而错过好论文会带来很大的损失。为了避免漏召，我们可以加入大量关键词，以保证搜集全该领域的文章。

然而，还有一种情况是无法避免的：某论文于 A 日提交，但直到 A+x 日才被公开。由于 arxiv 中基于公开日期的搜索只支持**以月份为粒度**，因此我们无法精确的获得**某天公开**的所有论文。

### 增量内容的判断

虽然我们不能指定搜索某日更新的论文，不过我们可以爬取一整月的论文，然后将其按照**越新越前**的方式进行排序。第一次运行爬虫时，我们将所有文章加入数据库中。之后每次我们都从前往后将他们加入数据库，直到我们遇到已经存在于数据库中的论文。这就完成了所有增量内容的更新。

如果基于**首次提交日期**进行搜索，是无法做到这样的效果的，因为一篇文章可能在提交一年以后才被公开，没法进行定向检索。当然，如果一篇文章先公开，又在我们爬到它之前隐藏了怎么办？只能期待这种蛇皮文章应该不会太多。

### 公布时间的推断

上述方法虽然可以保证我们总是能爬取到最新的论文，但如果我们只按照论文首次提交日期索引，就没办法**读取**最新的论文。

例如8.19我们爬到了8.12，8.16，8.18的论文各一篇，我们要读这三篇文章就得重新导出这三天的论文列表。一种折衷方式是每次都把“当日之前提交，但在当天才公布”的论文打印出来作为补充列表。但这样也很麻烦。

于是，我们可以尝试“推断”论文的首次公布日期。虽然我们不知道公布时间，但结果是按照公布时间排序的，结合`首次提交日期<首次公布日期`的条件，以及arxiv在周末和假日不公布论文，就可以用下列代码进行推断：

```py
from arxiv_time import next_arxiv_update_day
def infer_announced_date(self):
    """
    推断文章的首次公布日期
    """
    announced_date = self.search_from_date
    # 公布日期从搜索开始起慢慢往后
    for paper in reversed(self.papers):
        if announced_date < paper.first_submitted_date:
            announced_date = paper.first_submitted_date
        announced_date = next_arxiv_update_day(announced_date)
        paper.first_announced_date = announced_date
```

值得注意的是，这种情况存在一个问题，假设我们之前的数据库已经更新到了2024-08-01，那么我们在更新08-02的文章时得到如下结果：

```py
# paper, announce（不可见）, submit（可见)
(paper1, "2024-08-02", "2024-08-02")
(paper2, "2024-08-02", "2024-08-01")
(paper3, "2024-08-02", "2024-08-02")
(paper4, "2024-08-02", "2024-08-01")
(paper5, "2024-08-01", "2024-08-01")
```

当我们进行增量更新时，爬取到paper5时，我们会发现它已经被更新过了，因此paper1-4都是新文章。

但是，paper4的公布时间是什么时候呢？如果我们上一次是在8.1当天晚上运行的代码，那么paper4完全可以是8.1当天才公布的。因为我们只知道paper4比paper5晚公布，且比自己的提交日期晚，这两个条件给出的下界都是8.1。

不过，如果我们上一次是在8.2运行的爬虫，这一次是在8.3，那就可以很确切的知道paper4是8.2才公布的了。因为我们知道当前的提交日期一定要晚于上一次数据库的更新日期。因此，我们可以加入一个新的字段update_time来进行判断。运行时可以将update_time从本地时间转换为美国东部时间，再跳过周末和节假日，就是下一个arxiv更新的时间了。

```py
# 从上一次更新的最新文章的时间
self.search_from_date = self.paper_db.newest_updatetime()
# 搜到的论文实际上是从该时间的下一个arxiv更新日期开始
self.search_from_date = next_arxiv_update_day(native_to_arxiv(self.search_from_date))
```

```sql
SELECT MAX(update_time) as max_updated_time
FROM papers
WHERE first_announced_date = (SELECT MAX(first_announced_date) FROM papers)
```

## 相关技术

要爬取 arxiv，可用的方法至少有三种。

1. 使用 arxiv API。通过 pyarxiv 库，可以轻松地使用 arxiv API 来获取论文信息，并且可以精确的指定 subcategory。但是这种方式无法通过时间范围进行筛选。
2. 使用 arxiv 的 OAI-PMH 数据。arxivscraper 库使用这种方式进行爬取，但它返回的 xml 十分巨大，并且其时间是最后一次更新元数据的时间，而非初始提交时间。由于[一些特性](https://info.arxiv.org/help/oa/index.html)，甚至当作者完全没有更新过论文时，也会返回该论文。这会让我们看到很多过时的文章。
3. 基于 arxiv 网页。可选择的网页有许多，arxiv 的网页格式非常简单。为了提供精确的时间范围，我选择使用[https://arxiv.org/search/advanced](https://arxiv.org/search/advanced)，此外爬取[https://arxiv.org/list/cs/recent](https://arxiv.org/list/cs/recent)是一个不错的方式。

要进行 google 翻译，关键是要计算出正确的 token，参考了[zotero 翻译插件](https://github.com/windingwind/zotero-pdf-translate/blob/main/src/modules/services/google.ts)的代码。
