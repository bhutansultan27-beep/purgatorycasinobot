# Gran Tesero Casino Bot

## Overview

The Gran Tesero Casino Bot is a feature-rich Telegram bot offering a variety of casino games using Telegram's native animated emojis. Its purpose is to provide an engaging and interactive gambling experience within Telegram. The project aims to offer a complete casino bot solution with robust game mechanics, a smart bonus system, a referral program, and comprehensive user and transaction management. This bot has the potential to attract a broad user base interested in casual gaming and social interaction within the Telegram ecosystem.

## User Preferences

The user prefers that all game results are displayed in a simplified, clean format without excessive score details. Communication should be streamlined, and redundant information removed. The user values engaging, interactive gameplay experiences, which is why manual emoji sending for games was implemented. For development, the user prefers a focus on high-level features and architectural decisions over granular implementation specifics, and wants to avoid all changelogs, update logs, and date-wise entries in documentation.

**Important: The bot runs on Webdock (external VPS), NOT on Replit. Do not start or run the bot workflow on Replit as it will conflict with the production instance on Webdock. Replit is used only for code editing and development.**

### Replit Workflow Configuration

The "Casino Bot" workflow is configured but intentionally disabled. The workflow will show as "FAILED" status—this is expected and correct. The bot runs exclusively on the external Webdock VPS server, so:

- ✅ Use Replit for: Code editing, viewing files, making changes
- ❌ Do NOT use Replit for: Running the bot, testing live functionality
- All code changes should be deployed to the Webdock VPS to take effect

## System Architecture

The Gran Tesero Casino Bot is built using Python and the `python-telegram-bot` library, leveraging an asynchronous programming model for performance.

### UI/UX Decisions
- **Emoji-based Games**: Utilizes Telegram's native animated dice emojis for visual appeal and engaging gameplay across all games (Dice, Darts, Basketball, Soccer, Bowling, Slots, Predict, Coinflip).
- **Simplified Results**: Game results are displayed concisely (e.g., "@user won $10.00") rather than with detailed scores, providing a cleaner user experience.
- **Button Interfaces**: Roulette betting uses easy-to-use button interfaces.
- **Match History**: The `/history` command provides detailed results for the last 15 games, and transaction history uses green (🟢) and red (🔴) indicators for clarity.
- **Streamlined Messaging**: Win/loss messages are in lowercase, and button labels are simplified.

### Technical Implementations
- **Game Mechanics**: Includes fourteen casino games:
  - Dice, Darts, Basketball, Soccer, Bowling, Slots, Predict, Coinflip, Roulette
  - Blackjack with standard casino rules (hit, stand, double down, split, insurance)
  - **Mines**: Interactive 5x5 grid minefield game using Telegram buttons. Players choose number of mines (3-24), reveal tiles to find gems, and cash out anytime. Higher mine counts give higher multipliers (up to 24,750x with 24 mines).
  - **Baccarat**: Standard 8-deck Baccarat with Player/Banker/Tie betting. Follows traditional third-card rules. Player pays 2x, Banker pays 1.95x (5% commission), Tie pays 9x. Proper push handling when betting player/banker and result is tie.
  - **Keno**: Interactive 40-number grid game using invisible Telegram buttons (similar to Mines). Players pick up to 10 numbers, then draw 10 numbers randomly. Payouts based on number of hits with multipliers up to 100,000x for hitting 10/10.
  - **Limbo**: Fast-paced crypto-style game where players bet on a target multiplier. The game generates a random multiplier - if it's >= the target, the player wins their bet x target multiplier. Supports target multipliers from 1.01x up to 1,000,000x. RTP ~97%.
  - **Hi-Lo**: Card-based prediction game using a 52-card deck. Players predict if the next card is higher or lower than the current card. Features: Ace is lowest (1), King is highest (13). Same value counts as win for Higher/Lower. Tie bet available for higher payouts. Cash out anytime to secure winnings. Win multiplier increases with each correct prediction. Cards are burned (3 discarded) after each round. RTP ~96-98%.
- **Bonus System**: Features a $5 locked first-time bonus and a 1% daily bonus based on wagered amounts with a 24-hour cooldown and playthrough requirements.
- **Referral Program**: Users get unique referral links, earning a 1% commission on their referrals' wagered volume.
- **Leaderboard**: A paginated leaderboard displays top players based on total wagered amounts.
- **User Wallet & Transaction Management**: Comprehensive system for managing user balances, deposits, withdrawals, and tips.
- **Crypto Support**: Supports SOL (Solana) and LTC (Litecoin) for deposits and withdrawals via Plisio API with 1% fees on both.
- **Admin Management**: Features a dynamic admin system with permanent admins (set via `ADMIN_IDS` environment variable) and dynamic admins (added/removed via commands).
- **House Balance**: Tracks the bot's winnings and losses, influencing the displayed house balance.

### System Design Choices
- **Database**: Employs a JSON-based database (`casino_data.json`) for data persistence, featuring auto-save functionality every 5 minutes and a manual backup command.
- **Configuration**: Bot token and admin IDs are managed via environment variables (`BOT_TOKEN`, `ADMIN_IDS`).
- **Error Handling**: Comprehensive error handling is built into the system.
- **Security**: Includes playthrough requirements, bonus cooldowns, balance validation, and anti-spam withdrawal protection.

## External Dependencies

- **Telegram Bot API**: The core platform for bot interaction, accessed via the `python-telegram-bot` library.
- **JSON**: Used for persistent data storage in `casino_data.json`.