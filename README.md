# 🏴‍☠️ Gild Tesoro Casino Bot

A premium Telegram gambling bot with crypto deposits/withdrawals, level system, PvP games, and admin controls.

## 🚀 Quick Start

### Running on Webdock Server

1. **Upload files via FileZilla** to `~/casino-bot/`:
   - `main.py`
   - `blackjack.py`
   - `webhook_server.py`
   - `database.py`
   - `requirements.txt`

2. **SSH into your server** and run:
```bash
cd ~/casino-bot
python3 -m venv venv
source venv/bin/activate
pip install aiohttp python-telegram-bot APScheduler
```

3. **Set environment variables**:
```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export ADMIN_IDS="your_telegram_id"
export PLISIO_API_KEY="your_plisio_key"
export USE_POLLING=true
```

4. **Start the bot**:
```bash
python3 main.py
```

5. **Run 24/7** (background):
```bash
nohup python3 main.py > bot.log 2>&1 &
```

See `DEPLOY_EXTERNAL.md` for detailed systemd service setup.

---

## 🎮 Available Games

### 🎲 Dice
```
/dice 10          - Bet $10 against the bot
/dice 50 @friend  - Challenge a friend with $50
```
- Both players roll 1-6, highest wins 2x

### 🪙 CoinFlip
```
/coinflip 10 heads          - Bet $10 on heads vs bot
/coinflip 25 tails @friend  - Challenge friend
```
- Win = 2x your bet

### 🔮 Predict
```
/predict 10 #6    - Bet $10 predicting roll of 6
/predict all #3   - Bet all on rolling a 3
```
- Correct = 5x payout

### 🎳 Bowling
```
/bowling 10       - Bet $10 on bowling
/bowling all      - Bet entire balance
```
- Strike (6 pins) = 3x
- Spare (5 pins) = 2x
- 4+ pins = 1.5x

### 🎰 Roulette
```
/roulette 10 red      - Bet on red (2x)
/roulette 10 black    - Bet on black (2x)
/roulette 10 #17      - Bet on number 17 (35x)
/roulette 10 odd      - Bet on odd (2x)
/roulette 10 even     - Bet on even (2x)
```

### 🃏 Blackjack
```
/blackjack 25     - Play blackjack for $25
```
- Hit, Stand, Double Down, Split, Insurance, Surrender
- Blackjack pays 3:2
- 6-deck shoe

---

## 💰 Deposits & Withdrawals

### Supported Cryptocurrencies
- 💎 Litecoin (LTC)
- 🟣 Solana (SOL)
- 🔴 Tron (TRX)
- 💠 Toncoin (TON)
- ⟠ Ethereum (ETH)

### Commands
```
/deposit          - Generate deposit address
/withdraw         - Request withdrawal (requires admin approval)
/bal              - Check your balance
```

**Fees**: 0.5% house fee on deposits and withdrawals

---

## 📊 Level System

Progress through 65 levels across 14 tiers by wagering:

| Tier | Levels | Wager Required |
|------|--------|----------------|
| 🥉 Bronze | I-V | $100 - $5,000 |
| 🥈 Silver | I-V | $10,000 - $32,000 |
| 🏆 Gold | I-V | $39,000 - $81,000 |
| 💎 Platinum | I-V | $94,000 - $155,000 |
| 💠 Diamond | I-V | $173,000 - $253,000 |
| 💚 Emerald | I-V | $275,000 - $373,000 |
| ❤️ Ruby | I-V | $400,000 - $518,000 |
| 💙 Sapphire | I-V | $550,000 - $688,000 |
| 💜 Amethyst | I-V | $725,000 - $883,000 |
| 🖤 Obsidian | I-V | $925,000 - $1,107,000 |
| 🔮 Mythic | I-V | $1,159,000 - $1,393,000 |
| 👑 Legendary | I-V | $1,458,000 - $1,743,000 |
| ✨ Ethereal | I-V | $1,850,000 - $2,650,000 |

Each level unlocks bonus rewards!

---

## 📋 Player Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and menu |
| `/help` | Command list |
| `/bal` | Check balance |
| `/stats` | Your statistics |
| `/bonus` | Claim daily bonus |
| `/level` | View current level |
| `/achievements` | View badges |
| `/referral` | Get referral link |
| `/leaderboard` | Top players |
| `/biggestdices` | Biggest PvP wins |
| `/biggestdeposits` | Largest deposits |

---

## 👥 Referral System

Earn **1% commission** on referrals' wagered amount!

1. Use `/referral` to get your unique link
2. Share with friends
3. Earn automatically as they play
4. Claim earnings anytime

---

## 🛡️ Admin Commands

### User Management
```
/addbalance @user 100     - Add $100 to user
/removebalance @user 50   - Remove $50 from user
/setbalance @user 500     - Set balance to $500
/lookup @user             - View user details
/ban @user                - Ban user
/unban @user              - Unban user
```

### Admin Management
```
/addadmin 123456789       - Add new admin
/removeadmin 123456789    - Remove admin
/listadmins               - List all admins
/addapprover 123456789    - Add withdrawal approver
/removeapprover 123456789 - Remove approver
```

### Withdrawals
```
/pending                  - View pending withdrawals
/approve <id>             - Approve withdrawal
/deny <id>                - Deny withdrawal
```

### House Management
```
/house                    - View house balance
/addhouse 1000            - Add to house balance
```

### Stickers (for roulette)
```
/setsticker 17 <sticker>  - Set sticker for number 17
/liststickers             - List configured stickers
```

---

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes |
| `ADMIN_IDS` | Comma-separated admin Telegram IDs | Yes |
| `PLISIO_API_KEY` | Plisio API key for crypto | For deposits |
| `USE_POLLING` | Set to "true" for polling mode | Recommended |
| `WEBHOOK_URL` | Webhook URL if using webhook mode | Optional |

---

## 📁 File Structure

```
casino-bot/
├── main.py              # Main bot code
├── blackjack.py         # Blackjack game logic
├── webhook_server.py    # Webhook server for deposits
├── database.py          # Database utilities
├── requirements.txt     # Python dependencies
├── casino_data.json     # User data (auto-generated)
├── .env                 # Environment variables
└── bot.log              # Log file
```

---

## 🔒 Security Features

- Playthrough requirements prevent bonus abuse
- 24-hour cooldown on bonus claims
- Admin approval required for withdrawals
- Transaction logging for all operations
- Persistent JSON database with auto-save

---

## 🛠️ Technical Details

- **Python**: 3.10+
- **Framework**: python-telegram-bot v22+
- **Async**: Full async/await
- **Database**: JSON file storage
- **Crypto**: Plisio API integration

---

## 📞 Support

For issues or questions, contact the bot administrators.

Good luck and happy gambling! 🎰🍀
