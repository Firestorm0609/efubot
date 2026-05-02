"""eFootball DNA Build Bot — player archetype engineering via inline buttons."""
import logging
import sys
import os
import time
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters,
    ContextTypes,
)
from telegram.error import TelegramError

from scraper import search_players, fetch_player_detail, fetch_player_index
from optimizer import (
    DNA_CATEGORIES,
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
    "Engineer any player's DNA — choose upgrades and mutate playstyles.\n\n"
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
# Helpers
# ---------------------------------------------------------------------------

def _card_label(r: dict) -> str:
    """Build a search result button label that distinguishes card versions."""
    label = f"{r['name']}  ({r['overall']} OVR)"
    extras = []
    if r.get("position"):
        extras.append(r["position"])
    if r.get("cardType"):
        extras.append(r["cardType"])
    if extras:
        label += f"  · {' · '.join(extras)}"
    return label


def _card_caption(detail: dict) -> str:
    """Build the photo caption for the player confirmation screen."""
    name      = detail.get("name", "Unknown")
    overall   = detail.get("overall", "?")
    position  = detail.get("position", "")
    style     = detail.get("playingStyle", "")
    card_type = detail.get("cardType", "")
    level_cap = detail.get("levelCap", "")

    lines = [f"*{name}*  ·  {overall} OVR"]
    if card_type:
        lines.append(f"🃏 {card_type}")
    if position or style:
        lines.append(f"📍 {position}  ·  {style}" if position and style else f"📍 {position or style}")
    if level_cap:
        lines.append(f"⬆️ Level cap: {level_cap}")
    lines.append("\nIs this the card you want to engineer?")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍  Search Player", callback_data="nav:search")],
        [InlineKeyboardButton("📖  DNA Guide",     callback_data="nav:guide")],
    ])


def carousel_keyboard(index: int, total: int, player_id: int) -> InlineKeyboardMarkup:
    """Prev / Next nav + pick + back — shown under the card photo."""
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("◀️  Prev", callback_data=f"carousel:{index - 1}"))
    nav_row.append(InlineKeyboardButton(f"{index + 1} / {total}", callback_data="noop"))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton("Next  ▶️", callback_data=f"carousel:{index + 1}"))
    return InlineKeyboardMarkup([
        nav_row,
        [InlineKeyboardButton("✅  Engineer this card", callback_data=f"confirm:{player_id}")],
        [InlineKeyboardButton("🔍  Search again", callback_data="nav:search"),
         InlineKeyboardButton("🏠  Menu",         callback_data="nav:main")],
    ])


def confirm_keyboard(player_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅  Yes, engineer this card", callback_data=f"confirm:{player_id}")],
        [InlineKeyboardButton("🔍  Back to results",         callback_data="nav:search")],
    ])


def category_keyboard(player_id: int) -> InlineKeyboardMarkup:
    rows = []
    cats = list(DNA_CATEGORIES.items())
    for i in range(0, len(cats), 2):
        row = []
        for cat_key, cat in cats[i:i+2]:
            row.append(InlineKeyboardButton(
                cat["label"],
                callback_data=f"cat:{player_id}:{cat_key}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️  Back to search", callback_data="nav:search")])
    return InlineKeyboardMarkup(rows)


def upgrade_keyboard(player_id: int, cat_key: str) -> InlineKeyboardMarkup:
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
        callback_data=f"confirm:{player_id}",
    )])
    return InlineKeyboardMarkup(rows)



def result_keyboard(player_id: int, cat_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔄  Try another upgrade",
            callback_data=f"cat:{player_id}:{cat_key}",
        )],
        [InlineKeyboardButton(
            "🧬  New category",
            callback_data=f"confirm:{player_id}",
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
        await _safe_edit_text(
            query, MAIN_MENU_TEXT,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(),
        )
        return MAIN

    if dest == "search":
        context.user_data.pop("player_detail", None)
        await _safe_edit_text(
            query,
            "🔍 *Player Search*\n\nType a player name:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️  Back", callback_data="nav:main")]
            ]),
        )
        return SEARCHING

    if dest == "guide":
        await _safe_edit_text(
            query, GUIDE_TEXT, parse_mode="Markdown",
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
    context.user_data["carousel_index"] = 0

    # Show first card immediately as a photo carousel — no list at all
    await _send_carousel_card(context, update.effective_chat.id, 0)
    return MAIN


# ---------------------------------------------------------------------------
# Carousel helpers
# ---------------------------------------------------------------------------

async def _send_carousel_card(context: ContextTypes.DEFAULT_TYPE, chat_id: int, index: int) -> None:
    """Fetch player detail and send it as a new photo carousel message."""
    results = context.user_data.get("last_results", [])
    if not results or index < 0 or index >= len(results):
        return

    r = results[index]
    player_id = r["id"]
    total = len(results)

    try:
        detail = fetch_player_detail(player_id)
    except Exception as exc:
        logger.error("Carousel fetch error for player %s: %s", player_id, exc)
        detail = None

    if detail:
        context.user_data["player_detail"] = detail

    caption = _card_caption(detail) if detail else f"*{r['name']}*  ·  {r['overall']} OVR"
    img_url = detail.get("imageUrl") if detail else None
    keyboard = carousel_keyboard(index, total, player_id)

    if img_url:
        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=img_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
            return
        except TelegramError as e:
            logger.warning("send_photo failed for player %s: %s", player_id, e)

    # Fallback: text message
    await context.bot.send_message(
        chat_id=chat_id,
        text=caption,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def carousel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle ◀️ Prev / Next ▶️ navigation — swaps the photo in-place."""
    query = update.callback_query
    await query.answer()

    index = int(query.data.split(":")[1])
    results = context.user_data.get("last_results", [])
    if not results or index < 0 or index >= len(results):
        return MAIN

    r = results[index]
    player_id = r["id"]
    total = len(results)
    context.user_data["carousel_index"] = index

    try:
        detail = fetch_player_detail(player_id)
    except Exception as exc:
        logger.error("Carousel nav fetch error for player %s: %s", player_id, exc)
        detail = None

    if detail:
        context.user_data["player_detail"] = detail

    caption = _card_caption(detail) if detail else f"*{r['name']}*  ·  {r['overall']} OVR"
    img_url = detail.get("imageUrl") if detail else None
    keyboard = carousel_keyboard(index, total, player_id)

    if img_url:
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(media=img_url, caption=caption, parse_mode="Markdown"),
                reply_markup=keyboard,
            )
            return MAIN
        except TelegramError as e:
            logger.warning("edit_message_media failed: %s", e)

    # Fallback: just update the caption / text
    try:
        await query.edit_message_caption(caption=caption, parse_mode="Markdown", reply_markup=keyboard)
    except TelegramError:
        try:
            await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=keyboard)
        except TelegramError:
            await query.message.reply_text(caption, parse_mode="Markdown", reply_markup=keyboard)

    return MAIN


# ---------------------------------------------------------------------------
# player:{id} → fetch detail, show card photo confirmation
# ---------------------------------------------------------------------------

async def player_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    player_id = int(query.data.split(":", 1)[1])
    context.user_data["player_id"] = player_id

    # Show a loading state
    await _safe_edit_text(query, "⏳ Loading card…")

    # Fetch full detail (needed for image + position + cardType)
    try:
        detail = fetch_player_detail(player_id)
    except Exception as exc:
        logger.error("Fetch error for player %s: %s", player_id, exc)
        detail = None

    if not detail:
        await context.bot.send_message(
            update.effective_chat.id,
            "❌ Could not load player data. Try another card.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍  Back to results", callback_data="nav:search")],
            ]),
        )
        return MAIN

    # Cache detail so upgrade_callback can reuse it without a second fetch
    context.user_data["player_detail"] = detail

    caption = _card_caption(detail)
    img_url = detail.get("imageUrl")

    if img_url:
        # Send a new photo message; delete the "Loading…" text message first
        try:
            await query.message.delete()
        except TelegramError:
            pass
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_url,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=confirm_keyboard(player_id),
            )
            return MAIN
        except TelegramError as e:
            logger.warning("Failed to send card photo for player %s: %s", player_id, e)
            # Fall through to text confirmation

    # Fallback: text-only confirmation
    await context.bot.send_message(
        update.effective_chat.id,
        caption,
        parse_mode="Markdown",
        reply_markup=confirm_keyboard(player_id),
    )
    return MAIN


# ---------------------------------------------------------------------------
# confirm:{id} → show DNA categories (works for both photo and text messages)
# ---------------------------------------------------------------------------

async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    player_id = int(query.data.split(":", 1)[1])
    context.user_data["player_id"] = player_id

    detail = context.user_data.get("player_detail", {})
    player_name = detail.get("name") or f"Player {player_id}"
    player_ovr  = detail.get("overall", "")

    ovr_str = f" · {player_ovr} OVR" if player_ovr else ""
    text = (
        f"🧬 *{player_name}*{ovr_str}\n\n"
        "Choose a *DNA category* to engineer:"
    )

    await _safe_edit_text(
        query, text,
        parse_mode="Markdown",
        reply_markup=category_keyboard(player_id),
    )
    return MAIN


# ---------------------------------------------------------------------------
# cat / upg callbacks (unchanged logic, updated back buttons)
# ---------------------------------------------------------------------------

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts     = query.data.split(":")
    player_id = int(parts[1])
    cat_key   = parts[2]

    cat = DNA_CATEGORIES.get(cat_key)
    if not cat:
        await query.answer("Unknown category.", show_alert=True)
        return MAIN

    detail = context.user_data.get("player_detail", {})
    player_name = detail.get("name") or f"Player {player_id}"

    await _safe_edit_text(
        query,
        f"*{cat['label']}*\n_{cat['desc']}_\n\n"
        f"👤 *{player_name}* — choose an upgrade:",
        parse_mode="Markdown",
        reply_markup=upgrade_keyboard(player_id, cat_key),
    )
    return MAIN


async def upgrade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run the optimizer immediately with GOAT Mutation budget."""
    query = update.callback_query
    await query.answer("Engineering DNA…")

    parts     = query.data.split(":")
    player_id = int(parts[1])
    cat_key   = parts[2]
    upg_key   = parts[3]

    cat     = DNA_CATEGORIES.get(cat_key, {})
    upgrade = cat.get("upgrades", {}).get(upg_key)
    if not upgrade:
        await query.answer("Unknown upgrade.", show_alert=True)
        return MAIN

    await _safe_edit_text(query, "⚙️ Engineering your DNA build…")

    player_data = context.user_data.get("player_detail")
    if not player_data or "baseStats" not in player_data:
        try:
            player_data = fetch_player_detail(player_id)
        except Exception as exc:
            logger.error("Fetch error for player %s: %s", player_id, exc)
            player_data = None

    if not player_data or "baseStats" not in player_data:
        await context.bot.send_message(
            update.effective_chat.id,
            "❌ No stat data found for this player.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")]
            ]),
        )
        return MAIN

    try:
        result = optimize_dna(player_data, cat_key, upg_key)
        text   = format_dna_result(result)
    except Exception as exc:
        logger.error("Optimizer error for player %s: %s", player_id, exc)
        await context.bot.send_message(
            update.effective_chat.id,
            "❌ DNA engineering failed. Please try again.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠  Main Menu", callback_data="nav:main")]
            ]),
        )
        return MAIN

    await context.bot.send_message(
        update.effective_chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=result_keyboard(player_id, cat_key),
    )
    return MAIN


async def _safe_edit_text(query, text: str, **kwargs):
    """Edit a message as text whether it's currently a text or photo message."""
    try:
        await query.edit_message_text(text, **kwargs)
    except TelegramError:
        # Message was a photo — edit the caption instead, then swap to text
        try:
            await query.edit_message_caption(caption=text, **kwargs)
        except TelegramError:
            # Last resort: send a new message
            await query.message.reply_text(text, **kwargs)


# ---------------------------------------------------------------------------
# Fallback
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
                CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r"^noop$"),
                CallbackQueryHandler(carousel_callback, pattern=r"^carousel:"),
                CallbackQueryHandler(player_callback,   pattern=r"^player:"),
                CallbackQueryHandler(confirm_callback,  pattern=r"^confirm:"),
                CallbackQueryHandler(category_callback, pattern=r"^cat:"),
                CallbackQueryHandler(upgrade_callback,  pattern=r"^upg:"),

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
