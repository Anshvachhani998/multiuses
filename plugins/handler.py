from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import uuid

# Temporary in-memory DB (production me Mongo ya SQLite use karo)
MERGE_SESSIONS = {}

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

    # Make unique short ID
    unique_id = str(uuid.uuid4())[:8]

    # Save file_id temporarily
    MERGE_SESSIONS[unique_id] = {
        "file_id": video.file_id,
        "file_name": file_name,
        "size": video.file_size,
        "duration": video.duration,
        "user_id": message.from_user.id
    }

    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data=f"addmerge_{unique_id}")],
        [InlineKeyboardButton("🖼️ Generate Screenshot", callback_data=f"screenshot_{unique_id}")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data=f"audio_{unique_id}")],
        [InlineKeyboardButton("✂️ Trim Video", callback_data=f"trim_{unique_id}")],
        [InlineKeyboardButton("❌ Delete", callback_data=f"delete_{unique_id}")]
    ]

    await message.reply(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# Queue for every user
USER_QUEUE = {}

@Client.on_callback_query(filters.regex(r"addmerge_(.+)"))
async def add_to_merge(client, callback_query: CallbackQuery):
    unique_id = callback_query.data.split("_", 1)[1]
    session = MERGE_SESSIONS.get(unique_id)

    if not session:
        await callback_query.answer("❌ Session expired!", show_alert=True)
        return

    user_id = session["user_id"]

    # Get or create queue
    queue = USER_QUEUE.get(user_id, [])
    queue.append(session)
    USER_QUEUE[user_id] = queue

    total_size = sum([v["size"] for v in queue])
    total_duration = sum([v["duration"] for v in queue])

    text = (
        f"✅ Added `{session['file_name']}` to merge queue!\n\n"
        f"📦 **Total Files:** {len(queue)}\n"
        f"📦 **Total Size:** {round(total_size / (1024 * 1024), 2)} MB\n"
        f"⏳ **Total Duration:** {round(total_duration / 60, 2)} min"
    )

    await callback_query.answer("✅ Added to Merge!", show_alert=False)
    await callback_query.message.reply(text)
