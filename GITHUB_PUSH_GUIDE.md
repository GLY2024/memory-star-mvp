# 记忆星河 MVP - GitHub推送指南

## 项目已创建完成 ✅

项目位置：`~/memory-star-mvp/`

## 推送到GitHub步骤

### 方法一：使用GitHub CLI（推荐）

```bash
# 1. 安装GitHub CLI（如未安装）
# Ubuntu/Debian:
sudo apt install gh

# macOS:
brew install gh

# 2. 登录GitHub
gh auth login
# 选择: HTTPS → 使用浏览器登录 → 按提示完成认证

# 3. 创建仓库并推送
cd ~/memory-star-mvp
gh repo create memory-star-mvp --public --description "AI辅助老年人回忆录撰写平台 - MVP版本" --source=. --remote=origin --push
```

### 方法二：使用SSH密钥

```bash
# 1. 生成SSH密钥（如未生成）
ssh-keygen -t ed25519 -C "252045255+GLY2024@users.noreply.github.com"

# 2. 添加公钥到GitHub
# 复制 ~/.ssh/id_ed25519.pub 内容
# 访问: https://github.com/settings/keys → New SSH key

# 3. 配置远程仓库为SSH地址
cd ~/memory-star-mvp
git remote add origin git@github.com:ganansuan647/memory-star-mvp.git

# 4. 推送
git push -u origin main
```

### 方法三：使用Personal Access Token

```bash
# 1. 在GitHub创建Token
# 访问: https://github.com/settings/tokens → Generate new token
# 勾选: repo 权限

# 2. 配置Git使用Token
git config --global credential.helper cache

# 3. 推送（会提示输入密码，输入Token）
cd ~/memory-star-mvp
git push -u origin main
# Username: ganansuan647
# Password: [输入你的Personal Access Token]
```

## 项目结构

```
memory-star-mvp/
├── demo.py              # 主程序入口
├── core/                # 核心模块
│   ├── chat_engine.py   # 对话引擎
│   ├── question_generator.py  # AI提问生成
│   └── memoir_writer.py # 回忆录生成
├── utils/               # 工具模块
│   └── audio_handler.py # 语音处理
├── data/                # 数据存储
│   ├── conversations/   # 对话历史
│   └── memoirs/         # 生成的回忆录
├── requirements.txt     # 依赖
├── .env.example         # 环境变量示例
└── README.md            # 项目说明
```

## 运行Demo

```bash
cd ~/memory-star-mvp
export OPENROUTER_API_KEY="your-api-key"
python demo.py
```

## 功能演示

### 1. 启动Demo
```
✨ 记忆星河 ✨
Memory Star - AI辅助回忆录撰写平台

💾 会话ID: 20260221_143052

🤖 AI助手: 您好啊！今天很荣幸能和您坐在一起聊聊天...
```

### 2. 自然对话
- AI会自动收集基本信息（姓名、出生年份等）
- 根据背景生成个性化问题
- 支持深度追问

### 3. 生成回忆录
```
👤 您: /memoir

📝 正在生成回忆录...

[显示生成的回忆录预览]

✅ 回忆录已保存: data/memoirs/20260221_143052.md
```

### 4. 可用命令
- `/help` - 显示帮助
- `/save` - 保存会话
- `/memoir` - 生成回忆录
- `/exit` - 结束会话

## API密钥安全提示

⚠️ **重要**: 不要将API密钥提交到Git仓库！

项目已配置 `.gitignore` 忽略 `.env` 文件，请确保：
```bash
# 本地设置环境变量
export OPENROUTER_API_KEY="your-key"

# 不要执行以下操作！
# echo "API_KEY=xxx" > .env  # 然后提交
```

## 后续开发计划

- [ ] 语音输入/输出
- [ ] 记忆星球可视化
- [ ] 多文风支持
- [ ] 移动端适配

---

**记忆星河** - 让每个老人的故事都被珍藏 ✨
