"""eFootball DNA Build Bot — player archetype engineering via inline buttons."""
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
from optimizer import (
    DNA_CATEGORIES, DNA_TIERS,
    optimize_dna, format_dna_result,
)

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
# Static text
# ---------------------------------------------------------------------------

MAIN_MENU_TEXT = (
    "🧬 *eFootball DNA Lab*\n\n"
    "Engineer any player's DNA — choose upgrades, mutate playstyles "
    "and apply evolution tiers.\n\n"
    "_This isn't traits. This is archetype engineering._"
)

GUIDE_TEXT = (
    "🧬 *DNA Engineering Guide*\n\n"
    "*9 Categories to engineer your player:*\n\n"
    "⚡ *Athletic Engine* — physical & movement tuning\n"
    "🎮 *Ball Mastery* — control & dribbling behavior\n"
    "🎯 *Finishing Lab* — granular shooting upgrades\n"
    "🧠 *Football IQ* — AI behavior & decision-making\n"
    "🚀 *Playstyle Mutation* — full role transformations\n"
    "🔥 *Pressing & Intensity* — aggression engine\n"
    "🪽 *Wide Threat* — dynamic winger identities\n"
    "🛡️ *Defensive Core* — modern defender builds\n"
    "⭐ *Signature Builds* — pre-engineered legends\n\n"
    "*5 DNA Evolution Tiers:*\n"
    "🥉 Rookie  ·  🥈 Elite  ·  🥇 World Class  ·  💎 Legendary  ·  👑 GOAT Mutation"
)


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍  Search Player", callback_data="nav:search")],
        [InlineKeyboardButton("📖  DNA Guide",     callback_data="nav:guide")],
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


def category_keyboard(player_id: int) -> InlineKeyboardMarkup:
    """Show all 9 DNA category buttons."""
    rows = []
    cats = list(DNA_CATEGORIES.items())
    for i in range(0, len(cats), 2):
        row = []
        for cat_key, cat in cats[i:i+2]:
            # Extract just the emoji + short name
            label = cat["label"]
            row.append(InlineKeyboardButton(
                label,
                callback_data=f"cat:{player_id}:{cat_key}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️  Back to search", callback_data="nav:search")])
    return InlineKeyboardMarkup(rows)


def upgrade_keyboard(player_id: int, cat_key: str) -> InlineKeyboardMarkup:
    """Show all upgrades within a category."""
    cat = DNA_CATEGORIES.get(cat_key, {})
    upgrades = cat.get("upgrades", {})
    rows = []
    upg_list = list(upgrades.items())
    for i in range(0, len(upg_list), 2):
        row = []
        for upg_key, upg in upg_list[i:i+2]:
            row.append(InlineKeyboardButton(
                upg["label"],
                callback_data=f"upg:{player_id}:{cat_key}:{upg_key}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(
        "⬅️  Back to categories",
        callback_data=f"player:{player_id}",
    )])
    return InlineKeyboardMarkup(rows)


def tier_keyboard(player_id: int, cat_key: str, upg_key: str) -> InlineKeyboardMarkup:
    """Show the 5 DNA evolution tiers."""
    rows = []
    for tier_key, tier in DNA_TIERS.items():
        rows.append([InlineKeyboardButton(
            f"{tier['icon']}  {tier['label']}",
            callback_data=f"tier:{player_id}:{cat_key}:{upg_key}:{tier_key}",
        )])
    rows.append([InlineKeyboardButton(
        "⬅️  Back to upgrades",
        callback_data=f"cat:{player_id}:{cat_key}",
    )])
    return InlineKeyboardMarkup(rows)


def result_keyboard(player_id: int, cat_key: str) -> InlineKeyboardMarkup:
    """After showing result: try another upgrade or go home."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔄  Try another upgrade",
            callback_data=f"cat:{player_id}:{cat_key}",
        )],
        [InlineKeyboardButton(
            "🧬  New category",
            callback_data=f"player:{player_id}",
        )],
        [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")],
    ])


# ---------------------------------------------------------------------------
# Entry point — /start
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
# nav:* callbacks
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
            "🔍 *Player Search*\n\nType a player name:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️  Back", callback_data="nav:main")]
            ]),
        )
        return SEARCHING

    if dest == "guide":
        await query.edit_message_text(
            GUIDE_TEXT, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️  Back", callback_data="nav:main")]
            ]),
        )
        return MAIN

    return MAIN


# ---------------------------------------------------------------------------
# Text input: player search
# ---------------------------------------------------------------------------

async def search_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    if not query_text:
        await update.message.reply_text("Please type a player name.")
        return SEARCHING

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
                [InlineKeyboardButton("🏠  Main Menu",    callback_data="nav:main")],
            ]),
        )
        return MAIN

    context.user_data["last_results"] = results

    await context.bot.send_message(
        update.effective_chat.id,
        f"*Results for '{query_text}':*\n\nSelect a player to engineer:",
        parse_mode="Markdown",
        reply_markup=search_results_keyboard(results),
    )
    return MAIN


# ---------------------------------------------------------------------------
# player:{id} → show DNA categories
# ---------------------------------------------------------------------------

async def player_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    player_id = int(query.data.split(":", 1)[1])
    context.user_data["player_id"] = player_id

    results = context.user_data.get("last_results", [])
    player_name = next(
        (r["name"] for r in results if r["id"] == player_id),
        f"Player {player_id}",
    )
    player_ovr = next(
        (r["overall"] for r in results if r["id"] == player_id),
        "",
    )

    ovr_str = f" · {player_ovr} OVR" if player_ovr else ""
    await query.edit_message_text(
        f"🧬 *{player_name}*{ovr_str}\n\n"
        "Choose a *DNA category* to engineer:",
        parse_mode="Markdown",
        reply_markup=category_keyboard(player_id),
    )
    return MAIN


# ---------------------------------------------------------------------------
# cat:{player_id}:{cat_key} → show upgrades in category
# ---------------------------------------------------------------------------

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")   # cat : player_id : cat_key
    player_id = int(parts[1])
    cat_key   = parts[2]

    cat = DNA_CATEGORIES.get(cat_key)
    if not cat:
        await query.answer("Unknown category.", show_alert=True)
        return MAIN

    results = context.user_data.get("last_results", [])
    player_name = next(
        (r["name"] for r in results if r["id"] == player_id),
        f"Player {player_id}",
    )

    await query.edit_message_text(
        f"*{cat['label']}*\n_{cat['desc']}_\n\n"
        f"👤 *{player_name}* — choose an upgrade:",
        parse_mode="Markdown",
        reply_markup=upgrade_keyboard(player_id, cat_key),
    )
    return MAIN


# ---------------------------------------------------------------------------
# upg:{player_id}:{cat_key}:{upg_key} → show tier picker
# ---------------------------------------------------------------------------

async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts     = query.data.split(":")   # upg : player_id : cat_key : upg_key
    player_id = int(parts[1])
    cat_key   = parts[2]
    upg_key   = parts[3]

    cat     = DNA_CATEGORIES.get(cat_key, {})
    upgrade = cat.get("upgrades", {}).get(upg_key)
    if not upgrade:
        await query.answer("Unknown upgrade.", show_alert=True)
        return MAIN

    results = context.user_data.get("last_results", [])
    player_name = next(
        (r["name"] for r in results if r["id"] == player_id),
        f"Player {player_id}",
    )

    await query.edit_message_text(
        f"*{upgrade['label']}*\n"
        f"_{upgrade['desc']}_\n\n"
        f"👤 *{player_name}*\n\n"
        "Choose your *DNA Evolution Tier:*",
        parse_mode="Markdown",
        reply_markup=tier_keyboard(player_id, cat_key, upg_key),
    )
    return MAIN


# ---------------------------------------------------------------------------
# tier:{player_id}:{cat_key}:{upg_key}:{tier_key} → run build, show result
# ---------------------------------------------------------------------------

async def tier_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Engineering DNA…")

    parts     = query.data.split(":")   # tier : player_id : cat_key : upg_key : tier_key
    player_id = int(parts[1])
    cat_key   = parts[2]
    upg_key   = parts[3]
    tier_key  = parts[4]

    # Validate
    if cat_key not in DNA_CATEGORIES:
        await query.edit_message_text("❌ Unknown category.")
        return MAIN

    cat = DNA_CATEGORIES[cat_key]
    if upg_key not in cat.get("upgrades", {}):
        await query.edit_message_text("❌ Unknown upgrade.")
        return MAIN

    if tier_key not in DNA_TIERS:
        await query.edit_message_text("❌ Unknown tier.")
        return MAIN

    await query.edit_message_text("⚙️ Engineering your DNA build…")

    # Fetch player data
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

    # Run optimizer
    try:
        result = optimize_dna(player_data, cat_key, upg_key, tier_key)
        text   = format_dna_result(result)
    except Exception as exc:
        logger.error("Optimizer error for player %s: %s", player_id, exc)
        await query.edit_message_text(
            "❌ DNA engineering failed. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")]
            ]),
        )
        return MAIN

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=result_keyboard(player_id, cat_key),
    )
    return MAIN


# ---------------------------------------------------------------------------
# Fallback: unexpected text outside search state
# ---------------------------------------------------------------------------

async def unexpected_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use the buttons to navigate ⬇️",
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
                CallbackQueryHandler(nav_callback,      pattern=r"^nav:"),
                CallbackQueryHandler(player_callback,   pattern=r"^player:"),
                CallbackQueryHandler(category_callback, pattern=r"^cat:"),
                CallbackQueryHandler(upgrade_callback,  pattern=r"^upg:"),
                CallbackQueryHandler(tier_callback,     pattern=r"^tier:"),
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

    print("🧬 DNA Lab Bot started. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
