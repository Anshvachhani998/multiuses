from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import db
from config import Config
import logging
import asyncio
import random
import string
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

def admin_only(func):
    """Decorator to restrict commands to admins only"""
    async def wrapper(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id not in Config.ADMINS:
            await message.reply_text("❌ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
            return
        return await func(client, message)
    return wrapper

@Client.on_message(filters.command("broadcast") & filters.private)
@admin_only
async def broadcast_command(client: Client, message: Message):
    """Handle /broadcast command"""
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/broadcast <message>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/broadcast Hello everyone!`"
            )
            return
        
        broadcast_message = message.text.split(None, 1)[1]
        
        # Get confirmation
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ ᴄᴏɴꜰɪʀᴍ", callback_data=f"broadcast_confirm_{message.id}")],
            [InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ", callback_data="broadcast_cancel")]
        ])
        
        await message.reply_text(
            f"📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏɴꜰɪʀᴍᴀᴛɪᴏɴ**\n\n"
            f"**ᴍᴇssᴀɢᴇ:**\n{broadcast_message}\n\n"
            f"ᴄᴏɴꜰɪʀᴍ ᴛᴏ sᴇɴᴅ ᴛʜɪs ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs.",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ɪɴ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_callback_query(filters.regex(r"^broadcast_confirm_(\d+)$"))
async def broadcast_confirm(client: Client, callback_query):
    """Handle broadcast confirmation"""
    try:
        if callback_query.from_user.id not in Config.ADMINS:
            await callback_query.answer("❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
            return
        
        message_id = int(callback_query.matches[0].group(1))
        
        # Get original message
        original_message = await client.get_messages(callback_query.message.chat.id, message_id)
        broadcast_message = original_message.text.split(None, 1)[1]
        
        # Start broadcast
        await callback_query.edit_message_text(
            "📢 **ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ**\n\n"
            "sᴇɴᴅɪɴɢ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ᴜsᴇʀs..."
        )
        
        # Get all users
        users = await db.users.find({}).to_list(None)
        
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                await client.send_message(
                    user["user_id"],
                    f"📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ**\n\n{broadcast_message}"
                )
                sent_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send broadcast to {user['user_id']}: {e}")
        
        # Update status
        await callback_query.edit_message_text(
            f"📢 **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n"
            f"**ᴛᴏᴛᴀʟ ᴜsᴇʀs:** {len(users)}\n"
            f"**sᴇɴᴛ:** {sent_count}\n"
            f"**ꜰᴀɪʟᴇᴅ:** {failed_count}"
        )
        
    except Exception as e:
        logger.error(f"Error in broadcast confirm: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ ɪɴ ʙʀᴏᴀᴅᴄᴀsᴛ", show_alert=True)

@Client.on_callback_query(filters.regex("^broadcast_cancel$"))
async def broadcast_cancel(client: Client, callback_query):
    """Handle broadcast cancellation"""
    if callback_query.from_user.id not in Config.ADMINS:
        await callback_query.answer("❌ ᴜɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ", show_alert=True)
        return
    
    await callback_query.edit_message_text("❌ **ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴀɴᴄᴇʟʟᴇᴅ**")

@Client.on_message(filters.command("ban") & filters.private)
@admin_only
async def ban_command(client: Client, message: Message):
    """Handle /ban command"""
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/ban <user_id>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/ban 123456789`"
            )
            return
        
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ")
            return
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ")
            return
        
        # Ban user
        await db.ban_user(user_id)
        
        await message.reply_text(
            f"🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ**\n\n"
            f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
            f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}"
        )
        
        # Log ban
        if Config.LOG_CHANNEL_ID:
            try:
                log_text = f"🚫 **ᴜsᴇʀ ʙᴀɴɴᴇᴅ**\n\n"
                log_text += f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
                log_text += f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}\n"
                log_text += f"**ʙᴀɴɴᴇᴅ ʙʏ:** {message.from_user.id}"
                
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.error(f"Failed to log ban: {e}")
        
    except Exception as e:
        logger.error(f"Error in ban command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ʙᴀɴɴɪɴɢ ᴜsᴇʀ.")

@Client.on_message(filters.command("unban") & filters.private)
@admin_only
async def unban_command(client: Client, message: Message):
    """Handle /unban command"""
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/unban <user_id>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/unban 123456789`"
            )
            return
        
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ")
            return
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ")
            return
        
        # Unban user
        await db.unban_user(user_id)
        
        await message.reply_text(
            f"✅ **ᴜsᴇʀ ᴜɴʙᴀɴɴᴇᴅ**\n\n"
            f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
            f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}"
        )
        
        # Log unban
        if Config.LOG_CHANNEL_ID:
            try:
                log_text = f"✅ **ᴜsᴇʀ ᴜɴʙᴀɴɴᴇᴅ**\n\n"
                log_text += f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
                log_text += f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}\n"
                log_text += f"**ᴜɴʙᴀɴɴᴇᴅ ʙʏ:** {message.from_user.id}"
                
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.error(f"Failed to log unban: {e}")
        
    except Exception as e:
        logger.error(f"Error in unban command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴜɴʙᴀɴɴɪɴɢ ᴜsᴇʀ.")

@Client.on_message(filters.command("addpremium") & filters.private)
@admin_only
async def addpremium_command(client: Client, message: Message):
    """Handle /addpremium command"""
    try:
        if len(message.command) < 3:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/addpremium <user_id> <days>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/addpremium 123456789 30`"
            )
            return
        
        try:
            user_id = int(message.command[1])
            days = int(message.command[2])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ ᴏʀ ᴅᴀʏs")
            return
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ")
            return
        
        # Add premium time
        success = await db.add_premium_time(user_id, days)
        
        if success:
            await message.reply_text(
                f"💎 **ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ**\n\n"
                f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
                f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}\n"
                f"**ᴅᴀʏs ᴀᴅᴅᴇᴅ:** {days}"
            )
            
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"🎉 **ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴛɪᴠᴀᴛᴇᴅ**\n\n"
                    f"ᴄᴏɴɢʀᴀᴛᴜʟᴀᴛɪᴏɴs! ʏᴏᴜʀ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴏᴜɴᴛ ʜᴀs ʙᴇᴇɴ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!\n\n"
                    f"**ᴅᴜʀᴀᴛɪᴏɴ:** {days} ᴅᴀʏs\n"
                    f"**ᴇxᴘɪʀᴇs:** {(datetime.now() + timedelta(days=days)).strftime('%d/%m/%Y')}\n\n"
                    f"ᴇɴᴊᴏʏ ᴜɴʟɪᴍɪᴛᴇᴅ ᴠɪᴅᴇᴏ ᴘʀᴏᴄᴇssɪɴɢ!"
                )
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
            
            # Log premium addition
            if Config.LOG_CHANNEL_ID:
                try:
                    log_text = f"💎 **ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ**\n\n"
                    log_text += f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
                    log_text += f"**ɴᴀᴍᴇ:** {user.get('first_name', 'Unknown')}\n"
                    log_text += f"**ᴅᴀʏs:** {days}\n"
                    log_text += f"**ᴀᴅᴅᴇᴅ ʙʏ:** {message.from_user.id}"
                    
                    await client.send_message(Config.LOG_CHANNEL_ID, log_text)
                except Exception as e:
                    logger.error(f"Failed to log premium addition: {e}")
        else:
            await message.reply_text("❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴀᴅᴅ ᴘʀᴇᴍɪᴜᴍ")
        
    except Exception as e:
        logger.error(f"Error in addpremium command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴀᴅᴅɪɴɢ ᴘʀᴇᴍɪᴜᴍ.")

@Client.on_message(filters.command("createcode") & filters.private)
@admin_only
async def createcode_command(client: Client, message: Message):
    """Handle /createcode command"""
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/createcode <days>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/createcode 30`"
            )
            return
        
        try:
            days = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴅᴀʏs")
            return
        
        # Generate random code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Create code in database
        await db.create_premium_code(code, days, message.from_user.id)
        
        await message.reply_text(
            f"🎫 **ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ**\n\n"
            f"**ᴄᴏᴅᴇ:** `{code}`\n"
            f"**ᴅᴀʏs:** {days}\n"
            f"**ᴄʀᴇᴀᴛᴇᴅ ʙʏ:** {message.from_user.id}\n\n"
            f"ᴜsᴇʀs ᴄᴀɴ ʀᴇᴅᴇᴇᴍ ᴛʜɪs ᴄᴏᴅᴇ ᴜsɪɴɢ `/redeem {code}`"
        )
        
        # Log code creation
        if Config.LOG_CHANNEL_ID:
            try:
                log_text = f"🎫 **ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴅᴇ ᴄʀᴇᴀᴛᴇᴅ**\n\n"
                log_text += f"**ᴄᴏᴅᴇ:** `{code}`\n"
                log_text += f"**ᴅᴀʏs:** {days}\n"
                log_text += f"**ᴄʀᴇᴀᴛᴇᴅ ʙʏ:** {message.from_user.id}"
                
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.error(f"Failed to log code creation: {e}")
        
    except Exception as e:
        logger.error(f"Error in createcode command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴄʀᴇᴀᴛɪɴɢ ᴄᴏᴅᴇ.")

@Client.on_message(filters.command("status") & filters.private)
@admin_only
async def status_command(client: Client, message: Message):
    """Handle /status command"""
    try:
        # Get user stats
        stats = await db.get_user_stats()
        
        # Get operations count
        operations_count = await db.operations.count_documents({})
        
        # Get premium codes count
        unused_codes = await db.premium_codes.count_documents({"used": False})
        used_codes = await db.premium_codes.count_documents({"used": True})
        
        status_text = f"""
📊 **ʙᴏᴛ sᴛᴀᴛᴜs**

**ᴜsᴇʀ sᴛᴀᴛs:**
• **ᴛᴏᴛᴀʟ ᴜsᴇʀs:** {stats['total_users']}
• **ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs:** {stats['active_users']}
• **ᴘʀᴇᴍɪᴜᴍ ᴜsᴇʀs:** {stats['premium_users']}

**ᴏᴘᴇʀᴀᴛɪᴏɴs:**
• **ᴛᴏᴛᴀʟ ᴏᴘᴇʀᴀᴛɪᴏɴs:** {operations_count}

**ᴘʀᴇᴍɪᴜᴍ ᴄᴏᴅᴇs:**
• **ᴜɴᴜsᴇᴅ ᴄᴏᴅᴇs:** {unused_codes}
• **ᴜsᴇᴅ ᴄᴏᴅᴇs:** {used_codes}

**sʏsᴛᴇᴍ ɪɴꜰᴏ:**
• **ᴅᴇꜰᴀᴜʟᴛ ᴄʀᴇᴅɪᴛs:** {Config.DEFAULT_CREDITS}
• **ᴘʀᴏᴄᴇss ᴄᴏsᴛ:** {Config.PROCESS_COST}
• **ᴅᴀɪʟʏ ʟɪᴍɪᴛ:** {Config.DAILY_LIMIT}
• **ʀᴇꜰᴇʀʀᴀʟ ʙᴏɴᴜs:** {Config.REFERRAL_BONUS}

**ᴜᴘᴛɪᴍᴇ:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""
        
        await message.reply_text(status_text)
        
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ sᴛᴀᴛᴜs.")

@Client.on_message(filters.command("logs") & filters.private)
@admin_only
async def logs_command(client: Client, message: Message):
    """Handle /logs command"""
    try:
        # Get recent operations
        recent_ops = await db.operations.find({}).sort("date", -1).limit(10).to_list(None)
        
        if not recent_ops:
            await message.reply_text("📋 **ɴᴏ ʀᴇᴄᴇɴᴛ ᴏᴘᴇʀᴀᴛɪᴏɴs**")
            return
        
        logs_text = "📋 **ʀᴇᴄᴇɴᴛ ᴏᴘᴇʀᴀᴛɪᴏɴs**\n\n"
        
        for op in recent_ops:
            user_id = op.get("user_id")
            operation_type = op.get("operation_type")
            status = op.get("status")
            date = op.get("date")
            
            status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏳"
            
            logs_text += f"{status_emoji} **{operation_type}**\n"
            logs_text += f"   ᴜsᴇʀ: `{user_id}`\n"
            logs_text += f"   ᴅᴀᴛᴇ: {date.strftime('%d/%m %H:%M')}\n\n"
        
        await message.reply_text(logs_text)
        
    except Exception as e:
        logger.error(f"Error in logs command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ꜰᴇᴛᴄʜɪɴɢ ʟᴏɢs.")

@Client.on_message(filters.command("dbbackup") & filters.private)
@admin_only
async def dbbackup_command(client: Client, message: Message):
    """Handle /dbbackup command"""
    try:
        # Get all collections data
        users = await db.users.find({}).to_list(None)
        operations = await db.operations.find({}).to_list(None)
        premium_codes = await db.premium_codes.find({}).to_list(None)
        referrals = await db.referrals.find({}).to_list(None)
        
        backup_data = {
            "users": users,
            "operations": operations,
            "premium_codes": premium_codes,
            "referrals": referrals,
            "backup_date": datetime.now().isoformat()
        }
        
        # Convert to JSON
        backup_json = json.dumps(backup_data, default=str, indent=2)
        
        # Save to file
        backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = f"{Config.TEMP_DIR}/{backup_filename}"
        
        with open(backup_path, 'w') as f:
            f.write(backup_json)
        
        # Send file
        await client.send_document(
            message.chat.id,
            backup_path,
            caption=f"📦 **ᴅᴀᴛᴀʙᴀsᴇ ʙᴀᴄᴋᴜᴘ**\n\n"
                   f"**ᴅᴀᴛᴇ:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                   f"**ᴜsᴇʀs:** {len(users)}\n"
                   f"**ᴏᴘᴇʀᴀᴛɪᴏɴs:** {len(operations)}\n"
                   f"**ᴄᴏᴅᴇs:** {len(premium_codes)}\n"
                   f"**ʀᴇꜰᴇʀʀᴀʟs:** {len(referrals)}"
        )
        
        # Clean up
        import os
        try:
            os.remove(backup_path)
        except:
            pass
        
    except Exception as e:
        logger.error(f"Error in dbbackup command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴄʀᴇᴀᴛɪɴɢ ʙᴀᴄᴋᴜᴘ.")

@Client.on_message(filters.command("reset") & filters.private)
@admin_only
async def reset_command(client: Client, message: Message):
    """Handle /reset command"""
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/reset <user_id>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/reset 123456789`"
            )
            return
        
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ")
            return
        
        # Reset user's daily usage
        await db.reset_daily_usage(user_id)
        
        await message.reply_text(
            f"🔄 **ᴜsᴇʀ ʀᴇsᴇᴛ**\n\n"
            f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
            f"ᴅᴀɪʟʏ ᴜsᴀɢᴇ ʜᴀs ʙᴇᴇɴ ʀᴇsᴇᴛ."
        )
        
    except Exception as e:
        logger.error(f"Error in reset command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ʀᴇsᴇᴛᴛɪɴɢ ᴜsᴇʀ.")

@Client.on_message(filters.command("addsudo") & filters.private)
async def addsudo_command(client: Client, message: Message):
    """Handle /addsudo command (owner only)"""
    try:
        if message.from_user.id != Config.OWNER_ID:
            await message.reply_text("❌ ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
            return
        
        if len(message.command) < 2:
            await message.reply_text(
                "❌ **ɪɴᴠᴀʟɪᴅ ᴜsᴀɢᴇ**\n\n"
                "**ᴜsᴀɢᴇ:** `/addsudo <user_id>`\n"
                "**ᴇxᴀᴍᴘʟᴇ:** `/addsudo 123456789`"
            )
            return
        
        try:
            user_id = int(message.command[1])
        except ValueError:
            await message.reply_text("❌ ɪɴᴠᴀʟɪᴅ ᴜsᴇʀ ɪᴅ")
            return
        
        if user_id in Config.ADMINS:
            await message.reply_text("❌ ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ.")
            return
        
        # Add to admins list (runtime only)
        Config.ADMINS.append(user_id)
        
        await message.reply_text(
            f"👑 **ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ**\n\n"
            f"**ᴜsᴇʀ ɪᴅ:** `{user_id}`\n"
            f"ᴛʜᴇʏ ɴᴏᴡ ʜᴀᴠᴇ ᴀᴅᴍɪɴ ᴀᴄᴄᴇss."
        )
        
        # Notify new admin
        try:
            await client.send_message(
                user_id,
                "🎉 **ᴀᴅᴍɪɴ ᴀᴄᴄᴇss ɢʀᴀɴᴛᴇᴅ**\n\n"
                "ʏᴏᴜ ɴᴏᴡ ʜᴀᴠᴇ ᴀᴅᴍɪɴ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ʙᴏᴛ!"
            )
        except Exception as e:
            logger.error(f"Failed to notify new admin: {e}")
        
    except Exception as e:
        logger.error(f"Error in addsudo command: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴀᴅᴅɪɴɢ ᴀᴅᴍɪɴ.")
