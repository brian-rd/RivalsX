import discord
import os
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import re

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='r.', intents=intents)

reminders = []

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Synced slash commands for {bot.user}")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    print(f'Logged in as {bot.user}')


      
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot.run(TOKEN)