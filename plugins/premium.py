from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import Database
from config import Config
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
db = Database()

@Client.on_message(filters.command("premium") & filters.private)
async def premium_command(client: Client, message: Message):
    """Handle /premium command"""
    try:
        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Check if user already has premium
        is_premium = await db.is_user_premium(user_id)
        premium_until = user.get("premium_until")
        
        if is_premium and premium_until:
            remaining_days = (premium_until - datetime.now()).days
            current_plan_text = f"**ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ:** 💎 ᴘʀᴇᴍɪᴜᴍ\n**ᴇxᴘɪʀᴇs ɪɴ:** {remaining_days} ᴅᴀʏs\n\n"
        else:
            current_plan_text = "**ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ:** 🆓 ꜰʀᴇᴇ\n\n"
        
        premium_text = f"""
💎 **ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs**

{current_plan_text}**ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:**

📅 **ᴍᴏɴᴛʜʟʏ ᴘʟᴀɴ**
• **ᴄʀᴇᴅɪᴛs:** {Config.PREMIUM_PRICES['monthly']['credits']}
• **ᴅᴜʀᴀᴛɪᴏɴ:** {Config.PREMIUM_PRICES['monthly']['days']} ᴅᴀʏs
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** ᴜɴʟɪᴍɪᴛᴇᴅ

🗓️ **ʏᴇᴀʀʟʏ ᴘʟᴀɴ**
• **ᴄʀᴇᴅɪᴛs:** {Config.PREMIUM_PRICES['yearly']['credits']}
• **ᴅᴜʀᴀᴛɪᴏɴ:** {Config.PREMIUM_PRICES['yearly']['days']} ᴅᴀʏs
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** ᴜɴʟɪᴍɪᴛᴇᴅ
• **ʙᴇsᴛ ᴠᴀʟᴜᴇ!** 💰

**ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛs:**
✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ʟᴀʀɢᴇʀ ꜰɪʟᴇ sɪᴢᴇ sᴜᴘᴘᴏʀᴛ
✅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
✅ ᴘʀᴇᴍɪᴜᴍ sᴜᴘᴘᴏʀᴛ

**ᴘᴀʏᴍᴇɴᴛ ᴍᴇᴛʜᴏᴅs:**
• ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴘᴀʏᴍᴇɴᴛ ᴅᴇᴛᴀɪʟs
• ᴜsᴇ ɢɪꜰᴛ ᴄᴏᴅᴇs ɪꜰ ᴀᴠᴀɪʟᴀʙʟᴇ
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 ᴍᴏɴᴛʜʟʏ ᴘʟᴀɴ", callback_data="premium_monthly")],
            [InlineKeyboardButton("🗓️ ʏᴇᴀʀʟʏ ᴘʟᴀɴ", callback_data="premium_yearly")],
            [InlineKeyboardButton("🎫 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_code")],
            [InlineKeyboardButton("📊 ᴍʏ ᴘʟᴀɴ", callback_data="my_plan")]
        ])
        
        await message.reply_text(premium_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in premium command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴘʀᴇᴍɪᴜᴍ ɪɴꜰᴏ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_message(filters.command("myplan") & filters.private)
async def myplan_command(client: Client, message: Message):
    """Handle /myplan command"""
    try:
        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Check premium status
        is_premium = await db.is_user_premium(user_id)
        premium_until = user.get("premium_until")
        
        if is_premium and premium_until:
            remaining_days = (premium_until - datetime.now()).days
            expiry_date = premium_until.strftime("%d/%m/%Y")
            
            plan_text = f"""
📊 **ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ**

**ᴘʟᴀɴ ᴛʏᴘᴇ:** 💎 ᴘʀᴇᴍɪᴜᴍ
**sᴛᴀᴛᴜs:** ✅ ᴀᴄᴛɪᴠᴇ
**ᴇxᴘɪʀᴇs ᴏɴ:** {expiry_date}
**ᴅᴀʏs ʀᴇᴍᴀɪɴɪɴɢ:** {remaining_days} ᴅᴀʏs

**ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛs:**
✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ʟᴀʀɢᴇʀ ꜰɪʟᴇ sɪᴢᴇ sᴜᴘᴘᴏʀᴛ
✅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
✅ ᴘʀᴇᴍɪᴜᴍ sᴜᴘᴘᴏʀᴛ

**ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ:**
• **ᴄʀᴇᴅɪᴛs:** {user.get('credits', 0)}
• **ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {user.get('total_operations', 0)}
"""
        else:
            plan_text = f"""
📊 **ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ**

**ᴘʟᴀɴ ᴛʏᴘᴇ:** 🆓 ꜰʀᴇᴇ
**sᴛᴀᴛᴜs:** ✅ ᴀᴄᴛɪᴠᴇ
**ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** {Config.DAILY_LIMIT} ᴏᴘᴇʀᴀᴛɪᴏɴs

**ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ:**
• **ᴄʀᴇᴅɪᴛs:** {user.get('credits', 0)}
• **ᴛᴏᴅᴀʏ's ᴜsᴀɢᴇ:** {user.get('daily_usage', 0)}/{Config.DAILY_LIMIT}
• **ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {user.get('total_operations', 0)}

**ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ:**
• ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
• ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")],
            [InlineKeyboardButton("🎫 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_code")],
            [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await message.reply_text(plan_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in myplan command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴘʟᴀɴ ɪɴꜰᴏ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_message(filters.command("redeem") & filters.private)
async def redeem_command(client: Client, message: Message):
    """Handle /redeem command"""
    try:
        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Check if code is provided
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴄᴏᴍᴍᴀɴᴅ**\n\n"
                "**ᴜsᴀɢᴇ:** `/redeem <code>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/redeem PREMIUM30`\n\n"
                "ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴠᴀʟɪᴅ ɢɪꜰᴛ ᴄᴏᴅᴇs."
            )
            return
        
        code = message.command[1].upper()
        
        # Redeem code
        result = await db.redeem_premium_code(code, user_id)
        
        if result:
            await message.reply_text(
                f"🎉 **ᴄᴏᴅᴇ ʀᴇᴅᴇᴇᴍᴇᴅ sᴜᴄᴄᴇssꜰᴜʟʟʏ!**\n\n"
                f"**ᴄᴏᴅᴇ:** `{code}`\n"
                f"**ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ:** {result} ᴅᴀʏs\n\n"
                f"ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! ʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇss!"
            )
            
            # Log redemption
            if Config.LOG_CHANNEL_ID:
                try:
                    log_text = f"🎫 **ᴄᴏᴅᴇ ʀᴇᴅᴇᴇᴍᴇᴅ**\n\n"
                    log_text += f"**ᴜsᴇʀ:** `{user_id}`\n"
                    log_text += f"**ᴄᴏᴅᴇ:** `{code}`\n"
                    log_text += f"**ᴅᴀʏs:** {result}"
                    
                    await client.send_message(Config.LOG_CHANNEL_ID, log_text)
                except Exception as e:
                    logger.error(f"Failed to log redemption: {e}")
        else:
            await message.reply_text(
                f"❌ **ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ᴄᴏᴅᴇ**\n\n"
                f"**ᴄᴏᴅᴇ:** `{code}`\n\n"
                f"ᴘʟᴇᴀsᴇ ᴄʜᴇᴄᴋ ᴛʜᴇ ᴄᴏᴅᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.\n"
                f"ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ɪꜰ ʏᴏᴜ ʙᴇʟɪᴇᴠᴇ ᴛʜɪs ɪs ᴀɴ ᴇʀʀᴏʀ."
            )
        
    except Exception as e:
        logger.error(f"Error in redeem command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ʀᴇᴅᴇᴇᴍɪɴɢ ᴄᴏᴅᴇ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_callback_query(filters.regex("^premium_info$"))
async def premium_info_callback(client: Client, callback_query: CallbackQuery):
    """Handle premium info callback"""
    try:
        premium_text = f"""
💎 **ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs**

**ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʟᴀɴs:**

📅 **ᴍᴏɴᴛʜʟʏ ᴘʟᴀɴ**
• **ᴄʀᴇᴅɪᴛs:** {Config.PREMIUM_PRICES['monthly']['credits']}
• **ᴅᴜʀᴀᴛɪᴏɴ:** {Config.PREMIUM_PRICES['monthly']['days']} ᴅᴀʏs
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** ᴜɴʟɪᴍɪᴛᴇᴅ

🗓️ **ʏᴇᴀʀʟʏ ᴘʟᴀɴ**
• **ᴄʀᴇᴅɪᴛs:** {Config.PREMIUM_PRICES['yearly']['credits']}
• **ᴅᴜʀᴀᴛɪᴏɴ:** {Config.PREMIUM_PRICES['yearly']['days']} ᴅᴀʏs
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** ᴜɴʟɪᴍɪᴛᴇᴅ
• **ʙᴇsᴛ ᴠᴀʟᴜᴇ!** 💰

**ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛs:**
✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ʟᴀʀɢᴇʀ ꜰɪʟᴇ sɪᴢᴇ sᴜᴘᴘᴏʀᴛ
✅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
✅ ᴘʀᴇᴍɪᴜᴍ sᴜᴘᴘᴏʀᴛ
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 ᴍᴏɴᴛʜʟʏ ᴘʟᴀɴ", callback_data="premium_monthly")],
            [InlineKeyboardButton("🗓️ ʏᴇᴀʀʟʏ ᴘʟᴀɴ", callback_data="premium_yearly")],
            [InlineKeyboardButton("🎫 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_code")],
            [InlineKeyboardButton("📊 ᴍʏ ᴘʟᴀɴ", callback_data="my_plan")]
        ])
        
        await callback_query.edit_message_text(premium_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in premium info callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ʟᴏᴀᴅɪɴɢ ᴘʀᴇᴍɪᴜᴍ ɪɴꜰᴏ", show_alert=True)

@Client.on_callback_query(filters.regex("^premium_(monthly|yearly)$"))
async def premium_plan_callback(client: Client, callback_query: CallbackQuery):
    """Handle premium plan callbacks"""
    try:
        plan_type = callback_query.data.split("_")[1]
        plan_info = Config.PREMIUM_PRICES[plan_type]
        
        plan_text = f"""
💎 **{plan_type.title()} ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ**

**ᴅᴇᴛᴀɪʟs:**
• **ᴄʀᴇᴅɪᴛs:** {plan_info['credits']}
• **ᴅᴜʀᴀᴛɪᴏɴ:** {plan_info['days']} ᴅᴀʏs
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** ᴜɴʟɪᴍɪᴛᴇᴅ

**ɪɴᴄʟᴜᴅᴇᴅ ʙᴇɴᴇꜰɪᴛs:**
✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ʟᴀʀɢᴇʀ ꜰɪʟᴇ sɪᴢᴇ sᴜᴘᴘᴏʀᴛ
✅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
✅ ᴘʀᴇᴍɪᴜᴍ sᴜᴘᴘᴏʀᴛ

**ᴛᴏ ᴘᴜʀᴄʜᴀsᴇ ᴛʜɪs ᴘʟᴀɴ:**
1. ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ ꜰᴏʀ ᴘᴀʏᴍᴇɴᴛ ᴅᴇᴛᴀɪʟs
2. ᴍᴀᴋᴇ ᴘᴀʏᴍᴇɴᴛ ᴀɴᴅ sᴇɴᴅ ᴘʀᴏᴏꜰ
3. ᴀᴅᴍɪɴ ᴡɪʟʟ ᴀᴄᴛɪᴠᴀᴛᴇ ʏᴏᴜʀ ᴘʟᴀɴ

**ᴀʟᴛᴇʀɴᴀᴛɪᴠᴇʟʏ:**
ᴜsᴇ ᴀ ᴘʀᴇᴍɪᴜᴍ ɢɪꜰᴛ ᴄᴏᴅᴇ ɪꜰ ᴀᴠᴀɪʟᴀʙʟᴇ.
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💬 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url=f"tg://user?id={Config.OWNER_ID}")],
            [InlineKeyboardButton("🎫 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_code")],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="premium_info")]
        ])
        
        await callback_query.edit_message_text(plan_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in premium plan callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ʟᴏᴀᴅɪɴɢ ᴘʟᴀɴ ɪɴꜰᴏ", show_alert=True)

@Client.on_callback_query(filters.regex("^redeem_code$"))
async def redeem_code_callback(client: Client, callback_query: CallbackQuery):
    """Handle redeem code callback"""
    redeem_text = """
🎫 **ʀᴇᴅᴇᴇᴍ ɢɪꜰᴛ ᴄᴏᴅᴇ**

**ʜᴏᴡ ᴛᴏ ʀᴇᴅᴇᴇᴍ:**
1. ᴜsᴇ ᴛʜᴇ ᴄᴏᴍᴍᴀɴᴅ: `/redeem <code>`
2. ʀᴇᴘʟᴀᴄᴇ `<code>` ᴡɪᴛʜ ʏᴏᴜʀ ᴀᴄᴛᴜᴀʟ ᴄᴏᴅᴇ

**ᴇxᴀᴍᴘʟᴇ:**
`/redeem PREMIUM30`

**ᴡʜᴇʀᴇ ᴛᴏ ɢᴇᴛ ᴄᴏᴅᴇs:**
• ᴄᴏɴᴛᴇsᴛs ᴀɴᴅ ɢɪᴠᴇᴀᴡᴀʏs
• ᴄᴏᴍᴍᴜɴɪᴛʏ ᴇᴠᴇɴᴛs
• ᴘʀᴏᴍᴏᴛɪᴏɴᴀʟ ᴄᴀᴍᴘᴀɪɢɴs
• ᴘᴜʀᴄʜᴀsᴇ ꜰʀᴏᴍ ᴀᴅᴍɪɴ

**ɴᴏᴛᴇ:** ᴇᴀᴄʜ ᴄᴏᴅᴇ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜsᴇᴅ ᴏɴᴄᴇ.
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 ᴄᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ", url=f"tg://user?id={Config.OWNER_ID}")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="premium_info")]
    ])
    
    await callback_query.edit_message_text(redeem_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^my_plan$"))
async def my_plan_callback(client: Client, callback_query: CallbackQuery):
    """Handle my plan callback"""
    try:
        user_id = callback_query.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Check premium status
        is_premium = await db.is_user_premium(user_id)
        premium_until = user.get("premium_until")
        
        if is_premium and premium_until:
            remaining_days = (premium_until - datetime.now()).days
            expiry_date = premium_until.strftime("%d/%m/%Y")
            
            plan_text = f"""
📊 **ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ**

**ᴘʟᴀɴ ᴛʏᴘᴇ:** 💎 ᴘʀᴇᴍɪᴜᴍ
**sᴛᴀᴛᴜs:** ✅ ᴀᴄᴛɪᴠᴇ
**ᴇxᴘɪʀᴇs ᴏɴ:** {expiry_date}
**ᴅᴀʏs ʀᴇᴍᴀɪɴɪɴɢ:** {remaining_days} ᴅᴀʏs

**ᴀᴄᴛɪᴠᴇ ʙᴇɴᴇꜰɪᴛs:**
✅ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
✅ ʟᴀʀɢᴇʀ ꜰɪʟᴇ sɪᴢᴇ sᴜᴘᴘᴏʀᴛ
✅ ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
✅ ᴘʀᴇᴍɪᴜᴍ sᴜᴘᴘᴏʀᴛ

**ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ:**
• **ᴄʀᴇᴅɪᴛs:** {user.get('credits', 0)}
• **ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {user.get('total_operations', 0)}
"""
        else:
            plan_text = f"""
📊 **ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀɴ**

**ᴘʟᴀɴ ᴛʏᴘᴇ:** 🆓 ꜰʀᴇᴇ
**sᴛᴀᴛᴜs:** ✅ ᴀᴄᴛɪᴠᴇ
**ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** {Config.DAILY_LIMIT} ᴏᴘᴇʀᴀᴛɪᴏɴs

**ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ:**
• **ᴄʀᴇᴅɪᴛs:** {user.get('credits', 0)}
• **ᴛᴏᴅᴀʏ's ᴜsᴀɢᴇ:** {user.get('daily_usage', 0)}/{Config.DAILY_LIMIT}
• **ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {user.get('total_operations', 0)}

**ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ:**
• ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴘʀᴏᴄᴇssɪɴɢ
• ᴘʀɪᴏʀɪᴛʏ ᴘʀᴏᴄᴇssɪɴɢ
• ᴇxᴄʟᴜsɪᴠᴇ ꜰᴇᴀᴛᴜʀᴇs
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 ᴜᴘɢʀᴀᴅᴇ", callback_data="premium_info")],
            [InlineKeyboardButton("🎫 ʀᴇᴅᴇᴇᴍ ᴄᴏᴅᴇ", callback_data="redeem_code")],
            [InlineKeyboardButton("💰 ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await callback_query.edit_message_text(plan_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in my plan callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ʟᴏᴀᴅɪɴɢ ᴘʟᴀɴ ɪɴꜰᴏ", show_alert=True)
