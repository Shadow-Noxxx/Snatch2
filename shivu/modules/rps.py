import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.ext import CommandHandler, CallbackQueryHandler

active_rps_games = {}

RPS_CHOICES = ["🪨 Rock", "📄 Paper", "✂️ Scissors"]
RPS_EMOJI = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

def rps_result(choice1, choice2):
    if choice1 == choice2:
        return 0  # Draw
    wins = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    return 1 if wins[choice1] == choice2 else 2

async def rps(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if chat_id in active_rps_games:
            await update.message.reply_text(
                "❗ <b>A Rock Paper Scissors game is already running in this chat!</b>",
                parse_mode="HTML"
            )
            return
        active_rps_games[chat_id] = {
            "players": [update.effective_user.id],
            "usernames": {update.effective_user.id: update.effective_user.first_name},
            "choices": {},
            "started": False
        }
        await update.message.reply_text(
            "🎮 <b>Rock Paper Scissors Game Started!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Player 1: {update.effective_user.mention_html()}\n"
            "Waiting for a second player...\n"
            "<i>Send /joinrps to join the game!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Error in rps: {e}")
        await update.message.reply_text(
            "❌ <b>Failed to start Rock Paper Scissors game.</b>",
            parse_mode="HTML"
        )

async def joinrps(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        game = active_rps_games.get(chat_id)
        if not game:
            await update.message.reply_text(
                "❌ <b>No active Rock Paper Scissors game. Start one with /rps.</b>",
                parse_mode="HTML"
            )
            return
        if len(game["players"]) >= 2:
            await update.message.reply_text(
                "❌ <b>The game already has 2 players!</b>",
                parse_mode="HTML"
            )
            return
        if update.effective_user.id in game["players"]:
            await update.message.reply_text(
                "❗ <b>You have already joined the game.</b>",
                parse_mode="HTML"
            )
            return
        game["players"].append(update.effective_user.id)
        game["usernames"][update.effective_user.id] = update.effective_user.first_name
        game["started"] = True
        await update.message.reply_text(
            f"✅ <b>{update.effective_user.mention_html()} joined!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "<b>Both players, please select your move:</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🪨 Rock", callback_data="rps_choice:rock"),
                    InlineKeyboardButton("📄 Paper", callback_data="rps_choice:paper"),
                    InlineKeyboardButton("✂️ Scissors", callback_data="rps_choice:scissors"),
                ]
            ])
        )
    except Exception as e:
        logging.error(f"Error in joinrps: {e}")
        await update.message.reply_text(
            "❌ <b>Failed to join Rock Paper Scissors game.</b>",
            parse_mode="HTML"
        )

async def rps_button_handler(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        if not query:
            return
        await query.answer()
        data = query.data
        if not data.startswith("rps_choice:"):
            return
        choice = data.split(":")[1]
        chat_id = update.effective_chat.id
        user_id = query.from_user.id
        game = active_rps_games.get(chat_id)
        if not game or not game.get("started"):
            await query.edit_message_text(
                "❌ <b>No active Rock Paper Scissors game. Start one with /rps.</b>",
                parse_mode="HTML"
            )
            return
        if user_id not in game["players"]:
            await query.answer("❌ You are not a player in this game!", show_alert=True)
            return
        if user_id in game["choices"]:
            await query.answer("❗ You have already made your choice.", show_alert=True)
            return
        if choice not in RPS_EMOJI:
            await query.answer("❌ Invalid choice.", show_alert=True)
            return
        game["choices"][user_id] = choice
        await query.answer(f"You chose {RPS_EMOJI[choice]}")
        # If both players have chosen, determine result
        if len(game["choices"]) == 2:
            p1, p2 = game["players"]
            c1, c2 = game["choices"][p1], game["choices"][p2]
            uname1, uname2 = game["usernames"][p1], game["usernames"][p2]
            result = rps_result(c1, c2)
            result_text = (
                "🪨📄✂️ <b>Rock Paper Scissors Result</b> 🪨📄✂️\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{uname1}: <b>{RPS_EMOJI[c1]}</b>\n"
                f"{uname2}: <b>{RPS_EMOJI[c2]}</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
            if result == 0:
                result_text += "🤝 <b>It's a draw!</b>"
            elif result == 1:
                result_text += f"🏆 <b>{uname1} wins!</b>"
            else:
                result_text += f"🏆 <b>{uname2} wins!</b>"
            await context.bot.send_message(
                chat_id=chat_id,
                text=result_text,
                parse_mode="HTML"
            )
            active_rps_games.pop(chat_id, None)
        else:
            await query.answer("✅ Choice registered. Waiting for the other player.", show_alert=False)
    except Exception as e:
        logging.error(f"Error in rps_button_handler: {e}")
        try:
            await update.callback_query.answer("❌ An error occurred.", show_alert=True)
        except Exception:
            pass

async def cancelrps(update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        if chat_id in active_rps_games:
            active_rps_games.pop(chat_id, None)
            await update.message.reply_text(
                "❌ <b>Rock Paper Scissors game cancelled.</b>",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("No active Rock Paper Scissors game to cancel.")
    except Exception as e:
        logging.error(f"Error in cancelrps: {e}")
        await update.message.reply_text(
            "❌ <b>Could not cancel the game due to an unexpected error.</b>",
            parse_mode="HTML"
        )


def rps_handlers():
    return [
        CommandHandler("rps", rps, block=False),
        CommandHandler("joinrps", joinrps, block=False),
        CallbackQueryHandler(rps_button_handler, pattern=r"^rps_choice:"),
        CommandHandler("cancelrps", cancelrps, block=False)
    ]
