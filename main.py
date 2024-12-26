import yaml
from datetime import date, timedelta
from arxiv_crawler import ArxivScraper
from push_to_feishu import Push2Feishu
import asyncio
import os

if __name__ == "__main__":

    with open('config.yaml') as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    # 输出昨天更新的文章
    yesterday = date.today() - timedelta(days=1)

    categories = cfg['Categories']

    scraper = ArxivScraper(
        date_from=yesterday.strftime("%Y-%m-%d"),
        date_until=yesterday.strftime("%Y-%m-%d"),
        subject_list=cfg['Subject'],
        category_blacklist=(
            [] if categories['BlackList'] is None else categories['BlackList']
        ),
        category_whitelist=(
            [] if categories['WhiteList'] is None else categories['WhiteList']
        ),
        optional_keywords=cfg['Keywords'],
        trans_to=cfg['Tans_to'],
        proxy=None if cfg['Proxy']['Enable'] is False else cfg['Proxy']['Address'],
    )
    asyncio.run(scraper.fetch_all())
    scraper.to_markdown(output_dir=cfg['Output_Directory'], meta=True)
    scraper.to_csv(
        output_dir=cfg['Output_Directory'],
        header=False,
        csv_config=dict(delimiter="\t"),
    )

    # 推送到飞书
    feishu_cfg = cfg['Feishu']
    if feishu_cfg['Enable'] is True:
        push = Push2Feishu(feishu_cfg['App_ID'], feishu_cfg['App_Secret'], retry=1)
        csv_fname = os.path.join(
            cfg['Output_Directory'], f"{yesterday.strftime('%Y-%m-%d')}.csv"
        )
        push.to_feishu(csv_fname, feishu_cfg['User_ID'], feishu_cfg['include_filtered'])
