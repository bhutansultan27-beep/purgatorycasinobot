# 🏴‍☠️ Gild Tesoro Casino Bot

A premium Telegram casino bot with crypto deposits/withdrawals, level system, PvP games, and admin controls.

---

## 🚀 Deployment on Webdock Server

### Step 1: Upload Files via FileZilla
Upload to `~/casino-bot/`:
- `main.py`
- `blackjack.py`
- `webhook_server.py`
- `database.py`
- `requirements.txt`

### Step 2: SSH Setup
```bash
cd ~/casino-bot
python3 -m venv venv
source venv/bin/activate
pip install aiohttp python-telegram-bot APScheduler
```

### Step 3: Set Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export ADMIN_IDS="your_telegram_id"
export PLISIO_API_KEY="your_plisio_key"
export USE_POLLING=true
```

### Step 4: Run the Bot
```bash
python3 main.py
```

### Run 24/7 (Background)
```bash
nohup python3 main.py > bot.log 2>&1 &
```

---

## 🎮 Games

### 🎲 Dice
```
/dice <amount|all>
```
- Play vs Bot or create PvP challenge
- Both players roll 1-6
- Highest roll wins 2x the wager
- Ties refund both players in PvP

### 🎯 Darts
```
/darts <amount|all>
```
- Play vs Bot or PvP
- Roll 4+ to score (out of 6)
- Win if you score and opponent misses
- 2x payout on win

### 🏀 Basketball
```
/basketball <amount|all>
/bball <amount|all>
```
- Play vs Bot or PvP
- Roll 4+ to score
- Win if you score and opponent misses
- 2x payout on win

### ⚽ Soccer
```
/soccer <amount|all>
/football <amount|all>
```
- Play vs Bot or PvP
- Roll 3+ to score
- Win if you score and opponent misses
- 2x payout on win

### 🎳 Bowling
```
/bowling <amount|all>
```
- Play vs Bot or PvP
- Highest roll wins
- 2x payout on win

### 🪙 Coin Flip
```
/flip <amount|all>
```
- Choose Heads or Tails
- Play vs Bot only
- Win = 2x payout (1:1 odds)

### 🔮 Predict
```
/predict <amount|all> #<number>
```
Example: `/predict 10 #6`
- Predict what dice number you'll roll (1-6)
- Correct prediction = **6x payout**
- Wrong prediction = lose wager

### 🎡 Roulette
```
/roulette <amount|all>
/roulette <amount> #<number>
```

**Betting Options:**
| Bet Type | Command Example | Payout |
|----------|-----------------|--------|
| Red | `/roulette 10` then tap Red | 2x |
| Black | `/roulette 10` then tap Black | 2x |
| Green (0, 00) | `/roulette 10` then tap Green | 14x |
| Odd | `/roulette 10` then tap Odd | 2x |
| Even | `/roulette 10` then tap Even | 2x |
| Low (1-18) | `/roulette 10` then tap Low | 2x |
| High (19-36) | `/roulette 10` then tap High | 2x |
| Specific Number | `/roulette 10 #17` | 35x |

### 🃏 Blackjack
```
/blackjack <amount|all>
/bj <amount|all>
```

**Card Values:**
- 2-10: Face value
- J, Q, K: 10 points
- Ace: 1 or 11 points

**Payouts:**
- Blackjack (Ace + 10-value): **1.5x** (3:2)
- Regular Win: **1x** (1:1)
- Push (tie): Bet returned

**Actions:**
- Hit: Take another card
- Stand: Keep current hand
- Double: Double bet, get exactly 1 more card
- Split: Split pairs into 2 separate hands
- Surrender: Forfeit and lose half bet
- Insurance: When dealer shows Ace

---

## 💰 Deposits & Withdrawals

### Supported Cryptocurrencies
| Crypto | Symbol |
|--------|--------|
| 💎 Litecoin | LTC |
| 🟣 Solana | SOL |
| 🔴 Tron | TRX |
| 💠 Toncoin | TON |
| ⟠ Ethereum | ETH |

### Commands
```
/deposit   - Generate deposit address
/withdraw  - Request withdrawal (admin approval required)
/bal       - Check your balance
```

**Fees:** 0.5% house fee on deposits and withdrawals

---

## 🎁 Bonus System

### Rakeback Bonus
- Earn **0.5%** of your wagered amount since last withdrawal
- Claim anytime when bonus reaches at least $0.01
- Access via `/bonus` > Rakeback

### Level Up Bonus
- Earn bonus money when you reach new levels
- Based on total wagered amount
- Each level can only be claimed once
- Access via `/bonus` > Level Up Bonus

---

## 📊 Level System

Progress through 65 levels across 14 tiers by wagering:

| Tier | Emoji | Levels | Wager Range | Bonus Range |
|------|-------|--------|-------------|-------------|
| Bronze | 🥉 | I-V | $100 - $5,000 | $1 - $12.50 |
| Silver | 🥈 | I-V | $10,000 - $32,000 | $25 - $30 |
| Gold | 🏆 | I-V | $39,000 - $81,000 | $35 - $60 |
| Platinum | 💎 | I-V | $94,000 - $155,000 | $65 - $85 |
| Diamond | 💠 | I-V | $173,000 - $253,000 | $90 - $105 |
| Emerald | 💚 | I-V | $275,000 - $373,000 | $110 - $130 |
| Ruby | ❤️ | I-V | $400,000 - $518,000 | $135 - $155 |
| Sapphire | 💙 | I-V | $550,000 - $688,000 | $160 - $180 |
| Amethyst | 💜 | I-V | $725,000 - $883,000 | $185 - $205 |
| Obsidian | 🖤 | I-V | $925,000 - $1,107,000 | $210 - $245 |
| Mythic | 🔮 | I-V | $1,159,000 - $1,393,000 | $260 - $315 |
| Legendary | 👑 | I-V | $1,458,000 - $1,743,000 | $325 - $375 |
| Ethereal | ✨ | I-V | $1,850,000 - $2,650,000 | $535 - $1,250 |

---

## 📋 Player Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/bal` or `/balance` | Check your balance |
| `/bonus` | View Rakeback and Level Up bonuses |
| `/stats` | View your statistics |
| `/levels` | View level rewards |
| `/history` | View your game history |
| `/leaderboard` | View top players |
| `/housebal` | View house balance |
| `/deposit` | Deposit crypto |
| `/withdraw` | Request withdrawal |
| `/tip @user amount` | Tip another player |
| `/support` | Contact support |

---

## 🛡️ Admin Commands

### User Management
| Command | Description |
|---------|-------------|
| `/adminhelp` | Show admin commands |
| `/admin` | Check admin status |
| `/userid @user` | Get user's Telegram ID |
| `/givebal @user amount` | Give money to user |
| `/setbal @user amount` | Set user's balance |
| `/adddeposit @user amount` | Credit manual deposit |
| `/allusers` | List all registered users |
| `/allbalances` | View all balances (paginated) |
| `/userinfo @user` | View detailed user info |

### Admin Management
| Command | Description |
|---------|-------------|
| `/addadmin user_id` | Add new admin (permanent admins only) |
| `/removeadmin user_id` | Remove admin |
| `/listadmins` | List all admins |
| `/addapprover user_id` | Add withdrawal approver |
| `/removeapprover user_id` | Remove approver |
| `/listapprovers` | List all approvers |

### System
| Command | Description |
|---------|-------------|
| `/sethousebal amount` | Set house balance |
| `/ltcrate` | View current LTC/USD rate |
| `/setltcrate price` | Set manual LTC rate |
| `/walletbal` | View crypto wallet balances |
| `/pendingdeposits` | View pending deposits |
| `/pendingwithdraws` | View pending withdrawals |
| `/biggestdeposits` | View biggest deposits |
| `/backup` | Download database backup |

### Stickers (Roulette)
| Command | Description |
|---------|-------------|
| `/savesticker number file_id` | Save sticker for roulette number |
| `/stickers` | List saved stickers |
| `/saveroulette` | Save all roulette stickers |

---

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs | Yes |
| `PLISIO_API_KEY` | Plisio API key for crypto | For deposits |
| `USE_POLLING` | Set to `true` for polling mode | Recommended |
| `WEBHOOK_URL` | Webhook URL (auto-detected on Replit) | Optional |

---

## 📁 File Structure

```
casino-bot/
├── main.py              # Main bot code (5700+ lines)
├── blackjack.py         # Blackjack game logic
├── webhook_server.py    # Webhook for deposit callbacks
├── database.py          # Database utilities
├── requirements.txt     # Python dependencies
├── casino_data.json     # User data (auto-created)
└── bot.log              # Log file (when running with nohup)
```

---

## 🔒 Security Features

- Minimum bet: $0.01
- One game at a time per user
- Button ownership verification (only creator can use buttons)
- Admin approval required for withdrawals
- Permanent vs dynamic admin separation
- Transaction logging for all operations
- Auto-save to JSON database

---

## 🛠️ Technical Details

- **Python**: 3.10+
- **Framework**: python-telegram-bot v22+
- **Async**: Full async/await
- **Database**: JSON file storage with auto-save
- **Crypto**: Plisio API integration
- **Games**: Use Telegram dice/emoji animations

---

Good luck and happy gambling! 🎰🍀
