"""eFootball Build Bot - Telegram bot for optimizing player builds."""
import json
import logging
import sys
import os

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

from scraper import search_players, fetch_player_detail, fetch_player_index
from optimizer import optimize_build, PLAYSTYLES, format_build_result


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Player index cache
INDEX_CACHE = None

def get_index():
    global INDEX_CACHE
    if INDEX_CACHE is None:
        INDEX_CACHE = fetch_player_index()
    return INDEX_CACHE

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ *eFootball Build Bot*\n\n"
        "Commands:\n"
        "/search NAME - Search for a player\n"
        "/build NAME PLAYSTYLE - Get build recommendation\n"
        "/playstyles - List available playstyles\n"
        "/player PLAYER\\_ID - Get player details\n\n"
        "Examples:\n"
        "`/search Messi`\n"
        "`/build Messi dribble`\n"
        "`/build 89136409091415 speed`",
        parse_mode="Markdown"
    )

# /playstyles
async def playstyles_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = ["*Available Playstyles:*\n"]
    for key, val in PLAYSTYLES.items():
        lines.append(f"• `{key}` - {val['label']}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# /search
async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /search <player_name>")
        return

    query = " ".join(context.args)
    index = get_index()
    results = search_players(query, index)

    if not results:
        await update.message.reply_text(f"No players found for '{query}'.")
        return

    lines = [f"*Search results for '{query}':*\n"]
    for r in results[:8]:
        lines.append(f"• `{r['id']}` - {r['name']} ({r['overall']} OVR)")
    lines.append("\nUse `/build <id_or_name> <playstyle>` to get a build.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# /build
async def build_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: /build <player_name_or_id> <playstyle>\n"
            "Playstyles: " + ", ".join(PLAYSTYLES.keys())
        )
        return

    playstyle = context.args[-1].lower()
    player_query = " ".join(context.args[:-1])

    if playstyle not in PLAYSTYLES:
        await update.message.reply_text(
            f"Unknown playstyle '{playstyle}'.\n"
            "Available: " + ", ".join(PLAYSTYLES.keys())
        )
        return

    # Find player
    index = get_index()
    player_id = None

    if player_query.isdigit():
        player_id = int(player_query)
    else:
        results = search_players(player_query, index)
        if not results:
            await update.message.reply_text(f"No player found: '{player_query}'")
            return
        player_id = results[0]["id"]
        if len(results) > 1:
            names = "\n".join(f"• {r['name']} ({r['overall']})" for r in results[:5])
            await update.message.reply_text(
                f"Multiple results, using {results[0]['name']}.\n"
                f"Others:\n{names}"
            )

    await update.message.reply_text("Fetching player data...")

    player_data = fetch_player_detail(player_id)
    if not player_data or "baseStats" not in player_data:
        await update.message.reply_text("Failed to fetch player data. Try again later.")
        return

    await update.message.reply_text("Optimizing build...")

    result = optimize_build(player_data, playstyle)
    text = format_build_result(result)

    # Keyboard for other playstyles
    keyboard = [
        [InlineKeyboardButton(ps.capitalize(), callback_data=f"build_{player_id}_{ps}")]
        for ps in PLAYSTYLES if ps != playstyle
    ][:5]
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

# /player
async def player_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /player <player_id_or_name>")
        return

    query = " ".join(context.args)
    index = get_index()

    if query.isdigit():
        player_id = int(query)
    else:
        results = search_players(query, index)
        if not results:
            await update.message.reply_text(f"No player found: '{query}'")
            return
        player_id = results[0]["id"]

    player_data = fetch_player_detail(player_id)
    if not player_data or "baseStats" not in player_data:
        await update.message.reply_text("Failed to fetch player data.")
        return

    stats = player_data["baseStats"]
    name = player_data.get("slug", str(player_id)).replace("-", " ").title()
    pos = player_data.get("position", "?")
    level_cap = player_data.get("levelCap", "?")

    lines = [f"*{name}* ({pos})", f"Level Cap: {level_cap}\n"]
    lines.append("*Key Stats:*")
    for s in ["ballControl", "dribbling", "finishing", "speed", "acceleration",
              "defensiveAwareness", "physicalContact", "stamina"]:
        lines.append(f"  {s}: {stats.get(s, 0)}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# Callback for inline buttons
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("_")
    if parts[0] == "build" and len(parts) >= 3:
        player_id = int(parts[1])
        playstyle = parts[2]

        player_data = fetch_player_detail(player_id)
        if not player_data or "baseStats" not in player_data:
            await query.edit_message_text("Failed to fetch player data.")
            return

        result = optimize_build(player_data, playstyle)
        text = format_build_result(result)
        await query.edit_message_text(text, parse_mode="Markdown")

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        print("Get a token from @BotFather on Telegram.")
        sys.exit(1)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("build", build_cmd))
    app.add_handler(CommandHandler("player", player_cmd))
    app.add_handler(CommandHandler("playstyles", playstyles_cmd))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

