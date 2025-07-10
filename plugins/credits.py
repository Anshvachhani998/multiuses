from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import Database
from config import Config
import logging

logger = logging.getLogger(__name__)
db = Database()

@Client.on_message(filters.command("credits") & filters.private)
async def credits_command(client: Client, message: Message):
    """Handle /credits command"""
    try:
        # Ensure database is connected
        if not db._connected:
            await db.connect()
            
        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        credits = user.get("credits", 0)
        daily_usage = user.get("daily_usage", 0)
        total_operations = user.get("total_operations", 0)
        
        # Check if premium
        is_premium = await db.is_user_premium(user_id)
        premium_text = "💎 ᴘʀᴇᴍɪᴜᴍ" if is_premium else "🆓 ꜰʀᴇᴇ"
        
        credits_text = f"""
💰 **ʏᴏᴜʀ ᴄʀᴇᴅɪᴛs**

**ᴀᴠᴀɪʟᴀʙʟᴇ ᴄʀᴇᴅɪᴛs:** {credits}
**ᴘʟᴀɴ:** {premium_text}
**ᴛᴏᴅᴀʏ's ᴜsᴀɢᴇ:** {daily_usage}/{Config.DAILY_LIMIT if not is_premium else "∞"}
**ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {total_operations}

**ᴄᴏsᴛ ᴘᴇʀ ᴏᴘᴇʀᴀᴛɪᴏɴ:** {Config.PROCESS_COST} ᴄʀᴇᴅɪᴛs
**ᴇsᴛɪᴍᴀᴛᴇᴅ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {credits // Config.PROCESS_COST}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs", callback_data="earn_credits")],
            [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")],
            [InlineKeyboardButton("🎁 ʀᴇꜰᴇʀʀᴀʟ", callback_data="referral_info")]
        ])
        
        await message.reply_text(credits_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in credits command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴄʀᴇᴅɪᴛs. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_message(filters.command("earncredits") & filters.private)
async def earn_credits_command(client: Client, message: Message):
    """Handle /earncredits command"""
    earn_text = f"""
📊 **ʜᴏᴡ ᴛᴏ ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs**

**ꜰʀᴇᴇ ᴡᴀʏs:**
🎁 **ʀᴇꜰᴇʀʀᴀʟ ʙᴏɴᴜs**
• ɪɴᴠɪᴛᴇ ꜰʀɪᴇɴᴅs ᴜsɪɴɢ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ
• ᴇᴀʀɴ **{Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs** ꜰᴏʀ ᴇᴀᴄʜ ʀᴇꜰᴇʀʀᴀʟ
• ɴᴏ ʟɪᴍɪᴛ ᴏɴ ʀᴇꜰᴇʀʀᴀʟs!

**ᴘʀᴇᴍɪᴜᴍ ᴡᴀʏs:**
💎 **ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs**
• ᴍᴏɴᴛʜʟʏ: {Config.PREMIUM_PRICES['monthly']['credits']} ᴄʀᴇᴅɪᴛs
• ʏᴇᴀʀʟʏ: {Config.PREMIUM_PRICES['yearly']['credits']} ᴄʀᴇᴅɪᴛs
• ᴜɴʟɪᴍɪᴛᴇᴅ ᴅᴀɪʟʏ ᴜsᴀɢᴇ

🎫 **ɢɪꜰᴛ ᴄᴏᴅᴇs**
• ᴘᴀʀᴛɪᴄɪᴘᴀᴛᴇ ɪɴ ᴄᴏɴᴛᴇsᴛs
• ꜰᴏʟʟᴏᴡ ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛs
• ᴄᴏᴍᴍᴜɴɪᴛʏ ᴇᴠᴇɴᴛs

**ᴄᴜʀʀᴇɴᴛ ʙᴏɴᴜs ᴏꜰꜰᴇʀs:**
• ꜰɪʀsᴛ ᴛɪᴍᴇ ᴊᴏɪɴɪɴɢ: {Config.DEFAULT_CREDITS} ᴄʀᴇᴅɪᴛs
• ᴇᴀᴄʜ ʀᴇꜰᴇʀʀᴀʟ: {Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 ɢᴇᴛ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="referral_info")],
        [InlineKeyboardButton("💎 ᴠɪᴇᴡ ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")],
        [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
    ])
    
    await message.reply_text(earn_text, reply_markup=keyboard)

@Client.on_callback_query(filters.regex("^check_credits$"))
async def check_credits_callback(client: Client, callback_query: CallbackQuery):
    """Handle check credits callback"""
    try:
        # Ensure database is connected
        if not db._connected:
            await db.connect()
            
        user_id = callback_query.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        credits = user.get("credits", 0)
        daily_usage = user.get("daily_usage", 0)
        
        # Check if premium
        is_premium = await db.is_user_premium(user_id)
        premium_text = "💎 ᴘʀᴇᴍɪᴜᴍ" if is_premium else "🆓 ꜰʀᴇᴇ"
        
        credits_text = f"""
💰 **ʏᴏᴜʀ ᴄʀᴇᴅɪᴛs**

**ᴀᴠᴀɪʟᴀʙʟᴇ:** {credits} ᴄʀᴇᴅɪᴛs
**ᴘʟᴀɴ:** {premium_text}
**ᴛᴏᴅᴀʏ's ᴜsᴀɢᴇ:** {daily_usage}/{Config.DAILY_LIMIT if not is_premium else "∞"}
**ᴇsᴛɪᴍᴀᴛᴇᴅ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {credits // Config.PROCESS_COST}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ᴇᴀʀɴ ᴍᴏʀᴇ", callback_data="earn_credits")],
            [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")]
        ])
        
        await callback_query.edit_message_text(credits_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in check credits callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ᴄʀᴇᴅɪᴛs", show_alert=True)

@Client.on_callback_query(filters.regex("^earn_credits$"))
async def earn_credits_callback(client: Client, callback_query: CallbackQuery):
    """Handle earn credits callback"""
    earn_text = f"""
📊 **ʜᴏᴡ ᴛᴏ ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs**

**ꜰʀᴇᴇ ᴡᴀʏs:**
🎁 **ʀᴇꜰᴇʀʀᴀʟ ʙᴏɴᴜs**
• ɪɴᴠɪᴛᴇ ꜰʀɪᴇɴᴅs: +{Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs
• ɴᴏ ʟɪᴍɪᴛ ᴏɴ ʀᴇꜰᴇʀʀᴀʟs!

**ᴘʀᴇᴍɪᴜᴍ ᴡᴀʏs:**
💎 **ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs**
• ᴍᴏɴᴛʜʟʏ: {Config.PREMIUM_PRICES['monthly']['credits']} ᴄʀᴇᴅɪᴛs
• ʏᴇᴀʀʟʏ: {Config.PREMIUM_PRICES['yearly']['credits']} ᴄʀᴇᴅɪᴛs

🎫 **ɢɪꜰᴛ ᴄᴏᴅᴇs**
• ᴘᴀʀᴛɪᴄɪᴘᴀᴛᴇ ɪɴ ᴄᴏɴᴛᴇsᴛs
• ꜰᴏʟʟᴏᴡ ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛs
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 ɢᴇᴛ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="referral_info")],
        [InlineKeyboardButton("💎 ᴠɪᴇᴡ ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="check_credits")]
    ])
    
    await callback_query.edit_message_text(earn_text, reply_markup=keyboard)
