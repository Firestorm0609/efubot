"""Scraper for efhub.com player data.

efhub.com uses Next.js App Router (not Pages Router), so player data is
embedded in RSC (React Server Components) payload chunks:

    self.__next_f.push([1,"<json-escaped RSC text>"])

Each chunk's string is JSON-encoded, so \" → " after json.loads().
The unescaped text contains lines like:
    f:["$","$L3f",null,{"baseStats":{...},"name":"...","position":"..."}]

We collect all chunks, unescape them, concatenate, then extract fields.
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

# Matches: self.__next_f.push([1,"<escaped-content>"])
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
            # The captured group is the JSON-encoded string value; wrapping
            # it in quotes lets json.loads unescape it correctly.
            parts.append(json.loads(f'"{m.group(1)}"'))
        except (json.JSONDecodeError, ValueError):
            continue
    return "\n".join(parts)


def _extract_json_object(text: str, key: str) -> Optional[dict]:
    """Extract the first JSON object for *key* using brace-depth counting.

    Handles arbitrarily nested objects — unlike a simple [^}]+ regex which
    stops at the first closing brace it encounters.
    """
    pattern = rf'"{re.escape(key)}"\s*:\s*\{{'
    m = re.search(pattern, text)
    if not m:
        return None

    start = m.end() - 1   # index of the opening '{'
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
    """Search players by name. Returns list of {id, name, overall}."""
    if index_data is None:
        index_data = fetch_player_index()
    if not index_data:
        return []

    q = query.lower().strip()
    results = []
    for p in index_data:
        name = p.get("e", "")
        if q in name.lower():
            results.append({"id": p["i"], "name": name, "overall": p.get("o", 0)})

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

    # Collect and unescape all RSC push chunks
    rsc = _collect_rsc_text(html)

    if not rsc:
        logger.warning("No RSC chunks found for player %s", player_id)
        return None

    if "baseStats" not in rsc:
        logger.warning("No baseStats found in RSC payload for player %s", player_id)
        return None

    # --- baseStats (the only required field) ---
    base_stats = _extract_json_object(rsc, "baseStats")
    if not base_stats:
        logger.warning("Could not parse baseStats for player %s", player_id)
        return None

    player_data: dict = {
        "playerId": str(player_id),
        "baseStats": base_stats,
    }

    # --- Name: prefer explicit field, fall back to slug in <title> ---
    name = _extract_str(rsc, "name")
    if not name:
        title_m = re.search(r"<title[^>]*>([^<]+)</title>", html)
        if title_m:
            # e.g. "K. Kvaratskhelia — 85 OVR | eFHUB"
            name = title_m.group(1).split("—")[0].strip()
    player_data["name"] = name or f"Player {player_id}"

    # --- Other scalar fields ---
    pos = _extract_str(rsc, "position")
    if pos:
        player_data["position"] = pos

    ps = _extract_str(rsc, "playingStyle")
    if ps:
        player_data["playingStyle"] = ps

    lc = _extract_int(rsc, "initialLevelCap", "levelCap")
    if lc is not None:
        player_data["levelCap"] = lc

    ovr = _extract_int(rsc, "overall", "overallRating")
    if ovr is not None:
        player_data["overall"] = ovr

    boost = _extract_int(rsc, "initialBoostLeftId")
    if boost is not None:
        player_data["boostId"] = boost

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
            print(f"Level cap: {detail.get('levelCap')}")
            print(f"Overall:   {detail.get('overall')}")
            print(f"baseStats: {dict(list(detail.get('baseStats', {}).items())[:5])}")
        else:
            print("Failed to fetch detail")
    else:
        print("No Messi found in index")
