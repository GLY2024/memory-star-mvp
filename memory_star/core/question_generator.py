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
    
    # 中国历史大事件时间线（扩展版）
    HISTORICAL_EVENTS = {
        "1949-1959": [
            {"name": "新中国成立", "year": 1949, "prompt": "1949年新中国成立时，您家里有什么反应？有没有印象特别深刻的事？"},
            {"name": "抗美援朝", "year": 1950, "prompt": "抗美援朝时期，您身边有人参军吗？那时候大家是什么心情？"},
            {"name": "三大改造", "year": 1956, "prompt": "公私合营的时候，您家有发生什么变化吗？"},
        ],
        "1960-1969": [
            {"name": "三年困难时期", "year": 1959, "prompt": "困难时期粮食紧张，您家是怎么度过的？有什么难忘的记忆？"},
            {"name": "文化大革命", "year": 1966, "prompt": "文革开始时，您正在做什么？那段岁月对您有什么影响？"},
            {"name": "知青下乡", "year": 1968, "prompt": "您或者您的朋友有下乡插队的经历吗？能讲讲那时候的生活吗？"},
        ],
        "1970-1979": [
            {"name": "恢复高考", "year": 1977, "prompt": "1977年恢复高考，您或者您认识的人参加了吗？当时是什么情景？"},
            {"name": "改革开放", "year": 1978, "prompt": "改革开放后，您的生活发生了什么变化？"},
            {"name": "知青返城", "year": 1978, "prompt": "知青返城时，您身边有这样的人吗？他们后来怎么样了？"},
        ],
        "1980-1989": [
            {"name": "经济特区", "year": 1980, "prompt": "深圳等经济特区建立时，您有亲戚朋友去那边发展吗？"},
            {"name": "价格闯关", "year": 1988, "prompt": "物价改革那段时间，您家是怎么应对的？"},
            {"name": "下海经商", "year": 1992, "prompt": "有人"下海"做生意吗？您怎么看那个年代的机会？"},
        ],
        "1990-1999": [
            {"name": "浦东开发", "year": 1990, "prompt": "上海浦东开发开放，您有关注吗？后来去过上海吗？"},
            {"name": "国企改革", "year": 1997, "prompt": "国企改革下岗潮，您或者您认识的人经历过吗？"},
            {"name": "香港回归", "year": 1997, "prompt": "1997年香港回归，您当时在哪里？怎么看的直播？"},
        ],
        "2000-2009": [
            {"name": "加入WTO", "year": 2001, "prompt": "中国加入WTO后，您的工作或生活有什么变化？"},
            {"name": "非典", "year": 2003, "prompt": "2003年非典时期，您印象最深的是什么？"},
            {"name": "北京奥运会", "year": 2008, "prompt": "2008年北京奥运会，您有看开幕式吗？当时什么心情？"},
        ],
        "2010-2019": [
            {"name": "世博会", "year": 2010, "prompt": "上海世博会您去过吗？印象最深的是什么？"},
            {"name": "高铁时代", "year": 2011, "prompt": "高铁越来越方便，您第一次坐高铁是什么时候？去哪里？"},
            {"name": "全面小康", "year": 2020, "prompt": "这些年中国变化很大，您觉得最让您自豪的是什么？"},
        ],
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
        """获取相关历史背景（返回预设问题）"""
        if not birth_year:
            return ""
        
        # 找到对应的历史时期
        for period, events in self.HISTORICAL_EVENTS.items():
            start, end = map(int, period.split("-"))
            if start <= birth_year <= end:
                # 返回该时期最相关的问题
                age_at_mid = 1970 - birth_year if birth_year < 1970 else birth_year - 1970
                if events:
                    # 选择中间年份的事件
                    mid_idx = len(events) // 2
                    return events[mid_idx].get("prompt", events[mid_idx]["name"])
        
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
