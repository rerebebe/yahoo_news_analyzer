"""
main.py
"""

import csv
import os
from scraper import YahooNewsScraper
from dotenv import load_dotenv

from llm_analyzer import LLMAnalyzer

load_dotenv()


def main():
    scraper = YahooNewsScraper(headless=True)
    analyzer = LLMAnalyzer()

    raw_news_list = scraper.scrape(max_results=60, scroll_steps=5)

    final_rows = []

    for idx, news in enumerate(raw_news_list):
        print(f"=== [{idx+1}/{len(raw_news_list)}] 正在處理：{news['news_title']} ===")

        # 呼叫Selenium 裡的 get_article_content 方法，點進去抓內文
        full_article_content = scraper.get_article_content(news["news_link"])

        # 如果抓不到內文，拿標題頂替
        context_for_llm = (
            full_article_content
            if len(full_article_content) > 10
            else news["news_title"]
        )

        # 取得 LLM 回傳的結果
        print(f"=== 文章內容: /n{context_for_llm} ===")
        llm_res = analyzer.analyze_news(news["news_title"], context_for_llm)

        # 塞入最終要寫入 CSV 的欄位
        final_rows.append(
            {
                "新聞標題": news["news_title"],
                "新聞連結": news["news_link"],
                "新聞來源": news["news_source"],
                "新聞內文摘要": llm_res.get("summary", "無法生成摘要"),
                "實體（人名/團體）": llm_res.get("entities", "無"),
                "是否為演唱會": llm_res.get("is_concert", "否"),
            }
        )

    # 寫入 CSV
    fields = [
        "新聞標題",
        "新聞連結",
        "新聞來源",
        "新聞內文摘要",
        "實體（人名/團體）",
        "是否為演唱會",
    ]

    with open("yahoo_news_results.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(final_rows)

    print("CSV產出!")
    scraper.close()


if __name__ == "__main__":
    main()
