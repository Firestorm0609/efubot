# eFootball Build Bot

Telegram bot that finds eFootball players on efhub.com and generates optimal training builds for specific playstyles.

## Features

- Search players by name
- View player stats and details
- Generate optimized training builds for different playstyles
- Live data from efhub.com (no static database needed)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a Telegram bot via @BotFather and get your token.

3. Set the token as an environment variable:
```bash
# Windows
set TELEGRAM_BOT_TOKEN=your_token_here

# Linux/Mac
export TELEGRAM_BOT_TOKEN=your_token_here
```

4. Run the bot:
```bash
python bot.py
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show help | - |
| `/search <name>` | Search for a player | `/search Messi` |
| `/build <name> <playstyle>` | Get build recommendation | `/build Messi dribble` |
| `/build <id> <playstyle>` | Build by player ID | `/build 89136409091415 speed` |
| `/player <name_or_id>` | Show player stats | `/player Messi` |
| `/playstyles` | List available playstyles | - |

## Playstyles

- `dribble` - Dribbling Focus (ball control, dribbling, tight possession)
- `shoot` - Shooting Focus (finishing, kicking power)
- `pass` - Passing Focus (low pass, lofted pass)
- `speed` - Speedster (speed, acceleration)
- `defend` - Defender (defensive awareness, ball winning)
- `physical` - Physical Strength
- `balanced` - Balanced Build
- `goalkeeper` - Goalkeeper
- `playmaker` - Playmaker
- `striker` - Striker

## How it works

1. Player index is fetched from efhub.com's public JSON endpoint
2. Player details (stats, level cap) are scraped from the player page
3. The optimizer allocates training points using a greedy algorithm weighted by playstyle
4. Training cost follows the 4-2-3-4-5 click system per stat

## Files

- `bot.py` - Main Telegram bot
- `scraper.py` - efhub.com data fetching
- `optimizer.py` - Build optimization engine
- `requirements.txt` - Python dependencies
