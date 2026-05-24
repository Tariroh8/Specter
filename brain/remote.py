import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import discord
from discord.ext import commands
from brain.config import get_setting
from hands.skills import get_skill, get_all_skills_metadata

def start_discord_bot():
    token = get_setting("discord_bot_token")
    if not token:
        print("[-] Discord Bot Token not set. Remote mobile access disabled.")
        print("    Set it in the dashboard settings or via config.json.")
        return

    # Requires message_content intent
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        print(f"[+] Discord Remote Bot logged in as {bot.user}")
        print("[+] Listening for commands...")

    @bot.command(name="help")
    async def cmd_help(ctx):
        welcome_text = (
            "👋 **Welcome to Specter Remote!**\n\n"
            "I am your personal Cognitive OS bridge. From here, you can command "
            "your PC to execute tasks.\n\n"
            "**Commands:**\n"
            "`/skills` - List all available skills\n"
            "`/run <skill_name> [args]` - Run a specific skill\n\n"
            "**Example:** `/run scaffold_project type=python,name=my_app`"
        )
        await ctx.send(welcome_text)

    @bot.command(name="skills")
    async def list_skills(ctx):
        skills = get_all_skills_metadata()
        response = "**Available Skills:**\n\n"
        for name, meta in skills.items():
            response += f"🔹 **{name}**\n_{meta['description']}_\n\n"
        await ctx.send(response)

    @bot.command(name="run")
    async def run_skill_command(ctx, skill_name: str, *, args_str: str = ""):
        skill_class = get_skill(skill_name)
        if not skill_class:
            await ctx.send(f"❌ Skill '{skill_name}' not found.")
            return
            
        kwargs = {}
        if args_str:
            try:
                pairs = args_str.split(',')
                for pair in pairs:
                    k, v = pair.split('=', 1)
                    kwargs[k.strip()] = v.strip()
            except ValueError:
                await ctx.send("❌ Invalid args format. Use `key=value,key2=value2`")
                return
        
        message = await ctx.send(f"⏳ Executing `{skill_name}`...")
        
        # Execute in an executor to avoid blocking the async event loop
        def execute_skill():
            try:
                skill_instance = skill_class()
                return skill_instance.execute(**kwargs)
            except Exception as e:
                return {"success": False, "message": str(e)}

        result = await asyncio.to_thread(execute_skill)
        
        if result.get("success"):
            await message.edit(content=f"✅ **Success:**\n```\n{result.get('message')}\n```")
        else:
            await message.edit(content=f"❌ **Failed:**\n```\n{result.get('message')}\n```")

    try:
        bot.run(token)
    except Exception as e:
        print(f"[-] Failed to start Discord Bot: {e}")

if __name__ == "__main__":
    start_discord_bot()
