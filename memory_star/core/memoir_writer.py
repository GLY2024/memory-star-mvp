"""
记忆星河 - 回忆录生成器
将对话历史整理成结构化的回忆录文本
"""

import os
import json
from typing import List, Dict
from datetime import datetime


class MemoirWriter:
    """回忆录撰写器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
    
    def _call_llm(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """调用OpenRouter API"""
        import requests
        
        if not self.api_key:
            return "[API密钥未配置]"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://memory-star.app",
            "X-Title": "Memory Star MVP"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API调用错误: {e}")
            return f"[生成错误: {str(e)}]"
    
    def generate_memoir(self, session_data: Dict, style: str = "纪实") -> str:
        """
        生成完整回忆录
        
        Args:
            session_data: 会话数据
            style: 文风 - 纪实/文学/家书
        """
        profile = session_data.get("profile", {})
        messages = session_data.get("messages", [])
        
        # 提取对话内容
        conversation_text = self._extract_conversation(messages)
        
        # 构建写作提示
        style_prompts = {
            "纪实": "以客观纪实的风格撰写，注重时间线和事实准确性，语言平实真诚",
            "文学": "以散文式的文学风格撰写，注重情感表达和场景描写，语言优美流畅",
            "家书": "以对子孙后代说话的口吻撰写，亲切自然，充满温情和教诲"
        }
        
        style_desc = style_prompts.get(style, style_prompts["纪实"])
        
        system_prompt = f"""你是一位专业的回忆录撰写人。请将访谈记录整理成一篇完整的回忆录。

写作要求：
1. {style_desc}
2. 以第一人称"我"叙述
3. 按时间顺序组织内容
4. 保留老人的原话和语气
5. 适当补充过渡和背景，使文章连贯
6. 字数控制在2000-3000字
7. 包含标题"""
        
        user_prompt = f"""老人信息：
姓名：{profile.get('name', '未知')}
出生年份：{profile.get('birth_year', '未知')}
家乡：{profile.get('hometown', '未知')}
职业：{profile.get('occupation', '未知')}

访谈记录：
{conversation_text}

请根据以上信息，撰写一篇完整的回忆录。"""
        
        api_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(api_messages, temperature=0.75, max_tokens=3000)
    
    def generate_chapter(self, topic: str, related_messages: List[Dict], 
                        profile: Dict, style: str = "纪实") -> str:
        """生成单章内容"""
        
        conversation_text = self._extract_conversation(related_messages)
        
        system_prompt = """你是一位专业的回忆录撰写人。请将关于特定主题的访谈内容整理成一章回忆录。"""
        
        user_prompt = f"""主题：{topic}

老人信息：
{json.dumps(profile, ensure_ascii=False)}

相关访谈内容：
{conversation_text}

请撰写一章回忆录（约800-1200字），围绕"{topic}"这个主题展开。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages, temperature=0.75, max_tokens=2000)
    
    def generate_summary(self, session_data: Dict) -> str:
        """生成会话摘要"""
        
        profile = session_data.get("profile", {})
        messages = session_data.get("messages", [])
        
        # 只提取用户消息进行摘要
        user_messages = [m for m in messages if m.get("role") == "user"]
        user_content = "\n".join([m.get("content", "") for m in user_messages[-10:]])
        
        system_prompt = "请总结本次访谈的主要内容和收获。"
        
        user_prompt = f"""老人：{profile.get('name', '未知')}

本次访谈内容：
{user_content[:2000]}

请生成一份简短的访谈摘要（200字以内），包括：
1. 主要谈及的话题
2. 印象深刻的内容
3. 下次可以继续深入的方向"""
        
        api_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(api_messages, temperature=0.7, max_tokens=500)
    
    def _extract_conversation(self, messages: List[Dict]) -> str:
        """提取对话内容"""
        lines = []
        for msg in messages:
            role = "老人" if msg.get("role") == "user" else "访谈者"
            content = msg.get("content", "")
            lines.append(f"{role}：{content}")
        return "\n".join(lines)
    
    def export_to_markdown(self, memoir_text: str, profile: Dict, 
                          output_path: str = None) -> str:
        """导出为Markdown格式"""
        
        timestamp = datetime.now().strftime("%Y年%m月%d日")
        
        md_content = f"""# {profile.get('name', '未知')}回忆录

> 访谈日期：{timestamp}  
> 记录方式：AI辅助访谈

---

## 基本信息

- **姓名**：{profile.get('name', '未知')}
- **出生年份**：{profile.get('birth_year', '未知')}
- **家乡**：{profile.get('hometown', '未知')}
- **职业**：{profile.get('occupation', '未知')}

---

{memoir_text}

---

*本文由记忆星河AI辅助生成*
"""
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        return md_content
