import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatAction

MERGE_SESSIONS = {}
TEMP_DIR = "./temp_downloads"

def human_readable_size(size_bytes):
    # Converts bytes to human readable format
    for unit in ['B','KB','MB','GB','TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def create_progress_bar(progress: float, length=20):
    done = int(progress * length)
    return '█' * done + '░' * (length - done)

async def ffmpeg_merge(file_paths: list, output_path: str):
    list_txt_path = output_path + "_list.txt"
    with open(list_txt_path, "w") as f:
        for p in file_paths:
            abs_path = os.path.abspath(p)  # absolute path use karo yahan
            f.write(f"file '{abs_path}'\n")

    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_txt_path,
        "-c", "copy",
        output_path,
        "-y"
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    os.remove(list_txt_path)

    if proc.returncode != 0:
        raise Exception(f"FFmpeg failed:\n{stderr.decode()}")

    return output_path

async def progress_callback(current, total, start_time, message, prefix):
    now = time.time()
    elapsed = now - start_time
    speed = current / elapsed if elapsed > 0 else 0
    progress = current / total if total else 0
    percent = progress * 100

    speed_str = human_readable_size(speed) + "/s"
    current_str = human_readable_size(current)
    total_str = human_readable_size(total)

    bar = create_progress_bar(progress)

    text = (
        f"{prefix}\n"
        f"{bar} {percent:.2f}%\n"
        f"{current_str} / {total_str} @ {speed_str}"
    )

    try:
        await message.edit(text)
    except:
        pass

async def download_merge_upload(client: Client, user_id: int, queue: list, chat_id: int, message):
    os.makedirs(TEMP_DIR, exist_ok=True)

    file_paths = []
    total_files = len(queue)

    # Send initial progress message
    progress_msg = await client.send_message(chat_id, f"⬇️ Downloading videos: 0/{total_files}")

    for i, f in enumerate(queue, start=1):
        out_path = os.path.join(TEMP_DIR, f"{user_id}_{i-1}.mp4")

        start_time = time.time()
        # Pyrogram's download_media me progress callback laga rahe hain
        await client.download_media(
            f["file_id"], 
            file_name=out_path,
            progress=lambda cur, tot: asyncio.create_task(progress_callback(
                cur, tot, start_time, progress_msg,
                prefix=f"⬇️ Downloading video {i}/{total_files}"
            ))
        )
        file_paths.append(out_path)

        # Update download count after each video fully downloaded
        await progress_msg.edit(f"⬇️ Downloading videos: {i}/{total_files}")

    # Check all files exist
    for p in file_paths:
        if not os.path.isfile(p):
            await progress_msg.edit(f"❌ File not found: {p}")
            return

    output_path = os.path.abspath(os.path.join(TEMP_DIR, f"{user_id}_merged.mp4"))

    # Merging progress update
    await progress_msg.edit("🔄 Merging videos... Please wait...")

    try:
        await ffmpeg_merge(file_paths, output_path)
    except Exception as e:
        await progress_msg.edit(f"❌ Merge failed:\n{str(e)}")
        for f in file_paths:
            if os.path.exists(f):
                os.remove(f)
        return

    # Upload progress message before starting upload
    await progress_msg.edit("⬆️ Uploading merged video...")

    start_time = time.time()

    async def upload_progress(current, total):
        await progress_callback(current, total, start_time, progress_msg, prefix="⬆️ Uploading merged video...")

    await client.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
    await client.send_video(
        chat_id,
        output_path,
        caption="✅ Here is your merged video!",
        progress=upload_progress
    )

    # Cleanup temp files
    for f in file_paths + [output_path]:
        if os.path.exists(f):
            os.remove(f)

    # Delete progress message after all done
    await progress_msg.delete()


@Client.on_message(filters.video)
async def handle_video(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    session = MERGE_SESSIONS.get(user_id)

    if session and session["active"]:
        session["queue"].append({
            "file_id": message.video.file_id,
            "file_name": message.video.file_name or "Unknown",
            "size": message.video.file_size,
            "duration": message.video.duration
        })

        total_size = sum(f["size"] for f in session["queue"])
        total_duration = sum(f["duration"] for f in session["queue"])

        text = "✅ Video Added to Merge Queue!\n\n**Files:**\n"
        for i, f in enumerate(session["queue"], 1):
            text += f"{i}. `{f['file_name']}`\n"
        text += f"\n📦 Total Size: {round(total_size/1024/1024, 2)} MB\n⏳ Duration: {round(total_duration/60, 2)} min\n\n"
        text += "➕ Send another video or click 🚀 Start Merge below."

        buttons = [
            [InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")],
            [InlineKeyboardButton("❌ Cancel Merge", callback_data="cancel_merge")]
        ]

        await client.edit_message_text(
            chat_id=message.chat.id,
            message_id=session["origin_msg_id"],
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # First video normal flow
    video = message.video
    text = (
        f"📹 **Video Details:**\n"
        f"• File Name: `{video.file_name}`\n"
        f"• Size: `{round(video.file_size/1024/1024, 2)} MB`\n"
        f"• Duration: `{video.duration // 60}:{video.duration % 60} min`\n\n"
        f"👇 Choose an option:"
    )
    buttons = [
        [InlineKeyboardButton("➕ Add to Merge", callback_data=f"start_merge_{message.id}")],
        [InlineKeyboardButton("❌ Delete", callback_data="delete")]
    ]
    await message.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r"start_merge_(\d+)"))
async def start_merge(client, cb):
    user_id = cb.from_user.id
    if MERGE_SESSIONS.get(user_id):
        return await cb.answer("⚠️ You have an active merge. Cancel it first.", show_alert=True)

    msg_id = int(cb.data.split("_")[2])
    orig_msg = await client.get_messages(cb.message.chat.id, msg_id)
    if not orig_msg or not orig_msg.video:
        return await cb.answer("❌ Original video not found.", show_alert=True)

    video = orig_msg.video

    first_file = {
        "file_id": video.file_id,
        "file_name": video.file_name or "Unknown",
        "size": video.file_size,
        "duration": video.duration
    }

    MERGE_SESSIONS[user_id] = {
        "active": True,
        "queue": [first_file],
        "origin_msg_id": cb.message.id
    }

    total_size = round(first_file["size"] / 1024 / 1024, 2)
    total_duration = round(first_file["duration"] / 60, 2)

    text = (
        "**✅ Merge Started!**\n\n"
        f"**1.** `{first_file['file_name']}`\n\n"
        f"📦 Total Size: {total_size} MB\n"
        f"⏳ Duration: {total_duration} min\n\n"
        "➕ Send another video or click below:"
    )

    buttons = [
        [InlineKeyboardButton("🚀 Start Merge", callback_data="do_merge")],
        [InlineKeyboardButton("❌ Cancel Merge", callback_data="cancel_merge")]
    ]

    await cb.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    await cb.answer()


@Client.on_callback_query(filters.regex("do_merge"))
async def do_merge(client, cb):
    user_id = cb.from_user.id
    session = MERGE_SESSIONS.get(user_id)

    if not session or not session["queue"]:
        return await cb.answer("❌ Merge queue is empty!", show_alert=True)

    await cb.message.edit("🔄 Merging videos... Please wait...")

    await download_merge_upload(client, user_id, session["queue"], cb.message.chat.id, cb.message)

    MERGE_SESSIONS.pop(user_id, None)
    await cb.answer()


@Client.on_callback_query(filters.regex("cancel_merge"))
async def cancel_merge(client, cb):
    user_id = cb.from_user.id
    if MERGE_SESSIONS.pop(user_id, None):
        await cb.message.edit("✅ Merge cancelled.")
    else:
        await cb.answer("❌ No active merge session.", show_alert=True)
    await cb.answer()
