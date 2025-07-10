import os
import uuid
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import Database
from config import Config
from helpers.ffmpeg import FFmpegProcessor
from progress import ProgressTracker
import logging
import asyncio

logger = logging.getLogger(__name__)
db = Database()

# Store pending operations
pending_operations = {}

@Client.on_message(filters.video & filters.private)
async def handle_video(client: Client, message: Message):
    """Handle video uploads"""
    try:
        # Ensure database is connected
        if not db._connected:
            await db.connect()
            
        user_id = message.from_user.id
        
        # Check if user exists
        user = await db.get_user(user_id)
        if not user:
            await message.reply_text("❌ ᴘʟᴇᴀsᴇ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀsᴛ ᴜsɪɴɢ /start")
            return
        
        # Check if user is banned
        if await db.is_user_banned(user_id):
            await message.reply_text("🚫 ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ꜰʀᴏᴍ ᴜsɪɴɢ ᴛʜɪs ʙᴏᴛ.")
            return
        
        # Check daily limit
        if not await db.check_daily_limit(user_id):
            await message.reply_text(
                f"⏰ **ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ**\n\n"
                f"ꜰʀᴇᴇ ᴜsᴇʀs ᴄᴀɴ ᴏɴʟʏ ᴘʀᴏᴄᴇss {Config.DAILY_LIMIT} ᴠɪᴅᴇᴏs ᴘᴇʀ ᴅᴀʏ.\n\n"
                f"💎 ᴜᴘɢʀᴀᴅᴇ ᴛᴏ ᴘʀᴇᴍɪᴜᴍ ꜰᴏʀ ᴜɴʟɪᴍɪᴛᴇᴅ ᴘʀᴏᴄᴇssɪɴɢ!"
            )
            return
        
        # Show processing options
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✂️ ᴛʀɪᴍ ᴠɪᴅᴇᴏ", callback_data=f"option_trim_{message.id}"),
                InlineKeyboardButton("🗜️ ᴄᴏᴍᴘʀᴇss", callback_data=f"option_compress_{message.id}")
            ],
            [
                InlineKeyboardButton("🔄 ʀᴏᴛᴀᴛᴇ", callback_data=f"option_rotate_{message.id}"),
                InlineKeyboardButton("🔗 ᴍᴇʀɢᴇ", callback_data=f"option_merge_{message.id}")
            ],
            [
                InlineKeyboardButton("💧 ᴡᴀᴛᴇʀᴍᴀʀᴋ", callback_data=f"option_watermark_{message.id}"),
                InlineKeyboardButton("🔇 ᴍᴜᴛᴇ", callback_data=f"option_mute_{message.id}")
            ],
            [
                InlineKeyboardButton("🎵 ʀᴇᴘʟᴀᴄᴇ ᴀᴜᴅɪᴏ", callback_data=f"option_replace_audio_{message.id}"),
                InlineKeyboardButton("⏮️ ʀᴇᴠᴇʀsᴇ", callback_data=f"option_reverse_{message.id}")
            ],
            [
                InlineKeyboardButton("📝 sᴜʙᴛɪᴛʟᴇs", callback_data=f"option_subtitles_{message.id}"),
                InlineKeyboardButton("📏 ʀᴇsᴏʟᴜᴛɪᴏɴ", callback_data=f"option_resolution_{message.id}")
            ],
            [
                InlineKeyboardButton("🎶 ᴇxᴛʀᴀᴄᴛ ᴀᴜᴅɪᴏ", callback_data=f"option_extract_audio_{message.id}"),
                InlineKeyboardButton("📸 sᴄʀᴇᴇɴsʜᴏᴛ", callback_data=f"option_screenshot_{message.id}")
            ]
        ])
        
        video_info = f"📹 **ᴠɪᴅᴇᴏ ʀᴇᴄᴇɪᴠᴇᴅ**\n\n"
        video_info += f"**ꜰɪʟᴇ ɴᴀᴍᴇ:** {message.video.file_name or 'Unknown'}\n"
        video_info += f"**sɪᴢᴇ:** {message.video.file_size / (1024*1024):.2f} ᴍʙ\n"
        video_info += f"**ᴅᴜʀᴀᴛɪᴏɴ:** {message.video.duration // 60}:{message.video.duration % 60:02d}\n"
        video_info += f"**ʀᴇsᴏʟᴜᴛɪᴏɴ:** {message.video.width}x{message.video.height}\n\n"
        video_info += f"**ᴄᴏsᴛ:** {Config.PROCESS_COST} ᴄʀᴇᴅɪᴛs ᴘᴇʀ ᴏᴘᴇʀᴀᴛɪᴏɴ\n"
        video_info += f"**ʏᴏᴜʀ ᴄʀᴇᴅɪᴛs:** {user.get('credits', 0)}\n\n"
        video_info += "ᴄʜᴏᴏsᴇ ᴀ ᴘʀᴏᴄᴇssɪɴɢ ᴏᴘᴛɪᴏɴ:"
        
        await message.reply_text(video_info, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await message.reply_text("❌ ᴇʀʀᴏʀ ᴘʀᴏᴄᴇssɪɴɢ ᴠɪᴅᴇᴏ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ.")

# Handle option selection (with detailed configuration)
@Client.on_callback_query(filters.regex(r"^option_"))
async def handle_option_callback(client: Client, callback_query: CallbackQuery):
    """Handle video processing option callbacks"""
    try:
        # Ensure database is connected
        if not db._connected:
            await db.connect()
            
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Parse callback data
        parts = data.split("_")
        if len(parts) < 3:
            await callback_query.answer("❌ ɪɴᴠᴀʟɪᴅ ᴄᴀʟʟʙᴀᴄᴋ ᴅᴀᴛᴀ", show_alert=True)
            return
        
        operation = "_".join(parts[1:-1])
        message_id = int(parts[-1])
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Check if user is banned
        if await db.is_user_banned(user_id):
            await callback_query.answer("🚫 ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ", show_alert=True)
            return
        
        # Check credits
        if user.get("credits", 0) < Config.PROCESS_COST:
            await callback_query.answer(
                f"❌ ɪɴsᴜꜰꜰɪᴄɪᴇɴᴛ ᴄʀᴇᴅɪᴛs!\nʏᴏᴜ ɴᴇᴇᴅ {Config.PROCESS_COST} ᴄʀᴇᴅɪᴛs ʙᴜᴛ ʜᴀᴠᴇ {user.get('credits', 0)}",
                show_alert=True
            )
            return
        
        # Check daily limit
        if not await db.check_daily_limit(user_id):
            await callback_query.answer("⏰ ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ", show_alert=True)
            return
        
        # Get original video message
        try:
            video_message = await client.get_messages(callback_query.message.chat.id, message_id)
            if not video_message.video:
                await callback_query.answer("❌ ᴠɪᴅᴇᴏ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
                return
        except Exception as e:
            await callback_query.answer("❌ ᴠɪᴅᴇᴏ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Show detailed options based on operation type
        if operation == "trim":
            await show_trim_options(client, callback_query, video_message)
        elif operation == "compress":
            await show_compress_options(client, callback_query, video_message)
        elif operation == "rotate":
            await show_rotate_options(client, callback_query, video_message)
        elif operation == "merge":
            await show_merge_options(client, callback_query, video_message)
        elif operation == "watermark":
            await show_watermark_options(client, callback_query, video_message)
        elif operation == "screenshot":
            await show_screenshot_options(client, callback_query, video_message)
        elif operation == "resolution":
            await show_resolution_options(client, callback_query, video_message)
        elif operation == "extract_audio":
            await show_extract_audio_options(client, callback_query, video_message)
        elif operation == "subtitles":
            await show_subtitles_options(client, callback_query, video_message)
        else:
            # For simple operations, start processing directly
            await start_processing(client, callback_query, video_message, operation)
        
    except Exception as e:
        logger.error(f"Error in option callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ sʜᴏᴡɪɴɢ ᴏᴘᴛɪᴏɴs", show_alert=True)

# Handle processing confirmation
@Client.on_callback_query(filters.regex(r"^process_"))
async def handle_process_callback(client: Client, callback_query: CallbackQuery):
    """Handle video processing callbacks"""
    try:
        # Ensure database is connected
        if not db._connected:
            await db.connect()
            
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Parse callback data
        parts = data.split("_")
        if len(parts) < 3:
            await callback_query.answer("❌ ɪɴᴠᴀʟɪᴅ ᴄᴀʟʟʙᴀᴄᴋ ᴅᴀᴛᴀ", show_alert=True)
            return
        
        operation = "_".join(parts[1:-1])
        message_id = int(parts[-1])
        
        # Get user
        user = await db.get_user(user_id)
        if not user:
            await callback_query.answer("❌ ᴜsᴇʀ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Check if user is banned
        if await db.is_user_banned(user_id):
            await callback_query.answer("🚫 ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ", show_alert=True)
            return
        
        # Check credits
        if user.get("credits", 0) < Config.PROCESS_COST:
            await callback_query.answer(
                f"❌ ɪɴsᴜꜰꜰɪᴄɪᴇɴᴛ ᴄʀᴇᴅɪᴛs!\nʏᴏᴜ ɴᴇᴇᴅ {Config.PROCESS_COST} ᴄʀᴇᴅɪᴛs ʙᴜᴛ ʜᴀᴠᴇ {user.get('credits', 0)}",
                show_alert=True
            )
            return
        
        # Check daily limit
        if not await db.check_daily_limit(user_id):
            await callback_query.answer("⏰ ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ", show_alert=True)
            return
        
        # Get original video message
        try:
            video_message = await client.get_messages(callback_query.message.chat.id, message_id)
            if not video_message.video:
                await callback_query.answer("❌ ᴠɪᴅᴇᴏ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
                return
        except Exception as e:
            await callback_query.answer("❌ ᴠɪᴅᴇᴏ ɴᴏᴛ ꜰᴏᴜɴᴅ", show_alert=True)
            return
        
        # Start processing
        await start_processing(client, callback_query, video_message, operation)
        
    except Exception as e:
        logger.error(f"Error in process callback: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴘʀᴏᴄᴇss", show_alert=True)

async def show_trim_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show trim options"""
    duration = video_message.video.duration
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✂️ ꜰɪʀsᴛ 30s", callback_data=f"process_trim_30_{video_message.id}"),
            InlineKeyboardButton("✂️ ꜰɪʀsᴛ 60s", callback_data=f"process_trim_60_{video_message.id}")
        ],
        [
            InlineKeyboardButton("✂️ ꜰɪʀsᴛ 5ᴍɪɴ", callback_data=f"process_trim_300_{video_message.id}"),
            InlineKeyboardButton("✂️ ꜰɪʀsᴛ 10ᴍɪɴ", callback_data=f"process_trim_600_{video_message.id}")
        ],
        [
            InlineKeyboardButton("✂️ ᴄᴜsᴛᴏᴍ", callback_data=f"process_trim_custom_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"✂️ **ᴛʀɪᴍ ᴠɪᴅᴇᴏ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"**ᴏʀɪɢɪɴᴀʟ ᴅᴜʀᴀᴛɪᴏɴ:** {duration // 60}:{duration % 60:02d}\n\n"
    text += f"sᴇʟᴇᴄᴛ ʜᴏᴡ ᴍᴜᴄʜ ᴏꜰ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴛᴏ ᴋᴇᴇᴘ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_compress_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show compress options"""
    size_mb = video_message.video.file_size / (1024 * 1024)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🗜️ ʜɪɢʜ ǫᴜᴀʟɪᴛʏ", callback_data=f"process_compress_high_{video_message.id}"),
            InlineKeyboardButton("🗜️ ᴍᴇᴅɪᴜᴍ", callback_data=f"process_compress_medium_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🗜️ sᴍᴀʟʟ sɪᴢᴇ", callback_data=f"process_compress_small_{video_message.id}"),
            InlineKeyboardButton("🗜️ ᴛɪɴʏ sɪᴢᴇ", callback_data=f"process_compress_tiny_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"🗜️ **ᴄᴏᴍᴘʀᴇss ᴠɪᴅᴇᴏ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"**ᴏʀɪɢɪɴᴀʟ sɪᴢᴇ:** {size_mb:.2f} ᴍʙ\n\n"
    text += f"sᴇʟᴇᴄᴛ ᴄᴏᴍᴘʀᴇssɪᴏɴ ʟᴇᴠᴇʟ:\n"
    text += f"• ʜɪɢʜ ǫᴜᴀʟɪᴛʏ: ~{size_mb * 0.7:.1f} ᴍʙ\n"
    text += f"• ᴍᴇᴅɪᴜᴍ: ~{size_mb * 0.5:.1f} ᴍʙ\n"
    text += f"• sᴍᴀʟʟ sɪᴢᴇ: ~{size_mb * 0.3:.1f} ᴍʙ\n"
    text += f"• ᴛɪɴʏ sɪᴢᴇ: ~{size_mb * 0.1:.1f} ᴍʙ"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_rotate_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show rotate options"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 90° ᴄʟᴏᴄᴋᴡɪsᴇ", callback_data=f"process_rotate_90_{video_message.id}"),
            InlineKeyboardButton("🔄 180°", callback_data=f"process_rotate_180_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🔄 270° ᴄʟᴏᴄᴋᴡɪsᴇ", callback_data=f"process_rotate_270_{video_message.id}"),
            InlineKeyboardButton("🔄 ꜰʟɪᴘ ʜᴏʀɪᴢᴏɴᴛᴀʟ", callback_data=f"process_rotate_flip_h_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🔄 ꜰʟɪᴘ ᴠᴇʀᴛɪᴄᴀʟ", callback_data=f"process_rotate_flip_v_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"🔄 **ʀᴏᴛᴀᴛᴇ ᴠɪᴅᴇᴏ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"sᴇʟᴇᴄᴛ ʀᴏᴛᴀᴛɪᴏɴ ᴏᴘᴛɪᴏɴ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_merge_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show merge options"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📤 sᴇɴᴅ ᴀɴᴏᴛʜᴇʀ ᴠɪᴅᴇᴏ", callback_data=f"merge_wait_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"🔗 **ᴍᴇʀɢᴇ ᴠɪᴅᴇᴏs**\n\n"
    text += f"ᴛᴏ ᴍᴇʀɢᴇ ᴠɪᴅᴇᴏs, ɪ ɴᴇᴇᴅ ᴀɴᴏᴛʜᴇʀ ᴠɪᴅᴇᴏ ꜰʀᴏᴍ ʏᴏᴜ.\n\n"
    text += f"**ᴄᴜʀʀᴇɴᴛ ᴠɪᴅᴇᴏ:**\n"
    text += f"• ᴅᴜʀᴀᴛɪᴏɴ: {video_message.video.duration // 60}:{video_message.video.duration % 60:02d}\n"
    text += f"• sɪᴢᴇ: {video_message.video.file_size / (1024*1024):.2f} ᴍʙ\n\n"
    text += f"ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_watermark_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show watermark options"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💧 ᴛᴇxᴛ ᴡᴀᴛᴇʀᴍᴀʀᴋ", callback_data=f"watermark_text_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🏷️ ᴛɪᴍᴇsᴛᴀᴍᴘ", callback_data=f"process_watermark_timestamp_{video_message.id}"),
            InlineKeyboardButton("🎨 ᴄᴜsᴛᴏᴍ ᴛᴇxᴛ", callback_data=f"watermark_custom_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"💧 **ᴡᴀᴛᴇʀᴍᴀʀᴋ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"sᴇʟᴇᴄᴛ ᴡᴀᴛᴇʀᴍᴀʀᴋ ᴛʏᴘᴇ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_screenshot_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show screenshot options"""
    duration = video_message.video.duration
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📸 sɪɴɢʟᴇ (ᴍɪᴅᴅʟᴇ)", callback_data=f"process_screenshot_single_{video_message.id}"),
            InlineKeyboardButton("📸 3 sᴄʀᴇᴇɴsʜᴏᴛs", callback_data=f"process_screenshot_multi_3_{video_message.id}")
        ],
        [
            InlineKeyboardButton("📸 5 sᴄʀᴇᴇɴsʜᴏᴛs", callback_data=f"process_screenshot_multi_5_{video_message.id}"),
            InlineKeyboardButton("📸 10 sᴄʀᴇᴇɴsʜᴏᴛs", callback_data=f"process_screenshot_multi_10_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🎨 ʜᴅ ǫᴜᴀʟɪᴛʏ", callback_data=f"process_screenshot_hd_{video_message.id}"),
            InlineKeyboardButton("📝 ᴄᴜsᴛᴏᴍ ᴛɪᴍᴇ", callback_data=f"screenshot_custom_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"📸 **sᴄʀᴇᴇɴsʜᴏᴛ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"**ᴠɪᴅᴇᴏ ᴅᴜʀᴀᴛɪᴏɴ:** {duration // 60}:{duration % 60:02d}\n\n"
    text += f"sᴇʟᴇᴄᴛ sᴄʀᴇᴇɴsʜᴏᴛ ᴏᴘᴛɪᴏɴ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_resolution_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show resolution options"""
    current_res = f"{video_message.video.width}x{video_message.video.height}"
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📏 480ᴘ", callback_data=f"process_resolution_480_{video_message.id}"),
            InlineKeyboardButton("📏 720ᴘ", callback_data=f"process_resolution_720_{video_message.id}")
        ],
        [
            InlineKeyboardButton("📏 1080ᴘ", callback_data=f"process_resolution_1080_{video_message.id}"),
            InlineKeyboardButton("📏 1440ᴘ", callback_data=f"process_resolution_1440_{video_message.id}")
        ],
        [
            InlineKeyboardButton("📏 4ᴋ", callback_data=f"process_resolution_4k_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"📏 **ᴄʜᴀɴɢᴇ ʀᴇsᴏʟᴜᴛɪᴏɴ**\n\n"
    text += f"**ᴄᴜʀʀᴇɴᴛ ʀᴇsᴏʟᴜᴛɪᴏɴ:** {current_res}\n\n"
    text += f"sᴇʟᴇᴄᴛ ɴᴇᴡ ʀᴇsᴏʟᴜᴛɪᴏɴ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_extract_audio_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show extract audio options"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎶 ᴍᴘ3 (ʜɪɢʜ)", callback_data=f"process_extract_audio_mp3_high_{video_message.id}"),
            InlineKeyboardButton("🎶 ᴍᴘ3 (ᴍᴇᴅɪᴜᴍ)", callback_data=f"process_extract_audio_mp3_medium_{video_message.id}")
        ],
        [
            InlineKeyboardButton("🎶 ᴍᴘ3 (ʟᴏᴡ)", callback_data=f"process_extract_audio_mp3_low_{video_message.id}"),
            InlineKeyboardButton("🎵 ᴡᴀᴠ", callback_data=f"process_extract_audio_wav_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"🎶 **ᴇxᴛʀᴀᴄᴛ ᴀᴜᴅɪᴏ ᴏᴘᴛɪᴏɴs**\n\n"
    text += f"sᴇʟᴇᴄᴛ ᴀᴜᴅɪᴏ ғᴏʀᴍᴀᴛ ᴀɴᴅ ǫᴜᴀʟɪᴛʏ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def show_subtitles_options(client: Client, callback_query: CallbackQuery, video_message: Message):
    """Show subtitles options"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 sᴀᴍᴘʟᴇ sᴜʙᴛɪᴛʟᴇ", callback_data=f"process_subtitles_sample_{video_message.id}"),
            InlineKeyboardButton("📝 ᴄᴜsᴛᴏᴍ ᴛᴇxᴛ", callback_data=f"subtitles_custom_{video_message.id}")
        ],
        [
            InlineKeyboardButton("◀️ ʙᴀᴄᴋ", callback_data=f"back_to_options_{video_message.id}")
        ]
    ])
    
    text = f"📝 **ᴀᴅᴅ sᴜʙᴛɪᴛʟᴇs**\n\n"
    text += f"sᴇʟᴇᴄᴛ sᴜʙᴛɪᴛʟᴇ ᴏᴘᴛɪᴏɴ:"
    
    await callback_query.edit_message_text(text, reply_markup=keyboard)

async def start_processing(client: Client, callback_query: CallbackQuery, video_message: Message, operation: str):
    """Start the actual processing"""
    try:
        user_id = callback_query.from_user.id
        
        # Get user for credit deduction
        user = await db.get_user(user_id)
        
        # Deduct credits
        if not await db.deduct_credits(user_id, Config.PROCESS_COST):
            await callback_query.answer("❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴅᴇᴅᴜᴄᴛ ᴄʀᴇᴅɪᴛs", show_alert=True)
            return
        
        # Increment daily usage
        await db.increment_daily_usage(user_id)
        
        # Add operation record
        operation_record = await db.add_operation(user_id, operation, "processing")
        
        # Answer callback
        await callback_query.answer("✅ ᴘʀᴏᴄᴇssɪɴɢ sᴛᴀʀᴛᴇᴅ!")
        
        # Start processing
        await process_video(client, callback_query.message, video_message, operation, operation_record.inserted_id)
        
    except Exception as e:
        logger.error(f"Error starting processing: {e}")
        await callback_query.answer("❌ ᴇʀʀᴏʀ sᴛᴀʀᴛɪɴɢ ᴘʀᴏᴄᴇss", show_alert=True)

async def process_video(client: Client, reply_message: Message, video_message: Message, operation: str, operation_id):
    """Process video with selected operation"""
    try:
        user_id = reply_message.chat.id
        
        # Create unique process ID
        process_id = str(uuid.uuid4())
        
        # Initialize progress tracker
        progress_tracker = ProgressTracker(client)
        
        # Create progress message
        progress_msg = await reply_message.edit_text(
            f"🎬 **ᴘʀᴏᴄᴇssɪɴɢ ᴠɪᴅᴇᴏ**\n\n"
            f"**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}\n\n"
            f"📥 ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴠɪᴅᴇᴏ..."
        )
        
        # Start progress tracking for download
        await progress_tracker.start_progress(
            user_id,
            progress_msg.id,
            f"Downloading {operation.replace('_', ' ').title()}",
            video_message.video.file_size,
            f"{process_id}_download"
        )
        
        # Download video with progress tracking
        async def download_progress(current: int, total: int):
            await progress_tracker.update_progress(f"{process_id}_download", current)
        
        video_path = await client.download_media(
            video_message.video,
            file_name=f"{Config.DOWNLOADS_DIR}/{process_id}_{video_message.video.file_name or 'video.mp4'}",
            progress=download_progress
        )
        
        # Complete download progress
        await progress_tracker.complete_progress(f"{process_id}_download", True)
        
        # Start processing progress
        await progress_tracker.start_progress(
            user_id,
            progress_msg.id,
            f"Processing {operation.replace('_', ' ').title()}",
            video_message.video.file_size,
            f"{process_id}_process"
        )
        
        # Process video
        ffmpeg_processor = FFmpegProcessor()
        output_path = await ffmpeg_processor.process_video(video_path, operation, process_id, progress_tracker)
        
        if not output_path or not os.path.exists(output_path):
            await progress_tracker.complete_progress(f"{process_id}_process", False)
            await db.update_operation(operation_id, {"status": "failed"})
            return
        
        # Complete processing progress
        await progress_tracker.complete_progress(f"{process_id}_process", True)
        
        # Update final message
        await progress_msg.edit_text(
            f"✅ **ᴘʀᴏᴄᴇssɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n"
            f"**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}\n\n"
            f"🚀 ᴜᴘʟᴏᴀᴅɪɴɢ ᴘʀᴏᴄᴇssᴇᴅ ᴠɪᴅᴇᴏ..."
        )
        
        # Send processed video based on operation type
        if operation == "screenshot":
            # Send as photo
            await client.send_photo(
                user_id,
                output_path,
                caption=f"📸 **sᴄʀᴇᴇɴsʜᴏᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}"
            )
        elif operation == "extract_audio":
            # Send as audio
            await client.send_audio(
                user_id,
                output_path,
                caption=f"🎵 **ᴀᴜᴅɪᴏ ᴇxᴛʀᴀᴄᴛᴇᴅ**\n\n**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}"
            )
        else:
            # Send as video
            # Upload to media channel first
            if Config.MEDIA_CHANNEL_ID:
                try:
                    media_msg = await client.send_video(
                        Config.MEDIA_CHANNEL_ID,
                        output_path,
                        caption=f"ᴘʀᴏᴄᴇssᴇᴅ ᴠɪᴅᴇᴏ - {operation.replace('_', ' ').title()}"
                    )
                    
                    # Forward to user
                    await media_msg.forward(user_id)
                    
                except Exception as e:
                    logger.error(f"Failed to upload to media channel: {e}")
                    # Send directly to user
                    await client.send_video(
                        user_id,
                        output_path,
                        caption=f"✅ **ᴘʀᴏᴄᴇssɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}"
                    )
            else:
                # Send directly to user
                await client.send_video(
                    user_id,
                    output_path,
                    caption=f"✅ **ᴘʀᴏᴄᴇssɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}"
                )
        
        # Update operation status
        await db.update_operation(operation_id, {"status": "completed"})
        
        # Log to log channel
        if Config.LOG_CHANNEL_ID:
            try:
                log_text = f"✅ **ᴘʀᴏᴄᴇssɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ**\n\n"
                log_text += f"**ᴜsᴇʀ:** `{user_id}`\n"
                log_text += f"**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}\n"
                log_text += f"**ᴄʀᴇᴅɪᴛs ᴜsᴇᴅ:** {Config.PROCESS_COST}"
                
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.error(f"Failed to log operation: {e}")
        
        # Clean up files
        try:
            os.remove(video_path)
            os.remove(output_path)
        except Exception as e:
            logger.error(f"Failed to clean up files: {e}")
            
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        await db.update_operation(operation_id, {"status": "failed"})
        try:
            await client.send_message(
                user_id,
                f"❌ **ᴘʀᴏᴄᴇssɪɴɢ ꜰᴀɪʟᴇᴅ**\n\n"
                f"**ᴏᴘᴇʀᴀᴛɪᴏɴ:** {operation.replace('_', ' ').title()}\n\n"
                f"ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ᴏʀ ᴄᴏɴᴛᴀᴄᴛ sᴜᴘᴘᴏʀᴛ."
            )
        except:
            pass
