from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import humanize  # size ko readable banane ke liye

@Client.on_message(filters.video)
async def video_handler(client, message):
    video = message.video
    file_name = video.file_name or "Unknown"
    size_mb = round(video.file_size / (1024 * 1024), 2)
    duration_min = video.duration // 60
    duration_sec = video.duration % 60

    text = (
        f"📹 **Video Details:**\n"
        f"• File Name: `{file_name}`\n"
        f"• Size: `{size_mb} MB`\n"
        f"• Duration: `{duration_min} min {duration_sec} sec`\n\n"
        f"👇 **Choose Processing Option:**"
    )

    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data=f"addmerge_{video.file_id}")],
        [InlineKeyboardButton("🖼️ Generate Screenshot", callback_data=f"screenshot_{video.file_id}")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data=f"audio_{video.file_id}")],
        [InlineKeyboardButton("✂️ Trim Video", callback_data=f"trim_{video.file_id}")],
        [InlineKeyboardButton("❌ Delete", callback_data=f"delete_{video.file_id}")]
    ]

    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
