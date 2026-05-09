#!/usr/bin/env python3
"""
市場數據抓取模塊
抓取美股走向、國際匯率、台股現況等數據
"""

import json
import yfinance as yf
from datetime import datetime, timedelta, timezone
import logging
import sys

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_fetcher.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

class MarketDataFetcher:
    """市場數據抓取器"""
    
    def __init__(self):
        self.market_data = {
            'us_market': {},
            'tw_market': {},
            'exchange_rates': {},
            'timestamp': datetime.now(TW_TZ).isoformat()
        }
    
    def fetch_us_market(self):
        """抓取美股數據（S&P 500, 納斯達克, 道瓊）"""
        logger.info("正在抓取美股數據...")
        
        indices = {
            '^GSPC': 'S&P 500',      # 標普500
            '^IXIC': 'Nasdaq',       # 納斯達克
            '^DJI': 'Dow Jones',     # 道瓊
            '^VIX': 'VIX 恐懼指數'   # 波動率指數
        }
        
        try:
            for ticker, name in indices.items():
                data = yf.Ticker(ticker)
                hist = data.history(period='1d')
                
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else last_row['Close']
                    change = last_row['Close'] - prev_close
                    change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    self.market_data['us_market'][ticker] = {
                        'name': name,
                        'price': float(last_row['Close']),
                        'change': float(change),
                        'change_pct': float(change_pct),
                        'volume': int(last_row['Volume'])
                    }
                    
                    logger.info(f"  {name}: {last_row['Close']:.2f} ({change_pct:+.2f}%)")
        
        except Exception as e:
            logger.error(f"抓取美股數據出錯: {str(e)}")
            return False
        
        return True
    
    def fetch_exchange_rates(self):
        """抓取主要匯率（美元、人民幣、日圓）"""
        logger.info("正在抓取國際匯率...")
        
        rates = {
            'USDTWD=X': 'USD/TWD',   # 美元兌台幣
            'CNYUSD=X': 'CNY/USD',   # 人民幣兌美元
            'JPYUSD=X': 'JPY/USD',   # 日圓兌美元
        }
        
        try:
            for ticker, name in rates.items():
                data = yf.Ticker(ticker)
                hist = data.history(period='1d')
                
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else last_row['Close']
                    change = last_row['Close'] - prev_close
                    change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    self.market_data['exchange_rates'][ticker] = {
                        'name': name,
                        'rate': float(last_row['Close']),
                        'change': float(change),
                        'change_pct': float(change_pct)
                    }
                    
                    logger.info(f"  {name}: {last_row['Close']:.2f} ({change_pct:+.2f}%)")
        
        except Exception as e:
            logger.error(f"抓取匯率出錯: {str(e)}")
            return False
        
        return True
    
    def fetch_tw_market(self):
        """抓取台股數據 - 大盤指數及重點個股"""
        logger.info("正在抓取台股數據...")
        
        stocks = {
            '^TWII': '台灣加權指數',
            '2330.TW': '台積電',
            '2454.TW': '聯發科',
            '2317.TW': '鴻海',
            '1301.TW': '台塑',
            '2412.TW': '中華電'
        }
        
        try:
            for ticker, name in stocks.items():
                data = yf.Ticker(ticker)
                hist = data.history(period='5d')
                
                if not hist.empty:
                    last_row = hist.iloc[-1]
                    prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else last_row['Close']
                    change = last_row['Close'] - prev_close
                    change_pct = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    # 計算技術指標
                    ma_20 = hist['Close'].tail(20).mean() if len(hist) >= 20 else None
                    ma_60 = hist['Close'].tail(60).mean() if len(hist) >= 60 else None
                    
                    self.market_data['tw_market'][ticker] = {
                        'name': name,
                        'price': float(last_row['Close']),
                        'change': float(change),
                        'change_pct': float(change_pct),
                        'volume': int(last_row['Volume']),
                        'ma_20': float(ma_20) if ma_20 else None,
                        'ma_60': float(ma_60) if ma_60 else None
                    }
                    
                    logger.info(f"  {name}: {last_row['Close']:.2f} ({change_pct:+.2f}%)")
        
        except Exception as e:
            logger.error(f"抓取台股數據出錯: {str(e)}")
            return False
        
        return True
    
    def save_data(self, filename='data/market_data.json'):
        """保存市場數據到 JSON 文件"""
        try:
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.market_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 市場數據已保存到 {filename}")
            return True
        
        except Exception as e:
            logger.error(f"保存數據出錯: {str(e)}")
            return False
    
    def run(self):
        """執行完整的數據抓取流程"""
        logger.info("=" * 60)
        logger.info("開始執行市場數據抓取")
        logger.info("=" * 60)
        
        success = True
        success = self.fetch_us_market() and success
        success = self.fetch_exchange_rates() and success
        success = self.fetch_tw_market() and success
        
        if success:
            self.save_data()
            logger.info("✅ 所有數據抓取完成")
        else:
            logger.warning("⚠️ 部分數據抓取失敗")
        
        return success

if __name__ == '__main__':
    fetcher = MarketDataFetcher()
    success = fetcher.run()
    sys.exit(0 if success else 1)
