from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from info import Config
import logging

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        # Check if user exists
        user = await db.get_user(user_id)
        
        # Handle referral
        referred_by = None
        if len(message.command) > 1:
            try:
                referred_by = int(message.command[1])
                if referred_by == user_id:
                    referred_by = None  # Can't refer themselves
            except ValueError:
                pass
        
        if not user:
            # Create new user
            await db.create_user(user_id, username, first_name, referred_by)
            
            # Send welcome message with referral info
            welcome_text = Config.START_MESSAGE.format(process_cost=Config.PROCESS_COST)
            
            if referred_by:
                welcome_text += f"\n\n🎉 **ᴡᴇʟᴄᴏᴍᴇ ʙᴏɴᴜs!**\nʏᴏᴜ ᴡᴇʀᴇ ʀᴇꜰᴇʀʀᴇᴅ ᴀɴᴅ ɢᴏᴛ {Config.DEFAULT_CREDITS} ᴄʀᴇᴅɪᴛs!\nʏᴏᴜʀ ʀᴇꜰᴇʀʀᴇʀ ɢᴏᴛ {Config.REFERRAL_BONUS} ʙᴏɴᴜs ᴄʀᴇᴅɪᴛs!"
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")],
                [InlineKeyboardButton("📊 ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs", callback_data="earn_credits")],
                [InlineKeyboardButton("🎁 ʀᴇꜰᴇʀʀᴀʟ", callback_data="referral_info")],
                [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
            
            # Log new user
            if Config.LOG_CHANNEL_ID:
                try:
                    log_text = f"👤 **ɴᴇᴡ ᴜsᴇʀ**\n\n"
                    log_text += f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
                    log_text += f"**ɴᴀᴍᴇ:** {first_name}\n"
                    if username:
                        log_text += f"**ᴜsᴇʀɴᴀᴍᴇ:** @{username}\n"
                    if referred_by:
                        log_text += f"**ʀᴇꜰᴇʀʀᴇᴅ ʙʏ:** `{referred_by}`"
                    
                    await client.send_message(Config.LOG_CHANNEL_ID, log_text)
                except Exception as e:
                    logger.error(f"Failed to log new user: {e}")
        else:
            # Update existing user activity
            await db.update_user(user_id, {"last_activity": message.date})
            
            # Send welcome back message
            credits = user.get("credits", 0)
            welcome_text = f"""
🎬 **ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ!**

ʏᴏᴜ ʜᴀᴠᴇ **{credits} ᴄʀᴇᴅɪᴛs** ʀᴇᴍᴀɪɴɪɴɢ.

sᴇɴᴅ ᴍᴇ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ sᴛᴀʀᴛ ᴘʀᴏᴄᴇssɪɴɢ!
"""
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 ᴄʜᴇᴄᴋ ᴄʀᴇᴅɪᴛs", callback_data="check_credits")],
                [InlineKeyboardButton("📊 ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs", callback_data="earn_credits")],
                [InlineKeyboardButton("🎁 ʀᴇꜰᴇʀʀᴀʟ", callback_data="referral_info")],
                [InlineKeyboardButton("💎 ᴘʀᴇᴍɪᴜᴍ", callback_data="premium_info")]
            ])
            
            await message.reply_text(welcome_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.reply_text("❌ ᴀɴ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

@Client.on_message(filters.command("help") & filters.private)
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    help_text = """
🤖 **ʜᴇʟᴘ - ᴄᴏᴍᴍᴀɴᴅs**

**ᴜsᴇʀ ᴄᴏᴍᴍᴀɴᴅs:**
• `/start` - sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ
• `/help` - sʜᴏᴡ ᴛʜɪs ʜᴇʟᴘ
• `/credits` - ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴄʀᴇᴅɪᴛs
• `/earncredits` - ʟᴇᴀʀɴ ʜᴏᴡ ᴛᴏ ᴇᴀʀɴ ᴄʀᴇᴅɪᴛs
• `/refer` - ɢᴇᴛ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ
• `/refstats` - ᴄʜᴇᴄᴋ ʀᴇꜰᴇʀʀᴀʟ sᴛᴀᴛs
• `/premium` - ᴠɪᴇᴡ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴs
• `/myplan` - ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴘʟᴀɴ
• `/redeem <code>` - ʀᴇᴅᴇᴇᴍ ᴀ ɢɪꜰᴛ ᴄᴏᴅᴇ

**ʜᴏᴡ ᴛᴏ ᴜsᴇ:**
1. sᴇɴᴅ ᴀ ᴠɪᴅᴇᴏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ
2. ᴄʜᴏᴏsᴇ ᴀ ᴘʀᴏᴄᴇssɪɴɢ ᴏᴘᴛɪᴏɴ
3. ᴡᴀɪᴛ ꜰᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ
4. ᴅᴏᴡɴʟᴏᴀᴅ ʏᴏᴜʀ ᴘʀᴏᴄᴇssᴇᴅ ᴠɪᴅᴇᴏ

**ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʀᴏᴄᴇssɪɴɢ:**
• ᴛʀɪᴍ ᴠɪᴅᴇᴏ • ᴄᴏᴍᴘʀᴇss ᴠɪᴅᴇᴏ
• ʀᴏᴛᴀᴛᴇ ᴠɪᴅᴇᴏ • ᴍᴇʀɢᴇ ᴠɪᴅᴇᴏs
• ᴀᴅᴅ ᴡᴀᴛᴇʀᴍᴀʀᴋ • ᴍᴜᴛᴇ ᴠɪᴅᴇᴏ
• ʀᴇᴘʟᴀᴄᴇ ᴀᴜᴅɪᴏ • ʀᴇᴠᴇʀsᴇ ᴠɪᴅᴇᴏ
• ᴀᴅᴅ sᴜʙᴛɪᴛʟᴇs • ᴄʜᴀɴɢᴇ ʀᴇsᴏʟᴜᴛɪᴏɴ
• ᴇxᴛʀᴀᴄᴛ ᴀᴜᴅɪᴏ • ᴛᴀᴋᴇ sᴄʀᴇᴇɴsʜᴏᴛ

ᴇᴀᴄʜ ᴘʀᴏᴄᴇss ᴄᴏsᴛs **{Config.PROCESS_COST} ᴄʀᴇᴅɪᴛs**
"""
    
    await message.reply_text(help_text)
