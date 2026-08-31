#!/usr/bin/env python3
"""
市場數據抓取模塊 v2
抓取美股走向、國際匯率、台股現況等數據

v2 修正項目：
  1. 成交量單位：yfinance 回傳「股數」，台股一律轉為「張」(// 1000)
  2. 大盤成交金額：改用證交所 FMTQIK 官方資料（億元），yfinance 僅作備援
  3. 前收價：拉長歷史區間，確保 iloc[-2] 取得到真正的前一交易日
  4. 均線：period 拉長到 6 個月，MA5/MA20/MA60 才算得出來（原本永遠是 None）
  5. 所有數值欄位名稱直接帶單位，避免下游 AI 誤讀
"""

import json
import os
import sys
import logging
from datetime import datetime, timedelta, timezone

import requests
import yfinance as yf

# ---------------------------------------------------------------- 基礎設定

TW_TZ = timezone(timedelta(hours=8))
SHARES_PER_LOT = 1000          # 台股 1 張 = 1000 股
HTTP_TIMEOUT = 15

os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_fetcher.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 證交所每日市場成交資訊
TWSE_FMTQIK = 'https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK'
TWSE_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json',
}

# 合理區間，用來在 log 示警（不寫進 JSON，避免 AI 拿去寫「數據異常」的廢話）
SANITY_TURNOVER_BILLION = (1500, 20000)   # 台股單日成交金額（億元）


# ---------------------------------------------------------------- 小工具

def _num(value, default=None):
    """把 '1,234.56' / '--' / None 轉成 float"""
    if value is None:
        return default
    try:
        return float(str(value).replace(',', '').replace('%', '').strip())
    except (ValueError, AttributeError):
        return default


def _round(value, digits=2):
    return round(float(value), digits) if value is not None else None


def _history(ticker, period, interval='1d'):
    """抓歷史資料，失敗回 None"""
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=interval)
        if hist is None or hist.empty:
            logger.warning(f"  {ticker}: 無歷史資料")
            return None
        return hist
    except Exception as e:
        logger.warning(f"  {ticker}: 抓取失敗 - {e}")
        return None


def _quote(hist):
    """
    從歷史資料算出當前價、前收價、漲跌。
    需要至少 2 筆，否則不編造前收價（回 None，寧可缺資料也不要假資料）。
    """
    if hist is None or len(hist) < 2:
        return None

    last = hist.iloc[-1]
    prev = hist.iloc[-2]

    close = float(last['Close'])
    prev_close = float(prev['Close'])
    change = close - prev_close
    change_pct = (change / prev_close * 100) if prev_close else 0.0

    return {
        'price': _round(close),
        'prev_close': _round(prev_close),
        'change': _round(change),
        'change_pct': _round(change_pct),
        'date': hist.index[-1].strftime('%Y-%m-%d'),
        'prev_date': hist.index[-2].strftime('%Y-%m-%d'),
        'raw_volume': float(last['Volume']) if 'Volume' in last else None,
    }


def _moving_averages(hist, windows=(5, 20, 60)):
    """算均線；資料不足的窗格回 None，不用短資料硬湊"""
    out = {}
    closes = hist['Close']
    for w in windows:
        out[f'ma{w}'] = _round(closes.tail(w).mean()) if len(closes) >= w else None
    return out


# ---------------------------------------------------------------- 證交所大盤

def fetch_twse_market_stats(days_back=10):
    """
    證交所 FMTQIK：每日市場成交資訊。
    欄位順序：[日期, 成交股數, 成交金額, 成交筆數, 發行量加權股價指數, 漲跌點數]
    金額單位為「元」，成交股數單位為「股」。
    往回試最多 days_back 天，避開假日與尚未更新的情況。
    """
    now = datetime.now(TW_TZ)

    for i in range(days_back):
        day = now - timedelta(days=i)
        try:
            resp = requests.get(
                TWSE_FMTQIK,
                params={'date': day.strftime('%Y%m%d'), 'response': 'json'},
                headers=TWSE_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
            payload = resp.json()
        except Exception as e:
            logger.warning(f"  證交所查詢 {day:%Y%m%d} 失敗: {e}")
            continue

        if payload.get('stat') != 'OK' or not payload.get('data'):
            continue

        rows = payload['data']
        latest = rows[-1]
        prev = rows[-2] if len(rows) > 1 else None

        turnover_yuan = _num(latest[2])
        shares = _num(latest[1])
        index_close = _num(latest[4])
        index_change = _num(latest[5])

        if turnover_yuan is None or index_close is None:
            continue

        prev_close = None
        if index_change is not None:
            prev_close = index_close - index_change
        elif prev:
            prev_close = _num(prev[4])

        result = {
            'date': latest[0],
            'index_close': _round(index_close),
            'index_prev_close': _round(prev_close),
            'index_change': _round(index_change),
            'index_change_pct': _round(index_change / prev_close * 100)
                                if (index_change is not None and prev_close) else None,
            'turnover_billion_twd': _round(turnover_yuan / 1e8),
            'volume_lots': int(shares // SHARES_PER_LOT) if shares else None,
            'source': 'TWSE_FMTQIK',
        }

        lo, hi = SANITY_TURNOVER_BILLION
        if result['turnover_billion_twd'] and not (lo <= result['turnover_billion_twd'] <= hi):
            logger.warning(
                f"  ⚠️ 大盤成交金額 {result['turnover_billion_twd']} 億元 "
                f"超出合理區間 {lo}-{hi}，請人工複核"
            )

        logger.info(
            f"  加權指數({result['date']}): {result['index_close']} "
            f"({result['index_change_pct']:+.2f}%) "
            f"成交 {result['turnover_billion_twd']:,.0f} 億元"
            if result['index_change_pct'] is not None else
            f"  加權指數({result['date']}): {result['index_close']}"
        )
        return result

    logger.warning("  證交所資料取得失敗，將改用 yfinance 備援")
    return None


# ---------------------------------------------------------------- 主類別

class MarketDataFetcher:
    """市場數據抓取器"""

    US_INDICES = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'Nasdaq',
        '^DJI': 'Dow Jones',
        '^SOX': '費城半導體指數',
        '^VIX': 'VIX 恐懼指數',
    }

    FX_PAIRS = {
        'USDTWD=X': 'USD/TWD',
        'CNYUSD=X': 'CNY/USD',
        'JPYUSD=X': 'JPY/USD',
        'DX-Y.NYB': '美元指數 DXY',
    }

    TW_STOCKS = {
        '2330.TW': '台積電',
        '2454.TW': '聯發科',
        '2317.TW': '鴻海',
        '1301.TW': '台塑',
        '2412.TW': '中華電',
    }

    def __init__(self):
        self.market_data = {
            'us_market': {},
            'tw_market': {},
            'exchange_rates': {},
            'timestamp': datetime.now(TW_TZ).isoformat(),
        }

    # ------------------------------------------------------------ 美股

    def fetch_us_market(self):
        """美股指數。period 拉長到 1mo，確保取得到真正的前一交易日收盤"""
        logger.info("正在抓取美股數據...")
        ok = False

        for ticker, name in self.US_INDICES.items():
            hist = _history(ticker, period='1mo')
            quote = _quote(hist)
            if not quote:
                continue

            self.market_data['us_market'][ticker] = {
                'name': name,
                'price': quote['price'],
                'prev_close': quote['prev_close'],
                'change': quote['change'],
                'change_pct': quote['change_pct'],
                'trade_date': quote['date'],
                'prev_trade_date': quote['prev_date'],
                'volume_shares': int(quote['raw_volume']) if quote['raw_volume'] else None,
                **_moving_averages(hist),
            }
            ok = True
            logger.info(f"  {name}: {quote['price']} ({quote['change_pct']:+.2f}%)")

        return ok

    # ------------------------------------------------------------ 匯率

    def fetch_exchange_rates(self):
        logger.info("正在抓取國際匯率...")
        ok = False

        for ticker, name in self.FX_PAIRS.items():
            hist = _history(ticker, period='1mo')
            quote = _quote(hist)
            if not quote:
                continue

            self.market_data['exchange_rates'][ticker] = {
                'name': name,
                'rate': quote['price'],
                'prev_rate': quote['prev_close'],
                'change': quote['change'],
                'change_pct': quote['change_pct'],
                'trade_date': quote['date'],
                **_moving_averages(hist, windows=(20,)),
            }
            ok = True
            logger.info(f"  {name}: {quote['price']} ({quote['change_pct']:+.2f}%)")

        return ok

    # ------------------------------------------------------------ 台股

    def fetch_tw_market(self):
        """
        大盤走證交所官方資料（成交金額為億元）；
        個股走 yfinance，period='6mo' 讓 MA5/20/60 都算得出來，成交量一律轉張。
        """
        logger.info("正在抓取台股數據...")
        ok = False

        # --- 大盤 ---
        twse = fetch_twse_market_stats()
        if twse:
            index_hist = _history('^TWII', period='6mo')
            mas = _moving_averages(index_hist) if index_hist is not None else {}
            self.market_data['tw_market']['^TWII'] = {
                'name': '台灣加權指數',
                'price': twse['index_close'],
                'prev_close': twse['index_prev_close'],
                'change': twse['index_change'],
                'change_pct': twse['index_change_pct'],
                'trade_date': twse['date'],
                'turnover_billion_twd': twse['turnover_billion_twd'],
                'volume_lots': twse['volume_lots'],
                'data_source': twse['source'],
                **mas,
            }
            ok = True
        else:
            hist = _history('^TWII', period='6mo')
            quote = _quote(hist)
            if quote:
                self.market_data['tw_market']['^TWII'] = {
                    'name': '台灣加權指數',
                    'price': quote['price'],
                    'prev_close': quote['prev_close'],
                    'change': quote['change'],
                    'change_pct': quote['change_pct'],
                    'trade_date': quote['date'],
                    'prev_trade_date': quote['prev_date'],
                    'turnover_billion_twd': None,
                    'volume_lots': int(quote['raw_volume'] // SHARES_PER_LOT)
                                   if quote['raw_volume'] else None,
                    'data_source': 'yfinance_fallback',
                    **_moving_averages(hist),
                }
                ok = True
                logger.warning("  大盤成交金額不可得（yfinance 備援模式）")

        # --- 個股 ---
        for ticker, name in self.TW_STOCKS.items():
            hist = _history(ticker, period='6mo')
            quote = _quote(hist)
            if not quote:
                continue

            volume_lots = int(quote['raw_volume'] // SHARES_PER_LOT) if quote['raw_volume'] else None

            vol_series = hist['Volume']
            vol_ma20_lots = (int(vol_series.tail(20).mean() // SHARES_PER_LOT)
                             if len(vol_series) >= 20 else None)
            volume_ratio = (_round(volume_lots / vol_ma20_lots)
                            if volume_lots and vol_ma20_lots else None)

            self.market_data['tw_market'][ticker] = {
                'name': name,
                'price': quote['price'],
                'prev_close': quote['prev_close'],
                'change': quote['change'],
                'change_pct': quote['change_pct'],
                'trade_date': quote['date'],
                'prev_trade_date': quote['prev_date'],
                'volume_lots': volume_lots,
                'volume_ma20_lots': vol_ma20_lots,
                'volume_ratio': volume_ratio,     # 量比：今日量 / 20日均量
                **_moving_averages(hist),
            }
            ok = True
            logger.info(
                f"  {name}: {quote['price']} ({quote['change_pct']:+.2f}%) "
                f"量 {volume_lots:,} 張" if volume_lots else
                f"  {name}: {quote['price']} ({quote['change_pct']:+.2f}%)"
            )

        return ok

    # ------------------------------------------------------------ 輸出

    def save_data(self, filename='data/market_data.json'):
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.market_data, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 市場數據已保存到 {filename}")
            return True
        except Exception as e:
            logger.error(f"保存數據出錯: {e}")
            return False

    def run(self):
        logger.info("=" * 60)
        logger.info("開始執行市場數據抓取 (v2)")
        logger.info("=" * 60)

        us = self.fetch_us_market()
        fx = self.fetch_exchange_rates()
        tw = self.fetch_tw_market()

        if not (us and fx and tw):
            missing = [n for n, v in (('美股', us), ('匯率', fx), ('台股', tw)) if not v]
            logger.warning(f"⚠️ 部分數據抓取失敗: {', '.join(missing)}")
        else:
            logger.info("✅ 所有數據抓取完成")

        self.save_data()
        return tw   # 台股是報告核心，台股失敗才算真失敗


if __name__ == '__main__':
    fetcher = MarketDataFetcher()
    success = fetcher.run()
    # 單一來源失敗不中斷整條 pipeline，仍讓後續步驟產出報告
    sys.exit(0 if success else 1)
