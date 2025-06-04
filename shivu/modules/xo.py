import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Dictionary to track active games
active_xo_games = {}

async def start_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /xo command to start a new game"""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id in active_xo_games:
            await update.message.reply_text(
                "❗️ A game is already running in this chat!\n"
                "Use /joinxo to join or /cancelxo to cancel."
            )
            return
            
        # Initialize new game
        active_xo_games[chat_id] = {
            "players": [user_id],
            "symbols": {},
            "board": [[" " for _ in range(3)] for _ in range(3)],
            "turn": 0,
            "started": False,
            "usernames": {user_id: update.effective_user.first_name},
            "message_id": None
        }
        
        # Send initial message
        msg = await update.message.reply_text(
            "🎲 Tic-Tac-Toe game created!\n"
            f"Player 1: {update.effective_user.first_name}\n"
            "Waiting for second player to /joinxo..."
        )
        
        active_xo_games[chat_id]["message_id"] = msg.message_id
        
    except Exception as e:
        logging.error(f"Error in start_xo: {e}")
        await update.message.reply_text("❌ Failed to start game. Please try again.")

async def join_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /joinxo command to join an existing game"""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if chat_id not in active_xo_games:
            await update.message.reply_text("❌ No active game found. Start one with /xo!")
            return
            
        game = active_xo_games[chat_id]
        
        if game["started"]:
            await update.message.reply_text("❌ Game already in progress!")
            return
            
        if user_id in game["players"]:
            await update.message.reply_text("❗️ You already joined this game!")
            return
            
        # Add second player
        game["players"].append(user_id)
        game["usernames"][user_id] = update.effective_user.first_name
        game["symbols"] = {game["players"][0]: "❌", game["players"][1]: "⭕️"}
        game["started"] = True
        
        # Update game message
        start_message = (
            f"🎲 Tic-Tac-Toe started!\n"
            f"❌ {game['usernames'][game['players'][0]]}\n"
            f"⭕️ {game['usernames'][game['players'][1]]}\n\n"
            f"{game['usernames'][game['players'][0]]}'s turn first!"
        )
        
        await context.bot.edit_message_text(
            start_message,
            chat_id=chat_id,
            message_id=game["message_id"],
            reply_markup=create_xo_board(game["board"])
        )
        
    except Exception as e:
        logging.error(f"Error in join_xo: {e}")
        await update.message.reply_text("❌ Failed to join game. Please try again.")

async def handle_xo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for button presses in the game"""
    try:
        query = update.callback_query
        await query.answer()
        
        chat_id = update.effective_chat.id
        user_id = query.from_user.id
        
        if chat_id not in active_xo_games:
            await query.edit_message_text("❌ Game not found. Start a new one with /xo!")
            return
            
        game = active_xo_games[chat_id]
        
        if not game["started"]:
            await query.edit_message_text("❌ Game not started yet. Need a second player!")
            return
            
        # Parse callback data
        data = query.data
        if not data.startswith("xo_move:"):
            return
            
        _, row, col = data.split(":")
        row = int(row)
        col = int(col)
        
        # Validate move
        if game["players"][game["turn"]] != user_id:
            await query.answer("⏳ It's not your turn!", show_alert=True)
            return
            
        if game["board"][row][col] != " ":
            await query.answer("❌ Cell already taken!", show_alert=True)
            return
            
        # Make move
        symbol = game["symbols"][user_id]
        game["board"][row][col] = symbol
        
        # Check for winner
        winner = check_xo_winner(game["board"])
        if winner:
            winner_name = game["usernames"][game["players"][0 if symbol == "❌" else 1]]
            await query.edit_message_text(
                f"🏆 {winner_name} ({symbol}) wins!",
                reply_markup=None
            )
            del active_xo_games[chat_id]
            return
            
        # Check for draw
        if all(cell != " " for row in game["board"] for cell in row):
            await query.edit_message_text(
                "🤝 It's a draw!",
                reply_markup=None
            )
            del active_xo_games[chat_id]
            return
            
        # Switch turns
        game["turn"] = 1 - game["turn"]
        current_player = game["players"][game["turn"]]
        
        # Update board
        await query.edit_message_text(
            f"Turn: {game['usernames'][current_player]} ({game['symbols'][current_player]})",
            reply_markup=create_xo_board(game["board"])
        )
        
    except Exception as e:
        logging.error(f"Error in handle_xo_callback: {e}")
        await query.edit_message_text("❌ Error processing move. Game cancelled.")
        active_xo_games.pop(chat_id, None)

def create_xo_board(board):
    """Create an inline keyboard for the current board state"""
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            cell = board[i][j]
            display = cell if cell != " " else "⬜️"
            callback = f"xo_move:{i}:{j}" if cell == " " else "none"
            row.append(InlineKeyboardButton(display, callback_data=callback))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_xo_winner(board):
    """Check if there's a winner on the board"""
    # Check rows
    for row in board:
        if row[0] == row[1] == row[2] != " ":
            return row[0]
    
    # Check columns
    for col in range(3):
        if board[0][col] == board[1][col] == board[2][col] != " ":
            return board[0][col]
    
    # Check diagonals
    if board[0][0] == board[1][1] == board[2][2] != " ":
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != " ":
        return board[0][2]
    
    return None

async def cancel_xo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /cancelxo command to cancel current game"""
    chat_id = update.effective_chat.id
    if chat_id in active_xo_games:
        game = active_xo_games[chat_id]
        if game.get("message_id"):
            try:
                await context.bot.edit_message_text(
                    "❌ Game cancelled.",
                    chat_id=chat_id,
                    message_id=game["message_id"]
                )
            except:
                pass
        del active_xo_games[chat_id]
        await update.message.reply_text("Game cancelled.")
    else:
        await update.message.reply_text("No active game to cancel.")

def add_xo_handlers(application):
    """Add all XO game handlers to the application"""
    application.add_handler(CommandHandler("xo", start_xo))
    application.add_handler(CommandHandler("joinxo", join_xo))
    application.add_handler(CommandHandler("cancelxo", cancel_xo))
    application.add_handler(CallbackQueryHandler(handle_xo_callback, pattern=r"^xo_move:"))
