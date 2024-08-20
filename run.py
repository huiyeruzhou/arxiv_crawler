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
asyncio.run(scraper.translate())
scraper.output(meta=True)
scraper.paper_result.to_csv(csv_config=dict(delimiter="\t", header=False))
