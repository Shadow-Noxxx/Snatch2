import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from shivu import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, shivuu
from shivu import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from shivu.modules import ALL_MODULES
from shivu.modules import xo

locks = {}
message_counters = {}
spam_counters = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
message_counts = {}


for module_name in ALL_MODULES:
    imported_module = importlib.import_module("shivu.modules." + module_name)


last_user = {}
warned_users = {}
def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters
# Dictionary to keep track of active Tic-Tac-Toe games


active_xo_games = {}

async def xo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if chat_id in active_xo_games:
            await update.message.reply_text("❗️ A Tic-Tac-Toe game is already running in this chat!")
            return
        active_xo_games[chat_id] = {
            "players": [update.effective_user.id],
            "symbols": {},
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": 0,
            "started": False,
            "usernames": {update.effective_user.id: update.effective_user.first_name},
            "message_id": None
        }
        msg = await update.message.reply_text(
            "✅ Waiting for the second player. Another user should send /joinxo to join."
        )
        active_xo_games[chat_id]["message_id"] = msg.message_id
    except Exception as e:
        logging.error(f"Error in xo_start: {e}")
        await update.message.reply_text("❌ Oops! Something went wrong starting the game.")

async def xo_players_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return

async def join_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        game = active_xo_games.get(chat_id)
        if not game:
            await update.message.reply_text("❌ No game found. Start a game with /xo.")
            return
        if len(game["players"]) >= 2:
            await update.message.reply_text("❌ The game already has 2 players!")
            return
        if update.effective_user.id in game["players"]:
            await update.message.reply_text("❗️ You already joined this game!")
            return
        game["players"].append(update.effective_user.id)
        game["usernames"][update.effective_user.id] = update.effective_user.first_name
        game["symbols"] = {game["players"][0]: "❌", game["players"][1]: "⭕️"}
        game["started"] = True
        start_message = (
            f"🎲 Tic-Tac-Toe started!\n"
            f"{game['usernames'][game['players'][0]]} is ❌\n"
            f"{game['usernames'][game['players'][1]]} is ⭕️\n"
            f"{game['usernames'][game['players'][0]]} goes first.\n\n"
            "Tap an empty cell below to make your move:"
        )
        msg_id = game.get("message_id")
        if msg_id:
            await context.bot.edit_message_text(
                start_message,
                chat_id=chat_id,
                message_id=msg_id,
                reply_markup=None
            )
            await show_xo_board(update, context, chat_id, edit=True)
        else:
            msg = await update.message.reply_text(start_message)
            game["message_id"] = msg.message_id
            await show_xo_board(update, context, chat_id, edit=True)
    except Exception as e:
        logging.error(f"Error in join_xo: {e}")
        await update.message.reply_text("❌ Error while joining the game.")

async def xo_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = query.data
        if data.startswith("xo_move:"):
            parts = data.split(":")
            if len(parts) != 3:
                return
            row = int(parts[1])
            col = int(parts[2])
            chat_id = update.effective_chat.id
            game = active_xo_games.get(chat_id)
            if not game or not game.get("started"):
                await query.edit_message_text("❌ No active game. Start one with /xo!")
                return
            user_id = query.from_user.id
            if user_id not in game["players"]:
                await query.answer("❌ You are not playing this game!", show_alert=True)
                return
            if game["players"][game["turn"]] != user_id:
                await query.answer("⏳ It's not your turn yet!", show_alert=True)
                return
            if game["board"][row][col] != " ":
                await query.answer("❌ This cell is already taken!", show_alert=True)
                return
            symbol = game["symbols"][user_id]
            game["board"][row][col] = symbol
            await show_xo_board(update, context, chat_id, edit=True)
            winner = check_xo_winner(game["board"])
            msg_id = game.get("message_id")
            if winner:
                if msg_id:
                    await context.bot.edit_message_text(
                        f"🏆 {game['usernames'][user_id]} ({symbol}) wins! Congratulations!",
                        chat_id=chat_id,
                        message_id=msg_id,
                        parse_mode="HTML"
                    )
                else:
                    await context.bot.send_message(chat_id, f"🏆 {game['usernames'][user_id]} ({symbol}) wins! Congratulations!")
                active_xo_games.pop(chat_id, None)
                return
            if all(cell != " " for row_ in game["board"] for cell in row_):
                if msg_id:
                    await context.bot.edit_message_text(
                        "🤝 It's a draw! Great game everyone.",
                        chat_id=chat_id,
                        message_id=msg_id,
                        parse_mode="HTML"
                    )
                else:
                    await context.bot.send_message(chat_id, "🤝 It's a draw! Great game everyone.")
                active_xo_games.pop(chat_id, None)
                return
            game["turn"] = 1 - game["turn"]
            await show_xo_board(update, context, chat_id, edit=True)
    except Exception as e:
        logging.error(f"Error in xo_button_handler: {e}")

def check_xo_winner(board):
    try:
        for i in range(3):
            if board[i][0] != " " and board[i][0] == board[i][1] == board[i][2]:
                return board[i][0]
            if board[0][i] != " " and board[0][i] == board[1][i] == board[2][i]:
                return board[0][i]
        if board[0][0] != " " and board[0][0] == board[1][1] == board[2][2]:
            return board[0][0]
        if board[0][2] != " " and board[0][2] == board[1][1] == board[2][0]:
            return board[0][2]
    except Exception as e:
        logging.error(f"Error in check_xo_winner: {e}")
    return None

async def show_xo_board(update, context, chat_id, edit: bool = False):
    try:
        game = active_xo_games.get(chat_id)
        if not game:
            return
        board = game["board"]
        inline_buttons = []
        for i in range(3):
            row_buttons = []
            for j in range(3):
                cell = board[i][j]
                display = cell if cell != " " else "⬜️"
                callback = f"xo_move:{i}:{j}" if cell == " " else "none"
                row_buttons.append(InlineKeyboardButton(display, callback_data=callback))
            inline_buttons.append(row_buttons)
        reply_markup = InlineKeyboardMarkup(inline_buttons)
        turn_player = game["players"][game["turn"]]
        turn_text = f"<b>Tic-Tac-Toe</b>\n"
        turn_text += f"Turn: {game['usernames'][turn_player]} ({game['symbols'][turn_player]})\n"
        turn_text += "Make your move by tapping an empty cell:"
        msg_id = game.get("message_id")
        if edit and msg_id:
            try:
                await context.bot.edit_message_text(
                    turn_text,
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Error editing board message: {e}")
        elif msg_id:
            try:
                await context.bot.edit_message_text(
                    turn_text,
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logging.error(f"Error editing board message: {e}")
        else:
            msg = await context.bot.send_message(chat_id, turn_text, parse_mode="HTML", reply_markup=reply_markup)
            game["message_id"] = msg.message_id
    except Exception as e:
        logging.error(f"Error in show_xo_board: {e}")
        await context.bot.send_message(chat_id, "❌ Failed to display the board.", parse_mode="HTML")

async def cancel_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        game = active_xo_games.get(chat_id)
        msg_id = game.get("message_id") if game else None
        if chat_id in active_xo_games:
            active_xo_games.pop(chat_id, None)
            if msg_id:
                await context.bot.edit_message_text(
                    "❌ Tic-Tac-Toe game cancelled.",
                    chat_id=chat_id,
                    message_id=msg_id
                )
            else:
                await update.message.reply_text("❌ Tic-Tac-Toe game cancelled.")
        else:
            await update.message.reply_text("No active game to cancel.")
    except Exception as e:
        logging.error(f"Error in cancel_xo: {e}")
        await update.message.reply_text("❌ Could not cancel the game due to an unexpected error.")



async def message_counter(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    lock = locks[chat_id]

    async with lock:
        
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        if chat_frequency:
            message_frequency = chat_frequency.get('message_frequency', 100)
        else:
            message_frequency = 100

        
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
            
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

    
        if chat_id in message_counts:
            message_counts[chat_id] += 1
        else:
            message_counts[chat_id] = 1

    
        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            
            message_counts[chat_id] = 0
            
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    all_characters = list(await collection.find({}).to_list(length=None))
    
    if chat_id not in sent_characters:
        sent_characters[chat_id] = []

    if len(sent_characters[chat_id]) == len(all_characters):
        sent_characters[chat_id] = []

    character = random.choice([c for c in all_characters if c['id'] not in sent_characters[chat_id]])

    sent_characters[chat_id].append(character['id'])
    last_characters[chat_id] = character

    if chat_id in first_correct_guesses:
        del first_correct_guesses[chat_id]

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=character['img_url'],
        caption=f"""A New {character['rarity']} Character Appeared...\n/guess Character Name and add in Your Harem""",
        parse_mode='Markdown')


async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌️ Already Guessed By Someone.. Try Next Time Bruhh ')
        return

    guess = ' '.join(context.args).lower() if context.args else ''
    
    if "()" in guess or "&" in guess.lower():
        await update.message.reply_text("Nahh You Can't use This Types of words in your guess..❌️")
        return


    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(guess.split()) or any(part == guess for part in name_parts):

    
        first_correct_guesses[chat_id] = user_id
        
        user = await user_collection.find_one({'id': user_id})
        if user:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != user.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != user.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await user_collection.update_one({'id': user_id}, {'$set': update_fields})
            
            await user_collection.update_one({'id': user_id}, {'$push': {'characters': last_characters[chat_id]}})
      
        elif hasattr(update.effective_user, 'username'):
            await user_collection.insert_one({
                'id': user_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'characters': [last_characters[chat_id]],
            })

        
        group_user_total = await group_user_totals_collection.find_one({'user_id': user_id, 'group_id': chat_id})
        if group_user_total:
            update_fields = {}
            if hasattr(update.effective_user, 'username') and update.effective_user.username != group_user_total.get('username'):
                update_fields['username'] = update.effective_user.username
            if update.effective_user.first_name != group_user_total.get('first_name'):
                update_fields['first_name'] = update.effective_user.first_name
            if update_fields:
                await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$set': update_fields})
            
            await group_user_totals_collection.update_one({'user_id': user_id, 'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await group_user_totals_collection.insert_one({
                'user_id': user_id,
                'group_id': chat_id,
                'username': update.effective_user.username,
                'first_name': update.effective_user.first_name,
                'count': 1,
            })


    
        group_info = await top_global_groups_collection.find_one({'group_id': chat_id})
        if group_info:
            update_fields = {}
            if update.effective_chat.title != group_info.get('group_name'):
                update_fields['group_name'] = update.effective_chat.title
            if update_fields:
                await top_global_groups_collection.update_one({'group_id': chat_id}, {'$set': update_fields})
            
            await top_global_groups_collection.update_one({'group_id': chat_id}, {'$inc': {'count': 1}})
      
        else:
            await top_global_groups_collection.insert_one({
                'group_id': chat_id,
                'group_name': update.effective_chat.title,
                'count': 1,
            })


        
        keyboard = [[InlineKeyboardButton(f"See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]


        await update.message.reply_text(f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You Guessed a New Character ✅️ \n\n𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n𝗥𝗔𝗜𝗥𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\nThis Character added in Your harem.. use /harem To see your harem', parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        await update.message.reply_text('Please Write Correct Character Name... ❌️')
   

async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    
    if not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    character_id = context.args[0]

    
    user = await user_collection.find_one({'id': user_id})
    if not user:
        await update.message.reply_text('You have not Guessed any characters yet....')
        return


    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        await update.message.reply_text('This Character is Not In your collection')
        return

    
    user['favorites'] = [character_id]

    
    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    await update.message.reply_text(f'Character {character["name"]} has been added to your favorite...')
    


from shivu.modules import xo  # use your actual module name

def main() -> None:
    application.add_handler(CommandHandler(["guess", "protecc", "collect", "grab", "hunt"], guess, block=False))
    application.add_handler(CommandHandler("fav", fav, block=False))
    application.add_handler(MessageHandler(filters.ALL, message_counter, block=False))
    application.add_handler(CommandHandler("xo", xo_start))
    application.add_handler(CommandHandler("joinxo", join_xo))
    application.add_handler(CallbackQueryHandler(xo_button_handler, pattern=r"^xo_move:"))
    application.add_handler(CommandHandler("cancelxo", cancel_xo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xo_players_response))
    # Register XO game handlers


    application.run_polling(drop_pending_updates=True)


    
if __name__ == "__main__":
    shivuu.start()
    LOGGER.info("Bot started")
    main()

