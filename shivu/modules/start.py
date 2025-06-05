import random
import time
import re
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection

from shivu.modules import ping  # if needed

# MarkdownV2 escape function
def escape_md(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

# Uptime and ping
start_time = time.time()
end_time = time.time()
elapsed_time = round((end_time - start_time) * 1000, 3)

# Start message
start_msg = f"""
*ʜᴇʟʟᴏ...*

*ɪ'ᴍ sɴᴀᴛᴄʜ ʏᴏᴜʀ ᴄʜᴀʀᴀᴄᴛᴇʀ ʙᴏᴛ ᴀ ɢʀᴀʙ ʙᴏᴛ.....*

ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ɪ ᴡɪʟʟ sᴇɴᴅ ʀᴀɴᴅᴏᴍ ᴄʜᴀʀᴀᴄᴛᴇʀs ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ...

ᴛᴀᴘ ᴏɴ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ sᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs...

ᴍᴜsᴛ Jᴏɪɴ :- @The_League_Of_Snatchers*

➺ ᴘɪɴɢ: {elapsed_time}ms  
➺ ᴜᴘᴛɪᴍᴇ: 
"""

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ADD ME", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
        [InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
         InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
        [InlineKeyboardButton("HELP", callback_data='help')]
    ])

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat = update.effective_chat
    user_id = user.id
    first_name = user.first_name
    username = user.username

    user_data = await collection.find_one({"_id": user_id})
    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"New user started the bot.\nUser: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
            parse_mode='HTML'
        )
    elif user_data['first_name'] != first_name or user_data['username'] != username:
        await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    photo_url = random.choice(PHOTO_URL)
    reply_markup = get_main_keyboard()

    await context.bot.send_photo(
        chat_id=chat.id,
        photo=photo_url,
        caption=escape_md(start_msg),
        reply_markup=reply_markup,
        parse_mode='MarkdownV2'
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = """
*Help Section:*

`/guess` \\- Guess a character \\(group only\\)  
`/fav` \\- Add your favorite  
`/trade` \\- Trade characters  
`/gift` \\- Gift characters to others \\(group only\\)  
`/collection` \\- Show your character collection  
`/topgroups` \\- View top groups  
`/top` \\- View top users  
`/ctop` \\- View your group top  
`/changetime` \\- Change character appear time \\(group only\\)
"""
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)

        await context.bot.edit_message_caption(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            caption=escape_md(help_text),
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

    elif query.data == 'back':
        photo_url = random.choice(PHOTO_URL)
        reply_markup = get_main_keyboard()

        await context.bot.edit_message_caption(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            caption=escape_md(start_msg),
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

# Handlers
application.add_handler(CommandHandler('start', start, block=False))
application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
