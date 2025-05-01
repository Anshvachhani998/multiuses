from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import db
from info import LOG_CHANNEL, ADMINS

@Client.on_message(filters.photo)
async def handle_thumbnail(client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    file_id = message.photo.file_id
    await db.save_thumbnail(message.from_user.id, file_id)
    
    await message.reply_text("📸 **Your thumbnail has been saved successfully!**")

@Client.on_message(filters.command("show_thumbnail"))
async def show_thumbnail(client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    thumbnail_file_id = await db.get_user_thumbnail(message.from_user.id)
    
    if thumbnail_file_id:
        await message.reply_photo(thumbnail_file_id)
    else:
        await message.reply_text("🚫 **You haven't set a thumbnail yet. Please send a photo to set one.**")

@Client.on_message(filters.command("remove_thumbnail"))
async def remove_thumbnail(client, message: Message):
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)

    success = await db.remove_thumbnail(message.from_user.id)
    
    if success:
        await message.reply_text("❌ **Your thumbnail has been removed successfully.**")
    else:
        await message.reply_text("🚫 **You haven't set a thumbnail to remove.**")
