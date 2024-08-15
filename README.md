# ARXIV_CRAWLER

这是一个高效，快捷的arXiv论文爬虫，它可以将指定时间范围，指定主题，包含指定关键词的论文信息爬取到本地，并且将其中的标题和摘要翻译成中文。

## 使用方法

1. 克隆本仓库到本地

```bash
git clone https://github.com/huiyeruzhou/arxiv_crawker.git
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

如果你不需要翻译，只需要注释掉
```py
asyncio.run(scraper.translate())
```
即可

## 结果示例

假设爬取了七天的论文，那么结果可能形如：
```bash
output_llm
├── 10 August, 2024.md
├── 11 August, 2024.md
├── 12 August, 2024.md
├── 13 August, 2024.md
├── 14 August, 2024.md
├── 8 August, 2024.md
└── 9 August, 2024.md
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
   