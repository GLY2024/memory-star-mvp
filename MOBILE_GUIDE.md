# 记忆星河 - 移动端开发指南

## 概述

本文档说明如何将记忆星河从电脑端迁移到手机App，以及两端的差异。

## 电脑端 vs 手机端对比

| 特性 | 电脑端 (MVP) | 手机端 (App) |
|------|-------------|-------------|
| **运行环境** | Python脚本 | iOS/Android原生 |
| **语音采集** | sounddevice / PyAudio | AVAudioRecorder / AudioRecord |
| **语音播放** | sounddevice | AVAudioPlayer / AudioTrack |
| **AI语音API** | OpenAI/Gemini REST API | 相同，但需考虑网络切换 |
| **网络** | 稳定WiFi | 4G/5G/WiFi切换 |
| **使用场景** | 家中固定使用 | 随时随地 |
| **交互方式** | 键盘+鼠标+语音 | 触屏+语音为主 |
| **后台运行** | 可后台 | iOS限制严格，Android较宽松 |

## 技术架构选择

### 方案1: React Native (推荐)

适合快速开发，一套代码双端运行。

```
前端 (React Native)
├── 语音模块
│   ├── 录音: expo-av / react-native-audio-recorder-player
│   └── 播放: expo-av
├── AI连接
│   └── OpenAI Realtime API (WebSocket)
├── 状态管理
│   └── Zustand / Redux
└── 存储
    └── AsyncStorage + 后端同步

后端 (Python/FastAPI)
├── 会话管理
├── 回忆录生成
└── 文件存储 (OSS/S3)
```

**优点:**
- 开发效率高
- 社区成熟
- 热更新支持

**缺点:**
- 性能略低于原生
- 复杂动画受限

### 方案2: Flutter

Google框架，性能接近原生。

```
前端 (Flutter)
├── 语音模块: record / flutter_sound
├── AI连接: web_socket_channel
└── 状态管理: Riverpod
```

**优点:**
- 性能优秀
- UI一致性高

**缺点:**
- 学习曲线陡峭
- 包体积较大

### 方案3: 原生开发

**iOS (Swift):**
```swift
// 语音录制
import AVFoundation
let recorder = AVAudioRecorder()

// 语音播放
let player = AVAudioPlayer()

// WebSocket连接
import Starscream
```

**Android (Kotlin):**
```kotlin
// 语音录制
val recorder = MediaRecorder()

// 语音播放
val player = MediaPlayer()

// WebSocket
import okhttp3.WebSocket
```

**优点:**
- 性能最佳
- 系统特性完整支持

**缺点:**
- 开发成本高
- 两套代码维护

## 语音实现详解

### 电脑端实现 (已完成)

```python
# memory_star/voice.py

class DesktopAdapter:
    async def record_audio(self, duration=10.0) -> bytes:
        import sounddevice as sd
        recording = sd.rec(int(duration * 24000), 
                          samplerate=24000, 
                          channels=1)
        sd.wait()
        return recording.tobytes()
    
    async def play_audio(self, audio_data: bytes):
        import sounddevice as sd
        sd.play(audio_data, 24000)
```

### 手机端实现 (需原生开发)

**React Native 示例:**

```typescript
// VoiceModule.ts
import { Audio } from 'expo-av';

class VoiceManager {
  private recording: Audio.Recording | null = null;
  
  async startRecording() {
    await Audio.requestPermissionsAsync();
    
    this.recording = new Audio.Recording();
    await this.recording.prepareToRecordAsync({
      android: {
        extension: '.pcm',
        outputFormat: Audio.AndroidOutputFormat.DEFAULT,
        audioEncoder: Audio.AndroidAudioEncoder.DEFAULT,
        sampleRate: 24000,
        numberOfChannels: 1,
      },
      ios: {
        extension: '.pcm',
        audioQuality: Audio.IOSAudioQuality.HIGH,
        sampleRate: 24000,
        numberOfChannels: 1,
      },
    });
    
    await this.recording.startAsync();
  }
  
  async stopRecording(): Promise<Uint8Array> {
    await this.recording?.stopAndUnloadAsync();
    const uri = this.recording?.getURI();
    
    // 读取PCM数据
    const response = await fetch(uri!);
    const arrayBuffer = await response.arrayBuffer();
    return new Uint8Array(arrayBuffer);
  }
  
  async playAudio(pcmData: Uint8Array) {
    const { sound } = await Audio.Sound.createAsync(
      { uri: `data:audio/pcm;base64,${base64Encode(pcmData)}` }
    );
    await sound.playAsync();
  }
}
```

## OpenAI Realtime API 移动端适配

### WebSocket连接

```typescript
// OpenAIRealtimeClient.ts
import WebSocket from 'react-native-websocket';

class OpenAIRealtimeClient {
  private ws: WebSocket | null = null;
  
  connect() {
    this.ws = new WebSocket(
      'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview',
      '',
      {
        headers: {
          'Authorization': `Bearer ${OPENAI_API_KEY}`,
          'OpenAI-Beta': 'realtime=v1',
        }
      }
    );
    
    this.ws.onopen = () => {
      // 发送会话配置
      this.ws?.send(JSON.stringify({
        type: 'session.update',
        session: {
          modalities: ['text', 'audio'],
          instructions: '你是一位温暖的回忆录访谈助手...',
          voice: 'alloy',
          input_audio_format: 'pcm16',
          output_audio_format: 'pcm16',
          turn_detection: {
            type: 'server_vad',
            threshold: 0.5,
          }
        }
      }));
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
  }
  
  sendAudio(pcmData: Uint8Array) {
    const base64 = btoa(String.fromCharCode(...pcmData));
    this.ws?.send(JSON.stringify({
      type: 'input_audio_buffer.append',
      audio: base64
    }));
  }
  
  private handleMessage(data: any) {
    switch (data.type) {
      case 'response.audio.delta':
        // 播放音频
        this.playAudioChunk(data.delta);
        break;
      case 'response.text.delta':
        // 显示文字
        this.onTextUpdate?.(data.delta);
        break;
    }
  }
}
```

## 移动端特有考虑

### 1. 网络稳定性

```typescript
// 网络状态监听
import NetInfo from '@react-native-community/netinfo';

NetInfo.addEventListener(state => {
  if (!state.isConnected) {
    // 暂停录音，提示用户
    showToast('网络已断开，请检查网络');
  }
});
```

### 2. 后台运行

**iOS限制:**
- 录音时屏幕常亮
- 后台录音需申请特殊权限
- 建议使用CallKit模拟通话界面

**Android:**
- 前台服务保持运行
- 通知栏显示录音状态

```kotlin
// Android前台服务
class RecordingService : Service() {
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("记忆星河")
            .setContentText("正在记录您的故事...")
            .setSmallIcon(R.drawable.ic_recording)
            .build()
        
        startForeground(NOTIFICATION_ID, notification)
        return START_STICKY
    }
}
```

### 3. 电量优化

- 降低录音采样率（16kHz vs 24kHz）
- 使用硬件编码
- 批量上传而非实时

### 4. 存储管理

```typescript
// 自动清理旧录音
const MAX_STORAGE_DAYS = 7;

async function cleanupOldRecordings() {
  const files = await FileSystem.readDirectoryAsync(
    FileSystem.documentDirectory + 'recordings/'
  );
  
  for (const file of files) {
    const info = await FileSystem.getInfoAsync(file);
    const age = Date.now() - info.modificationTime;
    
    if (age > MAX_STORAGE_DAYS * 24 * 60 * 60 * 1000) {
      await FileSystem.deleteAsync(file);
    }
  }
}
```

## 推荐技术栈

### 前端 (React Native)

```json
{
  "dependencies": {
    "react-native": "0.73.x",
    "expo-av": "~13.10.0",
    "@react-native-voice/voice": "^3.2.0",
    "react-native-websocket": "^1.0.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "react-native-paper": "^5.11.0"
  }
}
```

### 后端 (Python)

继续使用现有架构：
- FastAPI
- PostgreSQL
- Redis
- Celery (异步任务)

## 迁移步骤

### Phase 1: API封装 (1-2周)

1. 将现有Python模块封装为REST API
2. 添加移动端认证（JWT）
3. 文件上传接口

### Phase 2: 基础App (2-3周)

1. React Native项目初始化
2. 基础UI框架
3. 语音录制/播放

### Phase 3: AI集成 (2周)

1. WebSocket连接OpenAI Realtime API
2. 对话状态管理
3. 回忆录生成流程

### Phase 4: 优化 (持续)

1. 性能优化
2. 离线支持
3. 推送通知

## 代码复用策略

### 可复用 (Python后端)

- ✅ 回忆录生成逻辑 (`memoir_writer.py`)
- ✅ 提问模板 (`question_generator.py`)
- ✅ 数据模型 (`chat_engine.py`)

### 需重写 (移动端)

- ❌ 语音采集/播放
- ❌ WebSocket连接管理
- ❌ UI界面

### 需适配

- ⚠️ 会话状态同步
- ⚠️ 文件存储（本地+云端）
- ⚠️ 网络状态处理

## 快速启动模板

已创建 `mobile/` 目录，包含:

```
mobile/
├── react-native/          # React Native模板
│   ├── src/
│   │   ├── api/          # API客户端
│   │   ├── components/   # UI组件
│   │   ├── hooks/        # 自定义Hooks
│   │   ├── screens/      # 页面
│   │   ├── stores/       # 状态管理
│   │   └── utils/        # 工具函数
│   ├── App.tsx
│   └── package.json
└── flutter/              # Flutter模板 (可选)
```

## 参考资源

- [OpenAI Realtime API Docs](https://platform.openai.com/docs/guides/realtime)
- [React Native Audio](https://github.com/hyochan/react-native-audio-recorder-player)
- [Expo AV](https://docs.expo.dev/versions/latest/sdk/av/)
- [WebSocket in React Native](https://github.com/pladaria/react-native-websocket)

---

**结论:** 电脑端MVP验证了核心AI能力，手机端需要重写UI和语音层，但后端逻辑可完全复用。建议采用React Native方案，4-6周可完成MVP。
