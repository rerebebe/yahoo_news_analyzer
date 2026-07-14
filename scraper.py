"""
scraper.py
"""

import random
import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from parser import parse_card


class YahooNewsScraper:
    TARGET_URL = "https://tw.news.yahoo.com/entertainment/archive/"

    STREAM_ID = "mfi-search-stream"

    def __init__(self, headless: bool = True, delay_range=(3, 6)):
        self.delay_range = delay_range
        self.driver = self._init_driver(headless)

    def _init_driver(self, headless: bool):

        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_bin = os.environ.get("CHROME_BIN")
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
        if chrome_bin:
            options.binary_location = chrome_bin

        if chromedriver_path:
            service = Service(chromedriver_path)
        else:
            service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            },
        )
        driver.set_page_load_timeout(20)
        return driver

    def scrape(self, max_results: int = 60, scroll_steps: int = 5):
        """直接抓取指定的分類頁面，採用階梯式邊滾邊抓策略"""
        print(f"正在載入: {self.TARGET_URL}")
        try:
            self.driver.get(self.TARGET_URL)
        except TimeoutException:
            print("頁面載入超過時間限制，但可能主要內容已經渲染完成，繼續嘗試抓取。")

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, self.STREAM_ID))
            )
        except TimeoutException:
            print(f"頁面未能在時間內載入（等待的 ID 是 '{self.STREAM_ID}'）。")
            return []

        unique_results = {}

        for i in range(scroll_steps):
            if len(unique_results) >= max_results:
                print(f"已達到目標數量 {max_results} 筆，提前結束滾動！")
                break

            # 分次往下滾動
            for _ in range(3):
                self.driver.execute_script(
                    "window.scrollBy(0, 1200);"
                )  # 每次往下滾 1200 像素

                time.sleep(0.6)  # 稍微停頓，讓瀏覽器反應

            # 滾完這一輪的小階梯後，在大停頓一下讓新新聞完全長出來
            time.sleep(random.uniform(2.5, 3.5))

            # 立刻抓取當前畫面上存在的「所有項目」
            current_items = self.driver.find_elements(
                By.CSS_SELECTOR, f"#{self.STREAM_ID} > li"
            )

            time.sleep(1)

            # 當場解析這批項目並塞進 dictionary
            for item in current_items:
                if len(unique_results) >= max_results:
                    break

                item_class = item.get_attribute("class") or ""

                if "stream-taboola-ad" in item_class:  # 過濾廣告
                    continue

                card_html = item.get_attribute("outerHTML")

                # print("有p tag嗎: ", "<p" in card_html)

                listing = parse_card(card_html)

                if listing and "news_link" in listing:
                    news_link = listing["news_link"]
                    if news_link not in unique_results:
                        unique_results[news_link] = listing

        # 將字典轉換回原本的 List 格式回傳給 main.py
        final_list = list(unique_results.values())
        print(f"=== 抓取結束！共取得 {len(final_list)} 則新聞資料 ===")
        return final_list

    def _infinite_scroll(self, steps: int = 5):
        for i in range(steps):
            print(f"scrolling.... ({i+1}/{steps})...")
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            print(
                f"給他時間load: {random.uniform(self.delay_range[0], self.delay_range[1])}"
            )
            time.sleep(random.uniform(self.delay_range[0], self.delay_range[1]))

    def close(self):
        self.driver.quit()

    def get_article_content(self, url: str) -> str:

        try:
            # 前往內文網址
            self.driver.get(url)

            # 畫面上任何一個帶有 mb-module-gap 的 p 出現就開工
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "p.mb-module-gap"))
                )
            except TimeoutException:
                pass

            # 撈出所有屬於新聞內文的 p tag (class: mb-module-gap)
            p_elements = self.driver.find_elements(By.CSS_SELECTOR, "p.mb-module-gap")

            # 4. 過濾掉末尾的「看更多」、「延伸閱讀」等無關文字
            valid_paragraphs = []
            for p in p_elements:
                text = p.text.strip()
                if not text:
                    continue

                p_class = p.get_attribute("class") or ""
                if "read-more-vendor" in p_class:
                    continue

                valid_paragraphs.append(text)

            # 組合內文
            full_text = " ".join(valid_paragraphs)

            # 防防爬蟲機制
            time.sleep(random.uniform(0.3, 0.7))

            return full_text if full_text else "無法讀取內文結構"

        except Exception as e:
            print(f"讀取內文失敗 ({url}): {str(e)}")
            return "讀取內文發生錯誤"
