import importlib
import time
import random
import re
import asyncio
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import (
    collection,
    top_global_groups_collection,
    group_user_totals_collection,
    user_collection,
    user_totals_collection,
    shivuu,
    application,
    SUPPORT_CHAT,
    UPDATE_CHAT,
    db,
    LOGGER,
)
from shivu.modules import ALL_MODULES

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}

# Dynamically import all modules and register their handlers if present
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)
    # Register handlers if the module provides them
    if hasattr(imported_module, "__handlers__"):
        for handler in imported_module.__handlers__:
            application.add_handler(handler)

last_user = {}
warned_users = {}

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

def main() -> None:
    """Run bot."""

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()
