"""Build optimizer for eFootball player training."""
from typing import Dict, Any, Optional

# Stats that matter for each playstyle
PLAYSTYLES: Dict[str, Dict] = {
    "dribble": {
        "label": "Dribbling Focus",
        "stats": {
            "ballControl": 1.0, "dribbling": 1.0, "tightPossession": 0.8,
            "acceleration": 0.5, "balance": 0.4, "speed": 0.3,
        },
    },
    "shoot": {
        "label": "Shooting Focus",
        "stats": {
            "finishing": 1.0, "kickingPower": 0.7, "ballControl": 0.5,
            "curl": 0.5, "physicalContact": 0.4, "speed": 0.3,
        },
    },
    "pass": {
        "label": "Passing Focus",
        "stats": {
            "lowPass": 1.0, "loftedPass": 1.0, "ballControl": 0.8,
            "curl": 0.5, "tightPossession": 0.3, "speed": 0.2,
        },
    },
    "speed": {
        "label": "Speedster",
        "stats": {
            "speed": 1.0, "acceleration": 1.0, "balance": 0.5,
            "dribbling": 0.3, "stamina": 0.3,
        },
    },
    "defend": {
        "label": "Defender",
        "stats": {
            "defensiveAwareness": 1.0, "ballWinning": 1.0,
            "defensiveEngagement": 0.8, "physicalContact": 0.7,
            "jump": 0.5, "speed": 0.3,
        },
    },
    "physical": {
        "label": "Physical Strength",
        "stats": {
            "physicalContact": 1.0, "balance": 0.7, "jump": 0.7,
            "kickingPower": 0.4, "stamina": 0.4,
        },
    },
    "balanced": {
        "label": "Balanced Build",
        "stats": {
            "ballControl": 0.7, "dribbling": 0.6, "finishing": 0.6,
            "lowPass": 0.6, "defensiveAwareness": 0.4, "speed": 0.4,
            "acceleration": 0.4, "physicalContact": 0.4,
        },
    },
    "goalkeeper": {
        "label": "Goalkeeper",
        "stats": {
            "gkAwareness": 1.0, "gkCatching": 1.0, "gkClearing": 0.8,
            "gkReflexes": 1.0, "gkReach": 0.8,
        },
    },
    "playmaker": {
        "label": "Playmaker",
        "stats": {
            "ballControl": 1.0, "tightPossession": 0.9, "lowPass": 0.9,
            "loftedPass": 0.7, "offensiveAwareness": 0.6, "curl": 0.5,
            "stamina": 0.4,
        },
    },
    "striker": {
        "label": "Striker",
        "stats": {
            "finishing": 1.0, "offensiveAwareness": 0.9, "ballControl": 0.6,
            "kickingPower": 0.6, "speed": 0.5, "acceleration": 0.5,
            "physicalContact": 0.4,
        },
    },
}

# All trainable outfield stats
TRAINABLE_STATS = [
    "offensiveAwareness", "ballControl", "dribbling", "tightPossession",
    "lowPass", "loftedPass", "finishing", "setPieceTaking", "curl",
    "heading", "defensiveAwareness", "ballWinning", "defensiveEngagement",
    "aggression", "kickingPower", "speed", "acceleration", "balance",
    "physicalContact", "jump", "stamina",
]

# GK-only stats
GK_STATS = ["gkAwareness", "gkCatching", "gkClearing", "gkReflexes", "gkReach"]

# Human-readable stat labels for display
STAT_LABELS: Dict[str, str] = {
    "offensiveAwareness": "Offensive Awareness",
    "ballControl": "Ball Control",
    "dribbling": "Dribbling",
    "tightPossession": "Tight Possession",
    "lowPass": "Low Pass",
    "loftedPass": "Lofted Pass",
    "finishing": "Finishing",
    "setPieceTaking": "Set Piece Taking",
    "curl": "Curl",
    "heading": "Heading",
    "defensiveAwareness": "Defensive Awareness",
    "ballWinning": "Ball Winning",
    "defensiveEngagement": "Def. Engagement",
    "aggression": "Aggression",
    "kickingPower": "Kicking Power",
    "speed": "Speed",
    "acceleration": "Acceleration",
    "balance": "Balance",
    "physicalContact": "Physical Contact",
    "jump": "Jump",
    "stamina": "Stamina",
    "gkAwareness": "GK Awareness",
    "gkCatching": "GK Catching",
    "gkClearing": "GK Clearing",
    "gkReflexes": "GK Reflexes",
    "gkReach": "GK Reach",
}


def get_stat_cost(points_spent: int) -> int:
    """
    Cost per additional training point, following eFootball's 4-2-3-4-5 tier system.
    Each tier covers 4 points spent, cost increments by 1 per tier.
    """
    tier = points_spent // 4  # 0-based tier
    return min(tier + 1, 5)


def optimize_build(
    player_data: Dict[str, Any],
    playstyle: str,
    total_budget: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Greedy optimizer: at each step pick the stat with the best weight/cost ratio.
    Respects the 99-cap per stat and the training point budget.
    """
    base_stats = player_data.get("baseStats", {})
    level_cap = player_data.get("levelCap", 34)

    if total_budget is None:
        # eFootball grants 4 training points per level
        total_budget = level_cap * 4

    if playstyle not in PLAYSTYLES:
        playstyle = "balanced"

    weights = PLAYSTYLES[playstyle]["stats"]
    relevant_stats = list(weights.keys())

    allocations: Dict[str, int] = {s: 0 for s in relevant_stats}
    spent_per_stat: Dict[str, int] = {s: 0 for s in relevant_stats}
    budget_remaining = total_budget

    while budget_remaining > 0:
        best_stat: Optional[str] = None
        best_score = -1.0

        for s in relevant_stats:
            w = weights.get(s, 0.0)
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

    # Merge allocations into final stats
    final_stats: Dict[str, int] = {}
    for s in TRAINABLE_STATS + GK_STATS:
        final_stats[s] = base_stats.get(s, 0) + allocations.get(s, 0)

    points_used = total_budget - budget_remaining

    return {
        "playstyle": PLAYSTYLES[playstyle]["label"],
        "playstyle_key": playstyle,
        "allocations": {s: v for s, v in allocations.items() if v > 0},
        "base_stats": base_stats,
        "final_stats": final_stats,
        "points_used": points_used,
        "points_remaining": budget_remaining,
        "level_cap": level_cap,
        "budget": total_budget,
        "player_name": player_data.get("name", "Unknown"),
        "position": player_data.get("position", ""),
        "overall": player_data.get("overall", 0),
    }


def format_build_result(result: Dict[str, Any]) -> str:
    """
    Format build result for Telegram (uses *bold* and `code` — Markdown parse mode).
    """
    name = result.get("player_name", "")
    pos = result.get("position", "")
    ovr = result.get("overall", 0)

    header = f"*{result['playstyle']} Build*"
    if name:
        sub = f"_{name}"
        if pos:
            sub += f" · {pos}"
        if ovr:
            sub += f" · {ovr} OVR"
        sub += "_"
        header = f"{header}\n{sub}"

    lines = [
        header,
        "",
        f"Level Cap: *{result['level_cap']}* | "
        f"Points used: *{result['points_used']}* | "
        f"Remaining: *{result['points_remaining']}*",
        "",
        "*Key Stat Changes:*",
    ]

    if result["allocations"]:
        for stat_key, pts in sorted(
            result["allocations"].items(), key=lambda x: -x[1]
        ):
            label = STAT_LABELS.get(stat_key, stat_key)
            base = result["base_stats"].get(stat_key, 0)
            final = result["final_stats"].get(stat_key, 0)
            bar = "█" * min(pts, 10)  # visual bar capped at 10
            lines.append(f"  `{label:<22}` {base} → *{final}* `+{pts}` {bar}")
    else:
        lines.append("  _No stats allocated — all may be capped at 99_")

    return "\n".join(lines)
