# rakebet Casino - Telegram Mini App

## Project Overview
A premium casino gaming application built with Flask and optimized for Telegram Mini Apps. The app features multiple casino games including Mines, Limbo, Keno, Hi-Lo, Baccarat, Roulette, Blackjack, and Coin Flip, with a comprehensive user management system.

## Technology Stack
- **Backend**: Python Flask
- **Database**: SQL (MySQL/PostgreSQL via SQLAlchemy)
- **Frontend**: HTML5, CSS3, JavaScript
- **Mobile**: Telegram WebApp SDK integration
- **Package Management**: Python pip

## Key Features
- Multiple casino games with real-time gameplay
- User authentication via Telegram WebApp initData
- Balance and wallet management
- Leaderboard system with level-based ranking
- Admin panel for game management
- Withdrawal system with crypto support (LTC, SOL)
- Game history and statistics tracking
- Responsive mobile-first design

## Recent Changes (December 28, 2025)

### Mobile Optimization Updates
1. **Added `webapp/static/css/mobile.css`**
   - Responsive breakpoints for screens < 768px
   - Safe area support for notched devices
   - Touch-friendly buttons (min 44px height)
   - Mobile-optimized grid layouts
   - Bottom navigation bar for mobile
   - Sidebar collapsing for small screens

2. **Created `webapp/static/js/telegram-app.js`**
   - Telegram WebApp SDK initialization
   - Viewport height management
   - Safe area inset handling
   - Mobile menu toggle functionality
   - Haptic feedback support
   - Double-tap zoom prevention
   - Network optimization detection

3. **Updated `webapp/templates/index.html`**
   - Added mobile.css stylesheet
   - Integrated telegram-app.js script
   - Maintained Telegram WebApp initialization

4. **Enhanced `webapp/app.py`**
   - Added security headers (X-UA-Compatible, X-Content-Type-Options, X-Frame-Options)
   - Cache control optimization for mobile

5. **Updated `webapp/static/manifest.json`**
   - Portrait-primary orientation
   - Mobile-optimized screenshots
   - Improved PWA metadata

## Project Structure
```
webapp/
├── app.py                      # Flask application
├── templates/                  # HTML templates
│   ├── index.html             # Main casino lobby
│   ├── blackjack.html
│   ├── mines.html
│   ├── limbo.html
│   ├── keno.html
│   ├── hilo.html
│   ├── baccarat.html
│   ├── roulette.html
│   ├── coinflip.html
│   ├── profile.html
│   ├── leaderboard.html
│   ├── history.html
│   ├── wallet.html
│   └── admin/                 # Admin pages
├── static/
│   ├── css/
│   │   ├── casino.css         # Main styles
│   │   ├── mobile.css         # Mobile optimizations (NEW)
│   │   └── [game-specific CSS]
│   ├── js/
│   │   ├── casino.js          # Main app logic
│   │   └── telegram-app.js    # Telegram integration (NEW)
│   ├── images/                # Game and promo images
│   └── manifest.json          # PWA manifest
```

## Environment Variables Required
- `TELEGRAM_BOT_TOKEN`: Bot token for Telegram API
- `BOT_USERNAME`: Telegram bot username
- `ADMIN_IDS`: Comma-separated admin user IDs
- `LTC_MASTER_ADDRESS`: Litecoin wallet address for deposits
- `SOL_MASTER_ADDRESS`: Solana wallet address for deposits (optional)

## Database Schema
- **users**: User profiles with balance and statistics
- **transactions**: Game transactions and wallet operations
- **withdrawals**: Pending withdrawal requests
- **game_history**: Detailed game outcome records

## Running the Application
```bash
python -m flask --app webapp.app run --host=0.0.0.0 --port=5000
```

## Mobile Optimization Features
- ✅ Telegram safe area support (notches, bottom bars)
- ✅ Touch-optimized UI (44px minimum touch targets)
- ✅ Responsive layouts (mobile-first design)
- ✅ Viewport height management
- ✅ Performance optimization for slow networks
- ✅ Haptic feedback support
- ✅ Bottom navigation for small screens
- ✅ Collapsible sidebar on mobile
- ✅ PWA support with service worker

## Next Steps for Enhancement
1. Add more games to the catalog
2. Implement advanced analytics
3. Add social features (friends, chat)
4. Enhance security with rate limiting
5. Add payment processor integrations
6. Implement push notifications

## User Preferences
- Mobile-first responsive design
- Telegram WebApp integration
- Dark theme aesthetic
- Touch-friendly interface
