from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.db import db
from info import Config
import logging

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("refer") & filters.private)
async def refer_command(client: Client, message: Message):
    """Handle /refer command"""
    try:

        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Get bot info
        bot_info = await client.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        # Get referral stats
        referral_count = await db.get_referral_stats(user_id)
        
        referral_text = f"""
🎁 **ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ**

**ʏᴏᴜʀ ʟɪɴᴋ:**
`{referral_link}`

**ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs:**
• **ᴛᴏᴛᴀʟ ʀᴇꜰᴇʀʀᴀʟs:** {referral_count}
• **ᴇᴀʀɴᴇᴅ ᴄʀᴇᴅɪᴛs:** {referral_count * Config.REFERRAL_BONUS}

**ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:**
1. sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ
2. ᴡʜᴇɴ sᴏᴍᴇᴏɴᴇ ᴊᴏɪɴs ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ
3. ʏᴏᴜ ɢᴇᴛ **{Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs** ɪɴsᴛᴀɴᴛʟʏ!

**ɴᴏ ʟɪᴍɪᴛ ᴏɴ ʀᴇꜰᴇʀʀᴀʟs!**
ᴋᴇᴇᴘ sʜᴀʀɪɴɢ ᴀɴᴅ ᴋᴇᴇᴘ ᴇᴀʀɴɪɴɢ!
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs", callback_data="ref_stats")],
            [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await message.reply_text(referral_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in refer command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ɢᴇɴᴇʀᴀᴛɪɴɢ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_message(filters.command("refstats") & filters.private)
async def refstats_command(client: Client, message: Message):
    """Handle /refstats command"""
    try:

        user_id = message.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Get referral stats
        referral_count = await db.get_referral_stats(user_id)
        earned_credits = referral_count * Config.REFERRAL_BONUS
        
        stats_text = f"""
📊 **ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs**

**ᴛᴏᴛᴀʟ ʀᴇꜰᴇʀʀᴀʟs:** {referral_count}
**ᴇᴀʀɴᴇᴅ ᴄʀᴇᴅɪᴛs:** {earned_credits}
**ʀᴇᴡᴀʀᴅ ᴘᴇʀ ʀᴇꜰᴇʀʀᴀʟ:** {Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs

**ʀᴇꜰᴇʀʀᴀʟ ʀᴀɴᴋɪɴɢ:**
{get_referral_rank(referral_count)}

**ɴᴇxᴛ ᴍɪʟᴇsᴛᴏɴᴇ:**
{get_next_milestone(referral_count)}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 ɢᴇᴛ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="referral_info")],
            [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await message.reply_text(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in refstats command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_callback_query(filters.regex("^referral_info$"))
async def referral_info_callback(client: Client, callback_query: CallbackQuery):
    """Handle referral info callback"""
    try:

        user_id = callback_query.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Get bot info
        bot_info = await client.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        # Get referral stats
        referral_count = await db.get_referral_stats(user_id)
        
        referral_text = f"""
🎁 **ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ**

**ʏᴏᴜʀ ʟɪɴᴋ:**
`{referral_link}`

**ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs:**
• **ᴛᴏᴛᴀʟ ʀᴇꜰᴇʀʀᴀʟs:** {referral_count}
• **ᴇᴀʀɴᴇᴅ ᴄʀᴇᴅɪᴛs:** {referral_count * Config.REFERRAL_BONUS}

**ʜᴏᴡ ɪᴛ ᴡᴏʀᴋs:**
1. sʜᴀʀᴇ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ
2. ᴡʜᴇɴ sᴏᴍᴇᴏɴᴇ ᴊᴏɪɴs ᴜsɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ
3. ʏᴏᴜ ɢᴇᴛ **{Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs** ɪɴsᴛᴀɴᴛʟʏ!

**ɴᴏ ʟɪᴍɪᴛ ᴏɴ ʀᴇꜰᴇʀʀᴀʟs!**
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 ᴅᴇᴛᴀɪʟᴇᴅ sᴛᴀᴛs", callback_data="ref_stats")],
            [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await callback_query.edit_message_text(referral_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in referral info callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ʀᴇꜰᴇʀʀᴀʟ ɪɴꜰᴏ", show_alert=True)

@Client.on_callback_query(filters.regex("^ref_stats$"))
async def ref_stats_callback(client: Client, callback_query: CallbackQuery):
    """Handle ref stats callback"""
    try:

        user_id = callback_query.from_user.id
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Get referral stats
        referral_count = await db.get_referral_stats(user_id)
        earned_credits = referral_count * Config.REFERRAL_BONUS
        
        stats_text = f"""
📊 **ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs**

**ᴛᴏᴛᴀʟ ʀᴇꜰᴇʀʀᴀʟs:** {referral_count}
**ᴇᴀʀɴᴇᴅ ᴄʀᴇᴅɪᴛs:** {earned_credits}
**ʀᴇᴡᴀʀᴅ ᴘᴇʀ ʀᴇꜰᴇʀʀᴀʟ:** {Config.REFERRAL_BONUS} ᴄʀᴇᴅɪᴛs

**ʀᴇꜰᴇʀʀᴀʟ ʀᴀɴᴋɪɴɢ:**
{get_referral_rank(referral_count)}

**ɴᴇxᴛ ᴍɪʟᴇsᴛᴏɴᴇ:**
{get_next_milestone(referral_count)}
"""
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎁 ɢᴇᴛ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ", callback_data="referral_info")],
            [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")]
        ])
        
        await callback_query.edit_message_text(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in ref stats callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ sᴛᴀᴛs", show_alert=True)

def get_referral_rank(count):
    """Get referral rank based on count"""
    if count == 0:
        return "🥉 ɴᴇᴡʙɪᴇ"
    elif count < 5:
        return "🥈 ʙᴇɢɪɴɴᴇʀ"
    elif count < 10:
        return "🥇 ɪɴᴛᴇʀᴍᴇᴅɪᴀᴛᴇ"
    elif count < 25:
        return "🏆 ᴀᴅᴠᴀɴᴄᴇᴅ"
    elif count < 50:
        return "💎 ᴇxᴘᴇʀᴛ"
    elif count < 100:
        return "👑 ᴍᴀsᴛᴇʀ"
    else:
        return "🌟 ʟᴇɢᴇɴᴅᴀʀʏ"

def get_next_milestone(count):
    """Get next milestone info"""
    if count < 5:
        return f"ʀᴇꜰᴇʀ {5 - count} ᴍᴏʀᴇ ᴜsᴇʀs ᴛᴏ ʙᴇᴄᴏᴍᴇ 🥈 ʙᴇɢɪɴɴᴇʀ"
    elif count < 10:
        return f"ʀᴇꜰᴇʀ {10 - count} ᴍᴏʀᴇ ᴜsᴇʀs ᴛᴏ ʙᴇᴄᴏᴍᴇ 🥇 ɪɴᴛᴇʀᴍᴇᴅɪᴀᴛᴇ"
    elif count < 25:
        return f"ʀᴇꜰᴇʀ {25 - count} ᴍᴏʀᴇ ᴜsᴇʀs ᴛᴏ ʙᴇᴄᴏᴍᴇ 🏆 ᴀᴅᴠᴀɴᴄᴇᴅ"
    elif count < 50:
        return f"ʀᴇꜰᴇʀ {50 - count} ᴍᴏʀᴇ ᴜsᴇʀs ᴛᴏ ʙᴇᴄᴏᴍᴇ 💎 ᴇxᴘᴇʀᴛ"
    elif count < 100:
        return f"ʀᴇꜰᴇʀ {100 - count} ᴍᴏʀᴇ ᴜsᴇʀs ᴛᴏ ʙᴇᴄᴏᴍᴇ 👑 ᴍᴀsᴛᴇʀ"
    else:
        return "ʏᴏᴜ ᴀʀᴇ ᴀ 🌟 ʟᴇɢᴇɴᴅᴀʀʏ ʀᴇꜰᴇʀʀᴇʀ!"
