from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import uuid

# Temporary in-memory DB (production me Mongo ya SQLite use karo)
MERGE_SESSIONS = {}


@Client.on_message(filters.video)
async def handle_video(client, message):
    user_id = message.from_user.id
    # If user already in merge flow, add directly
    if MERGE_SESSION.get(user_id, {}).get("active"):
        # Already in merge flow → add file
        queue = MERGE_SESSION[user_id]["queue"]
        queue.append({
          "file_id": message.video.file_id,
          "file_name": message.video.file_name or "Unknown",
          "size": message.video.file_size,
          "duration": message.video.duration
        })

        total_size = sum(x["size"] for x in queue)
        total_duration = sum(x["duration"] for x in queue)

        text = "✅ Added to Merge!\n\nFiles:\n"
        for i, f in enumerate(queue, 1):
            text += f"{i}. {f['file_name']}\n"

        text += f"\n📦 Total: {round(total_size/1024/1024,2)} MB | ⏳ {round(total_duration/60,2)} min"

        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")]]
        )

        await message.reply(text, reply_markup=btn)

        return

    # ELSE: Normal first time buttons
    video = message.video
    text = (
        f"📹 Video Details:\n"
        f"• File Name: `{video.file_name}`\n"
        f"• Size: `{round(video.file_size/1024/1024,2)} MB`\n"
        f"• Duration: `{video.duration // 60}:{video.duration % 60}` min\n\n"
        f"👇 Choose option:"
    )
    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data="start_merge")],
        [InlineKeyboardButton("🖼️ Screenshot", callback_data="screenshot")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data="audio")],
        [InlineKeyboardButton("✂️ Trim", callback_data="trim")],
        [InlineKeyboardButton("❌ Delete", callback_data="delete")]
    ]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))



@Client.on_callback_query(filters.regex("start_merge"))
async def start_merge_flow(client, cb):
    user_id = cb.from_user.id
    MERGE_SESSION[user_id] = {
      "active": True,
      "queue": []
    }
    await cb.message.reply(
      "**✅ Merge started!**\nAb jo videos merge karne hain woh bhejte jao.\nJab done ho jao, [🚀 Start Merge] dabao."
    )
    await cb.answer()



@Client.on_callback_query(filters.regex("do_merge"))
async def do_merge(client, cb):
    user_id = cb.from_user.id
    session = MERGE_SESSION.get(user_id)

    if not session or not session["queue"]:
        await cb.answer("❌ Queue empty!", show_alert=True)
        return

    await cb.message.reply("🔄 Merging...")

    # Yaha tum FFmpeg se sab download karke merge karo
    # Dummy example:
    # for file in session["queue"]:
    #   download file_id
    # make list.txt → ffmpeg concat → upload

    await cb.message.reply("✅ Done! Merged file bhej raha hoon...")

    MERGE_SESSION.pop(user_id)

