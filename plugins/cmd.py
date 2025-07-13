import os
import time
import logging 
import aiohttp
import requests
import asyncio
import subprocess
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import LOG_CHANNEL, ADMINS, DAILY_LIMITS, BOT_TOKEN
from database.db import db
  

logger = logging.getLogger(__name__)   
    
       
 
@Client.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Help", callback_data="help"), InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/AnS_Bots")]
    ])

    await message.reply_text(
        "🎬✨ **Welcome to the Ultimate YouTube Downloader!** ✨🎬\n\n"
        "🚀 **Download YouTube Videos, Shorts & Music Instantly!** 🎶\n"
        "💫 Just send any YouTube link & get **high-speed downloads in seconds!**\n\n"
        "⚡ **Fast & Secure Downloads**\n"
        "✅ **Supports Videos, Shorts, MP3, MP4 in HD Quality**\n"
        "🎵 **Download Audio (MP3) & Video (MP4)**\n"
        "🔹 **No Watermark, Full HD Quality**\n"
        "🌟 **Custom Thumbnails for Each Video**\n\n"
        "💖 **Enjoy Hassle-Free Downloads!** 💖",
        reply_markup=buttons                
    )



@Client.on_message(filters.command("restart"))
async def git_pull(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("🚫 **You are not authorized to use this command!**")
      
    working_directory = "/home/ubuntu/multiuses"

    process = subprocess.Popen(
        "git pull https://github.com/Anshvachhani998/multiuses",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE

    )

    stdout, stderr = process.communicate()
    output = stdout.decode().strip()
    error = stderr.decode().strip()
    cwd = os.getcwd()
    logging.info("Raw Output (stdout): %s", output)
    logging.info("Raw Error (stderr): %s", error)

    if error and "Already up to date." not in output and "FETCH_HEAD" not in error:
        await message.reply_text(f"❌ Error occurred: {os.getcwd()}\n{error}")
        logging.info(f"get dic {cwd}")
        return

    if "Already up to date." in output:
        await message.reply_text("🚀 Repository is already up to date!")
        return
      
    if any(word in output.lower() for word in [
        "updating", "changed", "insert", "delete", "merge", "fast-forward",
        "files", "create mode", "rename", "pulling"
    ]):
        await message.reply_text(f"📦 Git Pull Output:\n```\n{output}\n```")
        await message.reply_text("🔄 Git Pull successful!\n♻ Restarting bot...")

        subprocess.Popen("bash /home/ubuntu/multiuses/start.sh", shell=True)
        os._exit(0)

    await message.reply_text(f"📦 Git Pull Output:\n```\n{output}\n```")

@Client.on_message(filters.command("checkdc") & filters.private)
async def check_dc(client, message):
    try:
        me = await client.get_me()
        dc_id = me.dc_id
        await message.reply_text(f"🌍 **Your Data Center ID:** `{dc_id}`")
    except Exception as e:
        await message.reply_text(f"❌ Error while checking DC ID:\n`{e}`")
