import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

active_xo_games = {}

async def xo_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id in active_xo_games:
        await update.message.reply_text("❗ A game is already running. Use /joinxo or /cancelxo.")
        return

    active_xo_games[chat_id] = {
        "players": [user_id],
        "symbols": {},
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": 0,
        "started": False,
        "usernames": {user_id: update.effective_user.first_name},
        "message_id": None
    }

    msg = await update.message.reply_text(
        f"🎲 XO game started!\nPlayer 1: {update.effective_user.first_name}\nWaiting for second player..."
    )
    active_xo_games[chat_id]["message_id"] = msg.message_id

async def join_xo_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in active_xo_games:
        await update.message.reply_text("❌ No active game. Start one with /xo.")
        return

    game = active_xo_games[chat_id]
    if game["started"]:
        await update.message.reply_text("❌ Game already started.")
        return

    if user_id in game["players"]:
        await update.message.reply_text("⚠️ You are already in the game.")
        return

    game["players"].append(user_id)
    game["usernames"][user_id] = update.effective_user.first_name
    game["symbols"] = {
        game["players"][0]: "❌",
        game["players"][1]: "⭕"
    }
    game["started"] = True

    await context.bot.edit_message_text(
        f"🎮 Game started!\n❌ {game['usernames'][game['players'][0]]}\n⭕ {game['usernames'][game['players'][1]]}\n\n{game['usernames'][game['players'][0]]}'s turn first!",
        chat_id=chat_id,
        message_id=game["message_id"],
        reply_markup=create_board(game["board"])
    )

async def handle_xo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user_id = query.from_user.id

    if chat_id not in active_xo_games:
        await query.edit_message_text("❌ No active game.")
        return

    game = active_xo_games[chat_id]
    if not game["started"]:
        await query.answer("⚠️ Game not started.")
        return

    data = query.data
    _, row, col = data.split(":")
    row, col = int(row), int(col)

    if game["players"][game["turn"]] != user_id:
        await query.answer("⏳ Not your turn.", show_alert=True)
        return

    if game["board"][row][col] != " ":
        await query.answer("❌ Already taken!", show_alert=True)
        return

    symbol = game["symbols"][user_id]
    game["board"][row][col] = symbol

    winner = check_winner(game["board"])
    if winner:
        winner_name = game["usernames"][user_id]
        await query.edit_message_text(f"🏆 {winner_name} ({symbol}) wins!")
        del active_xo_games[chat_id]
        return

    if all(cell != " " for row in game["board"] for cell in row):
        await query.edit_message_text("🤝 It's a draw!")
        del active_xo_games[chat_id]
        return

    game["turn"] = 1 - game["turn"]
    next_player = game["players"][game["turn"]]
    await query.edit_message_text(
        f"🎮 Turn: {game['usernames'][next_player]} ({game['symbols'][next_player]})",
        reply_markup=create_board(game["board"])
    )

async def cancel_xo_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_xo_games:
        try:
            await context.bot.edit_message_text("❌ Game cancelled.",
                                                chat_id=chat_id,
                                                message_id=active_xo_games[chat_id]["message_id"])
        except:
            pass
        del active_xo_games[chat_id]
        await update.message.reply_text("Game cancelled.")
    else:
        await update.message.reply_text("No active game.")

def create_board(board):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            text = cell if cell != " " else "⬜"
            callback = f"xo_move:{i}:{j}" if cell == " " else "xo_disabled"
            row.append(InlineKeyboardButton(text, callback_data=callback))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_winner(board):
    # Rows and columns
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != " ":
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] != " ":
            return board[0][i]
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    return None

# Module integration hooks
def __handlers__(application):
    application.add_handler(CommandHandler("xo", xo_game, block=False))
    application.add_handler(CommandHandler("joinxo", join_xo_game, block=False))
    application.add_handler(CommandHandler("cancelxo", cancel_xo_game, block=False))
    application.add_handler(CallbackQueryHandler(handle_xo_callback, pattern=r"^xo_move:\d+:\d+"))

def __stats__():
    return ""

def __migrate__(old_chat_id, new_chat_id):
    if old_chat_id in active_xo_games:
        active_xo_games[new_chat_id] = active_xo_games.pop(old_chat_id)
