from contextlib import suppress
from pyrogram import Client, filters
import datetime
import time
from database.db import db
from info import ADMINS, LOG_CHANNEL
import asyncio
import logging
from pyrogram.errors import InputUserDeactivated, UserNotParticipant, FloodWait, UserIsBlocked, PeerIdInvalid


async def send_broadcast_message(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await send_broadcast_message(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - Removed from Database, deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} - Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        logging.error(f"Error broadcasting to {user_id}: {str(e)}")
        # Optional: send to log channel
        return False, "Error"

@Client.on_message(filters.command("broadcast") & filters.user(ADMINS) & filters.reply)
async def broadcast(client, message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message

    sts = await message.reply_text("📢 Broadcasting your message...")

    start_time = time.time()
    total_users = await db.total_users_count()
    done = success = blocked = deleted = failed = 0

    sem = asyncio.Semaphore(10)

    async def process_user(user):
        nonlocal success, blocked, deleted, failed, done
        async with sem:
            result, status = await send_broadcast_message(int(user["user_id"]), b_msg)
            if result:
                success += 1
            else:
                if status == "Blocked":
                    blocked += 1
                elif status == "Deleted":
                    deleted += 1
                elif status == "Error":
                    failed += 1
            done += 1

            if done % 100 == 0:
                with suppress(Exception):
                    await sts.edit(
                        f"📢 Broadcast in progress...\n\n"
                        f"👥 Total Users: {total_users}\n"
                        f"✅ Success: {success}\n"
                        f"⛔ Blocked: {blocked}\n"
                        f"🗑 Deleted: {deleted}\n"
                        f"❌ Failed: {failed}\n"
                        f"📦 Done: {done}/{total_users}"
                    )

    tasks = [process_user(user) async for user in users]
    await asyncio.gather(*tasks)

    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(
        f"✅ **Broadcast Completed** in `{time_taken}`\n\n"
        f"👥 Total Users: {total_users}\n"
        f"✅ Success: {success}\n"
        f"⛔ Blocked: {blocked}\n"
        f"🗑 Deleted: {deleted}\n"
        f"❌ Failed: {failed}"
    )
