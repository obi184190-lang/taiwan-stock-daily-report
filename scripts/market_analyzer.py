#!/usr/bin/env python3
"""
AI 市場分析模塊
使用 Claude API 生成專業的國際台股聯動分析報告
"""

import json
import os
import sys
import logging
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
        
        prompt = f"""你是一位資深的金融市場分析師，專門分析台灣股市的走勢和類股輪動。

今天是 {datetime.now(TW_TZ).strftime('%Y年%m月%d日 %H:%M')} (台灣時間)

【最新市場數據】
{market_summary}

【分析任務】
請根據上述市場數據，生成一份「國際台股聯動日報」。報告應該包含以下結構：

## 📊 國際台股聯動日報
**日期**：{datetime.now(TW_TZ).strftime('%Y年%m月%d日')}

### 🌍 昨晚國際情勢與美股走向
- 分析美股三大指數（S&P 500、納斯達克、道瓊）的表現
- 說明影響美股的關鍵因素（地緣政治、經濟數據、Fed 政策等）
- 評估美股走勢對台股的潛在影響

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
                model="claude-opus-4-20250805",
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            self.analysis_report = message.content[0].text
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
