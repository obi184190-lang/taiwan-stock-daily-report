# taiwan-stock-daily-report
「國際台股聯動日報 - 每日06:30自動產生市場分析與語音播報」
# 📊 國際台股聯動日報

一個自動化的台灣股市市場分析系統，每日早上 6:30 自動生成國際-台股聯動分析報告，並提供文字與語音版本。

## ✨ 核心功能

### 🌍 國際情勢分析
- 美股三大指數走勢（S&P 500、納斯達克、道瓊）
- 國際匯率變動（USD/TWD、CNY/USD、JPY/USD）
- 地緣政治影響分析

### 📈 台股現況
- 台灣加權指數技術分析
- 大盤支撐/壓力位置
- 成交量與籌碼面分析

### 🔄 類股輪動走向
- 半導體、電子、金融、石化等產業表現
- 資金流向分析
- 龍頭股票動向（台積電、聯發科、鴻海等）

### 🤖 AI 驅動
- 使用 Claude API 生成專業分析報告
- 深度市場洞察與預判

### 🔊 多媒體輸出
- **文字版本**：Markdown 格式報告
- **語音版本**：支援 Google Cloud TTS 與 Azure TTS

### 📱 即時推送
- Telegram Bot 推送（@taiwan_stock_report_bot）
- 文字報告 + 語音檔案

---

## 🚀 快速開始

### 前置準備

1. **GitHub Repository**
   - 已建立：`taiwan-stock-daily-report`

2. **Telegram Bot**
   - 建立新 Bot：@taiwan_stock_report_bot
   - 記錄 Bot Token 和 Chat ID

3. **API Keys**
   - Claude API Key（來自 Anthropic）
   - Google Cloud TTS Key（可選）
   - Azure TTS Key（可選）

### 部署步驟

#### Step 1: 本地克隆（可選，若想先測試）
```bash
git clone https://github.com/你的帳號/taiwan-stock-daily-report.git
cd taiwan-stock-daily-report
```

#### Step 2: 在 GitHub 設定 Secrets

進入 Repository → **Settings** → **Secrets and variables** → **Actions**

新增以下 Secrets：

| Secret 名稱 | 值 | 取得方式 |
|------------|-----|---------|
| `ANTHROPIC_API_KEY` | Claude API Key | https://console.anthropic.com |
| `TELEGRAM_BOT_TOKEN` | Bot Token | @BotFather 建立 |
| `TELEGRAM_CHAT_ID` | Chat ID | 訪問 `https://api.telegram.org/bot{TOKEN}/getUpdates` |
| `GOOGLE_CLOUD_TTS_KEY` | Google Cloud JSON | Google Cloud Console（可選） |
| `AZURE_TTS_KEY` | Azure 訂閱金鑰 | Azure Portal（可選） |

#### Step 3: 上傳文件到 GitHub

直接在 GitHub 網頁上：
1. **Code** → **Add file** → **Create new file**
2. 分別建立：
   - `.github/workflows/daily-report.yml`
   - `scripts/market_analyzer.py`
   - `scripts/data_fetcher.py`
   - `scripts/tts_generator.py`
   - `scripts/telegram_sender.py`
   - `config/sectors.json`
   - `requirements.txt`

或者用 Git 推送（本地電腦）：
```bash
git add .
git commit -m "初始化國際台股聯動日報系統"
git push origin main
```

#### Step 4: 測試執行

進入 Repository → **Actions** → **國際台股聯動日報**

點擊 **Run workflow** 進行手動測試

---

## 📋 文件結構

```
taiwan-stock-daily-report/
├── .github/
│   └── workflows/
│       └── daily-report.yml          # GitHub Actions 排程配置
├── scripts/
│   ├── data_fetcher.py               # 市場數據抓取
│   ├── market_analyzer.py            # AI 分析報告生成
│   ├── tts_generator.py              # 文字轉語音
│   └── telegram_sender.py            # Telegram 推送
├── config/
│   └── sectors.json                  # 台股類股配置
├── data/
│   ├── market_data.json              # 市場數據（自動生成）
│   ├── analysis_report.md            # 分析報告（自動生成）
│   └── audio_report.mp3              # 語音檔案（自動生成）
├── logs/
│   ├── data_fetcher.log              # 數據抓取日誌
│   ├── market_analyzer.log           # 分析日誌
│   ├── tts_generator.log             # TTS 日誌
│   └── telegram_sender.log           # 推送日誌
├── requirements.txt                  # Python 依賴
├── README.md                         # 專案說明
└── .gitignore
```

---

## ⏰ 自動執行排程

**每日 06:30 台灣時間自動執行**（UTC+8）

執行流程：
1. ⏰ 06:30 → 觸發 GitHub Actions
2. 📊 抓取美股、台股、匯率數據
3. 🤖 使用 Claude API 生成分析報告
4. 🔊 文字轉換為語音（TTS）
5. 📱 推送到 Telegram Bot

---

## 🔧 進階配置

### 修改執行時間

編輯 `.github/workflows/daily-report.yml`：

```yaml
on:
  schedule:
    - cron: '30 22 * * 0-4'  # 修改 cron 表達式
```

- 格式：`分 小時 日 月 星期（0=週日）`
- 時區：UTC（台灣時間需要 -8 小時）
- 例子：
  - `30 22 * * 0-4` = 每日 06:30 台灣時間
  - `0 1 * * 1-5` = 每個工作日 09:00 台灣時間

### 修改監控股票

編輯 `config/sectors.json` 以新增/移除監控的股票。

### 調整 TTS 語速

編輯 `scripts/tts_generator.py`：

```python
speaking_rate=0.9  # 0.5 (最慢) 到 1.5 (最快)
```

---

## 📊 輸出示例

### 文字報告格式
```
📊 國際台股聯動日報
日期: 2026年05月09日

🌍 昨晚國際情勢與美股走向
- S&P 500 上漲 0.5%，由於...
- 納斯達克上漲 1.2%，科技股領漲...
...

💱 國際匯率變動分析
- USD/TWD 升至 31.5，影響...
...

📈 今日台股現況分析
- 台灣加權指數開高走高...
...

🔄 類股輪動走向
- 半導體板塊領漲...
...
```

### 語音檔案
- 格式：MP3 或 WAV
- 長度：約 15-20 分鐘
- 語言：繁體中文（台灣）
- 速度：0.9 倍速（便於理解）

---

## 🐛 故障排查

### 無法發送到 Telegram

**原因**：
- Bot Token 或 Chat ID 錯誤
- 網路連線問題

**解決**：
1. 驗證 Secrets 配置
2. 檢查 GitHub Actions 日誌（logs/telegram_sender.log）

### 語音生成失敗

**原因**：
- Google Cloud TTS / Azure TTS 未正確配置
- API Key 無效

**解決**：
1. 檢查 TTS Key 是否正確設定
2. 驗證 API 額度未用盡
3. 查看 logs/tts_generator.log

### AI 分析報告錯誤

**原因**：
- Claude API Key 無效
- API 額度用盡

**解決**：
1. 驗證 ANTHROPIC_API_KEY
2. 檢查 API 使用額度：https://console.anthropic.com
3. 查看 logs/market_analyzer.log

### 市場數據抓取失敗

**原因**：
- yfinance 伺服器問題
- 代碼格式錯誤

**解決**：
1. 確認台股代碼格式（例：2330.TW）
2. 檢查 logs/data_fetcher.log
3. 稍後重試

---

## 📚 技術棧

| 組件 | 用途 | 版本 |
|------|------|------|
| Python | 主程式 | 3.11+ |
| GitHub Actions | 自動排程 | - |
| Anthropic Claude | AI 分析 | Claude API |
| yfinance | 市場數據 | 0.2.0+ |
| Google Cloud TTS | 語音合成 | 2.14.0+ |
| Azure TTS | 語音合成 | 1.31.0+ |
| Telegram Bot | 訊息推送 | - |

---

## 📈 後續功能規劃

- [ ] K線圖表自動生成
- [ ] 歷史分析比較
- [ ] 每週績效總結
- [ ] 自訂通知頻率
- [ ] 資料庫存儲（Supabase）

---

## ⚠️ 重要提醒

1. **API 成本**
   - Claude API：按 token 計費（較低）
   - Google Cloud TTS：按字符計費（月免費額度）
   - Azure TTS：按小時計費（有免費層）

2. **使用限制**
   - Telegram Bot 推送：無限制
   - GitHub Actions：免費帳戶每月 2,000 分鐘

3. **數據隱私**
   - 所有數據透過加密連線傳輸
   - 不保存個人資訊

---

## 📞 支援

如有問題，請檢查：
1. GitHub Actions 日誌
2. `logs/` 目錄下的詳細日誌
3. GitHub Issues

---

## 📝 授權

MIT License - 自由使用和修改

---

**製作時間**：2026年5月
**維護者**：@obi184190-lang
**最後更新**：2026年5月9日

