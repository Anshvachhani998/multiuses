import logging
import logging.config
import os
import asyncio
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from aiohttp import web
import pytz
from datetime import date, datetime
from aiohttp import web
from plugins import web_server
from info import SESSION, API_ID, API_HASH, BOT_TOKEN, LOG_CHANNEL, PORT, USER_SESSION
from pyrogram import types
from pyrogram import utils as pyroutils
from database.db import db
from asyncio import sleep
from apscheduler.schedulers.asyncio import AsyncIOScheduler

pyroutils.MIN_CHAT_ID = -999999999999
pyroutils.MIN_CHANNEL_ID = -100999999999999

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)


async def schedule_task_reset(self):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Kolkata"))
    scheduler.add_job(db.reset_daily_tasks, "cron", hour=0, minute=0, args=[self])  # Raat ke 12 baje reset hoga
    scheduler.start()


async def check_expired_premium(client):
    while True:
        data = await db.get_expired(datetime.utcnow())  # ✅ `utcnow()` Best h
        
        for user in data:
            user_id = user.get("user_id")  # ✅ "id" ki jagah "user_id"
            if not user_id:
          
                continue  # ❌ Skip invalid user data

            # ✅ Remove Premium Access
            await db.remove_premium_access(user_id)

            try:
                # ✅ Notify User
                message_text = (
                    "<b>⚠️ 𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐌𝐞𝐦𝐛𝐞𝐫𝐬𝐡𝐢𝐩 𝐄𝐱𝐩𝐢𝐫𝐞𝐝!</b>\n\n"
                    "🛑 ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss ʜᴀs ᴇxᴘɪʀᴇᴅ.\n"
                    "💖 ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜsɪɴɢ ᴏᴜʀ sᴇʀᴠɪᴄᴇ 😊\n\n"
                    "🔄 **Renew Your Plan** - @MovieGroup_Support"
                )

                await client.send_message(chat_id=user_id, text=message_text)

                # ✅ Log Channel Notification
                user_data = await client.get_users(user_id)
                mention = f"[{user_data.first_name}](tg://user?id={user_id})"
                log_message = (
                    f"❌ **Premium Expired**\n"
                    f"👤 **User:** {mention} (`{user_id}`)\n"
                    f"💎 **Premium Status:** ❌ Expired\n"
                    f"🕰 **Expired On:** `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC`"
                )

                await client.send_message(LOG_CHANNEL, log_message)

            except Exception as e:
                print("❌ Error sending message:", e)

            await asyncio.sleep(0.5)  # ✅ Avoid FloodWait

        await asyncio.sleep(1)  # ✅ Check Every 60 sec


class Bot(Client):
    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=1000,
            plugins={"root": "plugins"},
            sleep_threshold=10, 
            max_concurrent_transmissions=6
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        logging.info(f"🤖 {me.first_name} (@{me.username}) running on Pyrogram v{__version__} (Layer {layer})")
        asyncio.create_task(schedule_task_reset(self))
        self.loop.create_task(check_expired_premium(self))
        tz = pytz.timezone('Asia/Kolkata')
        today = date.today()
        now = datetime.now(tz)
        time = now.strftime("%H:%M:%S %p")
        await self.send_message(chat_id=LOG_CHANNEL, text=f"✅ Bot Restarted! 📅 Date: {today} 🕒 Time: {time}")
        app = web.AppRunner(await web_server())
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()
        logging.info(f"🌐 Web Server Running on PORT {PORT}")

    async def stop(self, *args):
        await super().stop()
        logging.info("🛑 Bot Stopped.")

app = Bot()
app.run()
