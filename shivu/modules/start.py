import random
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from shivu import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from shivu import pm_users as collection

# Yoruichi-themed photo URLs
import os
from pathlib import Path

# Get the base directory of your project
BASE_DIR = Path(__file__).parent.parent

# Define the path to your assets folder
ASSETS_DIR = BASE_DIR / "assets"

# List of Yoruichi image files (now using local paths)
YORUICHI_PHOTOS = [
    str(ASSETS_DIR / "yoruichi1.jpg"),
    str(ASSETS_DIR / "yoruichi2.jpg"),
    str(ASSETS_DIR / "yoruichi3.jpg")
]

# Command categories with detailed descriptions
COMMAND_CATEGORIES = {
    "moderation": {
        "title": "🐾 Stealth Force Moderation",
        "commands": {
            "/ban": "Banish intruders to Muken with reason\nUsage: /ban [reply] [reason]",
            "/mute": "Silence users with Flash Step speed\nUsage: /mute [reply] [duration]",
            "/warn": "Give a playful but firm warning\nUsage: /warn [reply] [reason]",
            "/purge": "Clean messages instantly\nUsage: /purge [number]"
        }
    },
    "settings": {
        "title": "🏯 Shihoin Clan Settings",
        "commands": {
            "/welcome": "Set feline-themed welcome messages\nUsage: /welcome [message]",
            "/rules": "Display clan regulations\nUsage: /rules set [text]",
            "/antiraid": "Activate Seireitei protection\nUsage: /antiraid [on/off]"
        }
    },
    "fun": {
        "title": "⚡ Yoruichi's Special Abilities",
        "commands": {
            "/cat": "Get random Yoruichi facts\nUsage: /cat",
            "/quote": "Wisdom from the Flash Goddess\nUsage: /quote",
            "/transform": "Surprise transformations\nUsage: /transform"
        }
    }
}

# Track current help page for users
help_pages = {}

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    user_data = await collection.find_one({"_id": user_id})
    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name})
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"New User Pounced In!\n<a href='tg://user?id={user_id}'>{escape(first_name)}</a>",
            parse_mode='HTML'
        )

    if update.effective_chat.type == "private":
        caption = f"""
🐾 *Yoruichi's Stealth Force Management* 🐾

*"Did you really think you could see me coming?"*

Welcome, {first_name}! I'm your Yoruichi-themed management bot, here to help you run your groups with feline grace and lightning speed.

Tap *Shunpo Commands* below to see what I can do!
"""

        keyboard = [
            [InlineKeyboardButton("ADD TO GROUP", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("SHIHOIN CLAN", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("SHUNPO COMMANDS", callback_data='help_main')]
        ]
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=random.choice(YORUICHI_PHOTOS),
            caption=caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='markdown'
        )
    else:
        caption = f"""
⚡ *Yoruichi's Management Activated* ⚡

*"This place is now under Shihoin Clan protection!"*

Use /help to see my commands, meow~
"""
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=random.choice(YORUICHI_PHOTOS),
            caption=caption,
            parse_mode='markdown'
        )

async def help_command(update: Update, context: CallbackContext) -> None:
    await show_help_menu(update, context, page_index=0)

async def show_help_menu(update: Update, context: CallbackContext, page_index: int):
    categories = list(COMMAND_CATEGORIES.keys())
    category = categories[page_index]
    category_data = COMMAND_CATEGORIES[category]
    
    # Create buttons for each command in this category
    buttons = []
    for cmd in category_data["commands"]:
        buttons.append([InlineKeyboardButton(cmd, callback_data=f'cmd_{category}_{cmd}')])
    
    # Add navigation buttons
    nav_buttons = []
    if page_index > 0:
        nav_buttons.append(InlineKeyboardButton("◀️", callback_data=f'help_{page_index-1}'))
    nav_buttons.append(InlineKeyboardButton("❌ Close", callback_data='help_close'))
    if page_index < len(categories)-1:
        nav_buttons.append(InlineKeyboardButton("▶️", callback_data=f'help_{page_index+1}'))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add back to main menu button
    buttons.append([InlineKeyboardButton("🏠 Back to Main", callback_data='help_main')])
    
    text = f"🐈 *{category_data['title']}* 🐈\n\n*Select a command to see details:*"
    
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='markdown'
        )

async def show_command_detail(update: Update, context: CallbackContext, category: str, command: str):
    category_data = COMMAND_CATEGORIES[category]
    description = category_data["commands"][command]
    
    buttons = [
        [InlineKeyboardButton("🔙 Back to Commands", callback_data=f'help_{list(COMMAND_CATEGORIES.keys()).index(category)}')],
        [InlineKeyboardButton("🏠 Back to Main", callback_data='help_main')]
    ]
    
    await update.callback_query.edit_message_text(
        text=f"⚡ *{command}* ⚡\n\n{description}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode='markdown'
    )

async def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == 'help_main':
        await show_help_menu(update, context, 0)
    elif data == 'help_close':
        await query.delete_message()
    elif data.startswith('help_'):
        page_index = int(data.split('_')[1])
        await show_help_menu(update, context, page_index)
    elif data.startswith('cmd_'):
        parts = data.split('_')
        await show_command_detail(update, context, parts[1], parts[2])

# Add handlers
application.add_handler(CommandHandler('help', help_command))
application.add_handler(CallbackQueryHandler(button_handler, pattern='^help_|^cmd_|^help_main|^help_close'))
application.add_handler(CommandHandler('start', start))
