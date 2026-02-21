"""
记忆星河 - 语音处理工具
处理语音输入输出（简化版，使用文字模拟）
"""

import os


class AudioHandler:
    """语音处理器"""
    
    def __init__(self, enable_voice: bool = False):
        self.enable_voice = enable_voice
        self.language = "zh-CN"
        
        if enable_voice:
            try:
                import speech_recognition as sr
                import pyttsx3
                self.recognizer = sr.Recognizer()
                self.tts_engine = pyttsx3.init()
                # 设置中文语音
                self.tts_engine.setProperty('rate', 150)  # 语速
                self._setup_chinese_voice()
            except ImportError:
                print("语音模块未安装，将使用文字模式")
                self.enable_voice = False
    
    def _setup_chinese_voice(self):
        """设置中文语音"""
        try:
            voices = self.tts_engine.getProperty('voices')
            # 尝试找到中文语音
            for voice in voices:
                if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
        except Exception as e:
            print(f"设置语音失败: {e}")
    
    def listen(self, timeout: int = 10) -> str:
        """
        监听语音输入
        返回识别到的文字，如果失败返回空字符串
        """
        if not self.enable_voice:
            return ""
        
        try:
            import speech_recognition as sr
            
            with sr.Microphone() as source:
                print("🎤 请说话...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout)
            
            print("📝 识别中...")
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text
        
        except sr.WaitTimeoutError:
            print("⏱️ 等待超时，未检测到语音")
            return ""
        except sr.UnknownValueError:
            print("❓ 无法识别语音")
            return ""
        except sr.RequestError as e:
            print(f"🔌 语音识别服务错误: {e}")
            return ""
        except Exception as e:
            print(f"❌ 语音处理错误: {e}")
            return ""
    
    def speak(self, text: str):
        """语音播报"""
        if not self.enable_voice:
            return
        
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"语音播报失败: {e}")
    
    def is_available(self) -> bool:
        """检查语音功能是否可用"""
        return self.enable_voice


def get_input_with_voice_option(audio_handler: AudioHandler) -> str:
    """
    获取用户输入，支持语音和文字
    如果语音可用，先尝试语音，失败则 fallback 到文字
    """
    if audio_handler.is_available():
        print("\n💡 提示：可以直接说话，或输入文字")
        
        # 尝试语音输入
        voice_input = audio_handler.listen(timeout=5)
        if voice_input:
            print(f"🎤 识别结果: {voice_input}")
            confirm = input("确认吗？(回车确认，n重录，直接输入文字): ").strip()
            if confirm.lower() != 'n':
                return voice_input if not confirm else confirm
    
    # 文字输入
    try:
        user_input = input("\n👤 您: ").strip()
        return user_input
    except EOFError:
        # 处理管道输入的情况
        return ""
