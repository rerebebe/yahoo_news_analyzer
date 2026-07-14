"""
llm_analyzer.py
"""

import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI

PROMPT_TEMPLATE = """你是一個專業的娛樂新聞助理。請根據提供的新聞標題與內容摘要，精確提取並分析出指定欄位。

新聞標題：{title}
新聞內容：{original_summary}

請嚴格遵循以下 JSON 格式回傳，請只回傳 JSON 內容本身，絕對不要包含任何額外的 Markdown 標記（如 ```json 等文字）：
{{
    "summary": "請對這篇新聞進行簡短流暢的中文摘要說明",
    "entities": "找出新聞中提到的人名、團體名或樂團名（如：五月天、周杰倫）。若有多個請用「，」隔開。如果完全沒有提到任何人名或團體，請填入 null",
    "is_concert": "判斷這篇新聞是否與「演唱會」或「音樂會」相關議題有關？如果是請填入 '是'，否則填入 '否'"
}}"""


class LLMAnalyzer:
    def __init__(self):
        # 選模型
        self.llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

    def _extract_text(self, content) -> str:

        if isinstance(content, str):  # if content is a string, return True
            return content
        if isinstance(content, list) and len(content) > 0:
            if isinstance(content[0], dict) and "text" in content[0]:
                return content[0]["text"]
        return str(content)

    def analyze_news(self, title: str, original_summary: str) -> dict:
        try:
            # 填資料到 Prompt
            formatted_prompt = PROMPT_TEMPLATE.format(
                title=title, original_summary=original_summary
            )

            # 呼叫 Gemini
            response = self.llm.invoke(formatted_prompt)

            print(f"回傳true就好: {bool(response)}")

            # 提取純文字內容
            raw_text = self._extract_text(response.content)

            # 清理並解析 JSON
            clean_content = raw_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_content)

            print(f"LLM 回傳的 JSON 內容: {data}")

            entities = data.get("entities")
            if entities is None or str(entities).lower() == "null":
                entities = "Null"

            return {
                "summary": data.get("summary", ""),
                "entities": entities,
                "is_concert": data.get("is_concert", "否"),
            }

        except Exception as e:

            print(f"LLM 分析出錯: {e}")
            return {
                "summary": original_summary,
                "entities": "Null",
                "is_concert": "否",
            }
