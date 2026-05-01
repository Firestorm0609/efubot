"""Build optimizer for eFootball player training."""
from typing import Dict, Any

# Stats that matter for each playstyle
PLAYSTYLES = {
    "dribble": {
        "label": "Dribbling Focus",
        "stats": {"ballControl": 1.0, "dribbling": 1.0, "tightPossession": 0.8,
                   "acceleration": 0.5, "balance": 0.4, "speed": 0.3},
    },
    "shoot": {
        "label": "Shooting Focus",
        "stats": {"finishing": 1.0, "kickingPower": 0.7, "ballControl": 0.5,
                   "curl": 0.5, "physicalContact": 0.4, "speed": 0.3},
    },
    "pass": {
        "label": "Passing Focus",
        "stats": {"lowPass": 1.0, "loftedPass": 1.0, "ballControl": 0.8,
                   "curl": 0.5, "tightPossession": 0.3, "speed": 0.2},
    },
    "speed": {
        "label": "Speedster",
        "stats": {"speed": 1.0, "acceleration": 1.0, "balance": 0.5,
                   "dribbling": 0.3, "stamina": 0.3},
    },
    "defend": {
        "label": "Defender",
        "stats": {"defensiveAwareness": 1.0, "ballWinning": 1.0, "defensiveEngagement": 0.8,
                   "physicalContact": 0.7, "jump": 0.5, "speed": 0.3},
    },
    "physical": {
        "label": "Physical Strength",
        "stats": {"physicalContact": 1.0, "balance": 0.7, "jump": 0.7,
                   "kickingPower": 0.4, "stamina": 0.4},
    },
    "balanced": {
        "label": "Balanced Build",
        "stats": {"ballControl": 0.7, "dribbling": 0.6, "finishing": 0.6,
                   "lowPass": 0.6, "defensiveAwareness": 0.4, "speed": 0.4,
                   "acceleration": 0.4, "physicalContact": 0.4},
    },
    "goalkeeper": {
        "label": "Goalkeeper",
        "stats": {"gkAwareness": 1.0, "gkCatching": 1.0, "gkClearing": 0.8,
                   "gkReflexes": 1.0, "gkReach": 0.8},
    },
    "playmaker": {
        "label": "Playmaker",
        "stats": {"ballControl": 1.0, "tightPossession": 0.9, "lowPass": 0.9,
                   "loftedPass": 0.7, "offensiveAwareness": 0.6, "curl": 0.5,
                   "stamina": 0.4},
    },
    "striker": {
        "label": "Striker",
        "stats": {"finishing": 1.0, "offensiveAwareness": 0.9, "ballControl": 0.6,
                   "kickingPower": 0.6, "speed": 0.5, "acceleration": 0.5,
                   "physicalContact": 0.4},
}

# All trainable stats (non-GK)
TRAINABLE_STATS = [
    "offensiveAwareness", "ballControl", "dribbling", "tightPossession",
    "lowPass", "loftedPass", "finishing", "setPieceTaking", "curl",
    "heading", "defensiveAwareness", "ballWinning", "defensiveEngagement",
    "aggression", "kickingPower", "speed", "acceleration", "balance",
    "physicalContact", "jump", "stamina",
]

# GK-only stats
GK_STATS = ["gkAwareness", "gkCatching", "gkClearing", "gkReflexes", "gkReach"]


def get_stat_cost(points_spent: int) -> int:
    if points_spent < 4:
        return 1
    elif points_spent < 8:
        return 2
    elif points_spent < 12:
        return 3
    elif points_spent < 16:
        return 4
    else:
        return 5


def optimize_build(player_data: Dict[str, Any], playstyle: str, total_budget: int = None) -> Dict[str, Any]:
    base_stats = player_data.get("baseStats", {})
    level_cap = player_data.get("levelCap", 34)
    if total_budget is None:
        total_budget = level_cap * 4

    if playstyle not in PLAYSTYLES:
        playstyle = "balanced"

    weights = PLAYSTYLES[playstyle]["stats"]
    relevant_stats = list(weights.keys())

    allocations = {s: 0 for s in relevant_stats}
    budget_remaining = total_budget
    spent_per_stat = {s: 0 for s in relevant_stats}

    while budget_remaining > 0:
        best_stat = None
        best_score = -1.0

        for s in relevant_stats:
            w = weights.get(s, 0)
            if w == 0:
                continue
            current_val = base_stats.get(s, 0) + allocations[s]
            if current_val >= 99:
                continue
            cost = get_stat_cost(spent_per_stat[s])
            if cost > budget_remaining:
                continue
            score = w / cost
            if score > best_score:
                best_score = score
                best_stat = s

        if best_stat is None:
            break

        cost = get_stat_cost(spent_per_stat[best_stat])
        allocations[best_stat] += 1
        spent_per_stat[best_stat] += 1
        budget_remaining -= cost

    # Build final stats
    all_stats = {}
    for s in TRAINABLE_STATS + GK_STATS:
        all_stats[s] = base_stats.get(s, 0) + allocations.get(s, 0)

    points_used = total_budget - budget_remaining

    return {
        "playstyle": PLAYSTYLES[playstyle]["label"],
        "allocations": {s: v for s, v in allocations.items() if v > 0},
        "base_stats": base_stats,
        "final_stats": all_stats,
        "points_used": points_used,
        "points_remaining": budget_remaining,
        "level_cap": level_cap,
        "budget": total_budget,
    }


def format_build_result(result: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"**{result['playstyle']} Build**")
    lines.append(f"Level Cap: {result['level_cap']} | Points used: {result['points_used']} | Remaining: {result['points_remaining']}")
    lines.append("")

    lines.append("**Key Stat Changes:**")
    for sn, pts in result["allocations"].items():
        base = result["base_stats"].get(sn, 0)
        final = result["final_stats"].get(sn, 0)
        if final > base:
            lines.append(f"  {sn}: {base} -> {final} (+{pts})")

    return "
".join(lines)
