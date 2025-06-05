import random
import time
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    # Save or update user data
    user_data = await collection.find_one({"_id": user_id})
    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"New user Started The Bot..\nUser: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
            parse_mode='HTML'
        )
    else:
        if user_data.get("first_name") != first_name or user_data.get("username") != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    # Ping and uptime
    start_time = time.time()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    ping = round((time.time() - start_time) * 1000, 3)

    uptime = "coming soon..."  # Replace with real uptime if needed

    # Start message
    start_msg = f"""
*ʜᴇʟʟᴏ...*

*ɪ'ᴍ sɴᴀᴛᴄʜ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʙᴏᴛ — ᴀ ɢʀᴀʙ ʙᴏᴛ...*

ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ɪ ᴡɪʟʟ sᴇɴᴅ ʀᴀɴᴅᴏᴍ ᴄʜᴀʀᴀᴄᴛᴇʀs ғᴏʀ ʏᴏᴜ ᴛᴏ ɢᴜᴇss, ᴄᴏʟʟᴇᴄᴛ & ᴛʀᴀᴅᴇ...

ᴛᴀᴘ ᴏɴ *ʜᴇʟᴘ* ʙᴜᴛᴛᴏɴ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs.

ᴍᴜsᴛ ᴊᴏɪɴ :- @The_League_Of_Snatchers

➺ *ᴘɪɴɢ:* `{ping} ms`
➺ *ᴜᴘᴛɪᴍᴇ:* `{uptime}`
"""

    # Keyboard
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("ADD ME", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        [
            InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
            InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')
        ],
        [InlineKeyboardButton("HELP", callback_data='help')]
    ])

    photo_url = random.choice(PHOTO_URL)

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo_url,
        caption=start_msg,
        reply_markup=keyboard,
        parse_mode='markdown'
    )


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
***Help Section:***

*/guess* – Guess a character (only in groups)  
*/fav* – Add your favorite  
*/trade* – Trade characters  
*/gift* – Gift a character to someone (only in groups)  
*/collection* – View your collection  
*/topgroups* – Top guessing groups  
*/top* – Top users  
*/ctop* – Chat-wise top  
*/changetime* – Change drop time (groups only)
"""
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await context.bot.edit_message_caption(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            caption=help_text,
            reply_markup=reply_markup,
            parse_mode='markdown'
        )

    elif query.data == 'back':
        # Ping again for refresh
        ping = round((time.time() - time.time()) * 1000, 3)
        uptime = "coming soon..."

        start_msg = f"""
*ʜᴇʟʟᴏ...*

*ɪ'ᴍ sɴᴀᴛᴄʜ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʙᴏᴛ — ᴀ ɢʀᴀʙ ʙᴏᴛ...*

ᴛᴀᴘ ᴏɴ *ʜᴇʟᴘ* ʙᴜᴛᴛᴏɴ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs.

ᴍᴜsᴛ ᴊᴏɪɴ :- @The_League_Of_Snatchers

➺ *ᴘɪɴɢ:* `{ping} ms`
➺ *ᴜᴘᴛɪᴍᴇ:* `{uptime}`
"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("ADD ME", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [
                InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
                InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')
            ],
            [InlineKeyboardButton("HELP", callback_data='help')]
        ])

        await context.bot.edit_message_caption(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            caption=start_msg,
            reply_markup=keyboard,
            parse_mode='markdown'
        )


# 🧠 Button handler (don't remove)
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))

# ✅ Your original way of adding start handler
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
