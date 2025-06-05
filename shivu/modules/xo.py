import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Dictionary to track active games
active_xo_games = {}

# --- Command: /xo ---
async def start_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id in active_xo_games:
        await update.message.reply_text(
            "❗ A game is already running in this chat.\nUse /joinxo or /cancelxo."
        )
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
        f"🎮 Tic-Tac-Toe game created!\n"
        f"Player 1: {update.effective_user.first_name}\n"
        f"Waiting for another player to /joinxo..."
    )

    active_xo_games[chat_id]["message_id"] = msg.message_id

# --- Command: /joinxo ---
async def join_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in active_xo_games:
        await update.message.reply_text("❌ No active game. Use /xo to start one.")
        return

    game = active_xo_games[chat_id]

    if game["started"]:
        await update.message.reply_text("❗ Game already started!")
        return

    if user_id in game["players"]:
        await update.message.reply_text("❗ You're already in this game!")
        return

    game["players"].append(user_id)
    game["usernames"][user_id] = update.effective_user.first_name
    game["symbols"] = {
        game["players"][0]: "❌",
        game["players"][1]: "⭕"
    }
    game["started"] = True

    await context.bot.edit_message_text(
        f"🎯 Game Started!\n"
        f"❌ {game['usernames'][game['players'][0]]}\n"
        f"⭕ {game['usernames'][game['players'][1]]}\n\n"
        f"{game['usernames'][game['players'][0]]}'s turn first!",
        chat_id=chat_id,
        message_id=game["message_id"],
        reply_markup=create_xo_board(game["board"])
    )

# --- Button Press Handler ---
async def handle_xo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if chat_id not in active_xo_games:
        await query.edit_message_text("❌ Game not found. Start with /xo.")
        return

    game = active_xo_games[chat_id]

    if not game["started"]:
        await query.edit_message_text("❌ Game hasn't started yet. Need a second player.")
        return

    data = query.data
    if not data.startswith("xo_move:"):
        return

    _, row, col = data.split(":")
    row, col = int(row), int(col)

    if game["players"][game["turn"]] != user_id:
        await query.answer("⏳ Not your turn!", show_alert=True)
        return

    if game["board"][row][col] != " ":
        await query.answer("❗ Cell already taken!", show_alert=True)
        return

    symbol = game["symbols"][user_id]
    game["board"][row][col] = symbol

    winner = check_xo_winner(game["board"])
    if winner:
        winner_name = game["usernames"][user_id]
        await query.edit_message_text(
            f"🏆 {winner_name} ({symbol}) wins!",
            reply_markup=None
        )
        del active_xo_games[chat_id]
        return

    if all(cell != " " for row in game["board"] for cell in row):
        await query.edit_message_text("🤝 It's a draw!", reply_markup=None)
        del active_xo_games[chat_id]
        return

    game["turn"] = 1 - game["turn"]
    next_player = game["players"][game["turn"]]

    await query.edit_message_text(
        f"Turn: {game['usernames'][next_player]} ({game['symbols'][next_player]})",
        reply_markup=create_xo_board(game["board"])
    )

# --- Command: /cancelxo ---
async def cancel_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in active_xo_games:
        try:
            await context.bot.edit_message_text(
                "❌ Game cancelled.",
                chat_id=chat_id,
                message_id=active_xo_games[chat_id]["message_id"]
            )
        except:
            pass
        del active_xo_games[chat_id]
        await update.message.reply_text("Game has been cancelled.")
    else:
        await update.message.reply_text("❌ No active game to cancel.")

# --- Utility: Create XO Keyboard ---
def create_xo_board(board):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            display = cell if cell != " " else "⬜"
            callback = f"xo_move:{i}:{j}" if cell == " " else "used"
            row.append(InlineKeyboardButton(display, callback_data=callback))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# --- Utility: Win Checker ---
def check_xo_winner(board):
    for row in board:
        if row[0] == row[1] == row[2] != " ":
            return row[0]
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    return None

# --- Loader Interface for Your Bot ---
def __handlers__(application):
    application.add_handler(CommandHandler("xo", start_xo, block=False))
    application.add_handler(CommandHandler("joinxo", join_xo, block=False))
    application.add_handler(CommandHandler("cancelxo", cancel_xo, block=False))
    application.add_handler(CallbackQueryHandler(handle_xo_callback, pattern=r"^xo_move:"))

def __migrate__(old_chat_id, new_chat_id):
    pass

def __stats__():
    return ""
