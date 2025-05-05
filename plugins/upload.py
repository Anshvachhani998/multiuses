import os
import time
import asyncio
from math import ceil
import logging
import ffmpeg
from info import DUMP_CHANNEL, LOG_CHANNEL
from database.db import db
from utils import split_video, active_tasks
from plugins.progress_bar import progress_for_pyrogram

async def upload_media(client, chat_id, output_filename, caption, duration, width, height, status_msg, thumbnail_path, youtube_link):
    if output_filename and os.path.exists(output_filename):
        await status_msg.edit_text("📤 **Uploading...**")
        start_time = time.time()

        async def upload_progress(sent, total):
            await progress_for_pyrogram(sent, total, "📤 **Uploading...**", status_msg, start_time)

        try:
            split_files = await split_video(output_filename)
            total_parts = len(split_files)
            user = await client.get_users(chat_id)
            mention_user = f"[{user.first_name}](tg://user?id={user.id})"

            # Get user settings
            user_settings = await db.get_user_settings(chat_id)
            upload_as_doc = user_settings.get("upload_as_doc", False)

            # Log user settings and upload type
            logging.info(f"User settings: {user_settings}")
            logging.info(f"upload_as_doc: {upload_as_doc}")

            for idx, part_file in enumerate(split_files, start=1):
                part_caption = f"**{caption}**\n**Part {idx}/{total_parts}**" if total_parts > 1 else f"**{caption}**"

                with open(part_file, "rb") as file:
                    logging.info(f"Upload Type: {'Document' if upload_as_doc else 'Video'}")

                    if upload_as_doc:
                        new_filename = part_file.replace(".mp4", ".mkv")
                        logging.info(f"Sending file as Document: {part_file}")
                        sent_message = await client.send_document(
                            chat_id=chat_id,
                            document=file,
                            caption=part_caption,
                            progress=upload_progress,
                            disable_notification=True,
                            thumb=thumbnail_path if thumbnail_path else None,
                            file_name=os.path.basename(new_filename)
                        )
                    else:
                        logging.info(f"Sending file as Video: {part_file}")
                        sent_message = await client.send_video(
                            chat_id=chat_id,
                            video=file,
                            caption=part_caption,
                            duration=duration // total_parts if total_parts > 1 else duration,
                            supports_streaming=True,
                            progress=upload_progress,
                            height=height,
                            width=width,
                            disable_notification=True,
                            thumb=thumbnail_path if thumbnail_path else None,
                            file_name=os.path.basename(part_file)
                        )

                # Send to dump channel
                formatted_caption = (
                    f"{part_caption}\n\n"
                    f"✅ **Downloaded By: {mention_user}**\n"
                    f"📌 **Source URL: [Click Here]({youtube_link})**"
                )

                with open(part_file, "rb") as file:
                    if upload_as_doc:
                        logging.info(f"Sending document to dump channel: {part_file}")
                        await client.send_document(
                            chat_id=DUMP_CHANNEL,
                            document=file,
                            caption=formatted_caption,
                            disable_notification=True,
                            thumb=thumbnail_path if thumbnail_path else None,
                            file_name=os.path.basename(part_file)
                        )
                    else:
                        logging.info(f"Sending video to dump channel: {part_file}")
                        await client.send_video(
                            chat_id=DUMP_CHANNEL,
                            video=file,
                            caption=formatted_caption,
                            duration=duration // total_parts if total_parts > 1 else duration,
                            supports_streaming=True,
                            disable_notification=True,
                            thumb=thumbnail_path if thumbnail_path else None,
                            file_name=os.path.basename(part_file)
                        )

                os.remove(part_file)

            await status_msg.edit_text("✅ **Upload Successful!**")
            await db.increment_task(chat_id)
            await db.increment_download_count()
            await status_msg.delete()

        except Exception as e:
            user = await client.get_users(chat_id)
            error_report = (
                f"❌ **Upload Failed!**\n\n"
                f"**User:** [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n"
                f"**Filename:** `{output_filename}`\n"
                f"**Source:** [YouTube Link]({youtube_link})\n"
                f"**Error:** `{str(e)}`"
            )
            await client.send_message(LOG_CHANNEL, error_report)
            await status_msg.edit_text("❌ **Oops! Something went wrong during upload.**")

        finally:
            if os.path.exists(output_filename):
                os.remove(output_filename)
            if thumbnail_path and os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
            active_tasks.pop(chat_id, None)
    else:
        try:
            user = await client.get_users(chat_id)
            error_report = (
                f"❌ **Upload Failed - File Not Found!**\n\n"
                f"**User:** [{user.first_name}](tg://user?id={user.id}) (`{user.id}`)\n"
                f"**Expected File:** `{output_filename}`\n"
                f"**Source:** [YouTube Link]({youtube_link})"
            )
            await client.send_message(LOG_CHANNEL, error_report)
        except Exception as e:
            await client.send_message(LOG_CHANNEL, f"❌ Error while logging failed upload:\n`{str(e)}`")

        await status_msg.edit_text("❌ **Oops! Upload failed. Please try again later.**")
        active_tasks.pop(chat_id, None)
