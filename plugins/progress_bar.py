import os
import math
import time
import psutil
from utils import humanbytes, TimeFormatter
import logging
import asyncio
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start

    if current == total or round(diff % 5.00) == 0:
        percentage = (current / total) * 100
        speed = current / diff if diff > 0 else 0
        estimated_total_time = TimeFormatter(milliseconds=(total - current) / speed * 1000) if speed > 0 else "∞"

        # CPU & RAM Usage
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        # Progress Bar
        progress_bar = "■" + "■" * math.floor(percentage / 5) + "□" * (20 - math.floor(percentage / 5))

        text = (
            f"**╭───────Uᴘʟᴏᴀᴅɪɴɢ───────〄**\n"
            f"**│**\n"
            f"**├📁 Sɪᴢᴇ : {humanbytes(current)} ✗ {humanbytes(total)}**\n"
            f"**│**\n"
            f"**├📦 Pʀᴏɢʀᴇꜱꜱ : {round(percentage, 2)}%**\n"
            f"**│**\n"
            f"**├🚀 Sᴘᴇᴇᴅ : {humanbytes(speed)}/s**\n"
            f"**│**\n"
            f"**├⏱️ Eᴛᴀ : {estimated_total_time}**\n"
            f"**│**\n"
            f"**├🏮 Cᴘᴜ : {cpu_usage}%  |  Rᴀᴍ : {ram_usage}%**\n"
            f"**│**\n"
            f"**╰─[{progress_bar}]**"
        )

        try:
            await message.edit(text=text)
        except:
            pass


async def progress_bar(current, total, status_message, start_time, last_update_time, label):
    try:
        elapsed_time = time.time() - start_time
        speed = current / elapsed_time / 1024 / 1024 if elapsed_time > 0 else 0  # MB/s
        uploaded = current / 1024 / 1024

        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        if time.time() - last_update_time[0] < 2:
            return
        last_update_time[0] = time.time()

        cancel_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{status_message.chat.id}")]
        ])

        if not total or "~" in str(total) or total < current:
            animation = ["□■□□□□□□□□□□□□□□□", "□□■□□□□□□□□□□□□□□", "□□□■□□□□□□□□□□□□□",
                         "□□□□■□□□□□□□□□□□□", "□□□□□■□□□□□□□□□□□", "□□□□□□■□□□□□□□□□□"]
            index = int(time.time()) % len(animation)
            text = (
                f"**╭─────Dᴏᴡɴʟᴏᴀᴅɪɴɢ─────〄**\n"
                "**│**\n"
                f"**├📁 Sɪᴢᴇ : {humanbytes(current)} ✗ Unknown**\n"
                "**│**\n"
                f"**├🚀 Sᴘᴇᴇᴅ : {speed:.2f} 𝙼𝙱/s**\n"
                "**│**\n"
                f"**├🏮 Cᴘᴜ : {cpu_usage}%  |  Rᴀᴍ : {ram_usage}%**\n"
                "**│**\n"
                f"**╰─[{animation[index]}]**"
            )
        else:
            safe_total = max(total, current + 1)
            percentage = min((current / safe_total) * 100, 100.0)
            remaining_size = (safe_total - current) / 1024 / 1024
            eta = (remaining_size / speed) if speed > 0 else 0
            eta = min(max(eta, 0), 60 * 60 * 24)
            eta_min = int(eta // 60)
            eta_sec = int(eta % 60)

            progress_blocks = int(percentage // 5)
            progress_bar_str = "■" * progress_blocks + "□" * (20 - progress_blocks)

            total_str = humanbytes(safe_total)

            text = (
                f"**╭─────Dᴏᴡɴʟᴏᴀᴅɪɴɢ─────〄**\n"
                "**│**\n"
                f"**├📁 Sɪᴢᴇ : {humanbytes(current)} ✗ {total_str}**\n"
                "**│**\n"
                f"**├📦 Pʀᴏɢʀᴇꜱꜱ : {percentage:.2f}%**\n"
                "**│**\n"
                f"**├🚀 Sᴘᴇᴇᴅ : {speed:.2f} 𝙼𝙱/s**\n"
                "**│**\n"
                f"**├⏱️ Eᴛᴀ : {eta_min}𝚖𝚒𝚗, {eta_sec}𝚜𝚎𝚌**\n"
                "**│**\n"
                f"**├🏮 Cᴘᴜ : {cpu_usage}%  |  Rᴀᴍ : {ram_usage}%**\n"
                "**│**\n"
                f"**╰─[{progress_bar_str}]**"
            )

        # Only edit if content is different
        if status_message.text != text:
            await status_message.edit(
                text,
                reply_markup=cancel_button
            )

        # Completion message
        if total and percentage >= 100:
            await status_message.edit(
                "✅ **Fɪʟᴇ Dᴏᴡɴʟᴏᴀᴅ Cᴏᴍᴘʟᴇᴛᴇ!**\n**🎵 Aᴜᴅɪᴏ Dᴏᴡɴʟᴏᴀᴅɪɴɢ...**"
            )

    except Exception as e:
        print(f"Error updating progress: {e}")

async def update_progress(message, queue):
    """Updates progress bar while downloading."""
    last_update_time = [0]
    start_time = time.time()

    while True:
        data = await queue.get()
        if data is None:
            break

        if isinstance(data, dict):
            status = data.get("status")
            if status == "finished":
                await message.edit_text("✅ **Download Finished!**")
                break
            elif status == "error":
                await message.edit_text("❌ **Error occurred!**")
                break
        else:
            current, total, label = data
            current_label = label
            await progress_bar(current, total, message, start_time, last_update_time, current_label)


def yt_progress_hook(d, queue, client, cancel_event):
    """Reports progress of yt-dlp to async queue in a thread-safe way and supports cancellation."""
    if cancel_event.is_set():
        raise Exception("Download cancelled by user")

    if d['status'] == 'downloading':
        current = d['downloaded_bytes']
        total = d.get('total_bytes', 1)
        asyncio.run_coroutine_threadsafe(queue.put((current, total, "⬇ **Downloading...**")), client.loop)

    elif d['status'] == 'finished':
        current = d.get('downloaded_bytes', 1)
        total = d.get('total_bytes', current)
        asyncio.run_coroutine_threadsafe(queue.put((current, total, "✅ **Download Complete! Uploading...**")), client.loop)
        asyncio.run_coroutine_threadsafe(queue.put(None), client.loop)

