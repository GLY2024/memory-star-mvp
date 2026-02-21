"""
记忆星河 - 语音处理模块
支持GPT-4o Realtime API和Gemini Live API
适配电脑端和手机端不同场景
"""

import os
import io
import base64
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, Callable, AsyncIterator
from dataclasses import dataclass
from enum import Enum


class VoiceProvider(Enum):
    """语音服务提供商"""
    OPENAI = "openai"      # GPT-4o Realtime API
    GEMINI = "gemini"      # Gemini Live API
    MOCK = "mock"          # 模拟模式（文字替代）


@dataclass
class VoiceConfig:
    """语音配置"""
    provider: VoiceProvider
    api_key: Optional[str] = None
    model: Optional[str] = None
    voice: str = "alloy"   # OpenAI: alloy, echo, fable, onyx, nova, shimmer
    language: str = "zh"   # 语言代码
    
    # 音频参数
    sample_rate: int = 24000
    channels: int = 1
    
    # 移动端特有配置
    enable_vad: bool = True        # 语音活动检测
    vad_threshold: float = 0.5     # VAD阈值
    
    @classmethod
    def from_env(cls) -> "VoiceConfig":
        """从环境变量创建配置"""
        provider_str = os.getenv("VOICE_PROVIDER", "mock").lower()
        
        if provider_str == "openai":
            provider = VoiceProvider.OPENAI
            api_key = os.getenv("OPENAI_API_KEY")
            model = "gpt-4o-realtime-preview"
        elif provider_str == "gemini":
            provider = VoiceProvider.GEMINI
            api_key = os.getenv("GEMINI_API_KEY")
            model = "gemini-2.0-flash-exp"
        else:
            provider = VoiceProvider.MOCK
            api_key = None
            model = None
        
        return cls(
            provider=provider,
            api_key=api_key,
            model=model,
            voice=os.getenv("VOICE_NAME", "alloy"),
            language=os.getenv("VOICE_LANGUAGE", "zh"),
        )


class BaseVoiceHandler(ABC):
    """语音处理器基类"""
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.is_listening = False
        self.is_speaking = False
    
    @abstractmethod
    async def connect(self):
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_audio(self, audio_data: bytes) -> str:
        """
        发送音频数据，返回AI文本回复
        电脑端：从麦克风读取
        手机端：从手机麦克风读取
        """
        pass
    
    @abstractmethod
    async def speak(self, text: str) -> bytes:
        """
        将文本转为语音
        返回音频数据（PCM或MP3）
        """
        pass
    
    @abstractmethod
    async def stream_conversation(
        self, 
        on_text: Callable[[str], None],
        on_audio: Callable[[bytes], None]
    ):
        """
        流式对话（Realtime模式）
        持续监听音频输入，实时输出语音回复
        """
        pass


class OpenAIVoiceHandler(BaseVoiceHandler):
    """OpenAI GPT-4o Realtime API 语音处理器"""
    
    def __init__(self, config: VoiceConfig):
        super().__init__(config)
        self.ws = None
        self.client = None
        
    async def connect(self):
        """建立WebSocket连接"""
        import websockets
        import json
        
        if not self.config.api_key:
            raise ValueError("OpenAI API key not configured")
        
        url = f"wss://api.openai.com/v1/realtime?model={self.config.model}"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        self.ws = await websockets.connect(url, extra_headers=headers)
        
        # 配置会话
        config_msg = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "你是一位温暖的回忆录访谈助手，用亲切的语气与老人交谈。",
                "voice": self.config.voice,
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": self.config.vad_threshold,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        await self.ws.send(json.dumps(config_msg))
    
    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
            self.ws = None
    
    async def send_audio(self, audio_data: bytes) -> str:
        """发送音频并获取回复"""
        import json
        import base64
        
        if not self.ws:
            await self.connect()
        
        # 发送音频数据
        audio_msg = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_data).decode()
        }
        await self.ws.send(json.dumps(audio_msg))
        
        # 提交音频
        await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        await self.ws.send(json.dumps({"type": "response.create"}))
        
        # 接收回复
        transcript = ""
        async for message in self.ws:
            data = json.loads(message)
            
            if data["type"] == "response.text.delta":
                transcript += data.get("delta", "")
            elif data["type"] == "response.done":
                break
        
        return transcript
    
    async def speak(self, text: str) -> bytes:
        """文本转语音"""
        from openai import OpenAI
        
        client = OpenAI(api_key=self.config.api_key)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice=self.config.voice,
            input=text,
            response_format="pcm"  # 返回PCM格式，便于流式播放
        )
        
        return response.content
    
    async def stream_conversation(
        self,
        on_text: Callable[[str], None],
        on_audio: Callable[[bytes], None]
    ):
        """流式对话（Realtime模式）"""
        import json
        import base64
        
        if not self.ws:
            await self.connect()
        
        self.is_listening = True
        
        try:
            async for message in self.ws:
                data = json.loads(message)
                msg_type = data.get("type")
                
                # 处理用户语音转录
                if msg_type == "conversation.item.input_audio_transcription.completed":
                    text = data.get("transcript", "")
                    on_text(f"[用户] {text}")
                
                # 处理AI文本回复
                elif msg_type == "response.text.delta":
                    delta = data.get("delta", "")
                    on_text(delta)
                
                # 处理AI语音回复
                elif msg_type == "response.audio.delta":
                    audio = base64.b64decode(data.get("delta", ""))
                    on_audio(audio)
                
                # 回复完成
                elif msg_type == "response.done":
                    on_text("\n")
                    
        except Exception as e:
            print(f"Stream error: {e}")
        finally:
            self.is_listening = False


class GeminiVoiceHandler(BaseVoiceHandler):
    """Gemini Live API 语音处理器"""
    
    def __init__(self, config: VoiceConfig):
        super().__init__(config)
        self.session = None
    
    async def connect(self):
        """建立连接"""
        import google.generativeai as genai
        
        if not self.config.api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=self.config.api_key)
        
        model = genai.GenerativeModel(
            model_name=self.config.model or "gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 2048,
            }
        )
        
        # 启动语音会话
        self.session = model.start_chat()
    
    async def disconnect(self):
        """断开连接"""
        self.session = None
    
    async def send_audio(self, audio_data: bytes) -> str:
        """发送音频并获取回复"""
        import google.generativeai as genai
        
        if not self.session:
            await self.connect()
        
        # Gemini支持直接发送音频
        audio_part = {
            "mime_type": "audio/pcm",
            "data": audio_data
        }
        
        response = self.session.send_message(audio_part)
        return response.text
    
    async def speak(self, text: str) -> bytes:
        """Gemini暂不支持直接TTS，使用OpenAI TTS作为fallback"""
        # 可以集成其他TTS服务
        raise NotImplementedError("Gemini TTS not implemented, use OpenAI TTS instead")
    
    async def stream_conversation(self, on_text, on_audio):
        """Gemini Live流式对话"""
        # Gemini Live API实现
        pass


class MockVoiceHandler(BaseVoiceHandler):
    """模拟语音处理器（文字模式）"""
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        pass
    
    async def send_audio(self, audio_data: bytes) -> str:
        """模拟：返回提示让用户输入文字"""
        return "[语音模式未启用，请输入文字]"
    
    async def speak(self, text: str) -> bytes:
        """模拟：仅打印文字"""
        print(f"[语音输出] {text}")
        return b""
    
    async def stream_conversation(self, on_text, on_audio):
        pass


def create_voice_handler(config: Optional[VoiceConfig] = None) -> BaseVoiceHandler:
    """工厂函数：创建语音处理器"""
    config = config or VoiceConfig.from_env()
    
    if config.provider == VoiceProvider.OPENAI:
        return OpenAIVoiceHandler(config)
    elif config.provider == VoiceProvider.GEMINI:
        return GeminiVoiceHandler(config)
    else:
        return MockVoiceHandler(config)


# ==================== 平台适配层 ====================

class PlatformAdapter(ABC):
    """
    平台适配器抽象基类
    电脑端和手机端有不同的音频采集和播放方式
    """
    
    @abstractmethod
    async def record_audio(self, duration: Optional[float] = None) -> bytes:
        """录制音频"""
        pass
    
    @abstractmethod
    async def play_audio(self, audio_data: bytes):
        """播放音频"""
        pass
    
    @abstractmethod
    def is_mobile(self) -> bool:
        """是否为移动端"""
        pass


class DesktopAdapter(PlatformAdapter):
    """电脑端适配器（Linux/Mac/Windows）"""
    
    def __init__(self):
        self.sample_rate = 24000
        self.channels = 1
        self.dtype = "int16"
    
    async def record_audio(self, duration: Optional[float] = None) -> bytes:
        """
        使用sounddevice录制音频
        电脑端：支持长时间录制，有停止按钮
        """
        import sounddevice as sd
        import numpy as np
        
        if duration:
            # 固定时长录制
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype
            )
            sd.wait()
            return recording.tobytes()
        else:
            # 持续录制直到手动停止（需要UI配合）
            # 这里简化处理，录制5秒
            return await self.record_audio(duration=5.0)
    
    async def play_audio(self, audio_data: bytes):
        """播放音频"""
        import sounddevice as sd
        import numpy as np
        
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio_array, self.sample_rate)
        sd.wait()
    
    def is_mobile(self) -> bool:
        return False


class MobileAdapter(PlatformAdapter):
    """
    手机端适配器
    注意：这是接口定义，实际实现需要在原生App中
    """
    
    async def record_audio(self, duration: Optional[float] = None) -> bytes:
        """
        手机端音频采集方式：
        - iOS: AVAudioRecorder
        - Android: MediaRecorder / AudioRecord
        - React Native: expo-av / react-native-audio-recorder-player
        """
        raise NotImplementedError(
            "Mobile audio recording should be implemented in native app"
        )
    
    async def play_audio(self, audio_data: bytes):
        """
        手机端音频播放方式：
        - iOS: AVAudioPlayer
        - Android: MediaPlayer / AudioTrack
        """
        raise NotImplementedError(
            "Mobile audio playback should be implemented in native app"
        )
    
    def is_mobile(self) -> bool:
        return True


# ==================== 统一语音接口 ====================

class VoiceInterface:
    """
    统一语音接口
    根据平台自动选择适配器，提供一致的语音交互体验
    """
    
    def __init__(
        self,
        voice_handler: Optional[BaseVoiceHandler] = None,
        platform_adapter: Optional[PlatformAdapter] = None
    ):
        self.voice = voice_handler or create_voice_handler()
        self.platform = platform_adapter or self._detect_platform()
        self.conversation_history = []
    
    def _detect_platform(self) -> PlatformAdapter:
        """自动检测平台"""
        # 简单检测：检查是否在移动环境
        # 实际项目中可以通过user agent或其他方式检测
        return DesktopAdapter()
    
    async def start_conversation(self):
        """开始语音对话"""
        await self.voice.connect()
        print("🎙️ 语音对话已启动，请说话...")
    
    async def stop_conversation(self):
        """停止语音对话"""
        await self.voice.disconnect()
        print("👋 语音对话已结束")
    
    async def speak_turn(self, prompt_text: Optional[str] = None) -> str:
        """
        一轮语音对话：
        1. 播放提示音（可选）
        2. 录制用户语音
        3. 发送到AI
        4. 播放AI回复
        5. 返回转录文本
        """
        # 播放提示音
        if prompt_text:
            await self.voice.speak(prompt_text)
        
        print("🎤 请说话...")
        
        # 录制音频
        audio_input = await self.platform.record_audio(duration=10.0)
        
        print("🤔 思考中...")
        
        # 发送到AI
        response_text = await self.voice.send_audio(audio_input)
        
        # 播放回复
        response_audio = await self.voice.speak(response_text)
        await self.platform.play_audio(response_audio)
        
        # 记录历史
        self.conversation_history.append({
            "user_audio": audio_input,
            "ai_text": response_text,
            "ai_audio": response_audio
        })
        
        return response_text
    
    async def continuous_chat(self, max_turns: int = 10):
        """
        连续多轮对话
        适合电脑端演示使用
        """
        await self.start_conversation()
        
        try:
            for i in range(max_turns):
                print(f"\n--- 第 {i+1} 轮 ---")
                response = await self.speak_turn()
                print(f"AI: {response}")
                
                # 检查是否结束
                if "再见" in response or "结束" in response:
                    break
        finally:
            await self.stop_conversation()
