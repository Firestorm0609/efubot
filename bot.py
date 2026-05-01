"""eFootball Build Bot — fully inline-button driven, no slash commands."""
import logging
import sys
import os
import time
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters,
    ContextTypes,
)

from scraper import search_players, fetch_player_detail, fetch_player_index
from optimizer import optimize_build, PLAYSTYLES, format_build_result

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------
MAIN, SEARCHING = range(2)

# ---------------------------------------------------------------------------
# Index cache with TTL
# ---------------------------------------------------------------------------
_INDEX_CACHE: Optional[list] = None
_INDEX_FETCHED_AT: float = 0.0
INDEX_TTL = 3600


def get_index() -> list:
    global _INDEX_CACHE, _INDEX_FETCHED_AT
    now = time.monotonic()
    if _INDEX_CACHE is None or (now - _INDEX_FETCHED_AT) > INDEX_TTL:
        logger.info("Refreshing player index cache…")
        _INDEX_CACHE = fetch_player_index()
        _INDEX_FETCHED_AT = now
    return _INDEX_CACHE or []


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍  Search Player", callback_data="nav:search")],
        [InlineKeyboardButton("📋  Playstyles Guide", callback_data="nav:playstyles")],
    ])


def search_results_keyboard(results: list) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"{r['name']}  ({r['overall']} OVR)",
            callback_data=f"player:{r['id']}",
        )]
        for r in results[:8]
    ]
    rows.append([InlineKeyboardButton("⬅️  Back", callback_data="nav:main")])
    return InlineKeyboardMarkup(rows)


def playstyle_keyboard(player_id: int, exclude: str = "") -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            val["label"],
            callback_data=f"build:{player_id}:{ps}",
        )
        for ps, val in PLAYSTYLES.items()
        if ps != exclude
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("⬅️  Back to search", callback_data="nav:search")])
    return InlineKeyboardMarkup(rows)


def build_result_keyboard(player_id: int, current_playstyle: str) -> InlineKeyboardMarkup:
    buttons = [
        InlineKeyboardButton(
            val["label"],
            callback_data=f"build:{player_id}:{ps}",
        )
        for ps, val in PLAYSTYLES.items()
        if ps != current_playstyle
    ]
    rows = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
    rows.append([InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")])
    return InlineKeyboardMarkup(rows)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MAIN_MENU_TEXT = (
    "⚽ *eFootball Build Bot*\n\n"
    "Search for any player and get an optimised training build "
    "for your preferred playstyle — all live from efhub.com."
)

PLAYSTYLES_TEXT = (
    "*Available Playstyles:*\n\n"
    + "\n".join(f"• *{val['label']}*" for val in PLAYSTYLES.values())
)


# ---------------------------------------------------------------------------
# Entry point — /start initiates the conversation
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MAIN_MENU_TEXT,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Navigation callbacks
# ---------------------------------------------------------------------------

async def nav_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, dest = query.data.split(":", 1)

    if dest == "main":
        context.user_data.clear()
        await query.edit_message_text(
            MAIN_MENU_TEXT, parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN

    if dest == "search":
        context.user_data.clear()
        await query.edit_message_text(
            "🔍 *Player Search*\n\nType a player name and send it:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️  Back", callback_data="nav:main")]
            ]),
        )
        return SEARCHING

    if dest == "playstyles":
        await query.edit_message_text(
            PLAYSTYLES_TEXT, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️  Back", callback_data="nav:main")]
            ]),
        )
        return MAIN

    return MAIN


# ---------------------------------------------------------------------------
# Search: receive typed player name
# ---------------------------------------------------------------------------

async def search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("Please type a player name.")
        return SEARCHING

    # Delete the user's text message to keep the chat tidy
    try:
        await update.message.delete()
    except Exception:
        pass

    index = get_index()
    if not index:
        await context.bot.send_message(
            update.effective_chat.id,
            "⚠️ Could not load player index. Please try again later.",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN

    results = search_players(query_text, index)

    if not results:
        await context.bot.send_message(
            update.effective_chat.id,
            f"❌ No players found for *{query_text}*.\n\nTry a different name.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍  Search again", callback_data="nav:search")],
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")],
            ]),
        )
        return MAIN

    context.user_data["last_results"] = results

    await context.bot.send_message(
        update.effective_chat.id,
        f"*Results for '{query_text}':*\n\nSelect a player:",
        parse_mode="Markdown",
        reply_markup=search_results_keyboard(results),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Player selected → show playstyle picker
# ---------------------------------------------------------------------------

async def player_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, player_id_str = query.data.split(":", 1)
    player_id = int(player_id_str)
    context.user_data["player_id"] = player_id

    results = context.user_data.get("last_results", [])
    player_name = next(
        (r["name"] for r in results if r["id"] == player_id),
        f"Player {player_id}",
    )

    await query.edit_message_text(
        f"🎯 *{player_name}*\n\nChoose a playstyle to optimise for:",
        parse_mode="Markdown",
        reply_markup=playstyle_keyboard(player_id),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Build callback → run optimizer and show result
# ---------------------------------------------------------------------------

async def build_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Calculating…")

    parts = query.data.split(":")  # "build:{player_id}:{playstyle}"
    if len(parts) < 3:
        await query.edit_message_text("❌ Invalid button data.")
        return MAIN

    player_id = int(parts[1])
    playstyle = parts[2]

    if playstyle not in PLAYSTYLES:
        await query.edit_message_text(f"❌ Unknown playstyle: {playstyle}")
        return MAIN

    await query.edit_message_text("⚙️ Optimising build…")

    try:
        player_data = fetch_player_detail(player_id)
    except Exception as exc:
        logger.error("Fetch error for player %s: %s", player_id, exc)
        await query.edit_message_text(
            "❌ Failed to fetch player data. Try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")]
            ]),
        )
        return MAIN

    if not player_data or "baseStats" not in player_data:
        await query.edit_message_text(
            "❌ No stat data found for this player.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")]
            ]),
        )
        return MAIN

    try:
        result = optimize_build(player_data, playstyle)
        text = format_build_result(result)
    except Exception as exc:
        logger.error("Optimizer error for player %s: %s", player_id, exc)
        await query.edit_message_text("❌ Build optimisation failed. Please try again.")
        return MAIN

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=build_result_keyboard(player_id, playstyle),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Fallback: unexpected text while not searching
# ---------------------------------------------------------------------------

async def unexpected_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use the buttons below to navigate ⬇️",
        reply_markup=main_menu_keyboard(),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set. Copy .env.example → .env and fill it in.")
        sys.exit(1)

    logger.info("Pre-loading player index…")
    get_index()

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN: [
                CallbackQueryHandler(nav_callback, pattern=r"^nav:"),
                CallbackQueryHandler(player_callback, pattern=r"^player:"),
                CallbackQueryHandler(build_callback, pattern=r"^build:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_message),
            ],
            SEARCHING: [
                CallbackQueryHandler(nav_callback, pattern=r"^nav:"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_input),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv)

    print("Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
