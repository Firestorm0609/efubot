"""Scraper for efhub.com player data."""
import re
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://efhub.com"
# Version param stripped — requests without it still work and won't break on rotation
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


def _extract_json_value(html: str, key: str) -> Optional[str]:
    """Extract a JSON value for a given key from raw HTML."""
    # Handles both quoted strings and numeric values
    pattern = rf'"{re.escape(key)}":\s*("(?:[^"\\]|\\.)*"|\d+|true|false|null|\{{[^}}]*\}})'
    m = re.search(pattern, html)
    return m.group(1) if m else None


def fetch_player_detail(player_id: int) -> Optional[dict]:
    """Fetch player detail by parsing the Next.js RSC payload in the page."""
    url = f"{BASE_URL}/en/players/{player_id}"
    try:
        r = requests.get(url, timeout=15, headers=HEADERS)
        r.raise_for_status()
    except requests.RequestException as exc:
        logger.error("HTTP error fetching player %s: %s", player_id, exc)
        return None

    html = r.text
    player_data: dict = {}

    # --- baseStats: grab the full {...} block after the key ---
    bs_match = re.search(r'"baseStats"\s*:\s*(\{[^}]+\})', html)
    if not bs_match:
        logger.warning("No baseStats found for player %s", player_id)
        return None
    try:
        player_data["baseStats"] = json.loads(bs_match.group(1))
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error for baseStats (player %s): %s", player_id, exc)
        return None

    # --- Player name: prefer explicit name field, fall back to slug ---
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', html)
    if name_match:
        player_data["name"] = name_match.group(1)
    else:
        slug_match = re.search(r'"slug"\s*:\s*"([^"]+)"', html)
        if slug_match:
            player_data["name"] = slug_match.group(1).replace("-", " ").title()
        else:
            player_data["name"] = f"Player {player_id}"

    # --- Position ---
    pos_match = re.search(r'"position"\s*:\s*"([^"]+)"', html)
    if pos_match:
        player_data["position"] = pos_match.group(1)

    # --- Level cap: check both field names ---
    for cap_key in ("initialLevelCap", "levelCap"):
        lc_match = re.search(rf'"{cap_key}"\s*:\s*(\d+)', html)
        if lc_match:
            player_data["levelCap"] = int(lc_match.group(1))
            break

    # --- Playing style ---
    ps_match = re.search(r'"playingStyle"\s*:\s*"([^"]+)"', html)
    if ps_match:
        player_data["playingStyle"] = ps_match.group(1)

    # --- Overall rating ---
    ovr_match = re.search(r'"overall(?:Rating)?"\s*:\s*(\d+)', html)
    if ovr_match:
        player_data["overall"] = int(ovr_match.group(1))

    # --- Boost info ---
    boost_match = re.search(r'"initialBoostLeftId"\s*:\s*(\d+)', html)
    if boost_match:
        player_data["boostId"] = int(boost_match.group(1))

    player_data["playerId"] = str(player_id)
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
            print(f"Name: {detail.get('name')}")
            print(f"Position: {detail.get('position')}")
            print(f"Level cap: {detail.get('levelCap')}")
            print(f"Overall: {detail.get('overall')}")
            print(f"Base stats sample: {dict(list(detail.get('baseStats', {}).items())[:5])}")
        else:
            print("Failed to fetch detail")
    else:
        print("No Messi found in index")
