# Yahoo 娛樂新聞爬蟲 + LLM 智慧分析

使用 Selenium 爬取 Yahoo 娛樂新聞封存頁的近期新聞，過濾出 12 小時內的項目，
點進內文後交給 Gemini 產生中文摘要、擷取人名/團體實體，並判斷是否與演唱會
相關，最終輸出成 CSV。

## 專案結構

```
.
├── main.py               # 入口點：調度爬蟲、LLM 分析、輸出 CSV
├── scraper.py             # Selenium 爬蟲：抓取新聞列表與內文
├── parser.py              # 解析新聞卡片 HTML、關鍵字快速判斷、12 小時時間過濾
├── llm_analyzer.py        # 呼叫 Gemini 做摘要 / 實體擷取 / 演唱會判斷
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example           # 環境變數範本，複製成 .env 後填入你的金鑰
├── .gitignore
└── yahoo_news_results.csv # 範例執行結果
```

## 資料清洗

- **廣告過濾**：`scraper.py` 的 `scrape()` 會跳過帶有 `stream-taboola-ad`
  class 的列表項目，避免把廣告卡片當成新聞抓進來。
- **去重**：`scrape()` 用 `news_link`（新聞網址）當 key 存進字典，同一則新聞
  在滾動過程中重複出現也只會保留一份。
- **來源欄位清洗**：`parser.py` 的 `parse_card()` 用「・」切開來源與時間字串
  （例如「中時新聞網・6小時前」），只取「中時新聞網」，去除時間後綴。
- **12 小時時間過濾**：`parse_time_to_hours()` 把「10 分鐘前」「6 小時前」
  「昨天」等相對時間字串換算成小時數，超過 12 小時的新聞直接捨棄。
- **內文雜訊過濾**：`scraper.py` 的 `get_article_content()` 抓取內文段落時，
  會跳過帶有 `read-more-vendor` class 的段落——這是 Yahoo 模板裡「更多OOO報導」
  這類與本文無關的延伸閱讀區塊。
- **LLM 回傳格式清洗**：`llm_analyzer.py` 會去除 Gemini 回傳內容中可能夾帶的
  ` ```json ` Markdown 標記，並把「無提及實體」統一正規化成 `Null`，確保
  CSV 欄位格式一致。

## 本機執行

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env # 編輯 .env，填入你的 GOOGLE_API_KEY

python main.py
```

`main.py` 開頭會呼叫 `load_dotenv()`，所以 `.env` 裡的 `GOOGLE_API_KEY` 會自動
被讀進環境變數，Gemini 呼叫（`langchain-google-genai`）會自動抓到它，不需要
手動 `export`。

執行完成後，結果會輸出到專案根目錄下的 `yahoo_news_results.csv`。

## Docker 建置與執行

```bash
docker build -t yahoo-news-analyzer .

docker run --rm --env-file .env -v "$(pwd):/app" yahoo-news-analyzer
```

- `--env-file .env`：在執行期把 `GOOGLE_API_KEY` 傳進容器，金鑰不會被打包進映像。
- `-v "$(pwd):/app"`：把專案資料夾掛載進容器，執行完成後 `yahoo_news_results.csv`
  會直接出現在你的主機目錄，不需要額外複製。

映像內建 Google Chrome（透過官方 apt 套件安裝）；`scraper.py` 使用
`webdriver-manager`，會在執行時自動下載與已安裝 Chrome 版本相符的
ChromeDriver，因此不需要在 Dockerfile 裡手動釘選 driver 版本。

## 輸出欄位

| 欄位              | 說明                                          |
| ----------------- | --------------------------------------------- |
| 新聞標題          | 文章標題                                      |
| 新聞連結          | 文章網址                                      |
| 新聞來源          | 來源媒體名稱（已去除「・6小時前」等時間後綴） |
| 新聞內文摘要      | Gemini 生成的中文摘要                         |
| 實體（人名/團體） | 多個以「，」分隔；無提及則為 Null             |
| 是否為演唱會      | 是 / 否                                       |

## 已知注意事項

- **Gemini 模型**：目前使用 `gemini-3.1-flash-lite`（GA 版本）。若之後遇到模型
  404 或額度問題，可以到 test_test.py 確認你的 API key 實際可用的模型清單，
  再回頭調整 `llm_analyzer.py` 裡的模型名稱。
- **抓取筆數**：`scraper.py` 裡 `scrape()` 的 `max_results` 參數預設為 60 筆。
  若想抓取更多或更少新聞，請自行調整 `main.py` 呼叫
  `scraper.scrape(max_results=...)` 時傳入的數值。
