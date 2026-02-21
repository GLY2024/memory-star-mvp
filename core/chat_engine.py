"""
记忆星河 - 对话引擎
处理与老人的多轮对话，管理会话状态
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class Message:
    """单条消息"""
    role: str  # 'user' 或 'assistant'
    content: str
    timestamp: str
    message_type: str = 'text'  # 'text' 或 'voice'
    
    def to_dict(self):
        return asdict(self)


@dataclass
class UserProfile:
    """用户画像"""
    name: str = ""
    birth_year: Optional[int] = None
    hometown: str = ""
    occupation: str = ""
    education: str = ""
    major_events: List[str] = None
    interests: List[str] = None
    
    def __post_init__(self):
        if self.major_events is None:
            self.major_events = []
        if self.interests is None:
            self.interests = []
    
    def to_dict(self):
        return asdict(self)


class ConversationSession:
    """对话会话管理"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages: List[Message] = []
        self.profile = UserProfile()
        self.current_stage = "greeting"  # greeting, info_collection, deep_interview, closing
        self.current_topic = None
        self.start_time = datetime.now().isoformat()
        
    def add_message(self, role: str, content: str, message_type: str = 'text'):
        """添加消息到会话"""
        msg = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            message_type=message_type
        )
        self.messages.append(msg)
        
    def get_recent_context(self, n: int = 10) -> List[Dict]:
        """获取最近n条消息作为上下文"""
        recent = self.messages[-n:] if len(self.messages) > n else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]
    
    def update_profile(self, **kwargs):
        """更新用户画像"""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
    
    def save(self, data_dir: str = "data/conversations"):
        """保存会话到文件"""
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, f"{self.session_id}.json")
        
        data = {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "profile": self.profile.to_dict(),
            "current_stage": self.current_stage,
            "current_topic": self.current_topic,
            "messages": [m.to_dict() for m in self.messages]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    @classmethod
    def load(cls, session_id: str, data_dir: str = "data/conversations"):
        """从文件加载会话"""
        filepath = os.path.join(data_dir, f"{session_id}.json")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = cls(data["session_id"])
        session.start_time = data["start_time"]
        session.current_stage = data["current_stage"]
        session.current_topic = data["current_topic"]
        
        # 恢复用户画像
        profile_data = data.get("profile", {})
        session.profile = UserProfile(**profile_data)
        
        # 恢复消息
        for msg_data in data.get("messages", []):
            session.messages.append(Message(**msg_data))
        
        return session


class ChatEngine:
    """对话引擎主类"""
    
    STAGES = ["greeting", "info_collection", "deep_interview", "closing"]
    
    def __init__(self):
        self.session = None
        
    def start_session(self, session_id: str = None) -> ConversationSession:
        """开始新会话"""
        self.session = ConversationSession(session_id)
        return self.session
    
    def load_session(self, session_id: str) -> ConversationSession:
        """加载已有会话"""
        self.session = ConversationSession.load(session_id)
        return self.session
    
    def get_session_summary(self) -> Dict:
        """获取会话摘要"""
        if not self.session:
            return {}
        
        return {
            "session_id": self.session.session_id,
            "duration_minutes": self._calculate_duration(),
            "total_messages": len(self.session.messages),
            "current_stage": self.session.current_stage,
            "profile": self.session.profile.to_dict()
        }
    
    def _calculate_duration(self) -> int:
        """计算会话时长（分钟）"""
        from datetime import datetime
        start = datetime.fromisoformat(self.session.start_time)
        now = datetime.now()
        return int((now - start).total_seconds() / 60)
    
    def advance_stage(self):
        """推进到下一阶段"""
        if not self.session:
            return
        
        current_idx = self.STAGES.index(self.session.current_stage)
        if current_idx < len(self.STAGES) - 1:
            self.session.current_stage = self.STAGES[current_idx + 1]
    
    def extract_key_info(self, user_input: str) -> Dict:
        """从用户输入中提取关键信息（简化版）"""
        info = {}
        
        # 简单的关键词提取
        if "岁" in user_input or "年" in user_input:
            # 尝试提取年份
            import re
            years = re.findall(r'(19\d{2}|20\d{2})', user_input)
            if years:
                info["birth_year"] = int(years[0])
        
        if "我是" in user_input or "叫" in user_input:
            # 尝试提取名字
            import re
            names = re.findall(r'(?:我是|叫)([^，。,.]+)', user_input)
            if names:
                info["name"] = names[0].strip()
        
        return info
