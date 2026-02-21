# 记忆星河 - 语音版使用指南

## 快速开始

### 1. 环境准备

```bash
# 确保已安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆仓库
git clone https://github.com/GLY2024/memory-star-mvp.git
cd memory-star-mvp

# 创建虚拟环境并安装依赖
uv venv
uv pip install -e ".[dev]"
```

### 2. 配置API密钥

```bash
# 方法1: 环境变量
export OPENAI_API_KEY="sk-..."
export VOICE_PROVIDER="openai"  # 或 gemini

# 方法2: .env文件
cp .env.example .env
# 编辑 .env 填入密钥
```

### 3. 运行语音Demo

```bash
# 激活环境
source .venv/bin/activate

# 运行语音版
uv run python voice_demo.py

# 或测试语音功能
uv run python voice_demo.py --test
```

## 功能说明

### 语音对话流程

1. **启动** - AI用语音问候并自我介绍
2. **录音** - 听到提示音后说话（最长10秒）
3. **等待** - AI处理并语音回复
4. **继续** - 可多轮对话
5. **结束** - 说"结束"或按Ctrl+C退出

### 可用命令

```bash
# 语音模式（默认）
uv run python voice_demo.py

# 语音测试
uv run python voice_demo.py --test

# 文字模式（原版）
uv run python demo.py
```

## 语音服务对比

| 服务 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **OpenAI Realtime** | 延迟低(<300ms)、自然度高 | 价格较高、需特殊权限 | 正式产品 |
| **Gemini Live** | 免费额度多、Google生态 | 中文支持稍弱 | 开发测试 |
| **Mock** | 无需密钥、免费 | 无真实语音 | 功能测试 |

## 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `GEMINI_API_KEY` | Gemini API密钥 | - |
| `VOICE_PROVIDER` | 语音服务提供商 | `mock` |
| `VOICE_NAME` | 语音音色 | `alloy` |
| `VOICE_LANGUAGE` | 语言 | `zh` |

### 音色选择 (OpenAI)

- `alloy` - 中性、温暖 (推荐)
- `echo` - 成熟男性
- `fable` - 年轻男性
- `onyx` - 深沉男性
- `nova` - 年轻女性
- `shimmer` - 明亮女性

## 常见问题

### Q: 无法录音
```bash
# Linux: 安装PortAudio
sudo apt-get install libportaudio2

# macOS: 允许麦克风权限
# 系统设置 → 隐私与安全 → 麦克风
```

### Q: API报错
- 检查API密钥是否正确
- 确认账号有Realtime API权限
- 查看OpenAI控制台使用情况

### Q: 语音延迟高
- 检查网络连接
- 尝试降低采样率
- 使用更稳定的网络

## 移动端开发

详见 [MOBILE_GUIDE.md](./MOBILE_GUIDE.md)

手机App需要：
1. 重写语音采集层（原生API）
2. 保持WebSocket连接
3. 处理网络切换

## 项目结构

```
memory_star/
├── voice.py           # 新增: 语音处理模块
├── core/              # 核心逻辑
└── utils/             # 工具函数

voice_demo.py         # 语音版入口
demo.py               # 文字版入口
pyproject.toml        # uv配置
```

## 更新日志

### v0.2.0 (2026-02-21)
- ✅ 迁移到uv管理
- ✅ 添加语音交互模块
- ✅ 支持OpenAI Realtime API
- ✅ 支持Gemini Live API
- ✅ 添加移动端开发指南

### v0.1.0 (2026-02-21)
- ✅ 基础对话系统
- ✅ AI引导提问
- ✅ 回忆录生成
