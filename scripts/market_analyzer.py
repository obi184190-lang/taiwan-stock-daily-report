#!/usr/bin/env python3
"""
AI 市場分析模塊
使用 Claude API 生成專業的國際台股聯動分析報告
"""

import json
import os
import sys
import logging
import re
from datetime import datetime, timezone, timedelta
from anthropic import Anthropic

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_analyzer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# 激進清理函數 - 移除美股冗餘數據說明
# ============================================================

def aggressive_clean_us_market_analysis(text: str) -> str:
    """
    激進清理美股分析中的冗餘數據說明段落
    """
    
    aggressive_patterns = [
        r"變動幅度均掛零[^。]*?[。]?",
        r"變動幅度均為零[^。]*?[。]?",
        r"當日變動幅度均為零[^。]*?[。]?",
        r"當日變動幅度均[^。]*?[。]?",
        r"[^。]*?變動幅度均[^。]*?[。][^。]*?這[代表|通常代表][^。]*?[。]",
        r"[^。]*?變動幅度均[^。]*?[。][^。]*?或數據尚未更新[^。]*?[。]",
        r"[^。]*?變動幅度均[^。]*?[。][^。]*?市場處於[^。]*?[。]",
        r"這代表昨日為美股休市日[^。]*?[。]?",
        r"代表昨日為美股休市[^。]*?[。]?",
        r"代表昨日為美國假日[^。]*?[。]?",
        r"昨日為美股休市日[^。]*?[。]?",
        r"數據尚未更新至最新收盤[^。]*?[。]?",
        r"或數據尚未更新[^。]*?[。]?",
        r"資料更新延遲的狀態[^。]*?[。]?",
        r"資料更新延遲[^。]*?[。]?",
        r"數據尚未更新[^。]*?[。]?",
        r"這通常代表數據為前一[^。]*?交易日[^。]*?[。]?",
        r"代表數據為前一[^。]*?交易日[^。]*?[。]?",
        r"前一個交易日的收盤留存[^。]*?[。]?",
        r"前一交易日的收盤[^。]*?[。]?",
        r"市場處於靜止狀態[^。]*?[。]?",
        r"市場處於假日[^。]*?[。]?",
        r"市場處於[^。]*?狀態[^。]*?[。]?",
        r"並無新的價格訊號[^。]*?[。]?",
    ]
    
    cleaned = text
    
    for pattern in aggressive_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
    
    cleaned = re.sub(r'\n\s*\n+', '\n\n', cleaned)
    cleaned = re.sub(r'(\n\s*){3,}', '\n\n', cleaned)
    cleaned = re.sub(r'\s+([。，！？])', r'\1', cleaned)
    cleaned = re.sub(r'^\s+', '', cleaned)
    cleaned = re.sub(r'\s+$', '', cleaned)
    cleaned = re.sub(r'^儘管如此[，，]', '', cleaned)
    cleaned = re.sub(r'^\s*儘管如此', '', cleaned)
    
    return cleaned.strip()

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

class MarketAnalyzer:
    """AI 市場分析器"""
    
    def __init__(self):
        self.client = Anthropic()
        self.market_data = self._load_market_data()
        self.analysis_report = None
    
    def _load_market_data(self):
        """載入市場數據"""
        try:
            with open('data/market_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("市場數據文件未找到，將使用空數據")
            return {}
    
    def _prepare_prompt(self):
        """準備分析提示詞"""
        
        market_summary = json.dumps(self.market_data, ensure_ascii=False, indent=2)
        
        prompt = f"""你是一位資深的金融市場分析師，專門分析台灣股市的走勢和股股輪動。請使用純文字格式輸出，不要使用任何 HTML 標籤（如 <b>、<u> 等），也不要使用 Markdown 語法（如 **粗體**）。

今天是 {datetime.now(TW_TZ).strftime('%Y年%m月%d日 %H:%M')} (台灣時間)

【最新市場數據】
{market_summary}

【分析任務】
請根據上述市場數據，生成一份「國際台股聯動日報」。報告應該包含以下結構：

## 📊 國際台股聯動日報
**日期**：{datetime.now(TW_TZ).strftime('%Y年%m月%d日')}

### 🌍 昨晚國際情勢與美股走向

【重要提示】
如果美股數據顯示變動幅度為零，這是正常現象（假日或數據延遲）。
請「永遠不要」說以下內容：
- 「變動幅度均為零」
- 「這代表昨日為美股休市日」
- 「數據為前一交易日」
- 任何關於「數據延遲」的說明

這些都是廢話。請直接分析當前報價的意義，不要解釋為什麼沒有變動。

分析要點：
- 美股三大指數（S&P 500、納斯達克、道瓊）的當前水位
- 這些點位在歷史上的相對位置（高位/中位/低位）
- 反映的市場情緒與投資信心
- 可能的推動因素（地緣政治、經濟數據、Fed 政策等）
- 對台股的潛在影響

記住：即使數據有延遲，根據現有報價的分析仍然有價值。

### 💱 國際匯率變動分析
- 說明主要匯率（USD/TWD、CNY/USD、JPY/USD）的變化
- 分析匯率變動對台股及產業的影響
- 重點說明美元兌台幣匯率的涵義

### 📈 今日台股現況分析
- 台灣加權指數的開盤、走勢、技術面
- 大盤關鍵位置（支撐、壓力）
- 成交量、籌碼面分析
- 與美股的同步性判斷

### 🔄 類股輪動走向
- 重點台股龍頭個股的表現（台積電、聯發科、鴻海等）
- 分析哪些產業板塊領漲/領跌
- 資金流向分析（進場/出場產業）
- 類股輪動的邏輯與後市預期

### 🎯 技術面與後市展望
- 短期技術面評估（支撐、壓力、趨勢）
- 風險提示與注意事項
- 短期操作建議與觀察重點

### 💡 核心投資機會與風險
- 當前最值得關注的投資機會
- 需要防範的風險因素
- 明日重點觀察項目

【報告要求】
1. 語氣專業、嚴謹、信任感強
2. 數據支撐：引用具體的價格、百分比、指數
3. 邏輯清晰：從國際→台股→類股逐層分析
4. 篇幅適中：2000-3000 字，便於朗讀
5. 中文表達：用繁體中文，避免過於複雜的用語
6. 格式：使用 markdown 格式，便於後續轉換為語音

請生成完整的分析報告。"""
        
        return prompt
    
    def generate_analysis(self):
        """使用 Claude API 生成分析報告"""
        logger.info("正在生成 AI 市場分析報告...")
        
        try:
            prompt = self._prepare_prompt()
            
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            self.analysis_report = message.content[0].text

            self.analysis_report = aggressive_clean_us_market_analysis(self.analysis_report)
            logger.info("✅ 冗餘內容已清理")
            
            logger.info("✅ AI 分析報告生成成功")
            return True
        
        except Exception as e:
            logger.error(f"生成分析報告失敗: {str(e)}")
            return False
    
    def save_report(self, filename='data/analysis_report.md'):
        """保存報告到文件"""
        try:
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.analysis_report)
            
            logger.info(f"✅ 分析報告已保存到 {filename}")
            return True
        
        except Exception as e:
            logger.error(f"保存報告失敗: {str(e)}")
            return False
    
    def get_report_summary(self, max_chars=500):
        """取得報告摘要（用於 Telegram 文字預覽）"""
        if not self.analysis_report:
            return ""
        
        lines = self.analysis_report.split('\n')
        summary = []
        char_count = 0
        
        for line in lines:
            if char_count + len(line) > max_chars:
                summary.append("...")
                break
            summary.append(line)
            char_count += len(line)
        
        return '\n'.join(summary)
    
    def run(self):
        """執行完整的分析流程"""
        logger.info("=" * 60)
        logger.info("開始執行市場分析")
        logger.info("=" * 60)
        
        if not self.generate_analysis():
            logger.error("❌ 分析報告生成失敗")
            return False
        
        if not self.save_report():
            logger.error("❌ 報告保存失敗")
            return False
        
        logger.info("✅ 市場分析完成")
        return True

if __name__ == '__main__':
    analyzer = MarketAnalyzer()
    success = analyzer.run()
    sys.exit(0 if success else 1)
