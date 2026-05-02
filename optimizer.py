"""eFootball DNA Build Optimizer — player archetype engineering, not generic traits."""
from typing import Dict, Any, Optional

# ---------------------------------------------------------------------------
# DNA Categories — the full archetype engineering framework
# ---------------------------------------------------------------------------

DNA_CATEGORIES: Dict[str, Dict] = {
    "athletic": {
        "label": "⚡ Athletic Engine",
        "desc": "Physical movement & athletic tuning",
        "upgrades": {
            "burst_accel": {
                "label": "Burst Acceleration",
                "desc": "Explosive first step — leave defenders behind in short bursts",
                "stats": {"acceleration": 1.0, "speed": 0.5, "balance": 0.3},
            },
            "sprint_vel": {
                "label": "Sprint Velocity",
                "desc": "Top-end speed for outrunning the defensive line",
                "stats": {"speed": 1.0, "acceleration": 0.5, "stamina": 0.3},
            },
            "agile_turns": {
                "label": "Agile Turns",
                "desc": "Sharp direction changes that leave defenders completely flat-footed",
                "stats": {"balance": 1.0, "acceleration": 0.8, "dribbling": 0.4},
            },
            "expl_leap": {
                "label": "Explosive Leap",
                "desc": "Vertical burst power for aerial dominance",
                "stats": {"jump": 1.0, "physicalContact": 0.5, "heading": 0.4},
            },
            "stamina_eng": {
                "label": "Stamina Engine",
                "desc": "Relentless 90-minute work rate that never drops",
                "stats": {"stamina": 1.0, "speed": 0.3, "acceleration": 0.2},
            },
            "press_endure": {
                "label": "Press Endurance",
                "desc": "Maintain high-intensity pressing throughout the full 90 minutes",
                "stats": {"stamina": 1.0, "aggression": 0.6, "speed": 0.3},
            },
            "cod": {
                "label": "Change of Direction",
                "desc": "Rapid 180° pivots — impossible to track in tight spaces",
                "stats": {"balance": 1.0, "dribbling": 0.8, "acceleration": 0.5},
            },
        },
    },
    "ball": {
        "label": "🎮 Ball Mastery",
        "desc": "Control, dribbling & possession behavior",
        "upgrades": {
            "tight_drib": {
                "label": "Tight Space Dribbler",
                "desc": "Navigate congested areas with elite close control",
                "stats": {"tightPossession": 1.0, "dribbling": 0.9, "ballControl": 0.7, "balance": 0.4},
            },
            "press_resist": {
                "label": "Press Resistance",
                "desc": "Hold the ball under aggressive defensive pressure without losing it",
                "stats": {"tightPossession": 1.0, "physicalContact": 0.7, "ballControl": 0.6, "balance": 0.5},
            },
            "one_touch": {
                "label": "One Touch Control",
                "desc": "Instant immaculate first touch under any condition",
                "stats": {"ballControl": 1.0, "tightPossession": 0.7, "lowPass": 0.4},
            },
            "wf_ctrl": {
                "label": "Weak Foot Control",
                "desc": "Dominant two-footed dribbling — equally dangerous on either side",
                "stats": {"dribbling": 1.0, "ballControl": 0.8, "balance": 0.5},
            },
            "shield": {
                "label": "Shielding Ability",
                "desc": "Body strength to protect possession against physical pressure",
                "stats": {"physicalContact": 1.0, "tightPossession": 0.8, "balance": 0.6},
            },
            "chaos_drib": {
                "label": "Chaos Dribbler",
                "desc": "Street football flair — unpredictable moves that break defensive structure",
                "stats": {"dribbling": 1.0, "tightPossession": 0.8, "acceleration": 0.6, "balance": 0.5},
            },
        },
    },
    "finishing": {
        "label": "🎯 Finishing Lab",
        "desc": "Granular, customisable shooting upgrades",
        "upgrades": {
            "shot_pow": {
                "label": "Shot Power Boost",
                "desc": "Explosive strike power — keepers don't react in time",
                "stats": {"kickingPower": 1.0, "physicalContact": 0.4, "finishing": 0.3},
            },
            "finesse": {
                "label": "Finesse Specialist",
                "desc": "Curl precision shots into the top corner with the outside of the boot",
                "stats": {"curl": 1.0, "finishing": 0.8, "ballControl": 0.4},
            },
            "first_time": {
                "label": "First Time Finisher",
                "desc": "Clinical one-touch finishes from crosses and through balls",
                "stats": {"finishing": 1.0, "offensiveAwareness": 0.7, "ballControl": 0.5},
            },
            "wf_finish": {
                "label": "Weak Foot Finishing",
                "desc": "Increase weak foot finishing under pressure — catch keepers off guard",
                "stats": {"finishing": 1.0, "curl": 0.6, "ballControl": 0.5},
            },
            "long_range": {
                "label": "Long Range Cannons",
                "desc": "Unstoppable outside-the-box threat — forces keepers off their line",
                "stats": {"kickingPower": 1.0, "curl": 0.8, "finishing": 0.6},
            },
            "composed": {
                "label": "Composed Finishing",
                "desc": "Ice-cold in 1v1s — never rushes, always picks the corner",
                "stats": {"finishing": 1.0, "offensiveAwareness": 0.8, "ballControl": 0.6},
            },
            "header": {
                "label": "Header Accuracy",
                "desc": "Dominant aerial finishing — wins and converts every cross",
                "stats": {"heading": 1.0, "jump": 0.7, "physicalContact": 0.4},
            },
            "acrobatic": {
                "label": "Acrobatic Finishing",
                "desc": "Volleys, bicycle kicks and scissor finishes in danger areas",
                "stats": {"finishing": 1.0, "balance": 0.7, "ballControl": 0.6},
            },
            "near_post": {
                "label": "Near Post Killer",
                "desc": "Deadly near-post runs and finishes that keepers never anticipate",
                "stats": {"offensiveAwareness": 1.0, "finishing": 0.9, "acceleration": 0.5},
            },
            "free_kick": {
                "label": "Free Kick Precision",
                "desc": "Wall-beating dead ball specialist — every set piece is a threat",
                "stats": {"setPieceTaking": 1.0, "curl": 0.9, "kickingPower": 0.4},
            },
        },
    },
    "iq": {
        "label": "🧠 Football IQ",
        "desc": "AI behavior & decision-making engineering",
        "upgrades": {
            "position": {
                "label": "Intelligent Positioning",
                "desc": "Always in the right place before the ball even arrives",
                "stats": {"offensiveAwareness": 1.0, "defensiveAwareness": 0.5},
            },
            "late_runs": {
                "label": "Late Box Runs",
                "desc": "Ghosting into the box at the perfect moment — consistently unmarked",
                "stats": {"offensiveAwareness": 1.0, "acceleration": 0.7, "stamina": 0.4},
            },
            "space_create": {
                "label": "Space Creator",
                "desc": "Off-ball movement that opens lanes and drags defenders out of shape",
                "stats": {"offensiveAwareness": 1.0, "acceleration": 0.6, "lowPass": 0.4},
            },
            "counter_read": {
                "label": "Counter Attack Reader",
                "desc": "Instant transition trigger — first to react when possession switches",
                "stats": {"offensiveAwareness": 0.8, "speed": 0.8, "acceleration": 0.7},
            },
            "pass_vision": {
                "label": "Passing Vision",
                "desc": "Sees the killer pass before anyone else — threads needles through defenses",
                "stats": {"loftedPass": 1.0, "lowPass": 0.9, "offensiveAwareness": 0.7},
            },
            "tempo": {
                "label": "Tempo Controller",
                "desc": "Dictates the pace of play — accelerates or slows the game at will",
                "stats": {"lowPass": 1.0, "ballControl": 0.8, "tightPossession": 0.7},
            },
            "kill_pass": {
                "label": "Killer Through Balls",
                "desc": "Thread the needle between defenders for clean 1v1s",
                "stats": {"loftedPass": 1.0, "lowPass": 0.8, "offensiveAwareness": 0.7},
            },
            "tactical_disc": {
                "label": "Tactical Discipline",
                "desc": "Structure-first mentality — holds shape and position under pressure",
                "stats": {"defensiveAwareness": 1.0, "offensiveAwareness": 0.6, "stamina": 0.5},
            },
        },
    },
    "mutation": {
        "label": "🚀 Playstyle Mutation",
        "desc": "Transform roles — changes behavior patterns, not just numbers",
        "upgrades": {
            "false_9": {
                "label": "False 9 Conversion",
                "desc": "Turn striker into a deep-dropping creator — pulls defenders, creates space",
                "stats": {"offensiveAwareness": 1.0, "ballControl": 0.9, "lowPass": 0.9, "tightPossession": 0.8, "acceleration": 0.5},
                "mutation_note": "Drops between lines · Creates midfield overloads · Triggers runs for CF partners",
            },
            "inside_fwd": {
                "label": "Inside Forward",
                "desc": "Convert winger to inside cutter — comes inside, shoots with strong foot",
                "stats": {"dribbling": 1.0, "finishing": 0.9, "curl": 0.8, "ballControl": 0.7, "acceleration": 0.5},
                "mutation_note": "Cuts inside from wide · Bends shots across keeper · Creates own shooting lanes",
            },
            "libero": {
                "label": "Libero CB",
                "desc": "Make CB play like a sweeper who starts attacks from deep",
                "stats": {"defensiveAwareness": 0.9, "lowPass": 1.0, "loftedPass": 0.8, "ballControl": 0.7, "speed": 0.5},
                "mutation_note": "Carries ball forward · Switches play · Reads danger before it develops",
            },
            "deep_play": {
                "label": "Deep Playmaker",
                "desc": "Transform CAM into a deep-lying orchestrator who controls tempo",
                "stats": {"lowPass": 1.0, "loftedPass": 0.9, "tightPossession": 0.9, "ballControl": 0.8, "stamina": 0.5},
                "mutation_note": "Drops into midfield · Distributes quickly · Dictates the game's rhythm",
            },
            "press_str": {
                "label": "High Press Striker",
                "desc": "Relentless high-press false 9 with explosive acceleration and aerial threat",
                "stats": {"aggression": 1.0, "stamina": 0.9, "speed": 0.8, "acceleration": 0.8, "defensiveAwareness": 0.5},
                "mutation_note": "Hunts the ball high up · Closes GK aggressively · Forces defensive errors",
            },
            "inverted_fb": {
                "label": "Inverted Fullback",
                "desc": "Make fullback drift inside as a third central midfielder",
                "stats": {"lowPass": 1.0, "ballControl": 0.9, "offensiveAwareness": 0.8, "tightPossession": 0.7, "acceleration": 0.4},
                "mutation_note": "Tucks into midfield · Creates central overloads · Recycles possession",
            },
            "target_man": {
                "label": "Target Man",
                "desc": "Convert poacher into a hold-up, link-play striker",
                "stats": {"physicalContact": 1.0, "heading": 0.9, "tightPossession": 0.8, "jump": 0.7, "ballControl": 0.6},
                "mutation_note": "Holds up play · Wins every aerial duel · Brings teammates into the game",
            },
            "box_crash": {
                "label": "Box Crashing Midfielder",
                "desc": "Turn CM into a late-arriving goal threat from midfield",
                "stats": {"offensiveAwareness": 1.0, "finishing": 0.9, "acceleration": 0.7, "stamina": 0.6, "ballControl": 0.5},
                "mutation_note": "Times late box runs perfectly · Scores from midfield · Engine-box hybrid",
            },
        },
    },
    "pressing": {
        "label": "🔥 Pressing & Intensity",
        "desc": "Aggression, pressing & defensive workrate",
        "upgrades": {
            "relentless": {
                "label": "Relentless Press",
                "desc": "Never gives the opponent time on the ball — suffocates from front",
                "stats": {"aggression": 1.0, "stamina": 0.9, "speed": 0.6, "defensiveAwareness": 0.5},
            },
            "counter_press": {
                "label": "Counter Press Beast",
                "desc": "Instant ball recovery within 5 seconds of losing possession",
                "stats": {"aggression": 1.0, "speed": 0.9, "acceleration": 0.8, "stamina": 0.6},
            },
            "intercept": {
                "label": "Interception Hunter",
                "desc": "Reads passing lanes and jumps routes before the ball arrives",
                "stats": {"defensiveAwareness": 1.0, "ballWinning": 0.8, "acceleration": 0.5},
            },
            "man_mark": {
                "label": "Man Mark Specialist",
                "desc": "Locks onto the opponent's key player and completely neutralizes them",
                "stats": {"defensiveAwareness": 1.0, "aggression": 0.7, "stamina": 0.7, "speed": 0.5},
            },
            "aggr_tackle": {
                "label": "Aggressive Tackler",
                "desc": "Hard-nosed ball winner who dominates every 50/50 physical duel",
                "stats": {"ballWinning": 1.0, "defensiveEngagement": 0.9, "aggression": 0.7, "physicalContact": 0.6},
            },
            "rec_sprint": {
                "label": "Recovery Sprinting",
                "desc": "Gets behind the ball faster than anyone else on the pitch",
                "stats": {"speed": 1.0, "acceleration": 0.9, "stamina": 0.6, "defensiveAwareness": 0.4},
            },
            "duel_mon": {
                "label": "Duel Monster",
                "desc": "Wins physical 1v1 ground battles with complete dominance",
                "stats": {"physicalContact": 1.0, "defensiveEngagement": 0.9, "ballWinning": 0.8, "aggression": 0.6},
            },
        },
    },
    "wide": {
        "label": "🪽 Wide Threat",
        "desc": "Dynamic winger & wide player identities",
        "upgrades": {
            "touchline": {
                "label": "Touchline Sprinter",
                "desc": "Beats fullbacks with pure electric pace down the flank",
                "stats": {"speed": 1.0, "acceleration": 0.9, "stamina": 0.4},
            },
            "inv_cutter": {
                "label": "Inverted Cutter",
                "desc": "Cuts inside to devastate defenses with the strong foot",
                "stats": {"dribbling": 1.0, "finishing": 0.8, "curl": 0.7, "acceleration": 0.6},
            },
            "cross_mach": {
                "label": "Crossing Machine",
                "desc": "Elite delivery from wide positions — every cross creates danger",
                "stats": {"loftedPass": 1.0, "curl": 0.8, "speed": 0.4},
            },
            "one_v_one": {
                "label": "1v1 Destroyer",
                "desc": "Takes on and beats defenders consistently in wide areas",
                "stats": {"dribbling": 1.0, "tightPossession": 0.9, "acceleration": 0.7, "balance": 0.5},
            },
            "wide_play": {
                "label": "Wide Playmaker",
                "desc": "Creates from wide — links play and switches the field intelligently",
                "stats": {"lowPass": 1.0, "loftedPass": 0.8, "ballControl": 0.7, "tightPossession": 0.6},
            },
            "early_cross": {
                "label": "Early Cross Specialist",
                "desc": "First-time delivery before the defense sets — catches them off guard",
                "stats": {"loftedPass": 1.0, "curl": 0.7, "offensiveAwareness": 0.6, "speed": 0.4},
            },
        },
    },
    "defend": {
        "label": "🛡️ Defensive Core",
        "desc": "Modern, dynamic defender identities",
        "upgrades": {
            "bw_dest": {
                "label": "Ball Winning Destroyer",
                "desc": "Aggressive physical presence who dominates every duel",
                "stats": {"ballWinning": 1.0, "defensiveEngagement": 0.9, "physicalContact": 0.7, "aggression": 0.6},
            },
            "sweeper": {
                "label": "Sweeper Defender",
                "desc": "Reads the game early — covers space and cleans up behind the line",
                "stats": {"defensiveAwareness": 1.0, "speed": 0.7, "acceleration": 0.6, "ballWinning": 0.4},
            },
            "build_up_cb": {
                "label": "Build Up Defender",
                "desc": "Comfortable on the ball — starts attacks from the back line",
                "stats": {"lowPass": 1.0, "ballControl": 0.8, "defensiveAwareness": 0.6, "loftedPass": 0.5},
            },
            "aerial_dom": {
                "label": "Aerial Dominance",
                "desc": "Wins every header — owns set pieces at both ends of the pitch",
                "stats": {"heading": 1.0, "jump": 1.0, "physicalContact": 0.7},
            },
            "last_man": {
                "label": "Last Man Specialist",
                "desc": "Ice-cool in 1v1s — holds shape, never dives in recklessly",
                "stats": {"defensiveAwareness": 1.0, "defensiveEngagement": 0.8, "speed": 0.6},
            },
            "front_foot": {
                "label": "Front Foot Defender",
                "desc": "Steps out aggressively to win the ball high — calculated risks that pay off",
                "stats": {"aggression": 1.0, "ballWinning": 0.9, "speed": 0.7, "defensiveAwareness": 0.6},
            },
            "tac_intercept": {
                "label": "Tactical Interceptor",
                "desc": "Reads the opponent's play — kills attacks before they even start",
                "stats": {"defensiveAwareness": 1.0, "ballWinning": 0.7, "lowPass": 0.4},
            },
        },
    },
    "signature": {
        "label": "⭐ Signature Builds",
        "desc": "Pre-engineered legendary player archetypes",
        "upgrades": {
            "prime_messi": {
                "label": "Prime Messi+",
                "desc": "Explosive burst · Tight dribbling · Outside box threat · Through balls · Agile turns",
                "stats": {
                    "acceleration": 0.9, "tightPossession": 1.0, "dribbling": 0.9,
                    "finishing": 0.8, "loftedPass": 0.8, "curl": 0.7, "balance": 0.6,
                },
                "mutation_note": "The complete attacker — destroys with dribbling, creates with vision, finishes with precision",
            },
            "haaland": {
                "label": "Haaland Monster",
                "desc": "Sprint velocity · Physical dominance · Header accuracy · Shot power · Near post killer",
                "stats": {
                    "speed": 1.0, "physicalContact": 0.9, "heading": 0.9,
                    "kickingPower": 1.0, "finishing": 0.9, "jump": 0.7, "offensiveAwareness": 0.8,
                },
                "mutation_note": "Pure unstoppable force — dominates physically and finishes clinically every time",
            },
            "kante": {
                "label": "Kanté Engine",
                "desc": "Relentless press · Recovery sprint · Interception hunter · Stamina · Tactical discipline",
                "stats": {
                    "aggression": 1.0, "speed": 0.9, "ballWinning": 1.0,
                    "stamina": 0.9, "defensiveAwareness": 0.9, "acceleration": 0.7,
                },
                "mutation_note": "Covers every blade of grass — the engine that never, ever stops running",
            },
            "tiki_maestro": {
                "label": "Tiki-Taka Maestro",
                "desc": "Ball control · Short passing · Tight possession · Tempo control · Off-ball movement",
                "stats": {
                    "ballControl": 1.0, "lowPass": 1.0, "tightPossession": 1.0,
                    "offensiveAwareness": 0.7, "stamina": 0.5, "curl": 0.4,
                },
                "mutation_note": "The heartbeat of possession football — never loses the ball, always finds the right pass",
            },
            "wing_dest": {
                "label": "Wing Destroyer",
                "desc": "Pace · Dribbling · Cutting inside · Finishing · Crossing — the complete wide threat",
                "stats": {
                    "speed": 0.9, "acceleration": 0.9, "dribbling": 1.0,
                    "finishing": 0.8, "loftedPass": 0.7, "curl": 0.6, "balance": 0.6,
                },
                "mutation_note": "Terrorizes fullbacks from wide — scores, creates and destroys in equal measure",
            },
        },
    },
}

# ---------------------------------------------------------------------------
# DNA Evolution Tiers — the progression system
# ---------------------------------------------------------------------------

DNA_TIERS: Dict[str, Dict] = {
    "rookie":      {"label": "Rookie",        "icon": "🥉", "multiplier": 0.7},
    "elite":       {"label": "Elite",         "icon": "🥈", "multiplier": 1.0},
    "world_class": {"label": "World Class",   "icon": "🥇", "multiplier": 1.4},
    "legendary":   {"label": "Legendary",     "icon": "💎", "multiplier": 1.8},
    "goat":        {"label": "GOAT Mutation", "icon": "👑", "multiplier": 2.5},
}

# ---------------------------------------------------------------------------
# Stat metadata
# ---------------------------------------------------------------------------

TRAINABLE_STATS = [
    "offensiveAwareness", "ballControl", "dribbling", "tightPossession",
    "lowPass", "loftedPass", "finishing", "setPieceTaking", "curl",
    "heading", "defensiveAwareness", "ballWinning", "defensiveEngagement",
    "aggression", "kickingPower", "speed", "acceleration", "balance",
    "physicalContact", "jump", "stamina",
]

GK_STATS = ["gkAwareness", "gkCatching", "gkClearing", "gkReflexes", "gkReach"]

STAT_LABELS: Dict[str, str] = {
    "offensiveAwareness":  "Offensive Awareness",
    "ballControl":         "Ball Control",
    "dribbling":           "Dribbling",
    "tightPossession":     "Tight Possession",
    "lowPass":             "Low Pass",
    "loftedPass":          "Lofted Pass",
    "finishing":           "Finishing",
    "setPieceTaking":      "Set Piece Taking",
    "curl":                "Curl",
    "heading":             "Heading",
    "defensiveAwareness":  "Def. Awareness",
    "ballWinning":         "Tackling",      # game renamed "Ball Winning" → "Tackling"
    "defensiveEngagement": "Def. Engagement",
    "aggression":          "Aggression",
    "kickingPower":        "Kicking Power",
    "speed":               "Speed",
    "acceleration":        "Acceleration",
    "balance":             "Balance",
    "physicalContact":     "Physical Contact",
    "jump":                "Jump",
    "stamina":             "Stamina",
    "gkAwareness":         "GK Awareness",
    "gkCatching":          "GK Catching",
    "gkClearing":          "GK Deflecting", # game renamed "GK Clearing" → "GK Deflecting"
    "gkReflexes":          "GK Reflexes",
    "gkReach":             "GK Reach",
}

# ---------------------------------------------------------------------------
# Real eFootball training categories (each click raises ALL stats in group by 1)
# Source: in-game Player Stats Upgrade screen
# ---------------------------------------------------------------------------

TRAINING_CATEGORIES: Dict[str, Dict] = {
    "cat_finish": {
        "label": "Finishing, Set Pieces, Curl",
        "stats": ["finishing", "setPieceTaking", "curl"],
    },
    "cat_pass": {
        "label": "Low Pass, Lofted Pass",
        "stats": ["lowPass", "loftedPass"],
    },
    "cat_drib": {
        "label": "Dribbling, Ball Control, Tight Possession",
        "stats": ["dribbling", "ballControl", "tightPossession"],
    },
    "cat_aware": {
        "label": "Offensive Awareness, Acceleration, Balance",
        "stats": ["offensiveAwareness", "acceleration", "balance"],
    },
    "cat_power": {
        "label": "Kicking Power, Speed, Stamina",
        "stats": ["kickingPower", "speed", "stamina"],
    },
    "cat_aerial": {
        "label": "Heading, Jumping, Physical Contact",
        "stats": ["heading", "jump", "physicalContact"],
    },
    "cat_defend": {
        # In-game UI renamed "Ball Winning" to "Tackling" but efhub.com data
        # still stores this stat under the key "ballWinning". Keep stat key as-is.
        "label": "Defensive Awareness, Tackling, Aggression, Defensive Engagement",
        "stats": ["defensiveAwareness", "ballWinning", "aggression", "defensiveEngagement"],
    },
    "cat_gk1": {
        "label": "GK Awareness, Jumping",
        "stats": ["gkAwareness", "jump"],
    },
    "cat_gk2": {
        # In-game UI renamed to "GK Deflecting" but efhub key is still "gkClearing"
        "label": "GK Deflecting, GK Reach",
        "stats": ["gkClearing", "gkReach"],
    },
    "cat_gk3": {
        "label": "GK Catching, GK Reflexes",
        "stats": ["gkCatching", "gkReflexes"],
    },
}

# ---------------------------------------------------------------------------
# Optimizer
# ---------------------------------------------------------------------------

def get_click_cost(clicks_already: int) -> int:
    """
    eFootball actual category-click cost.
    Clicks 1-4 on same category cost 1 PP each,
    clicks 5-8 cost 2 PP each, 9-12 cost 3 PP each, and so on.

      cost = (clicks_already // 4) + 1
    """
    return (clicks_already // 4) + 1


def optimize_dna(
    player_data: Dict[str, Any],
    cat_key: str,
    upg_key: str,
    tier_key: str,
) -> Dict[str, Any]:
    """
    Category-click DNA optimizer — mirrors the real eFootball training system.

    Each training "click" on a game category raises every stat in that group
    by +1 simultaneously.  Cost per click escalates every 4 clicks within
    the same category: clicks 1-4 = 1 PP, 5-8 = 2 PP, 9-12 = 3 PP, ...

    The greedy algorithm picks whichever relevant category gives the best
    weighted-benefit / PP-cost ratio on each step.

    Budget = level_cap * tier_multiplier  (Progression Points).
    DNA tiers are custom build intensities — not an in-game mechanic.
    """
    base_stats   = player_data.get("baseStats", {})
    level_cap    = player_data.get("levelCap", 34)

    tier    = DNA_TIERS.get(tier_key, DNA_TIERS["elite"])
    cat     = DNA_CATEGORIES.get(cat_key, {})
    upgrade = cat.get("upgrades", {}).get(upg_key, {})

    # PP budget: level_cap × tier multiplier
    total_budget = max(1, int(level_cap * tier["multiplier"]))
    weights      = upgrade.get("stats", {})   # stat_key -> priority weight

    # Identify which game categories contain at least one weighted stat
    relevant: Dict[str, Dict[str, float]] = {}
    for gcat_id, gcat in TRAINING_CATEGORIES.items():
        w_in_cat = {s: weights[s] for s in gcat["stats"] if weights.get(s, 0) > 0}
        if w_in_cat:
            relevant[gcat_id] = w_in_cat

    # State
    clicks: Dict[str, int] = {gcat: 0 for gcat in relevant}

    # Track gains for every stat touched (weighted + bonus side-effects)
    touched_stats: set = set()
    for gcat_id in relevant:
        touched_stats.update(TRAINING_CATEGORIES[gcat_id]["stats"])
    stat_gains: Dict[str, int] = {s: 0 for s in touched_stats}

    budget_remaining = total_budget

    while budget_remaining > 0:
        best_gcat:  Optional[str] = None
        best_score: float         = -1.0

        for gcat_id, w_stats in relevant.items():
            cost = get_click_cost(clicks[gcat_id])
            if cost > budget_remaining:
                continue
            # Only useful if at least one weighted stat can still improve
            benefit = sum(
                w for s, w in w_stats.items()
                if base_stats.get(s, 0) + stat_gains.get(s, 0) < 99
            )
            if benefit <= 0:
                continue
            score = benefit / cost
            if score > best_score:
                best_score = score
                best_gcat  = gcat_id

        if best_gcat is None:
            break

        cost = get_click_cost(clicks[best_gcat])
        clicks[best_gcat] += 1
        budget_remaining  -= cost

        # +1 to every stat in the clicked game category (capped at 99)
        for s in TRAINING_CATEGORIES[best_gcat]["stats"]:
            if s in stat_gains and base_stats.get(s, 0) + stat_gains[s] < 99:
                stat_gains[s] += 1

    # Split gains into target (weighted) vs bonus (side-effect) stats
    allocations = {s: stat_gains[s] for s in weights      if stat_gains.get(s, 0) > 0}
    bonus_gains = {s: stat_gains[s] for s in touched_stats
                   if s not in weights and stat_gains.get(s, 0) > 0}

    final_stats: Dict[str, int] = {}
    for s in TRAINABLE_STATS + GK_STATS:
        final_stats[s] = base_stats.get(s, 0) + stat_gains.get(s, 0)

    points_used = total_budget - budget_remaining

    return {
        "cat_key":          cat_key,
        "upg_key":          upg_key,
        "tier_key":         tier_key,
        "cat_label":        cat.get("label", ""),
        "upg_label":        upgrade.get("label", ""),
        "upg_desc":         upgrade.get("desc", ""),
        "tier_label":       tier["label"],
        "tier_icon":        tier["icon"],
        "mutation_note":    upgrade.get("mutation_note"),
        "allocations":      allocations,
        "bonus_gains":      bonus_gains,
        "base_stats":       base_stats,
        "final_stats":      final_stats,
        "clicks":           {k: v for k, v in clicks.items() if v > 0},
        "points_used":      points_used,
        "points_remaining": budget_remaining,
        "level_cap":        level_cap,
        "budget":           total_budget,
        "player_name":      player_data.get("name", "Unknown"),
        "position":         player_data.get("position", ""),
        "overall":          player_data.get("overall", 0),
    }


def format_dna_result(result: Dict[str, Any]) -> str:
    """Format DNA build result for Telegram Markdown."""
    name  = result.get("player_name", "")
    pos   = result.get("position", "")
    ovr   = result.get("overall", 0)
    t_ico = result.get("tier_icon", "")

    lines = [
        f"🧬 *{result['upg_label']}*",
        f"_{result['upg_desc']}_",
        "",
    ]

    identity = f"👤 *{name}*"
    if pos: identity += f" · {pos}"
    if ovr: identity += f" · {ovr} OVR"
    lines.append(identity)
    lines.append(f"{result['cat_label']}  ·  {t_ico} *{result['tier_label']} DNA*")
    lines.append(f"Budget: *{result['budget']} PP* (Level {result['level_cap']})")
    lines.append("")

    # --- Training click plan ---
    if result.get("clicks"):
        lines.append("*TRAINING PLAN:*")
        for gcat_id, n_clicks in result["clicks"].items():
            gcat_label = TRAINING_CATEGORIES[gcat_id]["label"]
            # Calculate PP cost for these clicks
            pp_cost = sum(get_click_cost(i) for i in range(n_clicks))
            # Two-line format: label on its own line, counts indented below.
            # The old `{gcat_label:<44}` monospace block was wider than a
            # Telegram mobile screen (~32 chars), causing ugly mid-line wraps.
            lines.append(f"  {gcat_label}")
            lines.append(f"    ×{n_clicks}  ({pp_cost} PP)")
        lines.append("")

    # --- Primary stat mutations ---
    lines.append("*STAT MUTATIONS:*")
    if result["allocations"]:
        sorted_allocs = sorted(result["allocations"].items(), key=lambda x: -x[1])
        for stat_key, pts in sorted_allocs:
            label = STAT_LABELS.get(stat_key, stat_key)
            base  = result["base_stats"].get(stat_key, 0)
            final = result["final_stats"].get(stat_key, 0)
            bar   = "█" * min(pts, 10)
            lines.append(f"  `{label:<20}` {base} → *{final}* `+{pts}` {bar}")
    else:
        lines.append("  _All target stats already at cap (99)_")

    # --- Bonus side-effect stats ---
    if result.get("bonus_gains"):
        lines.append("")
        lines.append("*BONUS GAINS:*")
        for stat_key, pts in sorted(result["bonus_gains"].items(), key=lambda x: -x[1]):
            label = STAT_LABELS.get(stat_key, stat_key)
            base  = result["base_stats"].get(stat_key, 0)
            final = result["final_stats"].get(stat_key, 0)
            lines.append(f"  `{label:<20}` {base} → *{final}* `+{pts}`")

    lines.append("")
    pct = int(result["points_used"] / result["budget"] * 100) if result["budget"] else 0
    lines.append(
        f"⚡ *{result['points_used']}* / {result['budget']} PP used ({pct}%)"
        f"  ·  {result['points_remaining']} remaining"
    )

    if result.get("mutation_note"):
        lines.append("")
        lines.append(f"💡 _{result['mutation_note']}_")

    return "\n".join(lines)
