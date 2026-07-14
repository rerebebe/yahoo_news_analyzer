"""
parser.py
"""

import re
from bs4 import BeautifulSoup


def parse_time_to_hours(time_str: str) -> float:
    # 文字轉為小時數
    time_str = time_str.strip()
    if "分鐘前" in time_str:
        minutes = int(re.search(r"\d+", time_str).group())
        return minutes / 60
    elif "小時前" in time_str:
        hours = int(re.search(r"\d+", time_str).group())
        return hours
    elif "昨天" in time_str:
        return 24.0
    elif "天前" in time_str:
        days = int(re.search(r"\d+", time_str).group())
        return days * 24
    # 如果是更久以前的日期格式，直接給一個很大的小時數使其被過濾
    return 999.0


def parse_card(card_html: str):
    # 解析單個新聞 HTML
    soup = BeautifulSoup(card_html, "html.parser")

    try:
        # 標題/連結
        h3_tag = soup.find("h3")
        if not h3_tag:
            return None
        a_tag = h3_tag.find("a")
        if not a_tag:
            return None

        title = a_tag.get_text(strip=True)
        link = a_tag.get("href", "")

        # 原始摘要 (抓不到)
        p_tag = soup.select_one("p.line-clamp-2") or soup.select_one("h3 + p")
        raw_summary = p_tag.get_text(strip=True) if p_tag else "無內文摘要"

        # 新聞來源/時間
        meta_div = soup.find("div", class_="text-px12")
        if not meta_div:
            return None

        meta_text = meta_div.get_text(strip=True)

        # 切割來源與時間
        if "・" in meta_text:
            source, time_str = meta_text.split("・", 1)
            source = source.strip()
            time_str = time_str.strip()
        else:

            source = meta_text
            time_str = ""

        # 超過 12 小時，直接過濾掉
        hours_ago = parse_time_to_hours(time_str)
        if hours_ago > 12:
            return None

        return {
            "news_title": title,
            "news_link": link,
            "news_source": source,
        }

    except Exception as e:
        print(f"解析發生錯誤: {e}")
        return None
