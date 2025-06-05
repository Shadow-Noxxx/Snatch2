import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Dictionary to track active XO games
active_games = {}

# Start a new XO game
async def start_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in active_games:
        await update.message.reply_text("❗️A game is already active! Use /joinxo or /cancelxo.")
        return

    active_games[chat_id] = {
        "players": [user.id],
        "usernames": {user.id: user.first_name},
        "symbols": {},
        "board": [[" " for _ in range(3)] for _ in range(3)],
        "turn": 0,
        "started": False,
        "message_id": None,
    }

    msg = await update.message.reply_text(
        f"🎮 New Tic-Tac-Toe game!\nPlayer 1: {user.first_name}\nWaiting for Player 2 to /joinxo..."
    )
    active_games[chat_id]["message_id"] = msg.message_id

# Join an existing XO game
async def join_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in active_games:
        await update.message.reply_text("❌ No active game. Start one with /xo.")
        return

    game = active_games[chat_id]

    if game["started"]:
        await update.message.reply_text("❗️Game already started!")
        return

    if user.id in game["players"]:
        await update.message.reply_text("You're already in the game.")
        return

    game["players"].append(user.id)
    game["usernames"][user.id] = user.first_name
    game["symbols"] = {
        game["players"][0]: "❌",
        game["players"][1]: "⭕️",
    }
    game["started"] = True

    text = (
        f"🎮 Game Started!\n"
        f"❌ {game['usernames'][game['players'][0]]}\n"
        f"⭕️ {game['usernames'][game['players'][1]]}\n\n"
        f"{game['usernames'][game['players'][0]]}'s turn!"
    )

    await context.bot.edit_message_text(
        chat_id=chat_id,
        message_id=game["message_id"],
        text=text,
        reply_markup=create_board(game["board"]),
    )

# Cancel the XO game
async def cancel_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in active_games:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=active_games[chat_id]["message_id"],
                text="❌ Game cancelled.",
            )
        except:
            pass
        del active_games[chat_id]
        await update.message.reply_text("Game cancelled.")
    else:
        await update.message.reply_text("No active game.")

# Handle XO board button clicks
async def handle_xo_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    user_id = query.from_user.id

    if chat_id not in active_games:
        await query.edit_message_text("Game not found. Use /xo to start one.")
        return

    game = active_games[chat_id]

    if not game["started"]:
        await query.edit_message_text("Game hasn’t started yet. Waiting for Player 2.")
        return

    if user_id != game["players"][game["turn"]]:
        await query.answer("⏳ It's not your turn!", show_alert=True)
        return

    data = query.data
    if not data.startswith("xo:"):
        return

    _, row, col = data.split(":")
    row, col = int(row), int(col)

    if game["board"][row][col] != " ":
        await query.answer("❌ This cell is already filled!", show_alert=True)
        return

    symbol = game["symbols"][user_id]
    game["board"][row][col] = symbol

    winner = check_winner(game["board"])
    if winner:
        winner_name = game["usernames"][user_id]
        await query.edit_message_text(f"🏆 {winner_name} ({symbol}) wins!", reply_markup=None)
        del active_games[chat_id]
        return

    if all(cell != " " for row in game["board"] for cell in row):
        await query.edit_message_text("🤝 It's a draw!", reply_markup=None)
        del active_games[chat_id]
        return

    # Switch turn
    game["turn"] = 1 - game["turn"]
    next_id = game["players"][game["turn"]]
    next_name = game["usernames"][next_id]
    next_symbol = game["symbols"][next_id]

    await query.edit_message_text(
        f"Turn: {next_name} ({next_symbol})",
        reply_markup=create_board(game["board"]),
    )

# Build XO board
def create_board(board):
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            label = cell if cell != " " else "⬜️"
            callback = f"xo:{i}:{j}" if cell == " " else "none"
            row.append(InlineKeyboardButton(label, callback_data=callback))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

# Check winner
def check_winner(board):
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

# Required by your loader system
def __handlers__(application):
    application.add_handler(CommandHandler("xo", start_xo, block=False))
    application.add_handler(CommandHandler("joinxo", join_xo, block=False))
    application.add_handler(CommandHandler("cancelxo", cancel_xo, block=False))
    application.add_handler(CallbackQueryHandler(handle_xo_move, pattern=r"^xo:\d+:\d+"))

def __migrate__(old_chat_id, new_chat_id):
    pass

def __stats__():
    return ""
