"""
记忆星河 - 提问生成器
基于用户画像和对话历史生成个性化引导问题
"""

import os
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime


class QuestionGenerator:
    """AI提问生成器"""
    
    # 中国历史大事件时间线
    HISTORICAL_EVENTS = {
        "1949-1959": ["新中国成立", "抗美援朝", "三大改造"],
        "1960-1969": ["三年困难时期", "文化大革命开始"],
        "1970-1979": ["恢复高考", "改革开放", "知青返城"],
        "1980-1989": ["经济特区", "价格闯关", "下海经商"],
        "1990-1999": ["浦东开发", "国企改革", "互联网进入中国"],
        "2000-2009": ["加入WTO", "北京奥运会", "金融危机"],
        "2010-2019": ["移动互联网", "高铁时代", "全面小康"],
    }
    
    # 人生阶段模板
    LIFE_STAGES = {
        "childhood": {
            "name": "童年时光",
            "age_range": (0, 12),
            "topics": ["家乡", "父母", "学校", "玩伴", "节日"]
        },
        "youth": {
            "name": "青春岁月",
            "age_range": (13, 25),
            "topics": ["求学", "初恋", "梦想", "朋友", "成长"]
        },
        "adulthood": {
            "name": "成家立业",
            "age_range": (26, 50),
            "topics": ["工作", "婚姻", "子女", "奋斗", "变迁"]
        },
        "senior": {
            "name": "退休生活",
            "age_range": (51, 100),
            "topics": ["退休", "孙辈", "爱好", "感悟", "传承"]
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3.5-sonnet"
        
    def _call_llm(self, messages: List[Dict], temperature: float = 0.8) -> str:
        """调用OpenRouter API"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
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
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API调用错误: {e}")
            return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """API失败时的备用回复"""
        return "能和我多讲讲吗？"
    
    def generate_greeting(self, profile: Dict) -> str:
        """生成开场白"""
        name = profile.get("name", "")
        
        system_prompt = """你是一位温暖、耐心的回忆录访谈助手。你的任务是通过轻松的对话，帮助老人回忆和记录他们的人生故事。
语气要亲切自然，像一位知心的晚辈。每次只问一个问题，给老人充分的表达空间。"""
        
        user_prompt = f"""请为一位老人生成一段温暖的开场白，介绍今天的目的：通过聊天记录人生故事。
老人姓名：{name if name else '未知'}
要求：
1. 语气亲切温暖
2. 说明今天的目的（轻松聊天，记录故事）
3. 询问老人希望如何称呼他/她
4. 控制在100字以内"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages, temperature=0.9)
    
    def generate_info_collection_question(self, profile: Dict, missing_fields: List[str]) -> str:
        """生成信息收集问题"""
        field_prompts = {
            "name": "请问您希望我怎么称呼您？",
            "birth_year": "您是哪一年出生的呢？",
            "hometown": "您的家乡在哪里？",
            "occupation": "您退休前是做什么工作的？",
            "education": "您的求学经历是怎样的？",
        }
        
        # 如果只有一个缺失字段，直接问
        if len(missing_fields) == 1 and missing_fields[0] in field_prompts:
            return field_prompts[missing_fields[0]]
        
        # 否则用AI生成自然的问题
        system_prompt = """你是一位温和的访谈者。请根据已知信息，自然地问出缺失的信息。
不要像查户口一样连续提问，要像聊天一样自然地获取信息。"""
        
        user_prompt = f"""已知信息：{json.dumps(profile, ensure_ascii=False)}
缺失信息：{', '.join(missing_fields)}

请生成一个自然的问题，在聊天中获取这些缺失的信息。只问一个问题，要温和自然。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages)
    
    def generate_deep_question(self, profile: Dict, conversation_history: List[Dict], 
                               current_topic: Optional[str] = None) -> str:
        """生成深度访谈问题"""
        
        # 确定当前人生阶段
        birth_year = profile.get("birth_year")
        if birth_year:
            current_year = datetime.now().year
            age = current_year - birth_year
            stage = self._determine_life_stage(age)
        else:
            stage = "adulthood"
        
        stage_info = self.LIFE_STAGES[stage]
        
        # 确定相关历史事件
        historical_context = self._get_historical_context(birth_year)
        
        system_prompt = """你是一位经验丰富的口述历史访谈者。你擅长：
1. 根据老人的背景提出有针对性的问题
2. 引导老人回忆细节和感受
3. 用共情的方式回应
4. 一个问题聚焦一个主题，给老人充分的表达空间

你的问题应该：
- 开放性强，不能用"是/否"回答
- 引导回忆具体场景、人物、对话
- 关注情感体验和人生感悟
- 温和、尊重、耐心"""
        
        # 构建上下文
        history_text = "\n".join([
            f"{'老人' if m['role'] == 'user' else '助手'}：{m['content'][:100]}..."
            for m in conversation_history[-5:]
        ])
        
        user_prompt = f"""老人画像：
{json.dumps(profile, ensure_ascii=False, indent=2)}

当前人生阶段：{stage_info['name']}（{stage_info['age_range'][0]}-{stage_info['age_range'][1]}岁）
相关历史背景：{historical_context}

近期对话：
{history_text}

{f'当前话题：{current_topic}' if current_topic else ''}

请生成一个深度访谈问题：
1. 与老人的人生阶段和历史背景相关
2. 引导回忆具体的故事和细节
3. 关注情感体验和人生感悟
4. 语气温暖亲切，像晚辈向长辈请教
5. 控制在50字以内"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages, temperature=0.85)
    
    def generate_follow_up(self, last_response: str, profile: Dict) -> str:
        """基于老人回答生成追问"""
        
        system_prompt = """你是一位善于倾听的访谈者。当老人分享了一个故事后，你会：
1. 先给予肯定和共情
2. 然后提出一个相关的追问，引导更深入的细节
3. 追问可以是关于：具体场景、人物对话、内心感受、后续发展"""
        
        user_prompt = f"""老人刚才说："{last_response[:200]}..."

请生成一个简短的追问，引导老人讲得更详细一些。要求：
1. 先简单回应老人的话（表示在听）
2. 然后提出一个具体的追问
3. 整体控制在40字以内"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages, temperature=0.8)
    
    def _determine_life_stage(self, age: int) -> str:
        """根据年龄确定人生阶段"""
        for stage_key, stage_info in self.LIFE_STAGES.items():
            if stage_info["age_range"][0] <= age <= stage_info["age_range"][1]:
                return stage_key
        return "senior"
    
    def _get_historical_context(self, birth_year: Optional[int]) -> str:
        """获取相关历史背景"""
        if not birth_year:
            return "未知年代"
        
        # 找到对应的历史时期
        for period, events in self.HISTORICAL_EVENTS.items():
            start, end = map(int, period.split("-"))
            if start <= birth_year <= end:
                return f"{period}年代，经历了：{', '.join(events[:2])}"
        
        return ""
    
    def generate_closing(self, profile: Dict, session_stats: Dict) -> str:
        """生成结束语"""
        
        system_prompt = "你是一位温暖的访谈助手，会话结束时要真诚地感谢老人。"
        
        user_prompt = f"""本次会话统计：
- 时长：{session_stats.get('duration_minutes', 0)}分钟
- 对话轮数：{session_stats.get('total_messages', 0) // 2}轮

请生成一段结束语：
1. 感谢老人的分享
2. 简单总结今天的收获
3. 说明下次会继续聊
4. 温暖、真诚"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self._call_llm(messages, temperature=0.9)
