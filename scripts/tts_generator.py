#!/usr/bin/env python3
"""
文字轉語音模塊
支援 Google Cloud TTS 和 Azure TTS
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tts_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

class GoogleCloudTTS:
    """Google Cloud Text-to-Speech 實現"""
    
    def __init__(self, api_key_json=None):
        try:
            from google.cloud import texttospeech
            self.client = texttospeech.TextToSpeechClient()
            self.available = True
            logger.info("✅ Google Cloud TTS 初始化成功")
        except ImportError:
            logger.warning("⚠️ Google Cloud TTS 庫未安裝")
            self.available = False
        except Exception as e:
            logger.error(f"Google Cloud TTS 初始化失敗: {str(e)}")
            self.available = False
    
    def synthesize(self, text, output_file='data/audio_report.mp3'):
        """將文字轉換為語音"""
        if not self.available:
            logger.error("Google Cloud TTS 不可用")
            return False
        
        try:
            from google.cloud import texttospeech
            
            # 建立語音合成請求
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code="zh-TW",  # 繁體中文（台灣）
                name="zh-TW-Neural2-A"   # Google 神經網絡語音
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9  # 說話速度：0.9 倍（稍慢，便於理解）
            )
            
            # 執行語音合成
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # 保存音檔
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'wb') as out:
                out.write(response.audio_content)
            
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            logger.info(f"✅ 語音檔案生成成功: {output_file} ({file_size:.2f} MB)")
            return True
        
        except Exception as e:
            logger.error(f"語音合成失敗: {str(e)}")
            return False

class AzureTTS:
    """Azure Cognitive Services Text-to-Speech 實現"""
    
    def __init__(self, subscription_key=None, region=None):
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            self.subscription_key = subscription_key or os.getenv('AZURE_TTS_KEY')
            self.region = region or os.getenv('AZURE_TTS_REGION', 'eastasia')
            
            if not self.subscription_key:
                logger.warning("⚠️ Azure TTS 訂閱金鑰未設定")
                self.available = False
                return
            
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoYuNeural"
            speech_config.set_speech_synthesis_output_to_default_speaker()
            
            self.speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
            self.available = True
            logger.info("✅ Azure TTS 初始化成功")
        
        except ImportError:
            logger.warning("⚠️ Azure Cognitive Services 庫未安裝")
            self.available = False
        except Exception as e:
            logger.error(f"Azure TTS 初始化失敗: {str(e)}")
            self.available = False
    
    def synthesize(self, text, output_file='data/audio_report.wav'):
        """將文字轉換為語音"""
        if not self.available:
            logger.error("Azure TTS 不可用")
            return False
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # 設定輸出檔案
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)
            
            speech_config = speechsdk.SpeechConfig(
                subscription=self.subscription_key,
                region=self.region
            )
            speech_config.speech_synthesis_voice_name = "zh-TW-HsiaoYuNeural"
            
            speech_synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=audio_config
            )
            
            # 執行語音合成
            result = speech_synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                logger.info(f"✅ 語音檔案生成成功: {output_file} ({file_size:.2f} MB)")
                return True
            else:
                logger.error(f"語音合成失敗: {result.error_details}")
                return False
        
        except Exception as e:
            logger.error(f"Azure TTS 處理失敗: {str(e)}")
            return False

class TTSGenerator:
    """文字轉語音管理器"""
    
    def __init__(self):
        self.report_text = None
        self.google_tts = None
        self.azure_tts = None
        self.audio_file = None
    
    def _load_report(self, filename='data/analysis_report.md'):
        """載入分析報告"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.report_text = f.read()
            logger.info(f"✅ 已載入報告: {filename}")
            return True
        except FileNotFoundError:
            logger.error(f"報告檔案未找到: {filename}")
            return False
    
    def _clean_text_for_speech(self, text):
        """清理文本以適應語音合成"""
        # 移除 markdown 標記
        text = text.replace('##', '').replace('###', '').replace('####', '')
        text = text.replace('**', '').replace('***', '').replace('~~', '')
        text = text.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        
        # 保留段落換行
        text = '\n'.join([line.strip() for line in text.split('\n') if line.strip()])
        
        return text
    
    def generate_with_google(self):
        """使用 Google Cloud TTS 生成語音"""
        logger.info("嘗試使用 Google Cloud TTS...")
        
        self.google_tts = GoogleCloudTTS()
        if not self.google_tts.available:
            logger.warning("Google Cloud TTS 不可用，嘗試 Azure TTS...")
            return False
        
        clean_text = self._clean_text_for_speech(self.report_text)
        success = self.google_tts.synthesize(clean_text, 'data/audio_report.mp3')
        
        if success:
            self.audio_file = 'data/audio_report.mp3'
        
        return success
    
    def generate_with_azure(self):
        """使用 Azure TTS 生成語音"""
        logger.info("嘗試使用 Azure TTS...")
        
        self.azure_tts = AzureTTS()
        if not self.azure_tts.available:
            logger.warning("Azure TTS 不可用")
            return False
        
        clean_text = self._clean_text_for_speech(self.report_text)
        success = self.azure_tts.synthesize(clean_text, 'data/audio_report.wav')
        
        if success:
            self.audio_file = 'data/audio_report.wav'
        
        return success
    
    def run(self):
        """執行文字轉語音流程"""
        logger.info("=" * 60)
        logger.info("開始生成語音版本")
        logger.info("=" * 60)
        
        # 載入報告
        if not self._load_report():
            logger.error("❌ 無法載入報告")
            return False
        
        # 嘗試使用 Google Cloud TTS
        if self.generate_with_google():
            logger.info("✅ 語音檔案生成完成（Google Cloud TTS）")
            return True
        
        # 如果 Google 失敗，嘗試 Azure TTS
        if self.generate_with_azure():
            logger.info("✅ 語音檔案生成完成（Azure TTS）")
            return True
        
        logger.error("❌ 語音生成失敗（所有服務都不可用）")
        return False

if __name__ == '__main__':
    generator = TTSGenerator()
    success = generator.run()
    sys.exit(0)
