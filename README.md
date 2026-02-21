# 记忆星河 MVP

AI辅助老年人回忆录撰写平台 - 最小可行性验证版本

## 功能特性

- 🎙️ 语音/文字双模态交互
- 🤖 AI引导式访谈
- 📝 智能回忆录生成
- 💾 对话历史保存

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/memory-star-mvp.git
cd memory-star-mvp
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
export OPENROUTER_API_KEY="your-api-key"
```

或者创建 `.env` 文件：

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 4. 运行Demo

```bash
python demo.py
```

## 使用指南

### 对话流程

1. **开场** - AI助手会自我介绍并询问如何称呼
2. **信息收集** - 简单了解基本信息（姓名、出生年份、家乡等）
3. **深度访谈** - AI根据背景生成个性化问题，引导回忆人生故事
4. **生成回忆录** - 输入 `/memoir` 命令生成完整回忆录

### 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/save` | 手动保存当前会话 |
| `/memoir` | 生成并导出回忆录 |
| `/exit` 或 `/quit` | 结束会话 |

## 项目结构

```
memory-star-mvp/
├── demo.py              # 主程序入口
├── core/
│   ├── __init__.py
│   ├── chat_engine.py   # 对话引擎（会话管理、状态追踪）
│   ├── question_generator.py  # 提问生成器（AI驱动）
│   └── memoir_writer.py # 回忆录生成器（AI撰写）
├── utils/
│   ├── __init__.py
│   └── audio_handler.py # 语音处理（可选）
├── data/
│   ├── conversations/   # 对话历史存储
│   └── memoirs/         # 生成的回忆录
├── requirements.txt
├── .env.example
└── README.md
```

## 技术栈

- **Python 3.9+**
- **OpenRouter API** - 调用 Claude/GPT-4 等大模型
- **Rich** - 终端美化
- **SpeechRecognition** - 语音输入（可选）
- **pyttsx3** - 语音输出（可选）

## 核心模块说明

### ChatEngine（对话引擎）

管理对话会话的全生命周期：
- 会话创建与恢复
- 消息历史记录
- 用户画像构建
- 阶段推进控制

### QuestionGenerator（提问生成器）

基于AI的个性化提问系统：
- 开场白生成
- 信息收集问题
- 深度访谈问题（基于人生阶段和历史背景）
- 智能追问

### MemoirWriter（回忆录撰写器）

将对话转化为结构化回忆录：
- 全文生成
- 分章节撰写
- 多文风支持（纪实/文学/家书）
- Markdown导出

## 数据存储

### 会话数据

会话数据以JSON格式保存在 `data/conversations/` 目录：

```json
{
  "session_id": "20260221_143052",
  "profile": {
    "name": "张大爷",
    "birth_year": 1952,
    "hometown": "上海",
    "occupation": "退休教师"
  },
  "messages": [...]
}
```

### 回忆录输出

生成的回忆录以Markdown格式保存在 `data/memoirs/` 目录。

## 开发计划

### MVP（当前）
- [x] 基础对话系统
- [x] AI引导提问
- [x] 回忆录生成
- [ ] 语音交互（待完善）

### v0.2
- [ ] 多会话管理
- [ ] 记忆星球可视化
- [ ] 更多文风选项

### v1.0
- [ ] 移动端APP
- [ ] 星河网络关联
- [ ] 出版对接

## 贡献指南

欢迎提交Issue和PR！

## 许可证

MIT License

---

**记忆星河** - 让每个老人的故事都被珍藏 ✨
