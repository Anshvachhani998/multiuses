from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

MERGE_SESSIONS = {}


# ✅ When user sends a video
@Client.on_message(filters.video)
async def handle_video(client, message):
    if not message.from_user:
        return await message.reply("❌ Unknown sender.")
    user_id = message.from_user.id

    session = MERGE_SESSIONS.get(user_id)

    if session and session["active"]:
        origin_msg_id = session["origin_msg_id"]

        # Check: user must reply to the same origin message
        if message.reply_to_message and message.reply_to_message.id == origin_msg_id:
            # Valid: add to queue
            queue = session["queue"]
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
            text += f"\n📦 **Total Size:** {round(total_size/1024/1024, 2)} MB\n⏳ **Total Duration:** {round(total_duration/60, 2)} min"

            buttons = [
                [InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")],
                [InlineKeyboardButton("❌ Cancel Merge", callback_data="cancel_merge")]
            ]

            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=origin_msg_id,
                text=text,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        else:
            # Not same session → reject
            await message.reply(
                "⚠️ You already have an active merge session.\n"
                "Please finish or cancel it first.",
                reply_to_message_id=origin_msg_id
            )
            return

    # Else: normal new video → show options
    video = message.video
    text = (
        f"📹 **Video Details:**\n"
        f"• File Name: `{video.file_name}`\n"
        f"• Size: `{round(video.file_size/1024/1024, 2)} MB`\n"
        f"• Duration: `{video.duration // 60}:{video.duration % 60} min`\n\n"
        f"👇 **Choose an option:**"
    )
    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data=f"start_merge_{message.id}")],
        [InlineKeyboardButton("🖼️ Screenshot", callback_data="screenshot")],
        [InlineKeyboardButton("🎵 Convert to Audio", callback_data="audio")],
        [InlineKeyboardButton("✂️ Trim", callback_data="trim")],
        [InlineKeyboardButton("❌ Delete", callback_data="delete")]
    ]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


# ✅ When user clicks Add to Merge
@Client.on_callback_query(filters.regex(r"start_merge_(\d+)"))
async def start_merge_flow(client, cb):
    if not cb.from_user:
        return await cb.answer("❌ Unknown user.", show_alert=True)
    user_id = cb.from_user.id

    msg_id = int(cb.data.split("_")[2])

    orig_msg = await client.get_messages(cb.message.chat.id, msg_id)
    if not orig_msg or not orig_msg.video:
        return await cb.answer("❌ Original video not found.", show_alert=True)

    video = orig_msg.video

    MERGE_SESSIONS[user_id] = {
        "active": True,
        "queue": [{
            "file_id": video.file_id,
            "file_name": video.file_name or "Unknown",
            "size": video.file_size,
            "duration": video.duration
        }],
        "origin_msg_id": cb.message.id  # CORRECT: .id not .message_id
    }

    text = (
        "**✅ Merge Started!**\n"
        "Now send more videos as **reply** to this message.\n"
        "When done, click [🚀 Start Merge] or [❌ Cancel]."
    )
    buttons = [
        [InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")],
        [InlineKeyboardButton("❌ Cancel Merge", callback_data="cancel_merge")]
    ]

    await cb.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    await cb.answer()


# ✅ When user clicks Start Merge
@Client.on_callback_query(filters.regex("do_merge"))
async def do_merge(client, cb):
    if not cb.from_user:
        return await cb.answer("❌ Unknown user.", show_alert=True)
    user_id = cb.from_user.id

    session = MERGE_SESSIONS.get(user_id)
    if not session or not session["queue"]:
        return await cb.answer("❌ Queue empty!", show_alert=True)

    await cb.message.edit("🔄 **Merging... Please wait...**")

    # 🔽 Add your download + ffmpeg merge logic here
    await cb.message.reply("✅ **Done!** (Send final merged video here)")

    MERGE_SESSIONS.pop(user_id, None)
    await cb.answer()


# ✅ When user clicks Cancel Merge
@Client.on_callback_query(filters.regex("cancel_merge"))
async def cancel_merge(client, cb):
    if not cb.from_user:
        return await cb.answer("❌ Unknown user.", show_alert=True)
    user_id = cb.from_user.id

    if MERGE_SESSIONS.pop(user_id, None):
        await cb.message.edit("✅ **Merge cancelled.**")
    else:
        await cb.answer("❌ No active session.", show_alert=True)
    await cb.answer()
