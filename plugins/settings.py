from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.db import db


@Client.on_message(filters.command("settings"))
async def settings(client, message):
    user_id = message.from_user.id
    user_settings = await db.get_user_settings(user_id)
    has_thumbnail = await db.get_user_thumbnail(user_id)

    upload_as_doc = user_settings.get("upload_as_doc", False)
    upload_mode = "📄 Document" if upload_as_doc else "🎬 Video"
    thumbnail_status = "✅ Set" if has_thumbnail else "❌ Not Set"

    # Summary text
    text = (
        "**⚙️ Your Current Settings:**\n\n"
        f"**Upload Mode:** {upload_mode}\n"
        f"**Thumbnail:** {thumbnail_status}\n\n"
        "You can change them using the buttons below 👇"
    )

    # Buttons
    upload_btn_text = "🔄 Upload as Video" if upload_as_doc else "🔄 Upload as Document"
    buttons = [[InlineKeyboardButton(upload_btn_text, callback_data="toggle_upload_mode")]]

    if has_thumbnail:
        buttons.append([
            InlineKeyboardButton("📷 Show Thumbnail", callback_data="show_thumbnail"),
            InlineKeyboardButton("🗑️ Remove Thumbnail", callback_data="remove_thumbnail")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🖼️ Set Thumbnail", callback_data="set_thumbnail")
        ])

    markup = InlineKeyboardMarkup(buttons)
    await message.reply(text, reply_markup=markup)

# Toggle Upload Mode
@Client.on_callback_query(filters.regex("toggle_upload_mode"))
async def toggle_upload_mode(client, callback_query):
    user_id = callback_query.from_user.id
    new_value = await db.toggle_upload_mode(user_id)
    has_thumbnail = await db.get_user_thumbnail(user_id)

    upload_mode = "📄 Document" if new_value else "🎬 Video"
    thumbnail_status = "✅ Set" if has_thumbnail else "❌ Not Set"

    text = (
        "**⚙️ Your Current Settings:**\n\n"
        f"**Upload Mode:** {upload_mode}\n"
        f"**Thumbnail:** {thumbnail_status}\n\n"
        "You can change them using the buttons below 👇"
    )

    upload_btn_text = "🔄 Upload as Video" if not new_value else "🔄 Upload as Document"
    buttons = [[InlineKeyboardButton(upload_btn_text, callback_data="toggle_upload_mode")]]

    if has_thumbnail:
        buttons.append([
            InlineKeyboardButton("📷 Show Thumbnail", callback_data="show_thumbnail"),
            InlineKeyboardButton("🗑️ Remove Thumbnail", callback_data="remove_thumbnail")
        ])
    else:
        buttons.append([
            InlineKeyboardButton("🖼️ Set Thumbnail", callback_data="set_thumbnail")
        ])

    markup = InlineKeyboardMarkup(buttons)
    await callback_query.edit_message_text(text, reply_markup=markup)

# Set Thumbnail
@Client.on_callback_query(filters.regex("set_thumbnail"))
async def set_thumbnail_callback(client, callback_query):
    await callback_query.message.edit("📸 Please send the photo you want to set as your thumbnail.")
    # You can now listen for the next photo message separately using on_message

# Show Thumbnail
@Client.on_callback_query(filters.regex("show_thumbnail"))
async def show_thumbnail_callback(client, callback_query):
    user_id = callback_query.from_user.id
    thumb = await db.get_user_thumbnail(user_id)
    if thumb:
        await client.send_photo(user_id, photo=thumb, caption="📷 This is your current thumbnail.")
        await callback_query.answer("✅ Thumbnail sent to your DM", show_alert=True)
    else:
        await callback_query.answer("❌ No thumbnail found", show_alert=True)

# Remove Thumbnail
@Client.on_callback_query(filters.regex("remove_thumbnail"))
async def remove_thumbnail_callback(client, callback_query):
    user_id = callback_query.from_user.id
    removed = await db.remove_thumbnail(user_id)

    user_settings = await db.get_user_settings(user_id)
    upload_as_doc = user_settings.get("upload_as_doc", False)
    upload_mode = "📄 Document" if upload_as_doc else "🎬 Video"
    thumbnail_status = "❌ Not Set"

    text = (
        "**⚙️ Your Current Settings:**\n\n"
        f"**Upload Mode:** {upload_mode}\n"
        f"**Thumbnail:** {thumbnail_status}\n\n"
        "You can change them using the buttons below 👇"
    )

    buttons = [
        [InlineKeyboardButton("🔄 Upload as Video" if upload_as_doc else "🔄 Upload as Document", callback_data="toggle_upload_mode")],
        [InlineKeyboardButton("🖼️ Set Thumbnail", callback_data="set_thumbnail")]
    ]

    if removed:
        await callback_query.answer("🗑️ Thumbnail removed!", show_alert=True)
    else:
        await callback_query.answer("❌ No thumbnail was set!", show_alert=True)

    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
