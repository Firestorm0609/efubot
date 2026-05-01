"""Scraper for efhub.com player data."""
import re
import json
import requests

BASE_URL = "https://efhub.com"
INDEX_URL = f"{BASE_URL}/search/player-index.json?v=dpl_6MLFAv4qUcgYrD5yx4Gex1ZCo7kD"
BOOSTS_URL = f"{BASE_URL}/data/boosts.json?v=dpl_6MLFAv4qUcgYrD5yx4Gex1ZCo7kD"

def fetch_player_index():
    """Fetch the full player index (id, name, overall)."""
    r = requests.get(INDEX_URL, timeout=15)
    r.raise_for_status()
    return r.json()

def search_players(query, index_data=None):
    """Search players by name. Returns list of {id, name, overall}."""
    if index_data is None:
        index_data = fetch_player_index()
    q = query.lower()
    results = []
    for p in index_data:
        if q in p.get("e", "").lower():
            results.append({"id": p["i"], "name": p["e"], "overall": p["o"]})
    return sorted(results, key=lambda x: -x["overall"])[:10]

def fetch_player_detail(player_id):
    """Fetch player detail by parsing the Next.js RSC payload in the page."""
    url = f"{BASE_URL}/en/players/{player_id}"
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    html = r.text

    # Extract the baseStats JSON blob from the page
    # Pattern: "baseStats":{"offensiveAwareness":79,...}
    stats_match = re.search(r'"baseStats":\{[^}]+\}', html)
    if not stats_match:
        return None

    # We need the full player object. Look for the RSC payload with player data.
    # The player data is in the HTML as part of the Next.js payload.
    # Extract a larger chunk containing the player info.
    player_match = re.search(
        r'"id":"?' + str(player_id) + r'"?(?:,"name":"?[^"]*"?)?,"nationality"',
        html
    )

    # Build player data dict from the page
    player_data = {}

    # Extract baseStats
    bs_match = re.search(r'"baseStats":(\{[^}]+\})', html)
    if bs_match:
        try:
            player_data["baseStats"] = json.loads(bs_match.group(1))
        except json.JSONDecodeError:
            pass

    # Extract position
    pos_match = re.search(r'"position":"([^"]+)"', html)
    if pos_match:
        player_data["position"] = pos_match.group(1)

    # Extract levelCap
    lc_match = re.search(r'"initialLevelCap":(\d+)', html)
    if not lc_match:
        lc_match = re.search(r'"levelCap":(\d+)', html)
    if lc_match:
        player_data["levelCap"] = int(lc_match.group(1))

    # Extract playingStyle
    ps_match = re.search(r'"playingStyle":"([^"]+)"', html)
    if ps_match:
        player_data["playingStyle"] = ps_match.group(1)

    # Extract playerId
    player_data["playerId"] = str(player_id)

    # Extract boost info
    boost_match = re.search(r'"initialBoostLeftId":(\d+)', html)
    if boost_match:
        player_data["boostId"] = int(boost_match.group(1))

    if "baseStats" not in player_data:
        return None

    return player_data

def fetch_boosts():
    """Fetch booster definitions."""
    r = requests.get(BOOSTS_URL, timeout=15)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    # Quick test
    print("Testing player index fetch...")
    idx = fetch_player_index()
    print(f"Got {len(idx)} players in index")
    messi = [p for p in idx if "messi" in p.get("e", "").lower()]
    if messi:
        pid = messi[0]["i"]
        print(f"Testing detail fetch for {messi[0]['e']} (id={pid})")
        detail = fetch_player_detail(pid)
        if detail:
            print(f"Position: {detail.get('position')}")
            print(f"Level cap: {detail.get('levelCap')}")
            print(f"Base stats sample: {dict(list(detail.get('baseStats', {}).items())[:5])}")
        else:
            print("Failed to fetch detail")
