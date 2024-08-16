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
  - Args:
    - date_from (str): 开始日期
    - date_until (str): 结束日期
    - category_blacklist (list, optional): 黑名单. Defaults to [].
    - category_whitelist (list, optional): 白名单. Defaults to ["cs.CV", "cs.AI", "cs.LG", "cs.CL"]. 
                                        如果一个文章的分类在黑名单中，且没有任何一个分类在白名单中，则被过滤掉
    - oprional_keywords (list, optional): 关键词, 各词之间关系为OR, 在标题/摘要中至少要出现一个关键词才会被爬取.
                                        Defaults to ["LLM", "language model", "multimodal", "finetuning", "GPT"].

   
- 如果你不需要翻译，只需要注释掉
```py
asyncio.run(scraper.translate())
```

- 输出文件名是根据日期生成的，可以使用`output`方法的`filename_format`参数修改日期格式，默认为`%Y-%m-%d`即形如`2024-08-08.md`。
```py
scraper.output(filename_format='%Y-%m-%d')
```

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

### Simplifying Translations for Children: Iterative Simplification Considering Age of Acquisition withLLMs
- **标题**: 简化儿童翻译：考虑法学硕士获得年龄的迭代简化
- **Categories**: cs.CL
- **摘要**: 近年来，神经机器翻译（NMT）已广泛应用于日常生活中。......
- **Date**: 8 August, 2024
- **URL**: https://arxiv.org/abs/2408.04217
- **Authors**: Masashi Oshika,Makoto Morishita,Tsutomu Hirao,Ryohei Sasano,Koichi Takeda
- **Abstract**: In recent years, neural machine translation (NMT) has been widely used in everyday life. ......

...(Some other content)

然后是被过滤掉的内容，会显示它被过滤的原因（命中了哪个黑名单领域）

- Are Social Sentiments Inherent inLLMs? An Empirical Study on Extraction of Inter-demographic Sentiments
  - **Reason**: cat:cs.CY **Categories**: cs.CL cs.CY
- Learning with Digital Agents: An Analysis based on the Activity Theory

## 相关技术

要爬取arxiv，可用的方法至少有三种。

1. 使用arxiv API。通过pyarxiv库，可以轻松地使用arxiv API来获取论文信息，并且可以精确的指定subcategory。但是这种方式无法通过时间范围进行筛选。
2. 使用arxiv的OAI-PMH数据。arxivscraper库使用这种方式进行爬取，但它返回的xml十分巨大，并且其时间是最后一次更新元数据的时间，而非初始提交时间。由于[一些特性](https://info.arxiv.org/help/oa/index.html)，甚至当作者完全没有更新过论文时，也会返回该论文。这会让我们看到很多过时的文章。
3. 基于arxiv网页。可选择的网页有许多，arxiv的网页格式非常简单。为了提供精确的时间范围，我选择使用[https://arxiv.org/search/advanced](https://arxiv.org/search/advanced)，此外爬取[https://arxiv.org/list/cs/recent](https://arxiv.org/list/cs/recent)是一个不错的方式。

要进行google翻译，关键是要计算出正确的token，参考了[zotero翻译插件](https://github.com/windingwind/zotero-pdf-translate/blob/main/src/modules/services/google.ts)的代码。
   