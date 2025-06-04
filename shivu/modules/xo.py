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

def setup_handlers(application):
    application.add_handler(CommandHandler("xo", xo_start))
    application.add_handler(CommandHandler("joinxo", join_xo))
    application.add_handler(CallbackQueryHandler(xo_button_handler, pattern=r"^xo_move:"))
    application.add_handler(CommandHandler("cancelxo", cancel_xo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, xo_players_response))
