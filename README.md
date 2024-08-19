# ARXIV_CRAWLER

这是一个高效，快捷的arXiv论文爬虫，它可以将指定时间范围，指定主题，包含指定关键词的论文信息爬取到本地，并且将其中的标题和摘要翻译成中文。

## 使用方法

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

```bash
python arxiv_crawler.py
```

这代码会将最近**一天**内大模型相关的论文信息爬取到本地，注意category白名单并不起作用，因为还没有设置黑名单。要广泛的爬取论文，可以添加不感兴趣的category到黑名单中，并用白名单进行豁免。

4. 用法说明

- 要修改爬取的时间范围，领域，关键字，请参考`arxiv_crawler.py`中`ArxivScraper`类的注释：
  一个文件被爬取到的条件是：首次提交时间在`date_from`和`date_until`之间，并且包含至少一个关键词。
  一个文章被详细展示（不被过滤）的条件是：至少有一个领域在白名单中，并且没有任何一个领域在黑名单中。
  - Args:
    - date_from (str): 开始日期
    - date_until (str): 结束日期
    - category_blacklist (list, optional): 黑名单. Defaults to [].
    - category_whitelist (list, optional): 白名单. Defaults to ["cs.CV", "cs.AI", "cs.LG", "cs.CL"]. 
    - optional_keywords (list, optional): 关键词, 各词之间关系为OR, 在标题/摘要中至少要出现一个关键词才会被爬取.
                                        Defaults to ["LLM", "language model", "multimodal", "finetuning", "GPT"].

   
- 如果你不需要翻译，只需要注释掉
```py
asyncio.run(scraper.translate())
```

- 输出文件名是根据日期生成的，可以使用`output`方法的`filename_format`参数修改日期格式，默认为`%Y-%m-%d`即形如`2024-08-08.md`。
```py
scraper.output(filename_format='%Y-%m-%d')
```

- 如果你希望将一条元信息添加到输出文件中，可以使用`output`方法的`meta`参数。
```py
scraper.output(meta=True)
```

元信息形如：
> 本文由 [https://github.com/huiyeruzhou/arxiv_crawler](https://github.com/huiyeruzhou/arxiv_crawler) 自动生成
>
> 领域白名单: cs.CV;cs.AI;cs.LG;cs.CL;cs.IR
> 关键词： LLM, LLMs, language+model, language+models, multimodal, finetuning, GPT
## 结果示例

假设爬取了七天的论文，那么结果可能形如：
```bash
output_llm
├── 2024-08-08.md
├── 2024-08-09.md
├── 2024-08-10.md
├── 2024-08-11.md
├── 2024-08-12.md
├── 2024-08-13.md
└── 2024-08-14.md
```

其中被保留的内容形如：

# 论文全览：2024-08-16

共有57篇相关领域论文，另有6篇其他论文

## 人工智能(cs.AI:Artificial Intelligence)

### [Fine-tuningLLMsfor Autonomous Spacecraft Control: A Case Study Using Kerbal Space Program](https://arxiv.org/abs/2408.08676)
> **Authors**: Alejandro Carrasco,Victor Rodriguez-Fernandez,Richard Linares
> **First submission**: 16 August, 2024
- **标题**: 用于自主航天器控制的微调LLM：使用坎巴拉太空计划的案例研究
- **领域**: 人工智能;天体物理学仪器和方法
- **摘要**: 最近出现的趋势是使用大型语言模型（LLM）作为自主代理，根据用户文本提示的内容采取行动。本研究探索使用微调大型语言模型 (LLM) 进行自主航天器控制，并使用坎巴拉太空计划微分游戏套件 (KSPDG) 作为测试环境。由于模拟能力和数据不足，传统的强化学习（RL）方法在该领域面临局限性。通过利用 LLM，特别是 GPT-3.5 和 LLaMA 等微调模型，我们演示了这些模型如何使用基于语言的输入和输出有效地控制航天器。我们的方法将实时任务遥测集成到LLM处理的文本提示中，然后通过代理生成控制操作。结果引发了一场关于法学硕士在空间操作方面的潜力的讨论，超出了其名义上用于文本相关任务的范围。未来的工作旨在将这种方法扩展到其他空间控制任务，并评估不同法学硕士系列的表现。该代码可通过以下 URL 获取：\texttt{https://github.com/ARCLab-MIT/kspdg}。


...(Some other content)

然后是被过滤掉的内容，会显示它被过滤的原因（命中了哪个黑名单领域/所有领域都不在白名单当中）

- [Vulnerability Handling of AI-Generated Code -- Existing Solutions and Open Challenges](https://arxiv.org/abs/2408.08549)
  - **标题**: 人工智能生成代码的漏洞处理——现有解决方案和开放挑战
  - **Filtered Reason**: cat:none of ['cs.SE'] in whitelist

## 相关技术

要爬取arxiv，可用的方法至少有三种。

1. 使用arxiv API。通过pyarxiv库，可以轻松地使用arxiv API来获取论文信息，并且可以精确的指定subcategory。但是这种方式无法通过时间范围进行筛选。
2. 使用arxiv的OAI-PMH数据。arxivscraper库使用这种方式进行爬取，但它返回的xml十分巨大，并且其时间是最后一次更新元数据的时间，而非初始提交时间。由于[一些特性](https://info.arxiv.org/help/oa/index.html)，甚至当作者完全没有更新过论文时，也会返回该论文。这会让我们看到很多过时的文章。
3. 基于arxiv网页。可选择的网页有许多，arxiv的网页格式非常简单。为了提供精确的时间范围，我选择使用[https://arxiv.org/search/advanced](https://arxiv.org/search/advanced)，此外爬取[https://arxiv.org/list/cs/recent](https://arxiv.org/list/cs/recent)是一个不错的方式。

要进行google翻译，关键是要计算出正确的token，参考了[zotero翻译插件](https://github.com/windingwind/zotero-pdf-translate/blob/main/src/modules/services/google.ts)的代码。
   