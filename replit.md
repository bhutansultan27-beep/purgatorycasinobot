# Gran Tesero Casino Bot

## Overview

The Gran Tesero Casino Bot is a Telegram bot offering casino games using Telegram's native animated emojis, paired with a web-based Mini App for additional casino games. The project has been simplified to focus on emoji-based games in Telegram while offering full casino experiences through the web interface.

## User Preferences

The user prefers that all game results are displayed in a simplified, clean format without excessive score details. Communication should be streamlined, and redundant information removed. The user values engaging, interactive gameplay experiences.

**IMPORTANT: Mobile-First Design**
- ALL UI/UX design must prioritize phone/mobile viewing
- The webapp runs inside Telegram Mini App which has a constrained mobile viewport
- Always test layouts for small screens first
- Keep headers compact, elements touch-friendly, and content scrollable
- Avoid desktop-only features like hover states for critical functionality

**Important: The bot runs on Webdock (external VPS), NOT on Replit. Replit is used only for code editing and development.**

### Replit Workflow Configuration

- **Web Casino** (port 5000): Flask-based Telegram Mini App with roulette, coinflip, and other casino games
- **Telegram Bot**: Configured for emoji games but requires TELEGRAM_BOT_TOKEN to run

## System Architecture

### Telegram Bot (main.py)
Simplified to support only emoji-based games:
- `/dice <amount>` - Roll dice (1-6)
- `/darts <amount>` - Throw darts at target
- `/basketball <amount>` - Shoot basketball
- `/soccer <amount>` - Kick soccer ball
- `/bowling <amount>` - Bowl for strikes
- `/predict <amount> <number>` - Predict a number
- `/bal` - Check balance (text only, no buttons)

### Webapp (Mini App)
Flask-based webapp serving as a Telegram Mini App:
- **Location**: `webapp/` directory
- **Pages**:
  - `/` - Main menu with game links
  - `/roulette` - European roulette (single 0) with betting UI
  - `/coinflip` - Heads/tails game with 1.98x multiplier
  - `/blackjack` - Classic blackjack
  - `/mines` - Minesweeper-style game
  - `/limbo` - Multiplier prediction game
  - `/keno` - Number picking game
  - `/hilo` - Higher/lower card game
  - `/deposit` - Cryptocurrency deposit page
  - `/withdraw` - Withdrawal request form
  - `/admin` - Admin panel
  - `/profile` - User profile
  - `/leaderboard` - Top players
  - `/history` - Game history
- **Port**: 5000 (for Telegram Mini App integration)

### Game Rules
- **Roulette**: European wheel (0-36), Red/Black/Green bets. Green pays 14x, others pay 2x
- **Coinflip**: 50/50 game with 1.98x multiplier (2% house edge)

### Technical Details
- **Database**: PostgreSQL with SQLAlchemy ORM (`sql_database.py`)
- **Authentication**: Telegram WebApp initData validation
- **Environment Variables**:
  - `TELEGRAM_BOT_TOKEN` - Required for Telegram bot
  - `ADMIN_IDS` - Comma-separated admin user IDs
  - `USE_POLLING` - Set to "true" for polling mode
  - `BOT_USERNAME` - Bot username for referrals
  - `DATABASE_URL` - PostgreSQL connection string

## External Dependencies

- **python-telegram-bot**: Telegram Bot API wrapper
- **Flask**: Web framework for Mini App
- **SQLAlchemy**: Database ORM
- **aiohttp**: Async HTTP client
