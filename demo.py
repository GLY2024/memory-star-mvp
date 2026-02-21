#!/usr/bin/env python3
"""
记忆星河 MVP Demo
AI辅助老年人回忆录撰写平台 - 最小可行性验证

使用方法:
    python demo.py
    
环境变量:
    OPENROUTER_API_KEY: OpenRouter API密钥
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from core import ChatEngine, QuestionGenerator, MemoirWriter
from utils import AudioHandler, get_input_with_voice_option


console = Console()


class MemoryStarDemo:
    """记忆星河Demo主类"""
    
    def __init__(self):
        self.chat_engine = ChatEngine()
        self.question_gen: Optional[QuestionGenerator] = None
        self.memoir_writer: Optional[MemoirWriter] = None
        self.audio_handler: Optional[AudioHandler] = None
        self._init_components()
    
    def _init_components(self):
        """初始化组件"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if api_key:
            self.question_gen = QuestionGenerator(api_key)
            self.memoir_writer = MemoirWriter(api_key)
        else:
            console.print("[yellow]⚠️ 未设置 OPENROUTER_API_KEY，将使用模拟模式[/yellow]")
        
        # 语音功能默认关闭（需要额外依赖）
        enable_voice = os.getenv("ENABLE_VOICE", "false").lower() == "true"
        self.audio_handler = AudioHandler(enable_voice=enable_voice)
    
    def print_banner(self):
        """打印欢迎横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ✨ 记忆星河 ✨                                              ║
║   Memory Star - AI辅助回忆录撰写平台                          ║
║                                                              ║
║   让每个老人的故事都被珍藏                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="cyan", border_style="blue"))
    
    def print_help(self):
        """打印帮助信息"""
        help_text = """
[bold]可用命令：[/bold]
  [green]/help[/green]     - 显示帮助
  [green]/save[/green]     - 保存当前会话
  [green]/memoir[/green]   - 生成回忆录
  [green]/exit[/green]     - 结束会话
  [green]/quit[/green]     - 同上
        """
        console.print(help_text)
    
    def run(self):
        """运行Demo"""
        self.print_banner()
        
        # 检查API密钥
        if not self.question_gen:
            console.print("\n[red]❌ 错误：未设置 OPENROUTER_API_KEY 环境变量[/red]")
            console.print("请运行: export OPENROUTER_API_KEY='your-api-key'")
            return 1
        
        # 开始新会话
        session = self.chat_engine.start_session()
        console.print(f"\n[dim]会话ID: {session.session_id}[/dim]\n")
        
        # 生成开场白
        with console.status("[bold green]正在生成开场白..."):
            greeting = self.question_gen.generate_greeting(session.profile.to_dict())
        
        console.print(f"\n[blue]🤖 AI助手:[/blue] {greeting}\n")
        
        # 主对话循环
        turn_count = 0
        max_turns = 20  # 演示模式限制轮数
        
        try:
            while turn_count < max_turns:
                # 获取用户输入
                user_input = self._get_input()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith("/"):
                    if self._handle_command(user_input):
                        break
                    continue
                
                # 记录用户消息
                session.add_message("user", user_input)
                
                # 提取关键信息
                extracted_info = self.chat_engine.session.extract_key_info(user_input)
                if extracted_info:
                    session.update_profile(**extracted_info)
                
                # 生成回复
                turn_count += 1
                
                with console.status("[bold green]AI思考中..."):
                    response = self._generate_response(user_input, turn_count)
                
                # 记录AI消息
                session.add_message("assistant", response)
                
                # 显示回复
                console.print(f"\n[blue]🤖 AI助手:[/blue] {response}\n")
                
                # 自动保存
                if turn_count % 5 == 0:
                    session.save()
        
        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠️ 用户中断[/yellow]")
        
        # 结束会话
        self._end_session()
        return 0
    
    def _get_input(self) -> str:
        """获取用户输入"""
        try:
            user_input = console.input("[bold green]👤 您:[/bold green] ").strip()
            return user_input
        except EOFError:
            return "/exit"
    
    def _generate_response(self, user_input: str, turn_count: int) -> str:
        """生成AI回复"""
        session = self.chat_engine.session
        profile = session.profile.to_dict()
        history = session.get_recent_context(n=5)
        
        # 根据会话阶段选择生成策略
        if session.current_stage == "greeting":
            # 收集基本信息阶段
            missing_fields = self._get_missing_fields(profile)
            
            if missing_fields and turn_count < 5:
                response = self.question_gen.generate_info_collection_question(
                    profile, missing_fields
                )
            else:
                # 进入深度访谈阶段
                self.chat_engine.advance_stage()
                response = self.question_gen.generate_deep_question(
                    profile, history
                )
        
        else:
            # 深度访谈阶段
            # 50%概率追问，50%概率新话题
            if turn_count % 2 == 0:
                response = self.question_gen.generate_follow_up(
                    user_input, profile
                )
            else:
                response = self.question_gen.generate_deep_question(
                    profile, history
                )
        
        return response
    
    def _get_missing_fields(self, profile: dict) -> list:
        """获取缺失的关键字段"""
        important_fields = ["name", "birth_year", "hometown", "occupation"]
        missing = []
        
        for field in important_fields:
            if not profile.get(field):
                missing.append(field)
        
        return missing
    
    def _handle_command(self, cmd: str) -> bool:
        """处理命令，返回True表示退出"""
        cmd = cmd.lower().strip()
        
        if cmd in ["/exit", "/quit"]:
            return True
        
        elif cmd == "/help":
            self.print_help()
        
        elif cmd == "/save":
            filepath = self.chat_engine.session.save()
            console.print(f"[green]✅ 会话已保存: {filepath}[/green]")
        
        elif cmd == "/memoir":
            self._generate_memoir()
        
        else:
            console.print(f"[yellow]未知命令: {cmd}，输入 /help 查看帮助[/yellow]")
        
        return False
    
    def _generate_memoir(self):
        """生成回忆录"""
        session = self.chat_engine.session
        
        if not self.memoir_writer:
            console.print("[red]❌ 回忆录生成器未初始化[/red]")
            return
        
        # 准备会话数据
        session_data = {
            "profile": session.profile.to_dict(),
            "messages": [m.to_dict() for m in session.messages],
            "session_id": session.session_id
        }
        
        console.print("\n[bold cyan]📝 正在生成回忆录...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("AI撰写中...", total=None)
            
            memoir_text = self.memoir_writer.generate_memoir(session_data)
            
            progress.update(task, completed=True)
        
        # 显示生成的回忆录
        console.print(Panel(memoir_text, title="回忆录预览", border_style="green"))
        
        # 保存到文件
        output_dir = "data/memoirs"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{session.session_id}.md")
        
        self.memoir_writer.export_to_markdown(
            memoir_text, 
            session.profile.to_dict(),
            output_path
        )
        
        console.print(f"\n[green]✅ 回忆录已保存: {output_path}[/green]\n")
    
    def _end_session(self):
        """结束会话"""
        session = self.chat_engine.session
        
        # 保存会话
        filepath = session.save()
        console.print(f"\n[dim]💾 会话已保存: {filepath}[/dim]")
        
        # 生成结束语
        if self.question_gen:
            stats = self.chat_engine.get_session_summary()
            closing = self.question_gen.generate_closing(
                session.profile.to_dict(),
                stats
            )
            console.print(f"\n[blue]🤖 AI助手:[/blue] {closing}\n")
        
        console.print("[cyan]感谢使用记忆星河！再见 👋[/cyan]\n")


def main():
    """主入口"""
    demo = MemoryStarDemo()
    return demo.run()


if __name__ == "__main__":
    sys.exit(main())
