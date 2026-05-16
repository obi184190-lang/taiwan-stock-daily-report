#!/usr/bin/env python3
"""
Telegram 推送模塊
發送文字分析報告和語音檔案到 Telegram
"""

import os
import sys
import logging
import requests
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/telegram_sender.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

class TelegramSender:
    """Telegram 推送管理器"""
    
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        if not self.bot_token or not self.chat_id:
            logger.error("❌ Telegram 認證資訊不完整")
            self.available = False
        else:
            self.available = True
            logger.info("✅ Telegram 配置完成")
    
    def send_message(self, text, parse_mode=None):
        """發送文字訊息"""
        if not self.available:
            logger.error("Telegram 不可用")
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
    'chat_id': self.chat_id,
    'text': text,
    'disable_web_page_preview': True
}
if parse_mode:
    payload['parse_mode'] = parse_mode
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ 訊息發送成功 (長度: {len(text)} 字)")
                return True
            else:
                logger.error(f"❌ 訊息發送失敗: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"發送訊息時出錯: {str(e)}")
            return False
    
    def send_audio(self, audio_file_path):
        """發送音檔"""
        if not self.available:
            logger.error("Telegram 不可用")
            return False
        
        if not os.path.exists(audio_file_path):
            logger.error(f"音檔不存在: {audio_file_path}")
            return False
        
        try:
            url = f"{self.api_url}/sendAudio"
            
            with open(audio_file_path, 'rb') as audio:
                files = {'audio': audio}
                data = {
                    'chat_id': self.chat_id,
                    'title': '國際台股聯動日報 - 語音版',
                    'performer': '市場分析',
                    'duration': 0  # 自動偵測
                }
                
                response = requests.post(url, data=data, files=files, timeout=30)
            
            if response.status_code == 200:
                file_size = os.path.getsize(audio_file_path) / (1024 * 1024)
                logger.info(f"✅ 音檔發送成功 ({file_size:.2f} MB)")
                return True
            else:
                logger.error(f"❌ 音檔發送失敗: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"發送音檔時出錯: {str(e)}")
            return False
    
    def _format_report_for_telegram(self, report_text):
        """將報告格式化為 Telegram 格式"""
        # HTML 標籤支援
        html_text = report_text.replace('**', '<b>').replace('__', '<u>')
        html_text = html_text.replace('##', '<u>').replace('###', '<i>')
        
        # 移除過長的 markdown
        lines = html_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            # 保留重要的格式，移除 markdown 特殊字符
            line = line.replace('#', '').strip()
            if line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def send_report(self, report_file='data/analysis_report.md'):
        """發送完整報告"""
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                report_text = f.read()
            
            # 由於 Telegram 訊息長度限制（4096 字），需要分割
            formatted_text = self._format_report_for_telegram(report_text)
            
            # 標題訊息
            header = f"""📊 國際台股聯動日報
日期: {datetime.now(TW_TZ).strftime('%Y年%m月%d日')}
{'='*30}
"""            
            # Telegram 訊息長度限制
            max_length = 4096
            messages = [header]
            current_message = ""
            
            for line in formatted_text.split('\n'):
                if len(current_message) + len(line) + 1 > max_length:
                    if current_message:
                        messages.append(current_message)
                    current_message = line
                else:
                    if current_message:
                        current_message += '\n' + line
                    else:
                        current_message = line
            
            if current_message:
                messages.append(current_message)
            
            # 發送所有訊息
            success = True
            for i, msg in enumerate(messages):
                if msg.strip():
                    if not self.send_message(msg):
                        success = False
                    # 避免速率限制，訊息之間延遲
                    if i < len(messages) - 1:
                        import time
                        time.sleep(1)
            
            if success:
                logger.info(f"✅ 報告已分 {len(messages)} 部分發送")
            
            return success
        
        except FileNotFoundError:
            logger.error(f"報告檔案未找到: {report_file}")
            return False
        except Exception as e:
            logger.error(f"發送報告時出錯: {str(e)}")
            return False
    
    def run(self):
        """執行完整的推送流程"""
        logger.info("=" * 60)
        logger.info("開始推送到 Telegram")
        logger.info("=" * 60)
        
        success = True
        
        # 發送報告
        if not self.send_report():
            logger.warning("⚠️ 報告發送失敗")
            success = False
        
        # 發送語音（如果存在）
        audio_files = ['data/audio_report.mp3', 'data/audio_report.wav']
        audio_sent = False
        
        for audio_file in audio_files:
            if os.path.exists(audio_file):
                if self.send_audio(audio_file):
                    audio_sent = True
                    break
                else:
                    logger.warning(f"⚠️ 無法發送 {audio_file}")
        
        if not audio_sent:
            logger.warning("⚠️ 未能找到或發送音檔")
        
        if success and audio_sent:
            logger.info("✅ 推送完成（報告 + 語音）")
        elif success:
            logger.info("✅ 報告已推送，但未能發送語音")
        else:
            logger.error("❌ 推送失敗")
        
        return success

if __name__ == '__main__':
    sender = TelegramSender()
    success = sender.run()
    sys.exit(0 if success else 1)
