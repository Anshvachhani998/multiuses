from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

MERGE_SESSIONS = {}

# ✅ When user sends video
@Client.on_message(filters.video)
async def handle_video(client, message):
    user_id = message.from_user.id

    # Agar user merge mode me hai → queue me add karo
    if MERGE_SESSIONS.get(user_id, {}).get("active"):
        queue = MERGE_SESSIONS[user_id]["queue"]
        queue.append({
            "file_id": message.video.file_id,
            "file_name": message.video.file_name or "Unknown",
            "size": message.video.file_size,
            "duration": message.video.duration
        })

        total_size = sum(x["size"] for x in queue)
        total_duration = sum(x["duration"] for x in queue)

        text = "✅ Video Added to Merge Queue!\n\n**Files:**\n"
        for i, f in enumerate(queue, 1):
            text += f"{i}. `{f['file_name']}`\n"

        text += f"\n📦 **Total Size:** {round(total_size/1024/1024,2)} MB\n⏳ **Total Duration:** {round(total_duration/60,2)} min"

        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")]]
        )

        await message.reply(text, reply_markup=btn)

        return

    # ELSE → normal pehla video → options do
    video = message.video
    text = (
        f"📹 **Video Details:**\n"
        f"• File Name: `{video.file_name}`\n"
        f"• Size: `{round(video.file_size/1024/1024, 2)} MB`\n"
        f"• Duration: `{video.duration // 60}:{video.duration % 60} min`\n\n"
        f"👇 **Choose Option:**"
    )
    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data=f"start_merge_{video.file_id}")],
        [InlineKeyboardButton("🖼️ Screenshot", callback_data="screenshot")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data="audio")],
        [InlineKeyboardButton("✂️ Trim", callback_data="trim")],
        [InlineKeyboardButton("❌ Delete", callback_data="delete")]
    ]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


# ✅ When user clicks Add to Merge → pehla video bhi queue me daalo
@Client.on_callback_query(filters.regex(r"start_merge_(.+)"))
async def start_merge_flow(client, cb):
    user_id = cb.from_user.id
    file_id = cb.data.split("_", 1)[1]

    # Pehla video ki info laane ke liye — original message se lo
    video = cb.message.reply_to_message.video if cb.message.reply_to_message else None

    if not video:
        await cb.answer("❌ Can't find original video.", show_alert=True)
        return

    MERGE_SESSIONS[user_id] = {
        "active": True,
        "queue": [{
            "file_id": file_id,
            "file_name": video.file_name or "Unknown",
            "size": video.file_size,
            "duration": video.duration
        }]
    }

    await cb.message.reply(
        "**✅ Merge Started!**\nAb baaki videos bhejo.\nSab ho jaye toh [🚀 Start Merge] dabao."
    )
    await cb.answer()


# ✅ When user clicks Start Merge
@Client.on_callback_query(filters.regex("do_merge"))
async def do_merge(client, cb):
    user_id = cb.from_user.id
    session = MERGE_SESSIONS.get(user_id)

    if not session or not session["queue"]:
        await cb.answer("❌ Queue empty!", show_alert=True)
        return

    await cb.message.reply("🔄 **Merging... Please wait...**")

    # Here you'll write:
    # 1. Download all videos using file_id → save temp dir
    # 2. Make list.txt for FFmpeg concat
    # 3. Run FFmpeg concat → output.mp4
    # 4. Upload final merged file back to user

    await cb.message.reply("✅ **Done!** (Here you send the merged video.)")

    # Clear user session
    MERGE_SESSIONS.pop(user_id, None)

    await cb.answer()
