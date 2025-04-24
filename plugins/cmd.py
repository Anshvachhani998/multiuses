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
from pyrogram.enums import ParseMode 


logger = logging.getLogger(__name__)

 
  
@Client.on_message(filters.command("start"))
async def start(client, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Help", callback_data="help"), InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/AnS_Bots")]
    ])
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(
            LOG_CHANNEL, 
            f"**#NewUser 🔻**\n**ID -> `{message.from_user.id}`**\n**Name -> {message.from_user.mention}**"
        )
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

@Client.on_callback_query(filters.regex("start"))
async def start_hendler(client, callback_query):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Help", callback_data="help"), InlineKeyboardButton("ℹ️ About", callback_data="about")],
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/AnS_Bots")]
    ])
    
    await callback_query.message.edit_text(
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



@Client.on_callback_query(filters.regex("help"))
async def help(client, callback_query):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="start"), InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])
    
    await callback_query.message.edit_text(
        "**❓ Help Guide - YouTube Downloader**\n\n"
        "📌 Just send any **YouTube video link** here.\n"
        "🔹 The bot will instantly fetch & send your download link.\n"
        "🎥 **Supports MP4 (Video) & MP3 (Audio) Downloads**\n"
        "🎵 **High-Quality Audio & Video** (upto 320kbps & 4K)\n"
        "🌟 **Custom Thumbnail Support**\n\n"
        "**🖼️ Thumbnail Features:**\n"
        "➤ Add a custom thumbnail using `/add_thumbnail`\n"
        "➤ Remove thumbnail using `/remove_thumbnail`\n"
        "➤ View your current thumbnail using `/show_thumbnail`\n"
        "➤ If no custom thumbnail is added, the bot will **auto-fetch the YouTube thumbnail**.\n\n"
        "**🎬 How to Download?**\n"
        "1️⃣ Send a YouTube link.\n"
        "2️⃣ Choose between **MP3 (Audio) or MP4 (Video).**\n"
        "3️⃣ Get your download instantly!\n\n"
        "🚀 **Fast, Secure & Unlimited Downloads!** 💖",
        reply_markup=buttons
    )
    


@Client.on_callback_query(filters.regex("about"))
async def about(client, callback_query):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="start"), InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await callback_query.message.edit_text(
        "**ℹ️ About This Bot**\n\n"
        "🎬 **YouTube Video & Audio Downloader**\n"
        "🚀 **Fastest YouTube downloader with custom thumbnail support!**\n"
        "🎥 **Supports:** MP4 (Video) & MP3 (Audio)\n"
        "🔹 **High-Quality Downloads** (upto 320kbps & 1080p)\n"
        "🖼️ **Custom Thumbnail Support**\n\n"
        "**⚡ Features:**\n"
        "➤ **Blazing Fast & Secure**\n"
        "➤ **Unlimited Downloads**\n"
        "➤ **Easy-to-use Interface**\n\n"
        "💎 **Developed By: [AnS </> Team](https://t.me/AnS_team)**\n"
        "💖 **Enjoy & Share!**",
        reply_markup=buttons,
        disable_web_page_preview=True
    )


@Client.on_message(filters.command('users') & filters.private)
async def total_users(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("🚫 **You are not authorized to use this command!**")

    response = await message.reply("🔍 Fetching total users...")

    total_users = await db.total_users_count()

    await response.edit_text(
        f"👑 **Admin Panel**\n\n"
        f"🌍 **Total Users in Database:** `{total_users}`\n\n"
        "**🚀 Thanks for managing this bot!**"
    )
    


@Client.on_message(filters.command("stats") & filters.private)
async def stats(client, message):
    if message.from_user.id not in ADMINS:
        return await message.reply_text("🚫 **You are not authorized to use this command!**")
  
    response = await message.reply("**🔍 Fetching Bot Statistics**")

    total_users = await db.total_users_count()
    total_downloads = await db.get_total_downloads()
    
    await response.edit_text(
        f"📊 **Bot Statistics**\n\n"
        f"👥 **Total Users:** {total_users}\n"
        f"⬇️ **Total Downloads:** {total_downloads}\n\n"
        "These stats show the total number of users and downloads recorded in the system."
    )


@Client.on_message(filters.command("mytasks"))
async def my_tasks(client, message):
    user_id = message.from_user.id
    allowed, tasks_used, user_type, total_tasks = await db.get_task_limit(user_id)

    if user_type == "Premium":
        remaining_tasks = "Unlimited 🚀"
        task_limit_text = "∞ (No Limit) 🔥"
    else:
        remaining_tasks = max(0, DAILY_LIMITS - tasks_used)
        task_limit_text = f"{DAILY_LIMITS}"

    text = (
        f"👤 **User Type:** `{user_type}`\n"
        f"📅 **Today's Tasks Used:** `{tasks_used}/{task_limit_text}`\n"
        f"🔹 **Remaining Today:** `{remaining_tasks}`\n"
        f"📊 **Total Tasks Completed:** `{total_tasks}`\n"
    )

    await message.reply_text(text)
    

@Client.on_message(filters.command("checkdc") & filters.private)
async def check_dc(client, message):
    try:
        me = await client.get_me()
        dc_id = me.dc_id
        await message.reply_text(f"🌍 **Your Data Center ID:** `{dc_id}`")
    except Exception as e:
        await message.reply_text(f"❌ Error while checking DC ID:\n`{e}`")



@Client.on_message(filters.command("delete") & filters.private)
async def delete_all_users_handler(client, message):
    deleted = await db.delete_all_users()
    await message.reply(f"✅ Deleted `{deleted}` users from database.")


import subprocess
import os

@Client.on_message(filters.command("restart"))
async def restart_bot(client, message):
    await message.reply_text("♻️ Restarting bot...")

    # Execute the bash script to update and restart Docker
    subprocess.Popen("bash /root/URL-UPLOADER/start.sh", shell=True)

    # Exit the current bot process
    os._exit(0)




@Client.on_message(filters.command("gitpull"))
async def git_pull(client, message):
    process = subprocess.Popen(
        "git pull https://github.com/Anshvachhani998/URL-UPLOADER",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    stdout, stderr = process.communicate()

    # Log the output properly
    logging.info("Raw Output (stdout): %s", stdout.decode())
    logging.info("Raw Error (stderr): %s", stderr.decode())

    # Decode outputs
    output = stdout.decode().strip()
    error = stderr.decode().strip()

    # If there's an error output
    if error and "Already up to date." not in output and "HEAD is now" not in output:
        await message.reply_text(f"❌ Error occurred: \n{error}")
        return

    # Format output if no major error
    if "Already up to date." in output:
        output = "🚀 Repository is already up to date!"
    elif "HEAD is now" in output:
        output = "🔄 Git Pull successful!"

    await message.reply_text(f"🔄 Git Pull Output: \n{output}")

