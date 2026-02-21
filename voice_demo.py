#!/usr/bin/env python3
"""
记忆星河 - 语音交互Demo
使用GPT-4o Realtime API或Gemini Live API

运行方式:
    uv run python voice_demo.py

环境变量:
    OPENAI_API_KEY - OpenAI API密钥
    VOICE_PROVIDER - 选择: openai / gemini / mock
"""

import os
import sys
import asyncio
import signal
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout

from memory_star.voice import (
    VoiceInterface, 
    VoiceConfig, 
    VoiceProvider,
    create_voice_handler,
    DesktopAdapter
)
from memory_star.core import ChatEngine, QuestionGenerator


console = Console()


class VoiceMemoryStar:
    """语音版记忆星河"""
    
    def __init__(self):
        self.chat_engine = ChatEngine()
        self.question_gen: QuestionGenerator = None
        self.voice_interface: VoiceInterface = None
        self.running = False
        
    def setup(self):
        """初始化配置"""
        # 检查API密钥
        openai_key = os.getenv("OPENAI_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if not openai_key and not gemini_key:
            console.print("[red]❌ 错误: 请设置 OPENAI_API_KEY 或 GEMINI_API_KEY[/red]")
            sys.exit(1)
        
        # 配置语音
        provider = os.getenv("VOICE_PROVIDER", "openai").lower()
        
        if provider == "openai" and openai_key:
            config = VoiceConfig(
                provider=VoiceProvider.OPENAI,
                api_key=openai_key,
                model="gpt-4o-realtime-preview",
                voice="alloy",  # 温暖的声音
                language="zh"
            )
        elif provider == "gemini" and gemini_key:
            config = VoiceConfig(
                provider=VoiceProvider.GEMINI,
                api_key=gemini_key,
                language="zh"
            )
        else:
            config = VoiceConfig(provider=VoiceProvider.MOCK)
        
        # 创建组件
        voice_handler = create_voice_handler(config)
        platform = DesktopAdapter()
        
        self.voice_interface = VoiceInterface(voice_handler, platform)
        self.question_gen = QuestionGenerator(api_key=openai_key or gemini_key)
        
        console.print(f"[green]✅ 语音服务已配置: {provider}[/green]")
    
    def print_banner(self):
        """打印欢迎界面"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎙️ 记忆星河 - 语音版 🎙️                                    ║
║                                                              ║
║   语音交互 · 自然对话 · 智能记录                              ║
║                                                              ║
║   提示: 说话后等待AI回复，说"结束"退出                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="cyan", border_style="blue"))
    
    async def run(self):
        """运行语音对话"""
        self.print_banner()
        self.setup()
        
        # 开始新会话
        session = self.chat_engine.start_session()
        console.print(f"[dim]会话ID: {session.session_id}[/dim]\n")
        
        # 生成开场白
        with console.status("[bold green]准备开场白..."):
            greeting = self.question_gen.generate_greeting(session.profile.to_dict())
        
        console.print(f"[blue]🤖 AI:[/blue] {greeting}\n")
        
        # 启动语音
        await self.voice_interface.start_conversation()
        self.running = True
        
        # 处理退出信号
        def signal_handler(sig, frame):
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        
        turn_count = 0
        max_turns = 20
        
        try:
            while self.running and turn_count < max_turns:
                turn_count += 1
                
                console.print(f"\n[cyan]--- 第 {turn_count} 轮 ---[/cyan]")
                
                # 语音对话
                try:
                    response = await self.voice_interface.speak_turn()
                    
                    # 记录到会话
                    session.add_message("assistant", response)
                    
                    # 检查结束
                    if any(word in response for word in ["再见", "结束", "拜拜"]):
                        console.print("\n[yellow]检测到结束信号[/yellow]")
                        break
                        
                except Exception as e:
                    console.print(f"[red]语音处理错误: {e}[/red]")
                    continue
                
                # 自动保存
                if turn_count % 5 == 0:
                    session.save()
                    console.print("[dim]💾 已自动保存[/dim]")
        
        finally:
            await self.voice_interface.stop_conversation()
            
            # 保存会话
            filepath = session.save()
            console.print(f"\n[dim]💾 会话已保存: {filepath}[/dim]")
            
            # 询问是否生成回忆录
            console.print("\n[cyan]是否生成回忆录? (y/n)[/cyan]")
            # 这里简化处理，实际可以用语音确认
            
            console.print("\n[green]感谢使用记忆星河语音版！再见 👋[/green]")


async def test_voice():
    """简单语音测试"""
    console.print("[bold]🎙️ 语音功能测试[/bold]\n")
    
    config = VoiceConfig.from_env()
    console.print(f"配置: {config.provider.value}")
    console.print(f"语音: {config.voice}")
    console.print(f"语言: {config.language}\n")
    
    if config.provider == VoiceProvider.MOCK:
        console.print("[yellow]当前为模拟模式，请设置 OPENAI_API_KEY 启用真实语音[/yellow]")
        return
    
    # 测试TTS
    console.print("[blue]测试语音合成...[/blue]")
    handler = create_voice_handler(config)
    
    try:
        await handler.connect()
        
        test_text = "您好，我是记忆星河的AI助手，很高兴为您服务。"
        console.print(f"合成文本: {test_text}")
        
        audio = await handler.speak(test_text)
        console.print(f"[green]✅ 语音合成成功，音频大小: {len(audio)} bytes[/green]")
        
        await handler.disconnect()
        
    except Exception as e:
        console.print(f"[red]❌ 测试失败: {e}[/red]")


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="记忆星河语音版")
    parser.add_argument("--test", action="store_true", help="运行语音测试")
    parser.add_argument("--text", action="store_true", help="文字模式（非语音）")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_voice())
    else:
        app = VoiceMemoryStar()
        asyncio.run(app.run())


if __name__ == "__main__":
    main()
