"""Scraper for efhub.com player data.

efhub.com uses Next.js App Router (not Pages Router), so player data is
embedded in RSC (React Server Components) payload chunks:

    self.__next_f.push([1,"<json-escaped RSC text>"])

Each chunk's string is JSON-encoded, so \" -> " after json.loads().
The unescaped text contains lines like:
    f:["$","$L3f",null,{"baseStats":{...},"name":"...","position":"..."}]
"""
import re
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://efhub.com"
INDEX_URL = f"{BASE_URL}/search/player-index.json"
BOOSTS_URL = f"{BASE_URL}/data/boosts.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_RSC_PUSH_RE = re.compile(
    r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)',
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _collect_rsc_text(html: str) -> str:
    """Unescape and concatenate all RSC push chunks from the page HTML."""
    parts = []
    for m in _RSC_PUSH_RE.finditer(html):
        try:
            parts.append(json.loads(f'"{m.group(1)}"'))
        except (json.JSONDecodeError, ValueError):
            continue
    return "\n".join(parts)


def _extract_json_object(text: str, key: str) -> Optional[dict]:
    """Extract a JSON object for *key* using brace-depth counting."""
    pattern = rf'"{re.escape(key)}"\s*:\s*\{{'
    m = re.search(pattern, text)
    if not m:
        return None

    start = m.end() - 1
    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                raw = text[start : i + 1]
                try:
                    return json.loads(raw)
                except json.JSONDecodeError as exc:
                    logger.debug("JSON parse error extracting '%s': %s", key, exc)
                    return None
    return None


def _extract_str(text: str, key: str) -> Optional[str]:
    m = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', text)
    return m.group(1) if m else None


def _extract_int(text: str, *keys: str) -> Optional[int]:
    for key in keys:
        m = re.search(rf'"{re.escape(key)}"\s*:\s*(\d+)', text)
        if m:
            return int(m.group(1))
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_player_index() -> list:
    """Fetch the full player index (id, name, overall)."""
    try:
        r = requests.get(INDEX_URL, timeout=15, headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.error("Failed to fetch player index: %s", exc)
        return []


def search_players(query: str, index_data: Optional[list] = None) -> list:
    """Search players by name. Returns list of {id, name, overall, ...}."""
    if index_data is None:
        index_data = fetch_player_index()
    if not index_data:
        return []

    q = query.lower().strip()
    results = []
    for p in index_data:
        name = p.get("e", "")
        if q in name.lower():
            entry: dict = {
                "id": p["i"],
                "name": name,
                "overall": p.get("o", 0),
            }
            # Pass through any extra fields the index exposes
            for src_key, dst_key in (
                ("p", "position"),
                ("t", "cardType"),
                ("c", "club"),
                ("n", "nation"),
            ):
                if p.get(src_key):
                    entry[dst_key] = p[src_key]
            results.append(entry)

    return sorted(results, key=lambda x: -x["overall"])[:10]


def fetch_player_detail(player_id: int) -> Optional[dict]:
    """Fetch player detail from the efhub.com RSC payload."""
    url = f"{BASE_URL}/en/players/{player_id}"
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
    except requests.RequestException as exc:
        logger.error("HTTP error fetching player %s: %s", player_id, exc)
        return None

    html = r.text
    rsc = _collect_rsc_text(html)

    if not rsc:
        logger.warning("No RSC chunks found for player %s", player_id)
        return None

    if "baseStats" not in rsc:
        logger.warning("No baseStats found in RSC payload for player %s", player_id)
        return None

    base_stats = _extract_json_object(rsc, "baseStats")
    if not base_stats:
        logger.warning("Could not parse baseStats for player %s", player_id)
        return None

    player_data: dict = {
        "playerId": str(player_id),
        "baseStats": base_stats,
    }

    # --- Name ---
    # Search for "name" only within the RSC line that contains "baseStats"
    # so we don't accidentally match Next.js component names like
    # "Next.MetadataOutlet" that appear earlier in the RSC payload.
    name = None
    bs_pos = rsc.find('"baseStats"')
    if bs_pos >= 0:
        line_start = rsc.rfind("\n", 0, bs_pos) + 1
        line_end = rsc.find("\n", bs_pos)
        chunk = rsc[line_start : line_end if line_end != -1 else len(rsc)]
        name = _extract_str(chunk, "name")
    if not name:
        name = _extract_str(rsc, "name")  # last-resort: full scan
    if not name:
        title_m = re.search(r"<title[^>]*>([^<]+)</title>", html)
        if title_m:
            name = title_m.group(1).split("\u2014")[0].split("--")[0].strip()
    player_data["name"] = name or f"Player {player_id}"

    # --- Scalar fields ---
    # String fields MUST be searched within `chunk` (the RSC line that holds
    # baseStats) rather than the full RSC text.  The Next.js component tree
    # that precedes the player object contains UI label strings like
    # "position":"Position" and "cardType":"Card Type" which are picked up
    # first by a full-text scan — the same trap that caused the name bug.
    # Integer fields don't have this problem (no integer "Position" labels).
    for field, keys in (
        ("position",     ("position",)),
        ("playingStyle", ("playingStyle",)),
        ("levelCap",     ("initialLevelCap", "levelCap")),
        ("overall",      ("overall", "overallRating")),
        ("boostId",      ("initialBoostLeftId",)),
        ("cardType",     ("cardType", "type")),
    ):
        if field in ("levelCap", "overall", "boostId"):
            val = _extract_int(rsc, *keys)
        else:
            val = None
            # Prefer the targeted chunk; fall back to full RSC scan
            search_targets = [chunk, rsc] if chunk else [rsc]
            for src in search_targets:
                for k in keys:
                    val = _extract_str(src, k)
                    if val:
                        break
                if val:
                    break
        if val is not None:
            player_data[field] = val

    # --- Card image URL ---
    # 1. Try known RSC field names
    img_url = None
    for img_key in ("imageUrl", "image", "cardImage", "imgUrl", "playerImage", "img", "photo"):
        raw = _extract_str(rsc, img_key)
        if raw:
            img_url = raw if raw.startswith("http") else BASE_URL + raw
            break

    # 2. Fall back to og:image meta tag (always present on efhub player pages)
    if not img_url:
        og_m = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            html,
        )
        if og_m:
            img_url = og_m.group(1)

    if img_url:
        player_data["imageUrl"] = img_url

    return player_data


def fetch_boosts() -> list:
    """Fetch booster definitions."""
    try:
        r = requests.get(BOOSTS_URL, timeout=15, headers=HEADERS)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.error("Failed to fetch boosts: %s", exc)
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing player index fetch...")
    idx = fetch_player_index()
    print(f"Got {len(idx)} players in index")
    messi = [p for p in idx if "messi" in p.get("e", "").lower()]
    if messi:
        pid = messi[0]["i"]
        print(f"Testing detail fetch for {messi[0]['e']} (id={pid})")
        detail = fetch_player_detail(pid)
        if detail:
            print(f"Name:      {detail.get('name')}")
            print(f"Position:  {detail.get('position')}")
            print(f"CardType:  {detail.get('cardType')}")
            print(f"Level cap: {detail.get('levelCap')}")
            print(f"Overall:   {detail.get('overall')}")
            print(f"ImageURL:  {detail.get('imageUrl')}")
            print(f"baseStats: {dict(list(detail.get('baseStats', {}).items())[:5])}")
        else:
            print("Failed to fetch detail")
    else:
        print("No Messi found in index")
