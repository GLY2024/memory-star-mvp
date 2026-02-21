# 记忆星河 MVP - 开发记录

## 2026-02-21 项目初始化

### 已完成
- [x] 项目基础架构搭建
- [x] 核心模块实现（ChatEngine, QuestionGenerator, MemoirWriter）
- [x] OpenRouter API集成
- [x] 命令行交互Demo
- [x] 数据持久化（JSON存储）

### 技术决策
1. **AI模型**: OpenRouter路由，主用Claude 3.5 Sonnet
2. **存储**: 本地JSON文件，便于演示和调试
3. **语音**: 当前使用文字交互，预留语音接口

### 待优化
- [ ] 添加语音输入/输出
- [ ] 优化提示词模板
- [ ] 增加更多历史事件数据
- [ ] 实现真正的多轮追问逻辑

## 快速测试

```bash
cd ~/memory-star-mvp
export OPENROUTER_API_KEY="your-key"
python demo.py
```
