import os
import asyncio
import random
import hashlib
import json
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sql_database import SQLDatabaseManager, migrate_json_to_sql

# Import Blackjack game logic
from blackjack import BlackjackGame

# Import Mines game logic
from mines import MinesGame

# Import Baccarat game logic
from baccarat import BaccaratGame

# Import Keno game logic
from keno import KenoGame

# Import Limbo game logic
from limbo import LimboGame, get_preset_multipliers

# Import Hi-Lo game logic
from hilo import HiLoGame
from connect4 import Connect4Game

# External dependencies (assuming they are installed via pip install python-telegram-bot)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Level System Configuration ---
LEVEL_TIERS = [
    {"name": "Bronze", "emoji": "🥉", "levels": [
        {"id": "bronze_i", "name": "Bronze I", "threshold": 100, "bonus": 1},
        {"id": "bronze_ii", "name": "Bronze II", "threshold": 500, "bonus": 2},
        {"id": "bronze_iii", "name": "Bronze III", "threshold": 1000, "bonus": 2.50},
        {"id": "bronze_iv", "name": "Bronze IV", "threshold": 2500, "bonus": 7.50},
        {"id": "bronze_v", "name": "Bronze V", "threshold": 5000, "bonus": 12.50},
    ]},
    {"name": "Silver", "emoji": "🥈", "levels": [
        {"id": "silver_i", "name": "Silver I", "threshold": 10000, "bonus": 25},
        {"id": "silver_ii", "name": "Silver II", "threshold": 15200, "bonus": 26},
        {"id": "silver_iii", "name": "Silver III", "threshold": 20500, "bonus": 26.50},
        {"id": "silver_iv", "name": "Silver IV", "threshold": 26000, "bonus": 27.50},
        {"id": "silver_v", "name": "Silver V", "threshold": 32000, "bonus": 30},
    ]},
    {"name": "Gold", "emoji": "🏆", "levels": [
        {"id": "gold_i", "name": "Gold I", "threshold": 39000, "bonus": 35},
        {"id": "gold_ii", "name": "Gold II", "threshold": 48000, "bonus": 45},
        {"id": "gold_iii", "name": "Gold III", "threshold": 58000, "bonus": 50},
        {"id": "gold_iv", "name": "Gold IV", "threshold": 69000, "bonus": 55},
        {"id": "gold_v", "name": "Gold V", "threshold": 81000, "bonus": 60},
    ]},
    {"name": "Platinum", "emoji": "💎", "levels": [
        {"id": "platinum_i", "name": "Platinum I", "threshold": 94000, "bonus": 65},
        {"id": "platinum_ii", "name": "Platinum II", "threshold": 107500, "bonus": 67.50},
        {"id": "platinum_iii", "name": "Platinum III", "threshold": 122000, "bonus": 72.50},
        {"id": "platinum_iv", "name": "Platinum IV", "threshold": 138000, "bonus": 80},
        {"id": "platinum_v", "name": "Platinum V", "threshold": 155000, "bonus": 85},
    ]},
    {"name": "Diamond", "emoji": "💠", "levels": [
        {"id": "diamond_i", "name": "Diamond I", "threshold": 173000, "bonus": 90},
        {"id": "diamond_ii", "name": "Diamond II", "threshold": 192000, "bonus": 95},
        {"id": "diamond_iii", "name": "Diamond III", "threshold": 211500, "bonus": 97.50},
        {"id": "diamond_iv", "name": "Diamond IV", "threshold": 232000, "bonus": 102},
        {"id": "diamond_v", "name": "Diamond V", "threshold": 253000, "bonus": 105},
    ]},
    {"name": "Emerald", "emoji": "💚", "levels": [
        {"id": "emerald_i", "name": "Emerald I", "threshold": 275000, "bonus": 110},
        {"id": "emerald_ii", "name": "Emerald II", "threshold": 298000, "bonus": 115},
        {"id": "emerald_iii", "name": "Emerald III", "threshold": 322000, "bonus": 120},
        {"id": "emerald_iv", "name": "Emerald IV", "threshold": 347000, "bonus": 125},
        {"id": "emerald_v", "name": "Emerald V", "threshold": 373000, "bonus": 130},
    ]},
    {"name": "Ruby", "emoji": "❤️", "levels": [
        {"id": "ruby_i", "name": "Ruby I", "threshold": 400000, "bonus": 135},
        {"id": "ruby_ii", "name": "Ruby II", "threshold": 428000, "bonus": 140},
        {"id": "ruby_iii", "name": "Ruby III", "threshold": 457000, "bonus": 145},
        {"id": "ruby_iv", "name": "Ruby IV", "threshold": 487000, "bonus": 150},
        {"id": "ruby_v", "name": "Ruby V", "threshold": 518000, "bonus": 155},
    ]},
    {"name": "Sapphire", "emoji": "💙", "levels": [
        {"id": "sapphire_i", "name": "Sapphire I", "threshold": 550000, "bonus": 160},
        {"id": "sapphire_ii", "name": "Sapphire II", "threshold": 583000, "bonus": 165},
        {"id": "sapphire_iii", "name": "Sapphire III", "threshold": 617000, "bonus": 170},
        {"id": "sapphire_iv", "name": "Sapphire IV", "threshold": 652000, "bonus": 175},
        {"id": "sapphire_v", "name": "Sapphire V", "threshold": 688000, "bonus": 180},
    ]},
    {"name": "Amethyst", "emoji": "💜", "levels": [
        {"id": "amethyst_i", "name": "Amethyst I", "threshold": 725000, "bonus": 185},
        {"id": "amethyst_ii", "name": "Amethyst II", "threshold": 763000, "bonus": 190},
        {"id": "amethyst_iii", "name": "Amethyst III", "threshold": 802000, "bonus": 195},
        {"id": "amethyst_iv", "name": "Amethyst IV", "threshold": 842000, "bonus": 200},
        {"id": "amethyst_v", "name": "Amethyst V", "threshold": 883000, "bonus": 205},
    ]},
    {"name": "Obsidian", "emoji": "🖤", "levels": [
        {"id": "obsidian_i", "name": "Obsidian I", "threshold": 925000, "bonus": 210},
        {"id": "obsidian_ii", "name": "Obsidian II", "threshold": 968000, "bonus": 215},
        {"id": "obsidian_iii", "name": "Obsidian III", "threshold": 1012000, "bonus": 220},
        {"id": "obsidian_iv", "name": "Obsidian IV", "threshold": 1058000, "bonus": 230},
        {"id": "obsidian_v", "name": "Obsidian V", "threshold": 1107000, "bonus": 245},
    ]},
    {"name": "Mythic", "emoji": "🔮", "levels": [
        {"id": "mythic_i", "name": "Mythic I", "threshold": 1159000, "bonus": 260},
        {"id": "mythic_ii", "name": "Mythic II", "threshold": 1213000, "bonus": 270},
        {"id": "mythic_iii", "name": "Mythic III", "threshold": 1270000, "bonus": 285},
        {"id": "mythic_iv", "name": "Mythic IV", "threshold": 1330000, "bonus": 300},
        {"id": "mythic_v", "name": "Mythic V", "threshold": 1393000, "bonus": 315},
    ]},
    {"name": "Legendary", "emoji": "👑", "levels": [
        {"id": "legendary_i", "name": "Legendary I", "threshold": 1458000, "bonus": 325},
        {"id": "legendary_ii", "name": "Legendary II", "threshold": 1525000, "bonus": 335},
        {"id": "legendary_iii", "name": "Legendary III", "threshold": 1595000, "bonus": 350},
        {"id": "legendary_iv", "name": "Legendary IV", "threshold": 1668000, "bonus": 365},
        {"id": "legendary_v", "name": "Legendary V", "threshold": 1743000, "bonus": 375},
    ]},
    {"name": "Ethereal", "emoji": "✨", "levels": [
        {"id": "ethereal_i", "name": "Ethereal I", "threshold": 1850000, "bonus": 535},
        {"id": "ethereal_ii", "name": "Ethereal II", "threshold": 2000000, "bonus": 750},
        {"id": "ethereal_iii", "name": "Ethereal III", "threshold": 2175000, "bonus": 875},
        {"id": "ethereal_iv", "name": "Ethereal IV", "threshold": 2400000, "bonus": 1125},
        {"id": "ethereal_v", "name": "Ethereal V", "threshold": 2650000, "bonus": 1250},
    ]},
]

LEVELS = []
for tier in LEVEL_TIERS:
    for level in tier["levels"]:
        LEVELS.append({
            "id": level["id"],
            "name": level["name"],
            "emoji": tier["emoji"],
            "threshold": level["threshold"],
            "bonus": level["bonus"],
            "tier_name": tier["name"]
        })

LEVELS.insert(0, {"id": "unranked", "name": "Unranked", "emoji": "⚪", "threshold": 0, "bonus": 0, "tier_name": "Unranked"})

# --- Supported Crypto Currencies for Deposits & Withdrawals (Plisio) ---
# Each crypto has its own fee percentage to account for different network fees
# Higher fees for expensive networks (BTC, ETH), lower fees for cheap networks (TRX, SOL)
SUPPORTED_CRYPTOS = {
    'SOL': {'name': 'Solana', 'emoji': '💜', 'plisio_code': 'SOL', 'fee_percent': 0.0, 'deposit_fee_percent': 0.0, 'min_withdraw': 2.00},
    'LTC': {'name': 'Litecoin', 'emoji': '💎', 'plisio_code': 'LTC', 'fee_percent': 0.0, 'deposit_fee_percent': 0.0, 'min_withdraw': 2.00},
}

SUPPORTED_DEPOSIT_CRYPTOS = SUPPORTED_CRYPTOS
SUPPORTED_WITHDRAWAL_CRYPTOS = SUPPORTED_CRYPTOS

# Default house fee percentage (used as fallback)
HOUSE_FEE_PERCENT = 0.02

def get_crypto_fee(currency: str) -> float:
    """Get the fee percentage for a specific cryptocurrency."""
    crypto_info = SUPPORTED_CRYPTOS.get(currency, {})
    return crypto_info.get('fee_percent', HOUSE_FEE_PERCENT)

def get_crypto_min_withdraw(currency: str) -> float:
    """Get the minimum withdrawal amount for a specific cryptocurrency."""
    crypto_info = SUPPORTED_CRYPTOS.get(currency, {})
    return crypto_info.get('min_withdraw', 1.00)

def get_user_level(total_wagered: float, user_id: Optional[int] = None, db = None) -> dict:
    """Returns the current level data based on total wagered amount."""
    current_level = LEVELS[0]
    for level in LEVELS:
        if total_wagered >= level["threshold"]:
            current_level = level
        else:
            break
    
    return current_level

def get_next_level(total_wagered: float) -> Optional[dict]:
    """Returns the next level data or None if at max level."""
    for i, level in enumerate(LEVELS):
        if total_wagered < level["threshold"]:
            return level
    return None

def get_tier_index(tier_name: str) -> int:
    """Get the index of a tier by name."""
    for i, tier in enumerate(LEVEL_TIERS):
        if tier["name"] == tier_name:
            return i
    return 0

def get_blockchain_explorer_url(currency: str, tx_id: str) -> str:
    """Get the blockchain explorer URL for a transaction."""
    explorers = {
        'LTC': f'https://blockchair.com/litecoin/transaction/{tx_id}',
        'BTC': f'https://blockchair.com/bitcoin/transaction/{tx_id}',
        'ETH': f'https://etherscan.io/tx/{tx_id}',
        'SOL': f'https://solscan.io/tx/{tx_id}',
        'TRX': f'https://tronscan.org/#/transaction/{tx_id}',
        'XMR': f'https://xmrchain.net/tx/{tx_id}',
        'TON': f'https://tonscan.org/tx/{tx_id}',
        'USDT': f'https://etherscan.io/tx/{tx_id}',
        'USDC': f'https://etherscan.io/tx/{tx_id}',
    }
    return explorers.get(currency.upper(), f'https://blockchair.com/search?q={tx_id}')

# --- 1. Database Manager (SQL-backed storage) ---
# Use SQL database for persistent storage shared between bot and webapp
DatabaseManager = SQLDatabaseManager

# Run migration from JSON to SQL on startup (only migrates if SQL is empty)
try:
    migrate_json_to_sql()
except Exception as e:
    logger.warning(f"Migration check: {e}")

# --- 2. Gran Tesero Casino Bot Class ---
class GranTeseroCasinoBot:
    def __init__(self, token: str):
        self.token = token
        # Initialize the internal database manager
        self.db = DatabaseManager()
        
        # Admin user IDs from environment variable (permanent admins)
        admin_ids_str = os.getenv("ADMIN_IDS", "")
        self.env_admin_ids = set()
        if admin_ids_str:
            try:
                self.env_admin_ids = set(int(id.strip()) for id in admin_ids_str.split(",") if id.strip())
                logger.info(f"Loaded {len(self.env_admin_ids)} permanent admin(s) from environment")
            except ValueError:
                logger.error("Invalid ADMIN_IDS format. Use comma-separated numbers.")
        
        # Load dynamic admins from database
        self.dynamic_admin_ids = set(self.db.get_dynamic_admins())
        if self.dynamic_admin_ids:
            logger.info(f"Loaded {len(self.dynamic_admin_ids)} dynamic admin(s) from database")
        
        # Load withdrawal approvers from database (can only approve/deny withdrawals)
        approvers_str = self.db.get_config('withdrawal_approvers', '[]')
        try:
            self.withdrawal_approvers = set(json.loads(approvers_str))
        except:
            self.withdrawal_approvers = set()
        if self.withdrawal_approvers:
            logger.info(f"Loaded {len(self.withdrawal_approvers)} withdrawal approver(s) from database")
        
        # Initialize bot application
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
        # Dictionary to store ongoing PvP challenges (in-memory, not persisted)
        self.pending_pvp: Dict[str, Any] = {}
        
        # Track button ownership: (chat_id, message_id) -> user_id mapping
        self.button_ownership: Dict[tuple, int] = {}
        # Track clicked buttons to prevent re-use: (chat_id, message_id, callback_data)
        self.clicked_buttons: set = set()
        # Track users with pending opponent selection (shown "Choose your opponent" but haven't clicked yet)
        self.pending_opponent_selection: set = set()
        
        # Sticker configuration - Load from database or initialize with defaults
        stickers_config = self.db.get_config('stickers', None)
        if not stickers_config:
            default_stickers = {
                "roulette": {
                    "00": "CAACAgQAAxkBAAEPnjFo-TLLYpgTZExC4IIOG6PIXwsviAAC1BgAAkmhgFG_0u82E59m3DYE",
                    "0": "CAACAgQAAxkBAAEPnjNo-TMFaqDdWCkRDNlus4jcuamAAwACOh0AAtQAAYBRlMLfm2ulRSM2BA",
                    "1": "CAACAgQAAxkBAAEPnjRo-TMFH5o5R9ztNtTFBJmQVK_t3wACqBYAAvTrgVE4WCoxbBzVCDYE",
                    "2": "CAACAgQAAxkBAAEPnjdo-TMvGdoX-f6IAuR7kpYO-hh9fwAC1RYAAob0eVF1zbcG00UjMzYE",
                    "3": "CAACAgQAAxkBAAEPnjho-TMwui0CFuGEK5iwS7xMRDiPfgACSRgAAs74gVEyHQtTsRykGjYE",
                    "4": "CAACAgQAAxkBAAEPnj1o-TNGYNdmhy4n5Uyp3pzWmukTgAACfBgAAg3IgFGEjdLKewti5zYE",
                    "5": "CAACAgQAAxkBAAEPnj5o-TNHTKLFF2NpdxfLhHnsnFGTXgACyhYAAltygVECKXn73kUyCjYE",
                    "6": "CAACAgQAAxkBAAEPnkFo-TNPGqrsJJwZNwUe_I6k4W86cwACyxoAAgutgVGyiCe4lNK2-DYE",
                    "7": "CAACAgQAAxkBAAEPnkJo-TNPksXPcYnpXDWYQC68AAGlqzQAAtUYAAKU_IFRJTHChQd2yfw2BA",
                    "8": "CAACAgQAAxkBAAEPnkdo-TQOIBN5WtoKKnvcthXdcy0LLgACgBQAAmlWgVFImh6M5RcAAdI2BA",
                    "9": "CAACAgQAAxkBAAEPnkho-TQO92px4jOuq80nT2uWjURzSAAC4BcAAvPKeVFBx-TZycAWDzYE",
                    "10": "CAACAgQAAxkBAAEPnkto-TZ8-6moW-biByRYl8J2QEPnTwAC8hgAArnAgFGen1zgHwABLPc2BA",
                    "11": "CAACAgQAAxkBAAEPnkxo-TZ8ncZZ7FYYyFMJHXRv2rB0TwAC2RMAAmzdgVEao0YAAdIy41g2BA",
                    "12": "CAACAgQAAxkBAAEPnk1o-TZ9z6xAxxIeccUPXoQQ9VaikQACVRgAAovngVFUjR-qYgq8LDYE",
                    "13": "CAACAgQAAxkBAAEPnlFo-TbUs79Rm549dK3JK2L3P83q-QACTR0AAmc0gFHXnJ509OdiOjYE",
                    "14": "CAACAgQAAxkBAAEPnlJo-TbUCpjrhSxP-x84jkBerEYB8AACQxkAAqXDeVEQ5uCH3dK9OjYE",
                    "15": "CAACAgQAAxkBAAEPnlNo-TbUZokc7ubz-neSYtK9kxQ0DAACrRYAAlBWgVH9BqGde-NivjYE",
                    "16": "CAACAgQAAxkBAAEPnlRo-TbUiOcqxKI6HNExFR8yT3qyvAACrxsAAkcfeVG9im0F0tuZPzYE",
                    "17": "CAACAgQAAxkBAAEPnllo-TdIFRtpAW3PeDbxD2QxTgjk2QACLhgAAiuXgVHaPo1woXZEYTYE",
                    "18": "CAACAgQAAxkBAAEPnlpo-TdI9Gdz2Nv3icxluy8jC3keBwACYxkAAnx7eFGsZP2AXXBKwzYE",
                    "19": "CAACAgQAAxkBAAEPnlto-TdIUktLbTIhkihQz3ymy4lUIwACKRkAArDwgFH0iKqIPPiHYDYE",
                    "20": "CAACAgQAAxkBAAEPnlxo-TdJVrOSPiCRuD8Jc0XGvF3B8AACcxoAAr7OeFGSuSoHyKxf5TYE",
                    "21": "CAACAgQAAxkBAAEPnl1o-TdJ1jlMSjGQPO0zkaS_rOv5JQACxhcAAv1dgFF3khtGYFneYzYE",
                    "22": "CAACAgQAAxkBAAEPnmNo-Te2OhfAwfprG1HfmY-UNtkEAgADGQACE8KAUSJTKzPQQQ9INgQ",
                    "23": "CAACAgQAAxkBAAEPnmRo-Te3rAHmt7_CRgFp55KSNVYdKwACTBgAAundgVF6unXyM34ZYzYE",
                    "24": "CAACAgQAAxkBAAEPnmVo-Te3LcVARwsUx3Akt75bruvNXAAC4RoAAnkvgFHRL4l2927wnDYE",
                    "25": "CAACAgQAAxkBAAEPnmZo-Te3lY0O1JxF8tTLYJJhN1QcnAAC5hcAAiPegFFsMkNzpqfR0zYE",
                    "26": "CAACAgQAAxkBAAEPnmto-TgIsR6UdO8EukNYajboFnX3mgACzSAAAn15gVG-oQ4oaJLYrzYE",
                    "27": "CAACAgQAAxkBAAEPnmxo-TgIVFkyEf19Je-9awnfcm0HNAACoBcAAjK0gVFqoRMWJ0V2AjYE",
                    "28": "CAACAgQAAxkBAAEPnm1o-TgIEaTKLI1hP_FD5NoPNMoRrQAC8xUAAjTtgVFbDjOI7hjkyDYE",
                    "29": "CAACAgQAAxkBAAEPnm5o-TgIrfmuYVnfQps2DUcaDPJtYAACehcAAgL2eFFyvPJETxqlljYE",
                    "30": "CAACAgQAAxkBAAEPnm9o-TgIumJ40cFAJ7xQVVJu8yioGQACrBUAAqMsgVEiKujpQgVfJDYE",
                    "31": "CAACAgQAAxkBAAEPnndo-ThreZX7kJJpPO5idNcOeIWZpQACDhsAArW6gFENcv6I97q9xDYE",
                    "32": "CAACAgQAAxkBAAEPni9o-Ssij-qcC2-pLlmtFrUQr5AUgQACWxcAAsmneVGFqOYh9w81_TYE",
                    "33": "CAACAgQAAxkBAAEPnnto-Thsmi6zNRuaeXnBFpXJ-w2JnQACjBkAAo3JeFEYXOtgIzFLjTYE",
                    "34": "CAACAgQAAxkBAAEPnnlo-ThrHvyKnt3O8UiLblKzGgWqzQACWBYAAvn3gVElI6JyUvoRYzYE",
                    "35": "CAACAgQAAxkBAAEPnn9o-Tij1sCB1_UVenRU6QvBnfFKagACkhYAAsKTgFHHcm9rj3PDyDYE",
                    "36": "CAACAgQAAxkBAAEPnoBo-Tik1zRaZMCVCaOi9J1FtVvEiAACrBcAAtbQgVFt8Uw1gyn4MDYE"
                }
            }
            self.db.set_config('stickers', json.dumps(default_stickers))
            self.stickers = default_stickers
        else:
            self.stickers = json.loads(stickers_config)
        
        # Dictionary to store active Blackjack games: user_id -> BlackjackGame instance
        self.blackjack_sessions: Dict[int, BlackjackGame] = {}
        
        # Dictionary to store active Mines games: user_id -> MinesGame instance
        self.mines_sessions: Dict[int, MinesGame] = {}
        
        # Dictionary to store active Keno games: user_id -> KenoGame instance
        self.keno_sessions: Dict[int, KenoGame] = {}
        
        # Dictionary to store active Limbo games: user_id -> LimboGame instance
        self.limbo_sessions: Dict[int, LimboGame] = {}
        
        # Dictionary to store active Hi-Lo games: user_id -> HiLoGame instance
        self.hilo_sessions: Dict[int, HiLoGame] = {}
        
        # Dictionary to store active Connect 4 games: game_id -> Connect4Game instance
        self.connect4_sessions: Dict[str, Connect4Game] = {}
        
        # Game timeout tracking: game_key -> (asyncio.Task, token)
        # game_key format: "type_user_id" (e.g., "blackjack_123456", "connect4_gameid", "pvp_gameid")
        self.game_timeout_tasks: Dict[str, tuple] = {}
        
        # Timeout token counter to prevent duplicate processing
        self.timeout_token_counter = 0
        
        # Timeout duration in seconds
        self.GAME_TIMEOUT_SECONDS = 30

    def user_has_active_game(self, user_id: int) -> bool:
        """Check if a user already has an active game (PvP, blackjack, mines, keno, or pending opponent selection)"""
        if user_id in self.blackjack_sessions:
            logger.info(f"[ACTIVE_GAME] User {user_id} has active blackjack session")
            return True
        
        if user_id in self.mines_sessions:
            logger.info(f"[ACTIVE_GAME] User {user_id} has active mines session")
            return True
        
        if user_id in self.keno_sessions:
            logger.info(f"[ACTIVE_GAME] User {user_id} has active keno session")
            return True
        
        if user_id in self.limbo_sessions:
            logger.info(f"[ACTIVE_GAME] User {user_id} has active limbo session")
            return True
        
        if user_id in self.hilo_sessions:
            logger.info(f"[ACTIVE_GAME] User {user_id} has active hilo session")
            return True
        
        for game_id, game in self.connect4_sessions.items():
            if user_id == game.player1_id or user_id == game.player2_id:
                logger.info(f"[ACTIVE_GAME] User {user_id} has active connect4 session: {game_id}")
                return True
        
        if user_id in self.pending_opponent_selection:
            logger.info(f"[ACTIVE_GAME] User {user_id} has pending opponent selection")
            return True
        
        for game_id, challenge in self.pending_pvp.items():
            challenger = challenge.get('challenger')
            opponent = challenge.get('opponent')
            player = challenge.get('player')
            if challenger == user_id or opponent == user_id or player == user_id:
                logger.info(f"[ACTIVE_GAME] User {user_id} has active game: {game_id}")
                return True
        return False

    def clear_user_game_state(self, user_id: int) -> list:
        """Clear all game states for a user. Returns list of cleared game types."""
        cleared = []
        
        if user_id in self.blackjack_sessions:
            del self.blackjack_sessions[user_id]
            cleared.append("blackjack")
        
        if user_id in self.mines_sessions:
            del self.mines_sessions[user_id]
            cleared.append("mines")
        
        if user_id in self.keno_sessions:
            del self.keno_sessions[user_id]
            cleared.append("keno")
        
        if user_id in self.limbo_sessions:
            del self.limbo_sessions[user_id]
            cleared.append("limbo")
        
        if user_id in self.hilo_sessions:
            del self.hilo_sessions[user_id]
            cleared.append("hilo")
        
        connect4_to_remove = []
        for game_id, game in self.connect4_sessions.items():
            if user_id == game.player1_id or user_id == game.player2_id:
                connect4_to_remove.append(game_id)
        for game_id in connect4_to_remove:
            del self.connect4_sessions[game_id]
            if "connect4" not in cleared:
                cleared.append("connect4")
        
        if user_id in self.pending_opponent_selection:
            self.pending_opponent_selection.discard(user_id)
            cleared.append("pending_selection")
        
        pvp_to_remove = []
        for game_id, challenge in self.pending_pvp.items():
            challenger = challenge.get('challenger')
            opponent = challenge.get('opponent')
            player = challenge.get('player')
            if challenger == user_id or opponent == user_id or player == user_id:
                pvp_to_remove.append(game_id)
        for game_id in pvp_to_remove:
            del self.pending_pvp[game_id]
            if "pvp" not in cleared:
                cleared.append("pvp")
        
        timeout_keys_to_cancel = [key for key in self.game_timeout_tasks if str(user_id) in key]
        for key in timeout_keys_to_cancel:
            self.cancel_game_timeout(key)
            cleared.append(f"timeout_{key}")
        
        return cleared

    async def resetgame_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset stuck game state for a user"""
        user_id = update.effective_user.id
        
        target_user_id = user_id
        if context.args and self.is_admin(user_id):
            try:
                target_user_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID")
                return
        
        cleared = self.clear_user_game_state(target_user_id)
        
        if cleared:
            if target_user_id == user_id:
                await update.message.reply_text(f"✅ Game state reset! Cleared: {', '.join(cleared)}\n\nYou can now start a new game.")
            else:
                await update.message.reply_text(f"✅ Reset game state for user {target_user_id}. Cleared: {', '.join(cleared)}")
            logger.info(f"[RESET] User {user_id} reset game state for {target_user_id}: {cleared}")
        else:
            await update.message.reply_text("ℹ️ No active games found to reset.")

    def get_active_game_type(self, user_id: int) -> str:
        """Get the type of active game for a user"""
        if user_id in self.blackjack_sessions:
            return "blackjack"
        if user_id in self.mines_sessions:
            return "mines"
        if user_id in self.keno_sessions:
            return "keno"
        if user_id in self.limbo_sessions:
            return "limbo"
        if user_id in self.hilo_sessions:
            return "hilo"
        for game_id, game in self.connect4_sessions.items():
            if user_id == game.player1_id or user_id == game.player2_id:
                return "connect4"
        if user_id in self.pending_opponent_selection:
            return "pvp"
        for game_id, challenge in self.pending_pvp.items():
            challenger = challenge.get('challenger')
            opponent = challenge.get('opponent')
            player = challenge.get('player')
            if challenger == user_id or opponent == user_id or player == user_id:
                return "pvp"
        return ""

    def start_game_timeout(self, game_key: str, game_type: str, user_id: int, chat_id: int, 
                           wager: float, is_pvp: bool = False, opponent_id: int = None,
                           game_id: str = None, bot = None):
        """Start a 30-second timeout for a game. If time expires, player forfeits."""
        self.cancel_game_timeout(game_key)
        
        self.timeout_token_counter += 1
        token = self.timeout_token_counter
        
        async def timeout_handler():
            try:
                await asyncio.sleep(self.GAME_TIMEOUT_SECONDS)
                await self.handle_game_timeout(game_key, game_type, user_id, chat_id, 
                                               wager, is_pvp, opponent_id, game_id, bot, token)
            except asyncio.CancelledError:
                pass
        
        task = asyncio.create_task(timeout_handler())
        self.game_timeout_tasks[game_key] = (task, token)
        logger.info(f"[TIMEOUT] Started {self.GAME_TIMEOUT_SECONDS}s timeout for {game_key} (token={token})")

    def cancel_game_timeout(self, game_key: str):
        """Cancel an existing timeout for a game."""
        if game_key in self.game_timeout_tasks:
            task, token = self.game_timeout_tasks[game_key]
            task.cancel()
            del self.game_timeout_tasks[game_key]
            logger.info(f"[TIMEOUT] Cancelled timeout for {game_key} (token={token})")

    def reset_game_timeout(self, game_key: str, game_type: str, user_id: int, chat_id: int,
                           wager: float, is_pvp: bool = False, opponent_id: int = None,
                           game_id: str = None, bot = None):
        """Reset (restart) the timeout for a game after a player makes a move."""
        self.start_game_timeout(game_key, game_type, user_id, chat_id, wager, 
                                is_pvp, opponent_id, game_id, bot)

    async def handle_game_timeout(self, game_key: str, game_type: str, user_id: int, 
                                   chat_id: int, wager: float, is_pvp: bool = False,
                                   opponent_id: int = None, game_id: str = None, bot = None,
                                   token: int = None):
        """Handle game timeout - forfeit wager to house, refund opponent in PvP."""
        logger.info(f"[TIMEOUT] Game timeout triggered for {game_key} (token={token})")
        
        if game_key in self.game_timeout_tasks:
            stored_task, stored_token = self.game_timeout_tasks[game_key]
            if token != stored_token:
                logger.info(f"[TIMEOUT] Ignoring stale timeout for {game_key} (token={token}, current={stored_token})")
                return
            del self.game_timeout_tasks[game_key]
        else:
            logger.info(f"[TIMEOUT] Ignoring timeout for {game_key} - already processed or cancelled")
            return
        
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
        if game_type == "blackjack":
            if user_id in self.blackjack_sessions:
                game = self.blackjack_sessions[user_id]
                total_bet = sum(h['bet'] for h in game.player_hands)
                self.db.update_house_balance(total_bet)
                del self.blackjack_sessions[user_id]
                
                self.db.add_transaction(user_id, "blackjack_timeout", -total_bet, 
                                        f"Blackjack timeout - Forfeited ${total_bet:.2f}")
                self.db.record_game({
                    "type": "blackjack",
                    "player_id": user_id,
                    "wager": total_bet,
                    "result": "timeout",
                    "outcome": "loss"
                })
                
                if bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ @{username} was inactive for 30 seconds and forfeited ${total_bet:.2f} to the house.",
                        parse_mode="Markdown"
                    )
        
        elif game_type == "hilo":
            if user_id in self.hilo_sessions:
                game = self.hilo_sessions[user_id]
                forfeit_amount = game.initial_wager
                self.db.update_house_balance(forfeit_amount)
                del self.hilo_sessions[user_id]
                
                self.db.add_transaction(user_id, "hilo_timeout", -forfeit_amount,
                                        f"Hi-Lo timeout - Forfeited ${forfeit_amount:.2f}")
                
                self.db.record_game({
                    'type': 'hilo',
                    'player_id': user_id,
                    'username': username,
                    'wager': forfeit_amount,
                    'rounds': game.round_number,
                    'result': 'timeout',
                    'outcome': 'loss',
                    'payout': 0,
                    'balance_after': user_data['balance']
                })
                
                if bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ @{username} was inactive for 30 seconds and forfeited ${forfeit_amount:.2f} to the house.",
                        parse_mode="Markdown"
                    )
        
        elif game_type == "mines":
            if user_id in self.mines_sessions:
                game = self.mines_sessions[user_id]
                revealed_count = len(game.revealed_tiles)
                
                if revealed_count > 0:
                    cashout_amount = game.get_potential_payout()
                    user_data_mines = self.db.get_user(user_id)
                    user_data_mines['balance'] += cashout_amount
                    profit = cashout_amount - game.wager
                    user_data_mines['total_wagered'] += game.wager
                    user_data_mines['games_played'] += 1
                    if profit > 0:
                        user_data_mines['games_won'] += 1
                        user_data_mines['total_pnl'] += profit
                        self.db.update_house_balance(-profit)
                    else:
                        user_data_mines['total_pnl'] += profit
                        self.db.update_house_balance(-profit)
                    self.db.update_user(user_id, user_data_mines)
                    del self.mines_sessions[user_id]
                    
                    self.db.add_transaction(user_id, "mines_timeout_cashout", cashout_amount,
                                            f"Mines timeout - Auto cashout ${cashout_amount:.2f}")
                    
                    self.db.record_game({
                        'type': 'mines',
                        'player_id': user_id,
                        'username': username,
                        'wager': game.wager,
                        'num_mines': game.num_mines,
                        'tiles_revealed': revealed_count,
                        'multiplier': game.current_multiplier,
                        'payout': cashout_amount,
                        'result': 'win' if profit > 0 else 'loss',
                        'balance_after': user_data_mines['balance']
                    })
                    
                    if bot:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"@{username} timed out - won ${cashout_amount:.2f}",
                            parse_mode="Markdown"
                        )
                else:
                    forfeit_amount = game.wager
                    self.db.update_house_balance(forfeit_amount)
                    del self.mines_sessions[user_id]
                    
                    self.db.add_transaction(user_id, "mines_timeout", -forfeit_amount,
                                            f"Mines timeout - Forfeited ${forfeit_amount:.2f}")
                    
                    self.db.record_game({
                        'type': 'mines',
                        'player_id': user_id,
                        'username': username,
                        'wager': forfeit_amount,
                        'num_mines': game.num_mines,
                        'tiles_revealed': 0,
                        'multiplier': 1.0,
                        'payout': 0,
                        'result': 'timeout',
                        'outcome': 'loss',
                        'balance_after': user_data['balance']
                    })
                    
                    if bot:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"⏰ @{username} was inactive for 30 seconds and forfeited ${forfeit_amount:.2f} to the house.",
                            parse_mode="Markdown"
                        )
        
        elif game_type == "keno":
            if user_id in self.keno_sessions:
                game = self.keno_sessions[user_id]
                forfeit_amount = game.wager
                self.db.update_house_balance(forfeit_amount)
                del self.keno_sessions[user_id]
                
                self.db.add_transaction(user_id, "keno_timeout", -forfeit_amount,
                                        f"Keno timeout - Forfeited ${forfeit_amount:.2f}")
                
                self.db.record_game({
                    'type': 'keno',
                    'player_id': user_id,
                    'username': username,
                    'wager': forfeit_amount,
                    'picks': list(game.picked_numbers),
                    'drawn': [],
                    'hits': 0,
                    'multiplier': 0,
                    'payout': 0,
                    'result': 'timeout',
                    'outcome': 'loss',
                    'balance_after': user_data['balance']
                })
                
                if bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ @{username} was inactive for 30 seconds and forfeited ${forfeit_amount:.2f} to the house.",
                        parse_mode="Markdown"
                    )
        
        elif game_type == "connect4":
            if game_id and game_id in self.connect4_sessions:
                game = self.connect4_sessions[game_id]
                p1_data = self.db.get_user(game.player1_id)
                p2_data = self.db.get_user(game.player2_id)
                p1_username = p1_data.get('username', 'Player 1')
                p2_username = p2_data.get('username', 'Player 2')
                
                inactive_id = user_id
                active_id = game.player2_id if inactive_id == game.player1_id else game.player1_id
                active_username = p2_username if inactive_id == game.player1_id else p1_username
                inactive_username = p1_username if inactive_id == game.player1_id else p2_username
                
                active_data = self.db.get_user(active_id)
                active_data['balance'] += game.wager
                self.db.update_user(active_id, {'balance': active_data['balance']})
                
                self.db.update_house_balance(game.wager)
                
                self.db.add_transaction(inactive_id, "connect4_timeout", -game.wager,
                                        f"Connect 4 timeout - Forfeited ${game.wager:.2f}")
                self.db.add_transaction(active_id, "connect4_refund", game.wager,
                                        f"Connect 4 refund - Opponent timed out")
                
                inactive_data = self.db.get_user(inactive_id)
                self.db.record_game({
                    'type': 'connect4',
                    'player1_id': game.player1_id,
                    'player2_id': game.player2_id,
                    'winner_id': active_id,
                    'loser_id': inactive_id,
                    'wager': game.wager,
                    'result': 'timeout',
                    'winner_payout': game.wager,
                    'loser_loss': game.wager,
                    'balance_after_winner': active_data['balance'],
                    'balance_after_loser': inactive_data['balance']
                })
                
                del self.connect4_sessions[game_id]
                
                if bot:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"⏰ @{inactive_username} was inactive for 30 seconds and forfeited ${game.wager:.2f} to the house. @{active_username} was refunded ${game.wager:.2f}.",
                        parse_mode="Markdown"
                    )
        
        elif game_type == "pvp" or game_type.endswith("_pvp"):
            if game_id and game_id in self.pending_pvp:
                challenge = self.pending_pvp[game_id]
                challenger_id = challenge.get('challenger')
                opponent_id_pvp = challenge.get('opponent')
                pvp_wager = challenge.get('wager', wager)
                
                inactive_id = user_id
                
                if opponent_id_pvp and challenger_id:
                    active_id = opponent_id_pvp if inactive_id == challenger_id else challenger_id
                    active_data = self.db.get_user(active_id)
                    inactive_data = self.db.get_user(inactive_id)
                    active_username = active_data.get('username', f'User{active_id}')
                    inactive_username = inactive_data.get('username', f'User{inactive_id}')
                    
                    active_data['balance'] += pvp_wager
                    self.db.update_user(active_id, {'balance': active_data['balance']})
                    
                    self.db.update_house_balance(pvp_wager)
                    
                    self.db.add_transaction(inactive_id, "pvp_timeout", -pvp_wager,
                                            f"PvP timeout - Forfeited ${pvp_wager:.2f}")
                    self.db.add_transaction(active_id, "pvp_refund", pvp_wager,
                                            f"PvP refund - Opponent timed out")
                    
                    del self.pending_pvp[game_id]
                    self.db.data['pending_pvp'] = self.pending_pvp
                    self.db.save_data()
                    
                    if bot:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"⏰ @{inactive_username} was inactive for 30 seconds and forfeited ${pvp_wager:.2f} to the house. @{active_username} was refunded ${pvp_wager:.2f}.",
                            parse_mode="Markdown"
                        )
                else:
                    player_id = challenge.get('player')
                    if player_id:
                        self.db.update_house_balance(pvp_wager)
                        
                        self.db.add_transaction(player_id, "game_timeout", -pvp_wager,
                                                f"Game timeout - Forfeited ${pvp_wager:.2f}")
                        
                        del self.pending_pvp[game_id]
                        self.db.data['pending_pvp'] = self.pending_pvp
                        self.db.save_data()
                        
                        player_data = self.db.get_user(player_id)
                        player_username = player_data.get('username', f'User{player_id}')
                        
                        if bot:
                            await bot.send_message(
                                chat_id=chat_id,
                                text=f"⏰ @{player_username} was inactive for 30 seconds and forfeited ${pvp_wager:.2f} to the house.",
                                parse_mode="Markdown"
                            )

    def setup_handlers(self):
        """Setup all command and callback handlers - Emoji games only"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("bal", self.balance_command))
        
        # Emoji games only
        self.app.add_handler(CommandHandler("dice", self.dice_command))
        self.app.add_handler(CommandHandler("darts", self.darts_command))
        self.app.add_handler(CommandHandler("basketball", self.basketball_command))
        self.app.add_handler(CommandHandler("bball", self.basketball_command))
        self.app.add_handler(CommandHandler("soccer", self.soccer_command))
        self.app.add_handler(CommandHandler("football", self.soccer_command))
        self.app.add_handler(CommandHandler("bowling", self.bowling_command))
        self.app.add_handler(CommandHandler("predict", self.predict_command))
        
        # Emoji response handler for game results
        self.app.add_handler(MessageHandler(filters.Dice.ALL, self.handle_emoji_response))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_input))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def creditdeposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to manually credit a deposit."""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin only command.")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "Usage: `/creditdeposit <user_id> <ltc_amount> <tx_id>`\n"
                "Example: `/creditdeposit 123456789 0.05 abc123def456`",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
            ltc_amount = float(context.args[1])
            tx_id = context.args[2]
        except ValueError:
            await update.message.reply_text("❌ Invalid user_id or amount.")
            return
        
        if 'processed_deposits' not in self.db.data:
            self.db.data['processed_deposits'] = []
        
        if tx_id in self.db.data['processed_deposits']:
            await update.message.reply_text("❌ This transaction has already been processed.")
            return
        
        target_data = self.db.get_user(target_user_id)
        deposit_fee = 0.01  # 1% deposit fee (not shown to user)
        credited_amount = round(ltc_amount * (1 - deposit_fee), 2)
        
        target_data['balance'] += credited_amount
        self.db.update_user(target_user_id, target_data)
        
        self.db.add_transaction(target_user_id, "deposit", credited_amount, f"LTC Deposit (Manual) - TX: {tx_id[:16]}...")
        self.db.record_deposit(target_user_id, target_data.get('username', f'User{target_user_id}'), credited_amount, ltc_amount, tx_id)
        
        self.db.data['processed_deposits'].append(tx_id)
        if 'deposit_history' not in self.db.data:
            self.db.data['deposit_history'] = []
        self.db.data['deposit_history'].append({
            'tx_id': tx_id,
            'user_id': target_user_id,
            'ltc_amount': ltc_amount,
            'usd_amount': credited_amount,
            'timestamp': datetime.now().isoformat()
        })
        self.db.save_data()
        
        try:
            await self.app.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ **Deposit Confirmed!**\n\n"
                     f"Amount: **${ltc_amount:.2f}**\n\n"
                     f"New Balance: ${target_data['balance']:.2f}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id} of deposit: {e}")
        
        await update.message.reply_text(
            f"✅ Credited ${credited_amount:.2f} to user {target_user_id}\n"
            f"TX: {tx_id}"
        )

    async def check_expired_challenges(self, context: ContextTypes.DEFAULT_TYPE):
        """Check for challenges older than 30 seconds and handle refunds/forfeits"""
        try:
            current_time = datetime.now()
            expired_challenges = []
            
            for challenge_id, challenge in list(self.pending_pvp.items()):
                chat_id = challenge.get('chat_id')
                wager = challenge.get('wager', 0)
                
                # Case 1: Unaccepted challenges - refund challenger
                if 'created_at' in challenge and challenge.get('opponent') is None:
                    created_at = datetime.fromisoformat(challenge['created_at'])
                    time_diff = (current_time - created_at).total_seconds()
                    
                    if time_diff > 30:
                        expired_challenges.append(challenge_id)
                        
                        # Refund the challenger
                        challenger_id = challenge['challenger']
                        challenger_data = self.db.get_user(challenger_id)
                        
                        self.db.update_user(challenger_id, {
                            'balance': challenger_data['balance'] + wager
                        })
                        
                        if chat_id:
                            try:
                                await self.app.bot.send_message(
                                    chat_id=chat_id,
                                    text=f"⏰ Challenge expired after 30 seconds. ${wager:.2f} has been refunded to @{challenger_data['username']}.",
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                logger.error(f"Failed to send expiration message: {e}")
                
                # Case 2: Waiting for challenger emoji - challenger forfeits, acceptor gets refund
                elif challenge.get('waiting_for_challenger_emoji') and 'emoji_wait_started' in challenge:
                    wait_started = datetime.fromisoformat(challenge['emoji_wait_started'])
                    time_diff = (current_time - wait_started).total_seconds()
                    
                    if time_diff > 30:
                        expired_challenges.append(challenge_id)
                        
                        challenger_id = challenge['challenger']
                        acceptor_id = challenge['opponent']
                        challenger_data = self.db.get_user(challenger_id)
                        acceptor_data = self.db.get_user(acceptor_id)
                        
                        # Challenger forfeits to house
                        self.db.update_house_balance(wager)
                        
                        # Acceptor gets refunded
                        self.db.update_user(acceptor_id, {
                            'balance': acceptor_data['balance'] + wager
                        })
                        
                        if chat_id:
                            try:
                                await self.app.bot.send_message(
                                    chat_id=chat_id,
                                    text=f"⏰ @{challenger_data['username']} was inactive for 30 seconds and forfeited ${wager:.2f} to the house. @{acceptor_data['username']} was refunded ${wager:.2f}.",
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                logger.error(f"Failed to send forfeit message: {e}")
                
                # Case 3: Waiting for opponent/player emoji - opponent forfeits, challenger/bot gets paid
                elif challenge.get('waiting_for_emoji') and 'emoji_wait_started' in challenge:
                    wait_started = datetime.fromisoformat(challenge['emoji_wait_started'])
                    time_diff = (current_time - wait_started).total_seconds()
                    
                    if time_diff > 30:
                        expired_challenges.append(challenge_id)
                        
                        # Check if PvP or bot vs player
                        if challenge.get('opponent'):
                            # PvP case: opponent forfeits, challenger gets refund
                            challenger_id = challenge['challenger']
                            opponent_id = challenge['opponent']
                            challenger_data = self.db.get_user(challenger_id)
                            opponent_data = self.db.get_user(opponent_id)
                            
                            # Opponent forfeits to house
                            self.db.update_house_balance(wager)
                            
                            # Challenger gets refunded
                            self.db.update_user(challenger_id, {
                                'balance': challenger_data['balance'] + wager
                            })
                            
                            if chat_id:
                                try:
                                    await self.app.bot.send_message(
                                        chat_id=chat_id,
                                        text=f"⏰ @{opponent_data['username']} was inactive for 30 seconds and forfeited ${wager:.2f} to the house. @{challenger_data['username']} was refunded ${wager:.2f}.",
                                        parse_mode="Markdown"
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send forfeit message: {e}")
                        
                        elif challenge.get('player'):
                            # Bot vs player: player forfeits, house keeps money
                            player_id = challenge['player']
                            player_data = self.db.get_user(player_id)
                            
                            # Player forfeits to house (money already taken)
                            self.db.update_house_balance(wager)
                            
                            if chat_id:
                                try:
                                    await self.app.bot.send_message(
                                        chat_id=chat_id,
                                        text=f"⏰ @{player_data['username']} was inactive for 30 seconds and forfeited ${wager:.2f} to the house.",
                                        parse_mode="Markdown"
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to send forfeit message: {e}")
            
            # Remove expired challenges
            for challenge_id in expired_challenges:
                del self.pending_pvp[challenge_id]
            
            if expired_challenges:
                self.db.data['pending_pvp'] = self.pending_pvp
                self.db.save_data()
                logger.info(f"Expired/forfeited {len(expired_challenges)} challenge(s)")
                
        except Exception as e:
            logger.error(f"Error checking expired challenges: {e}")
    
    # --- COMMAND HANDLERS ---
    
    def ensure_user_registered(self, update: Update) -> Dict[str, Any]:
        """Ensure user exists and has username set"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        # Update username if it has changed or is not set
        if user.username and user_data.get("username") != user.username:
            self.db.update_user(user.id, {"username": user.username, "user_id": user.id})
            user_data = self.db.get_user(user.id)
        
        return user_data
    
    async def send_with_buttons(self, chat_id: int, text: str, keyboard: InlineKeyboardMarkup, user_id: int, parse_mode: str = "Markdown"):
        """Send a message with buttons and register ownership"""
        sent_message = await self.app.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        self.button_ownership[(chat_id, sent_message.message_id)] = user_id
        return sent_message
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin (environment or dynamic)"""
        return user_id in self.env_admin_ids or user_id in self.dynamic_admin_ids
    
    def can_approve_withdrawals(self, user_id: int) -> bool:
        """Check if a user can approve/deny withdrawals (admin or withdrawal approver)"""
        return self.is_admin(user_id) or user_id in self.withdrawal_approvers
    
    def find_user_by_username_or_id(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find a user by username (@username) or user ID"""
        # Remove @ if present
        if identifier.startswith('@'):
            username = identifier[1:]
            # Search by username
            for user_data in self.db.data['users'].values():
                if user_data.get('username', '').lower() == username.lower():
                    return user_data
            return None
        else:
            # Try to parse as user ID
            try:
                user_id = int(identifier)
                return self.db.get_user(user_id)
            except ValueError:
                return None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome message and initial user setup."""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        # Update username if it has changed
        if user_data.get("username") != user.username:
            # Only update if the user has a public username set
            if user.username:
                self.db.update_user(user.id, {"username": user.username})
            user_data = self.db.get_user(user.id) # Reload data if updated
        
        # Handle deep links from web app (e.g., /start deposit -> dispatch to deposit command)
        if context.args and len(context.args) > 0:
            deep_link_param = context.args[0].lower()
            command_mapping = {
                'deposit': self.deposit_command,
                'withdraw': self.withdraw_command,
                'profile': self.balance_command,
                'leaderboard': self.leaderboard_command,
                'history': self.history_command,
                'admin': self.admin_command,
                'stats': self.stats_command,
                'pending': self.pending_withdraws_command,
                'menu': self.menu_command,
                'support': self.menu_command,
            }
            if deep_link_param in command_mapping:
                # Clear context.args so handlers don't misinterpret them
                context.args = []
                await command_mapping[deep_link_param](update, context)
                return
        
        welcome_text = """🎰 **Gran Tesero Casino**

Hey there! Ready to play?

**Getting Started:**
1. Deposit funds using the button below
2. Pick a game and place your wager
3. Win big and withdraw anytime!

**Available Games:**
🎲 Dice - /dice
🎯 Darts - /darts
🏀 Basketball - /basketball
⚽ Soccer - /soccer
🎳 Bowling - /bowling
🪙 Coinflip - /flip
🔮 Prediction - /predict
🎡 Roulette - /roulette
🎰 Slots - /slots
♠️ Blackjack - /blackjack
💣 Mines - /mines
🃏 Baccarat - /baccarat
🎱 Keno - /keno
🚀 Limbo - /limbo
📈 Hi-Lo - /hilo
🔴 Connect 4 - /connect

📋 /menu - Open the main menu

Good luck! 🍀"""
        
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
        
        balance_text = f"🏦 **Menu**\n\n💰 Balance: **${user_data['balance']:.2f}**"
        
        webapp_url = os.getenv("WEBHOOK_URL", "")
        
        keyboard = [
            [InlineKeyboardButton("🎮 Open Casino App", web_app=WebAppInfo(url=webapp_url))] if webapp_url else [],
            [InlineKeyboardButton("🎮 Play (Bot Version)", callback_data="menu_play")],
            [InlineKeyboardButton("💳 Deposit", callback_data="deposit_mock"),
             InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_mock")],
            [InlineKeyboardButton("🎁 Bonuses", callback_data="menu_bonuses"),
             InlineKeyboardButton("📚 More Content", callback_data="menu_more_content")],
            [InlineKeyboardButton("⚙️ Commands", callback_data="menu_commands"),
             InlineKeyboardButton("📞 Support", callback_data="menu_support")]
        ]
        # Filter out empty rows if webapp_url is missing
        keyboard = [row for row in keyboard if row]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user.id
    
    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show the main menu"""
        user = update.effective_user
        if update.effective_chat.type != "private" and not self.is_admin(user.id):
            await update.message.reply_text("❌ Use /menu in DMs only.")
            return
        user_data = self.ensure_user_registered(update)
        
        menu_text = f"🏦 **Menu**\n\n💰 Balance: **${user_data['balance']:.2f}**"
        
        webapp_url = os.getenv("WEBHOOK_URL", "")
        
        keyboard = [
            [InlineKeyboardButton("🎮 Open Casino App", web_app=WebAppInfo(url=webapp_url))] if webapp_url else [],
            [InlineKeyboardButton("🎮 Play (Bot Version)", callback_data="menu_play")],
            [InlineKeyboardButton("💳 Deposit", callback_data="deposit_mock"),
             InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_mock")],
            [InlineKeyboardButton("🎁 Bonuses", callback_data="menu_bonuses"),
             InlineKeyboardButton("📚 More Content", callback_data="menu_more_content")],
            [InlineKeyboardButton("⚙️ Commands", callback_data="menu_commands"),
             InlineKeyboardButton("📞 Support", callback_data="menu_support")]
        ]
        # Filter out empty rows if webapp_url is missing
        keyboard = [row for row in keyboard if row]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user.id
    
    async def adminhelp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all admin commands - admin only"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for admins only.")
            return
        
        admin_help_text = """🔐 **Admin Commands**

**General:**
/admin - Open admin panel
/adminhelp - Show this help message

**User Management:**
/userid @user - Get user's ID
/userinfo @user - View user details
/setbal <user_id> <amount> - Set user balance
/givebal @user <amount> - Give balance to user
/allusers - List all users
/allbalances - Show all user balances

**Admin Management:**
/addadmin <user_id> - Add a new admin
/removeadmin <user_id> - Remove an admin
/listadmins - List all admins
/addapprover <user_id> - Add a withdrawal approver
/removeapprover <user_id> - Remove an approver
/listapprovers - List all approvers

**Financial:**
/housebal - View house balance
/sethousebal <amount> - Set house balance
/walletbal - View wallet balance
/pendingdeposits - View pending deposits
/pendingwithdraws - View pending withdrawals
/biggestdeposits - View largest deposits

**LTC Rate:**
/ltcrate - View current LTC rate
/setltcrate <price> - Set manual LTC/USD rate

**System:**
/backup - Create database backup

**Stickers:**
/savesticker - Save a sticker
/stickers - List saved stickers
/saveroulette - Save roulette stickers
"""
        await update.message.reply_text(admin_help_text, parse_mode="Markdown")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show balance as text only"""
        user_data = self.ensure_user_registered(update)
        
        balance_text = f"💰 Balance: **${user_data['balance']:.2f}**"
        
        await update.message.reply_text(balance_text, parse_mode="Markdown")
    
    async def bonus_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bonus status with rakeback and level up options"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        # Build bonus text matching the new design
        bonus_text = "🎁 **Bonus**\n\n"
        bonus_text += "In this section you can find bonuses that you can get by playing games!\n\n"
        bonus_text += "💎 **Rakeback**\n"
        bonus_text += "Play games and claim your rakeback bonus anytime!\n\n"
        bonus_text += "💎 **Level Up Bonus**\n"
        bonus_text += "Play games, level up and earn money!"
        
        # Build keyboard with two buttons side by side, then back button
        keyboard = [
            [
                InlineKeyboardButton("🎁 Rakeback", callback_data="view_rakeback"),
                InlineKeyboardButton("🎁 Level Up Bonus", callback_data="view_level_bonus")
            ],
            [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(bonus_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show player statistics"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        username = update.effective_user.username or f"User{user_id}"
        
        balance = user_data.get('balance', 0)
        games_played = user_data.get('games_played', 0)
        games_won = user_data.get('games_won', 0)
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        total_wagered = user_data.get('total_wagered', 0)
        total_pnl = user_data.get('total_pnl', 0)
        total_won = total_wagered + total_pnl if total_pnl > 0 else total_wagered
        
        current_level = get_user_level(total_wagered, user_id, self.db)
        
        stats_text = f"""ℹ️ Stats of {username}

💰 Balance: ${balance:.2f}

Level: {current_level['emoji']} {current_level['name']}
Games Played: {games_played}
Wins: {games_won} ({win_rate:.2f}%)
Total Wagered: ${total_wagered:,.2f}
Total Won: ${total_won:,.2f}"""
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
    
    async def levels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show levels with tier navigation"""
        user_id = update.effective_user.id
        user_data = self.ensure_user_registered(update)
        total_wagered = user_data.get('total_wagered', 0)
        current_level = get_user_level(total_wagered, user_id, self.db)
        
        current_tier_name = current_level.get('tier_name', 'Bronze')
        if current_tier_name == 'Unranked':
            current_tier_name = 'Bronze'
        
        tier_index = get_tier_index(current_tier_name)
        
        levels_text, keyboard = self.build_tier_display(tier_index, total_wagered, user_id)
        
        sent_msg = await update.message.reply_text(levels_text, reply_markup=keyboard, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    def build_tier_display(self, tier_index: int, total_wagered: float, user_id: Optional[int] = None):
        """Build the display for a specific tier with navigation buttons."""
        tier_index = max(0, min(tier_index, len(LEVEL_TIERS) - 1))
        tier = LEVEL_TIERS[tier_index]
        current_level = get_user_level(total_wagered, user_id, self.db) if user_id else get_user_level(total_wagered)
        
        levels_text = f"{tier['emoji']} **{tier['name']} Prestige** ({tier_index + 1}/{len(LEVEL_TIERS)})\n\n"
        
        for level in tier["levels"]:
            level_id = level["id"]
            is_current = level_id == current_level['id']
            
            level_from_flat = None
            for l in LEVELS:
                if l['id'] == level_id:
                    level_from_flat = l
                    break
            
            if level_from_flat:
                is_reached = total_wagered >= level_from_flat['threshold']
            else:
                is_reached = False
            
            threshold = level["threshold"]
            bonus = level["bonus"]
            
            bonus_text = f"${bonus:,.2f}" if bonus != int(bonus) else f"${int(bonus)}"
            
            status_icon = "✅" if is_reached else "🔒"
            current_marker = " ⭐" if is_current else ""
            
            levels_text += f"{status_icon} **{level['name']}**{current_marker}\n"
            levels_text += f"Wager: ${threshold:,} | Bonus: {bonus_text}\n\n"
        
        keyboard = []
        nav_buttons = []
        
        if tier_index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"levels_tier_{tier_index - 1}"))
        
        if tier_index < len(LEVEL_TIERS) - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"levels_tier_{tier_index + 1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("🎁 Claim Bonus", callback_data="view_level_bonus")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
        
        return levels_text, InlineKeyboardMarkup(keyboard)
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show leaderboard - most wagered all time"""
        await self.show_leaderboard_wagered(update, back_to="back_to_menu")

    async def show_leaderboard_wagered(self, update: Update, back_to: str = "back_to_menu"):
        """Display the most wagered all time leaderboard"""
        leaderboard = self.db.get_leaderboard()[:10]

        leaderboard_text = "🏆 **Leaderboard**\n\nMost Wagered all time:\n\n"

        if not leaderboard:
            leaderboard_text += "No players yet"
        else:
            for idx, player in enumerate(leaderboard, start=1):
                user_id = player.get('user_id')
                total_wagered = player.get('total_wagered', 0)
                level = get_user_level(total_wagered)
                level_emoji = level.get('emoji', '⚪')
                username = player.get('username', 'Unknown')
                leaderboard_text += f"{idx}) {level_emoji} {username} - ${total_wagered:,.2f}\n"

        keyboard = [
            [
                InlineKeyboardButton("Wagered", callback_data=f"lb_wagered_{back_to}"),
                InlineKeyboardButton("Dices Week", callback_data=f"lb_dices_week_{back_to}"),
                InlineKeyboardButton("Dices All", callback_data=f"lb_dices_all_{back_to}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                leaderboard_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                leaderboard_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

    async def show_leaderboard_dices(self, update: Update, time_filter: str, back_to: str = "back_to_menu"):
        """Display biggest dices leaderboard"""
        dices = self.db.get_biggest_dices(time_filter)

        if time_filter == "week":
            title = "Biggest Dices this week:"
        else:
            title = "Biggest Dices all time:"

        leaderboard_text = f"🏆 **Leaderboard**\n\n{title}\n\n"

        if not dices:
            leaderboard_text += "No dice games yet"
        else:
            for idx, dice in enumerate(dices[:5], start=1):
                winner_id = dice.get('winner_id')
                loser_id = dice.get('loser_id')
                winner_username = dice.get('winner_username', 'Unknown')
                loser_username = dice.get('loser_username', 'Unknown')
                amount = dice.get('amount', 0)
                wager = amount / 2
                game_mode = dice.get('game_mode', 'pvp')

                winner_user = self.db.get_user(winner_id) if winner_id else {}
                winner_level = get_user_level(winner_user.get('total_wagered', 0))
                winner_emoji = winner_level.get('emoji', '⚪')

                if loser_id and loser_id != 0:
                    loser_user = self.db.get_user(loser_id)
                    loser_level = get_user_level(loser_user.get('total_wagered', 0))
                    loser_emoji = loser_level.get('emoji', '⚪')
                    leaderboard_text += f"{idx}) {winner_emoji} {winner_username} vs {loser_emoji} {loser_username} • ${wager:,.2f}\n"
                else:
                    leaderboard_text += f"{idx}) {winner_emoji} {winner_username} vs 🤖 Bot • ${wager:,.2f}\n"

        keyboard = [
            [
                InlineKeyboardButton("Wagered", callback_data=f"lb_wagered_{back_to}"),
                InlineKeyboardButton("Dices Week", callback_data=f"lb_dices_week_{back_to}"),
                InlineKeyboardButton("Dices All", callback_data=f"lb_dices_all_{back_to}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            leaderboard_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    
    
    async def get_plisio_wallet_balance(self, currency: str = 'LTC') -> Optional[dict]:
        """Fetch the wallet balance for a specific currency from Plisio API. Returns dict with 'balance' and 'usd_balance'."""
        plisio_api_key = os.getenv("PLISIO_API_KEY")
        if not plisio_api_key:
            logger.warning("PLISIO_API_KEY not set")
            return None
        
        try:
            url = f"https://api.plisio.net/api/v1/balances/{currency}?api_key={plisio_api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('status') == 'success':
                            data = result.get('data', {})
                            balance_str = data.get('balance', '0')
                            usd_balance_str = data.get('balance_usd', '0')
                            return {
                                'balance': float(balance_str),
                                'usd_balance': float(usd_balance_str),
                                'currency': currency
                            }
                        else:
                            logger.error(f"Plisio balance API error for {currency}: {result}")
                    else:
                        logger.error(f"Plisio balance API HTTP error for {currency}: {response.status}")
        except Exception as e:
            logger.error(f"Failed to fetch Plisio balance for {currency}: {e}")
        return None
    
    async def get_all_wallet_balances(self) -> Dict[str, dict]:
        """Fetch all crypto wallet balances from Plisio API."""
        balances = {}
        for currency in SUPPORTED_DEPOSIT_CRYPTOS.keys():
            balance_data = await self.get_plisio_wallet_balance(currency)
            if balance_data:
                balances[currency] = balance_data
        return balances

    async def housebal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show house balance"""
        house_balance = self.db.get_house_balance()
        await update.message.reply_text(f"🏦 House: ${house_balance:.2f}")

    async def walletbal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show crypto wallet balances (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        await update.message.reply_text("⏳ Fetching wallet balances...")
        
        balances = await self.get_all_wallet_balances()
        
        total_usd = 0.0
        balance_lines = []
        
        if balances:
            for currency, data in balances.items():
                crypto_info = SUPPORTED_DEPOSIT_CRYPTOS.get(currency, {})
                emoji = crypto_info.get('emoji', '💰')
                balance = data['balance']
                usd_balance = data['usd_balance']
                total_usd += usd_balance
                if balance > 0:
                    balance_lines.append(f"{emoji} {currency}: {balance:.8f} (${usd_balance:.2f})")
            
            wallet_text = f"""🔐 Crypto Wallet Balances

💰 Total Balance: ${total_usd:.2f} USD

━━━━━━━━━━━━━━━━━━━━

"""
            if balance_lines:
                wallet_text += "\n".join(balance_lines)
            else:
                wallet_text += "No balances found"
        else:
            wallet_text = """🔐 Crypto Wallet Balances

⚠️ Unable to fetch wallet balances
(Check PLISIO_API_KEY)"""
        
        await update.message.reply_text(wallet_text)

    async def biggestdeposits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show biggest deposits leaderboard (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        weekly_deposits = self.db.get_biggest_deposits("week")
        alltime_deposits = self.db.get_biggest_deposits("all")
        
        text = "💰 **Biggest Deposits**\n\n"
        
        text += "📅 **This Week:**\n"
        if weekly_deposits:
            for i, dep in enumerate(weekly_deposits[:10], 1):
                username = dep.get('username', f"User{dep['user_id']}")
                amount = dep.get('amount', 0)
                text += f"{i}. @{username} - ${amount:.2f}\n"
        else:
            text += "No deposits this week\n"
        
        text += "\n🏆 **All Time:**\n"
        if alltime_deposits:
            for i, dep in enumerate(alltime_deposits[:10], 1):
                username = dep.get('username', f"User{dep['user_id']}")
                amount = dep.get('amount', 0)
                text += f"{i}. @{username} - ${amount:.2f}\n"
        else:
            text += "No deposits recorded\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def userid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user their Telegram ID"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "N/A"
        await update.message.reply_text(
            f"🆔 **Your User ID:** `{user_id}`\n"
            f"👤 **Username:** @{username}",
            parse_mode="Markdown"
        )
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show match history with pagination"""
        user_id = update.effective_user.id
        await self._show_history_page(update.message, user_id, 0)
    
    async def _show_history_page(self, message, user_id: int, page: int, edit_message=False, show_back=False):
        """Display a page of history with 7 games per page."""
        games_per_page = 7
        
        user_data = self.db.get_user(user_id)
        current_balance = user_data.get('balance', 0.0)
        
        user_games = [
            game for game in self.db.data.get('games', [])
            if game.get('player_id') == user_id or 
               game.get('challenger') == user_id or 
               game.get('opponent') == user_id
        ]
        
        user_games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        total_games = len(user_games)
        total_pages = max(1, (total_games + games_per_page - 1) // games_per_page)
        
        start_idx = page * games_per_page
        end_idx = min(start_idx + games_per_page, total_games)
        page_games = user_games[start_idx:end_idx]
        
        if not page_games:
            if edit_message:
                await message.edit_text("📜 No history yet")
            else:
                await message.reply_text("📜 No history yet")
            return
        
        history_text = f"🎮 **History** (Page {page + 1}/{total_pages})\n\n"
        
        for game in page_games:
            game_type = game.get('type', 'unknown')
            timestamp = game.get('timestamp', '')
            
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
            else:
                time_str = "Unknown"
            
            result = game.get('result', game.get('outcome', 'unknown'))
            wager = game.get('wager', 0)
            
            balance_after = game.get('balance_after')
            if balance_after is None:
                if game.get('challenger') == user_id:
                    balance_after = game.get('challenger_balance_after')
                elif game.get('opponent') == user_id:
                    balance_after = game.get('opponent_balance_after')
            balance_str = f" | Bal: ${balance_after:.2f}" if balance_after is not None else ""
            
            if game_type == 'mines':
                result_emoji = "✅" if result == "win" else "❌"
                num_mines = game.get('num_mines', '?')
                tiles_revealed = game.get('tiles_revealed', 0)
                payout = game.get('payout', 0)
                multiplier = game.get('multiplier', 1.0)
                history_text += f"{result_emoji} **Mines** - ${wager:.2f}\n"
                if result == "win":
                    history_text += f"   {num_mines} mines | {tiles_revealed} revealed | {multiplier:.2f}x | Won ${payout:.2f} | {time_str}{balance_str}\n\n"
                else:
                    history_text += f"   {num_mines} mines | {tiles_revealed} revealed | {time_str}{balance_str}\n\n"
            elif 'bot' in game_type or game_type in ['roulette', 'blackjack', 'baccarat', 'dice_predict', 'slots', 'slots_bot']:
                result_emoji = "✅" if result == "win" else "❌" if result == "loss" else "🤝"
                
                if game_type == 'dice_bot':
                    player_roll = game.get('player_roll', 0)
                    bot_roll = game.get('bot_roll', 0)
                    history_text += f"{result_emoji} **Dice vs Bot** - ${wager:.2f}\n"
                    history_text += f"   You: {player_roll} | Bot: {bot_roll} | {time_str}{balance_str}\n\n"
                elif game_type == 'coinflip_bot':
                    choice = game.get('choice', 'unknown')
                    flip_result = game.get('result', 'unknown')
                    history_text += f"{result_emoji} **CoinFlip** - ${wager:.2f}\n"
                    history_text += f"   Chose: {choice.capitalize()} | Landed: {flip_result.capitalize()} | {time_str}{balance_str}\n\n"
                elif game_type == 'roulette':
                    bet_choice = game.get('choice', '?')
                    landed = game.get('result', '?')
                    history_text += f"{result_emoji} **Roulette** - ${wager:.2f}\n"
                    history_text += f"   Bet: {bet_choice} | Landed: {landed} | {time_str}{balance_str}\n\n"
                elif game_type == 'blackjack':
                    player_hand = game.get('player_hand', '?')
                    dealer_hand = game.get('dealer_hand', '?')
                    history_text += f"{result_emoji} **Blackjack** - ${wager:.2f}\n"
                    history_text += f"   Player: {player_hand} | Dealer: {dealer_hand} | {time_str}{balance_str}\n\n"
                elif game_type == 'baccarat':
                    player_hand = game.get('player_hand', '?')
                    banker_hand = game.get('banker_hand', '?')
                    bet_type = game.get('bet_type', '?')
                    history_text += f"{result_emoji} **Baccarat** - ${wager:.2f}\n"
                    history_text += f"   Bet: {bet_type.capitalize()} | Player: {player_hand} | Banker: {banker_hand} | {time_str}{balance_str}\n\n"
                elif game_type == 'dice_predict':
                    predicted = game.get('predicted', '?')
                    actual = game.get('actual_roll', '?')
                    history_text += f"{result_emoji} **Predict** - ${wager:.2f}\n"
                    history_text += f"   Predicted: {predicted} | Rolled: {actual} | {time_str}{balance_str}\n\n"
                elif game_type in ['slots', 'slots_bot']:
                    multiplier = game.get('multiplier', 0)
                    dice_value = game.get('dice_value', '?')
                    if multiplier == 22:
                        outcome_text = "777 JACKPOT! (22x)"
                    elif multiplier == 8:
                        outcome_text = "Three of a Kind (8x)"
                    elif multiplier == 2:
                        outcome_text = "Two 7s (2x)"
                    else:
                        outcome_text = "No match"
                    history_text += f"{result_emoji} **Slots** - ${wager:.2f}\n"
                    history_text += f"   [{dice_value}] {outcome_text} | {time_str}{balance_str}\n\n"
                else:
                    history_text += f"{result_emoji} **{game_type.replace('_', ' ').title()}** - ${wager:.2f}\n"
                    history_text += f"   {time_str}{balance_str}\n\n"
            else:
                opponent_id = game.get('opponent') if game.get('challenger') == user_id else game.get('challenger')
                if opponent_id:
                    opponent_user = self.db.get_user(opponent_id)
                    opponent_username = opponent_user.get('username', f'User{opponent_id}')
                    result_emoji = "✅" if result == "win" else "❌" if result == "loss" else "🤝"
                    history_text += f"{result_emoji} **{game_type.replace('_', ' ').title()}** - ${wager:.2f}\n"
                    history_text += f"   vs @{opponent_username} | {time_str}{balance_str}\n\n"
                else:
                    result_emoji = "✅" if result == "win" else "❌" if result == "loss" else "🤝"
                    history_text += f"{result_emoji} **{game_type.replace('_', ' ').title()}** - ${wager:.2f}\n"
                    history_text += f"   {time_str}{balance_str}\n\n"
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"history_page_{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"history_page_{page + 1}"))
        
        keyboard_rows = []
        if nav_buttons:
            keyboard_rows.append(nav_buttons)
        if show_back:
            keyboard_rows.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_more_content")])
        
        keyboard = InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None
        
        if edit_message:
            await message.edit_text(history_text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            sent_msg = await message.reply_text(history_text, reply_markup=keyboard, parse_mode="Markdown")
            if keyboard:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id

    async def matches_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View match history for self or another user with pagination."""
        user_id = update.effective_user.id
        username = update.effective_user.username or f"User{user_id}"
        
        target_user_id = user_id
        target_username = username
        
        if context.args:
            search_term = context.args[0].lstrip('@').lower()
            found = False
            for uid, udata in self.db.data['users'].items():
                if udata.get('username', '').lower() == search_term:
                    target_user_id = int(uid)
                    target_username = udata.get('username', f'User{uid}')
                    found = True
                    break
            if not found:
                await update.message.reply_text(f"User @{search_term} not found.")
                return
        
        await self._show_matches_page(update.message, target_user_id, target_username, 0, user_id)
    
    async def _show_matches_page(self, message, target_user_id: int, target_username: str, page: int, requester_id: int):
        """Display a page of match history."""
        games_per_page = 10
        
        user_games = []
        for game in self.db.data.get('games', []):
            if (game.get('player_id') == target_user_id or 
                game.get('challenger') == target_user_id or 
                game.get('opponent') == target_user_id):
                user_games.append(game)
        
        user_games.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        total_games = len(user_games)
        total_pages = max(1, (total_games + games_per_page - 1) // games_per_page)
        
        start_idx = page * games_per_page
        end_idx = min(start_idx + games_per_page, total_games)
        page_games = user_games[start_idx:end_idx]
        
        if not page_games:
            await message.reply_text(f"@{target_username} has no match history.")
            return
        
        lines = [f"Match History for @{target_username} (Page {page + 1}/{total_pages}):\n"]
        
        for game in page_games:
            game_type = game.get('type', 'Unknown')
            wager = game.get('wager', 0)
            result = game.get('result', game.get('outcome', 'unknown'))
            timestamp = game.get('timestamp', '')[:16].replace('T', ' ')
            
            details = ""
            if game_type == 'dice_bot':
                details = f" (You: {game.get('player_roll', '?')} vs Bot: {game.get('bot_roll', '?')})"
            elif game_type == 'coinflip_bot':
                details = f" (chose: {game.get('choice', '?')}, landed: {game.get('result', '?')})"
            elif game_type == 'dice_predict':
                details = f" (predicted: {game.get('predicted', '?')}, rolled: {game.get('actual_roll', '?')})"
            elif game_type == 'roulette':
                details = f" (bet: {game.get('choice', '?')}, landed: {game.get('result', '?')})"
            elif game_type == 'blackjack':
                details = f" (player: {game.get('player_hand', '?')}, dealer: {game.get('dealer_hand', '?')})"
            elif game_type == 'slots':
                details = f" (value: {game.get('slot_value', '?')})"
            elif 'pvp' in game_type.lower() or game_type in ['dice', 'darts', 'basketball', 'soccer', 'bowling', 'coinflip']:
                challenger = game.get('challenger')
                opponent = game.get('opponent')
                if challenger and opponent:
                    other_id = opponent if challenger == target_user_id else challenger
                    other_user = self.db.get_user(other_id)
                    other_name = other_user.get('username', f'User{other_id}')
                    details = f" (vs @{other_name})"
            
            result_emoji = "✅" if result == 'win' else "❌" if result == 'loss' else "🔄"
            lines.append(f"{result_emoji} {game_type.replace('_', ' ').title()}: ${wager:.2f}{details} - {timestamp}")
        
        buttons = []
        if page > 0:
            buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"matches_page_{target_user_id}_{page - 1}"))
        if page < total_pages - 1:
            buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"matches_page_{target_user_id}_{page + 1}"))
        
        keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
        
        sent_msg = await message.reply_text("\n".join(lines), reply_markup=keyboard)
        if keyboard:
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = requester_id
    
    async def dice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play dice game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/dice <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"dice_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"dice_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🎲 **Dice Game**\n\nWager: ${wager:.2f}\n\nChoose your opponent:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def darts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play darts game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/darts <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"darts_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"darts_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🎯 **Darts Game**\n\nWager: ${wager:.2f}\n\nChoose your opponent:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def basketball_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play basketball game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/basketball <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"basketball_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"basketball_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🏀 **Basketball Game**\n\nWager: ${wager:.2f}\n\nChoose your opponent:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def soccer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play soccer game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/soccer <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"soccer_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"soccer_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"⚽ **Soccer Game**\n\nWager: ${wager:.2f}\n\nChoose your opponent:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def bowling_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play bowling game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/bowling <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"bowling_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"bowling_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🎳 **Bowling Game**\n\nWager: ${wager:.2f}\n\nChoose your opponent:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def predict_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play dice predict game - predict what you'll roll"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔮 **Dice Prediction**\n\n"
                "Predict the dice roll and win 6x your wager!\n\n"
                "**Usage:** `/predict <amount|all>`",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from user balance
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Show 6 buttons for prediction
        keyboard = [
            [InlineKeyboardButton("1️⃣", callback_data=f"predict_select_{wager:.2f}_1"),
             InlineKeyboardButton("2️⃣", callback_data=f"predict_select_{wager:.2f}_2"),
             InlineKeyboardButton("3️⃣", callback_data=f"predict_select_{wager:.2f}_3")],
            [InlineKeyboardButton("4️⃣", callback_data=f"predict_select_{wager:.2f}_4"),
             InlineKeyboardButton("5️⃣", callback_data=f"predict_select_{wager:.2f}_5"),
             InlineKeyboardButton("6️⃣", callback_data=f"predict_select_{wager:.2f}_6")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(
            f"🔮 **Dice Prediction**\n\n"
            f"Wager: **${wager:.2f}**\n\n"
            f"Choose your prediction (30 seconds):",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        
        # Store pending prediction for timeout
        predict_key = f"predict_{sent_msg.chat_id}_{sent_msg.message_id}"
        if not hasattr(self, 'pending_predictions'):
            self.pending_predictions = {}
        self.pending_predictions[predict_key] = {
            'user_id': user_id,
            'wager': wager,
            'chat_id': sent_msg.chat_id,
            'message_id': sent_msg.message_id,
            'timestamp': datetime.now()
        }
        
        # Schedule timeout refund after 30 seconds
        asyncio.create_task(self._predict_timeout(predict_key, user_id, wager, sent_msg.chat_id, sent_msg.message_id))
    
    async def _predict_timeout(self, predict_key: str, user_id: int, wager: float, chat_id: int, message_id: int):
        """Handle prediction timeout - refund wager after 30 seconds if no selection"""
        await asyncio.sleep(30)
        
        if not hasattr(self, 'pending_predictions'):
            return
        
        if predict_key in self.pending_predictions:
            # Still pending - refund the wager
            del self.pending_predictions[predict_key]
            
            user_data = self.db.get_user(user_id)
            self.db.update_user(user_id, {'balance': user_data['balance'] + wager})
            
            try:
                await self.app.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"⏰ **Time's up!**\n\nYour ${wager:.2f} wager has been refunded.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to edit predict timeout message: {e}")
    
    async def slots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play slots game using Telegram's slot machine emoji"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "**Slots**\n\n"
                "**Payouts:**\n"
                "777 Jackpot: 22x\n"
                "Three of a Kind: 8x\n"
                "Two 7s: 2x\n\n"
                "**Usage:** `/slots <amount|all>`",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from user balance and update local reference
        new_bal_after_wager = user_data['balance'] - wager
        self.db.update_user(user_id, {'balance': new_bal_after_wager})
        
        # Send the slot machine emoji and wait for result
        slots_message = await update.message.reply_dice(emoji="🎰")
        dice_value = slots_message.dice.value
        
        await asyncio.sleep(3)
        
        # Determine payout based on dice value
        # All triples pay 25x (1/64 chance each = ~61% house edge)
        # Value 1 = Triple Bars, Value 22 = Triple Grapes
        # Value 43 = Triple Lemons, Value 64 = Triple 7s
        
        payout_multiplier = 0
        
        if dice_value in (1, 22, 43, 64):
            payout_multiplier = 25
        
        username = user_data.get('username', f'User{user_id}')
        
        if payout_multiplier > 0:
            payout = wager * payout_multiplier
            profit = payout - wager
            new_balance = new_bal_after_wager + payout
            
            self.db.update_user(user_id, {
                'balance': new_balance,
                'total_wagered': user_data['total_wagered'] + wager,
                'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                'games_played': user_data['games_played'] + 1,
                'games_won': user_data['games_won'] + 1
            })
            self.db.update_house_balance(-profit)
            
            keyboard = [[InlineKeyboardButton("Spin Again", callback_data=f"slots_play_{wager:.2f}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await update.message.reply_text(
                f"@{username} won ${profit:.2f}",
                reply_markup=reply_markup
            )
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        else:
            self.db.update_user(user_id, {
                'total_wagered': user_data['total_wagered'] + wager,
                'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                'games_played': user_data['games_played'] + 1
            })
            self.db.update_house_balance(wager)
            
            keyboard = [[InlineKeyboardButton("Spin Again", callback_data=f"slots_play_{wager:.2f}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await update.message.reply_text(
                f"@{username} lost ${wager:.2f}",
                reply_markup=reply_markup
            )
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        
        # Calculate final balance for history
        final_user_data = self.db.get_user(user_id)
        self.db.record_game({
            'type': 'slots',
            'player_id': user_id,
            'wager': wager,
            'dice_value': dice_value,
            'result': 'win' if payout_multiplier > 0 else 'loss',
            'payout': wager * payout_multiplier if payout_multiplier > 0 else 0,
            'multiplier': payout_multiplier,
            'balance_after': final_user_data['balance']
        })
    
    async def slots_play(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play slots from button callback"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        chat_id = query.message.chat_id
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from user balance and track the new balance
        new_bal_after_wager = user_data['balance'] - wager
        self.db.update_user(user_id, {'balance': new_bal_after_wager})
        
        # Send the slot machine emoji and wait for result
        slots_message = await context.bot.send_dice(chat_id=chat_id, emoji="🎰")
        dice_value = slots_message.dice.value
        
        await asyncio.sleep(3)
        
        # Determine payout based on dice value
        # All triples pay 25x (1/64 chance each = ~61% house edge)
        # Value 1 = Triple Bars, Value 22 = Triple Grapes
        # Value 43 = Triple Lemons, Value 64 = Triple 7s
        
        payout_multiplier = 0
        
        if dice_value in (1, 22, 43, 64):
            payout_multiplier = 25
        
        username = user_data.get('username', f'User{user_id}')
        
        if payout_multiplier > 0:
            payout = wager * payout_multiplier
            profit = payout - wager
            new_balance = new_bal_after_wager + payout
            
            self.db.update_user(user_id, {
                'balance': new_balance,
                'total_wagered': user_data['total_wagered'] + wager,
                'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                'games_played': user_data['games_played'] + 1,
                'games_won': user_data['games_won'] + 1
            })
            self.db.update_house_balance(-profit)
            
            keyboard = [[InlineKeyboardButton("Spin Again", callback_data=f"slots_play_{wager:.2f}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"@{username} won ${profit:.2f}",
                reply_markup=reply_markup
            )
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        else:
            self.db.update_user(user_id, {
                'total_wagered': user_data['total_wagered'] + wager,
                'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                'games_played': user_data['games_played'] + 1
            })
            self.db.update_house_balance(wager)
            
            keyboard = [[InlineKeyboardButton("Spin Again", callback_data=f"slots_play_{wager:.2f}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=f"@{username} lost ${wager:.2f}",
                reply_markup=reply_markup
            )
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        
        # Calculate final balance for history
        final_user_data = self.db.get_user(user_id)
        self.db.record_game({
            'type': 'slots',
            'player_id': user_id,
            'wager': wager,
            'dice_value': dice_value,
            'result': 'win' if payout_multiplier > 0 else 'loss',
            'payout': wager * payout_multiplier if payout_multiplier > 0 else 0,
            'multiplier': payout_multiplier,
            'balance_after': final_user_data['balance']
        })

    async def coinflip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play coinflip game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/flip <amount|all>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
            
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Check for PvP opponent mention (this part is complex and often relies on bot permissions)
        opponent_id = None
        if len(context.args) > 1 and context.args[1].startswith('@'):
            # In a real bot, we'd need to fetch user ID from username
            # For simplicity, we'll keep the Bot vs. Bot or open challenge structure for now.
            await update.message.reply_text("❌ Player-to-player challenges are currently only supported via callback buttons after initiating a game.")
            return

        # Default is Bot vs. Player with Heads/Tails selection
        keyboard = [
            [InlineKeyboardButton("Heads", callback_data=f"flip_bot_{wager:.2f}_heads")],
            [InlineKeyboardButton("Tails", callback_data=f"flip_bot_{wager:.2f}_tails")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🪙 **Coin Flip**\n\nWager: ${wager:.2f}\n\nChoose heads or tails:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def roulette_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play roulette game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: `/roulette <amount|all>` or `/roulette <amount> #<number>`", parse_mode="Markdown")
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        if len(context.args) > 1 and context.args[1].startswith('#'):
            try:
                number_str = context.args[1][1:]
                if number_str == "00":
                    specific_num = 37
                else:
                    specific_num = int(number_str)
                    if specific_num < 0 or specific_num > 36:
                        await update.message.reply_text("❌ Number must be 0-36 or 00")
                        return
                
                await self.roulette_play_direct(update, context, wager, f"num_{specific_num}")
                return
            except ValueError:
                await update.message.reply_text("❌ Invalid number format. Use #0, #1, #2, ... #36, or #00")
                return
        
        keyboard = [
            [InlineKeyboardButton("Red (2x)", callback_data=f"roulette_{wager:.2f}_red"),
             InlineKeyboardButton("Black (2x)", callback_data=f"roulette_{wager:.2f}_black")],
            [InlineKeyboardButton("Odd (2x)", callback_data=f"roulette_{wager:.2f}_odd"),
             InlineKeyboardButton("Even (2x)", callback_data=f"roulette_{wager:.2f}_even")],
            [InlineKeyboardButton("Low (2x)", callback_data=f"roulette_{wager:.2f}_low"),
             InlineKeyboardButton("High (2x)", callback_data=f"roulette_{wager:.2f}_high")],
            [InlineKeyboardButton("0 (35x)", callback_data=f"roulette_{wager:.2f}_zero"),
             InlineKeyboardButton("00 (35x)", callback_data=f"roulette_{wager:.2f}_doublezero")],
            [InlineKeyboardButton("Green (14x)", callback_data=f"roulette_{wager:.2f}_green")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"🎰 **Roulette** - Wager: ${wager:.2f}\n\n"
            f"**Choose your bet:**\n"
            f"• Red/Black: 2x payout\n"
            f"• Odd/Even: 2x payout\n"
            f"• Low (1-18)/High (19-36): 2x payout\n"
            f"• 0/00: 35x payout\n"
            f"• Green (0/00): 14x payout\n\n"
            f"*Tip: Bet on a specific number with `/roulette <amount> #<number>` for 35x payout!*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def blackjack_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Blackjack game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "**Usage:** `/blackjack <amount|all>`",
                parse_mode="Markdown"
            )
            return
        
        # Parse wager
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from balance
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        # Create new Blackjack game
        game = BlackjackGame(bet_amount=wager)
        game.start_game()
        self.blackjack_sessions[user_id] = game
        
        # Start 30-second timeout for the game
        chat_id = update.effective_chat.id
        game_key = f"blackjack_{user_id}"
        self.start_game_timeout(game_key, "blackjack", user_id, chat_id, wager, 
                                bot=context.bot)
        
        # Display game state
        await self._display_blackjack_state(update, context, user_id)
    
    async def _display_blackjack_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Display the current Blackjack game state with action buttons"""
        if user_id not in self.blackjack_sessions:
            return
        
        game = self.blackjack_sessions[user_id]
        state = game.get_game_state()
        
        # Build message text
        message = "🃏 **Blackjack**\n\n"
        message += f"**Dealer:** {state['dealer']['cards']} "
        if state['game_over']:
            message += f"(Value: {state['dealer']['value']})\n\n"
        else:
            message += f"(Showing: {state['dealer']['value']})\n\n"
        
        # Display all player hands
        for hand in state['player_hands']:
            hand_status = ""
            if len(state['player_hands']) > 1:
                hand_status = f"**Hand {hand['id'] + 1}:** "
            
            hand_status += f"{hand['cards']} (Value: {hand['value']})"
            
            if hand['status'] == 'Blackjack':
                hand_status += " 🎉 BLACKJACK!"
            elif hand['status'] == 'Bust':
                hand_status += " 💥 BUST"
            elif hand['is_current_turn']:
                hand_status += " ⬅️ Your turn"
            
            message += hand_status + "\n"
        
        # Insurance info
        if state['is_insurance_available']:
            message += f"\n**Insurance available:** ${state['insurance_bet']:.2f}\n"
        
        # Game over - show results
        if state['game_over']:
            if state['dealer']['final_status'] == 'Bust':
                message += f"\nDealer busts with {state['dealer']['value']}!"
            elif state['dealer']['is_blackjack']:
                message += "\nDealer has Blackjack!"
            
            total_payout = state['total_payout']
            
            # Update user balance
            user_data = self.db.get_user(user_id)
            # Add back: total payout + all hand bets + insurance bet (if taken)
            insurance_refund = state['insurance_bet'] if state['insurance_bet'] > 0 else 0
            user_data['balance'] += total_payout + sum(h['bet'] for h in state['player_hands']) + insurance_refund
            user_data['total_wagered'] += sum(h['bet'] for h in state['player_hands'])
            user_data['total_pnl'] += total_payout
            user_data['games_played'] += 1
            if total_payout > 0:
                user_data['games_won'] += 1
            self.db.update_user(user_id, user_data)
            
            # Record game
            self.db.record_game({
                'type': 'blackjack',
                'player_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'wager': sum(h['bet'] for h in state['player_hands']),
                'payout': total_payout,
                'result': 'win' if total_payout > 0 else ('loss' if total_payout < 0 else 'push'),
                'balance_after': user_data['balance'],
                'player_hand': ' | '.join([f"{h['cards']} ({h['value']})" for h in state['player_hands']]),
                'dealer_hand': f"{state['dealer']['cards']} ({state['dealer']['value']})"
            })
            
            # Store original bet before removing session
            original_bet = game.initial_bet
            
            # Cancel timeout since game is over
            game_key = f"blackjack_{user_id}"
            self.cancel_game_timeout(game_key)
            
            # Remove session
            del self.blackjack_sessions[user_id]
            
            # Add Play Again button with the ORIGINAL bet amount (not doubled/split amount)
            keyboard = [[InlineKeyboardButton(f"Play Again (${original_bet:.2f})", callback_data=f"bj_{user_id}_playagain_{original_bet:.2f}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Build the result message with @username format
            username = update.effective_user.username or update.effective_user.first_name or f"User{user_id}"
            if total_payout > 0:
                result_message = f"@{username} won ${total_payout:.2f}"
            elif total_payout < 0:
                result_message = f"@{username} lost ${abs(total_payout):.2f}"
            else:
                result_message = f"@{username} push - bet returned"
            
            # Edit the game message (without result) and send result as separate message
            chat_id = update.effective_chat.id
            if update.callback_query:
                await update.callback_query.edit_message_text(message, parse_mode="Markdown")
            else:
                await update.effective_message.reply_text(message, parse_mode="Markdown")
            
            # Send result in a separate message with Play Again button
            await context.bot.send_message(chat_id, result_message, reply_markup=reply_markup, parse_mode="Markdown")
            return
        
        # Build action buttons for current hand
        keyboard = []
        current_hand = state['player_hands'][state['current_hand_index']]
        
        if current_hand['is_current_turn']:
            actions = current_hand.get('actions', {})
            
            # Always show Hit and Stand
            keyboard.append([
                InlineKeyboardButton("Hit", callback_data=f"bj_{user_id}_hit"),
                InlineKeyboardButton("Stand", callback_data=f"bj_{user_id}_stand")
            ])
            
            # Double Down button
            if actions.get('can_double'):
                keyboard.append([InlineKeyboardButton("Double Down", callback_data=f"bj_{user_id}_double")])
            
            # Split button
            if actions.get('can_split'):
                keyboard.append([InlineKeyboardButton("Split", callback_data=f"bj_{user_id}_split")])
        
        # Insurance button
        if state['is_insurance_available']:
            keyboard.append([InlineKeyboardButton("Take Insurance", callback_data=f"bj_{user_id}_insurance")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Edit message if from callback, otherwise reply
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            sent_msg = await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if reply_markup:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def _display_blackjack_state_new_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Display the current Blackjack game state as a NEW message (for Play Again)"""
        if user_id not in self.blackjack_sessions:
            return
        
        game = self.blackjack_sessions[user_id]
        state = game.get_game_state()
        
        # Build message text
        message = "🃏 **Blackjack**\n\n"
        message += f"**Dealer:** {state['dealer']['cards']} "
        if state['game_over']:
            message += f"(Value: {state['dealer']['value']})\n\n"
        else:
            message += f"(Showing: {state['dealer']['value']})\n\n"
        
        # Display all player hands
        for hand in state['player_hands']:
            hand_status = ""
            if len(state['player_hands']) > 1:
                hand_status = f"**Hand {hand['id'] + 1}:** "
            
            hand_status += f"{hand['cards']} (Value: {hand['value']})"
            
            if hand['status'] == 'Blackjack':
                hand_status += " 🎉 BLACKJACK!"
            elif hand['status'] == 'Bust':
                hand_status += " 💥 BUST"
            elif hand['is_current_turn']:
                hand_status += " ⬅️ Your turn"
            
            message += hand_status + "\n"
        
        # Insurance info
        if state['is_insurance_available']:
            message += f"\n**Insurance available:** ${state['insurance_bet']:.2f}\n"
        
        # Build action buttons for current hand
        keyboard = []
        current_hand = state['player_hands'][state['current_hand_index']]
        
        if current_hand['is_current_turn']:
            actions = current_hand.get('actions', {})
            
            # Always show Hit and Stand
            keyboard.append([
                InlineKeyboardButton("Hit", callback_data=f"bj_{user_id}_hit"),
                InlineKeyboardButton("Stand", callback_data=f"bj_{user_id}_stand")
            ])
            
            # Double Down button
            if actions.get('can_double'):
                keyboard.append([InlineKeyboardButton("Double Down", callback_data=f"bj_{user_id}_double")])
            
            # Split button
            if actions.get('can_split'):
                keyboard.append([InlineKeyboardButton("Split", callback_data=f"bj_{user_id}_split")])
        
        # Insurance button
        if state['is_insurance_available']:
            keyboard.append([InlineKeyboardButton("Take Insurance", callback_data=f"bj_{user_id}_insurance")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        # Always send as a NEW message
        chat_id = update.effective_chat.id
        sent_msg = await context.bot.send_message(chat_id, message, reply_markup=reply_markup, parse_mode="Markdown")
        if reply_markup:
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def mines_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Mines game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "**Usage:** `/mines <amount>`",
                parse_mode="Markdown"
            )
            return
        
        # Parse wager
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Show mine count selection
        keyboard = [
            [InlineKeyboardButton("3 Mines (Low Risk)", callback_data=f"mines_start_{wager:.2f}_3")],
            [InlineKeyboardButton("5 Mines (Medium)", callback_data=f"mines_start_{wager:.2f}_5")],
            [InlineKeyboardButton("10 Mines (High Risk)", callback_data=f"mines_start_{wager:.2f}_10")],
            [InlineKeyboardButton("15 Mines (Very High)", callback_data=f"mines_start_{wager:.2f}_15")],
            [InlineKeyboardButton("20 Mines (Extreme)", callback_data=f"mines_start_{wager:.2f}_20")],
            [InlineKeyboardButton("24 Mines (Max Risk)", callback_data=f"mines_start_{wager:.2f}_24")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_opponent_selection.add(user_id)
        
        sent_msg = await update.message.reply_text(
            f"💣 **Mines** - Wager: ${wager:.2f}\n\n"
            f"**Select difficulty (number of mines):**\n\n"
            f"More mines = Higher risk = Bigger multipliers!\n"
            f"• 3 mines: Up to 2.23x\n"
            f"• 5 mines: Up to 7.42x\n"
            f"• 10 mines: Up to 113.85x\n"
            f"• 15 mines: Up to 9,176x\n"
            f"• 24 mines: Up to 24,750x",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    def _build_mines_grid_keyboard(self, game: MinesGame) -> InlineKeyboardMarkup:
        """Build the 5x5 mines grid keyboard"""
        user_id = game.user_id
        grid = game.get_grid_display(reveal_all=game.game_over)
        keyboard = []
        
        for row in range(5):
            row_buttons = []
            for col in range(5):
                pos = row * 5 + col
                tile = grid[row][col]
                
                if game.game_over or pos in game.revealed_tiles:
                    row_buttons.append(InlineKeyboardButton(tile, callback_data=f"mines_noop"))
                else:
                    row_buttons.append(InlineKeyboardButton(tile, callback_data=f"mines_reveal_{user_id}_{pos}"))
            keyboard.append(row_buttons)
        
        # Add cash out button if game is active and at least one tile revealed
        if not game.game_over and len(game.revealed_tiles) > 0:
            payout = game.get_potential_payout()
            keyboard.append([InlineKeyboardButton(f"💰 Cash Out ${payout:.2f}", callback_data=f"mines_cashout_{user_id}")])
        
        # Add play again options if game is over
        if game.game_over:
            keyboard.append([
                InlineKeyboardButton("🔄 Play Again", callback_data=f"mines_again_{user_id}_{game.wager}_{game.num_mines}"),
                InlineKeyboardButton("💣 Change Mines", callback_data=f"mines_change_{user_id}_{game.wager}")
            ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _display_mines_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, is_new: bool = False):
        """Display the current Mines game state with grid buttons"""
        if user_id not in self.mines_sessions:
            return
        
        game = self.mines_sessions[user_id]
        
        # Build message
        revealed = len(game.revealed_tiles)
        safe_tiles = 25 - game.num_mines
        result_message = None
        
        if game.game_over:
            if game.hit_mine:
                # Grid message (no result text)
                message = f"💎 **Mines**\n\n"
                message += f"**Mines:** {game.num_mines} | **Revealed:** {revealed}/{safe_tiles}\n"
                message += f"**Bet:** ${game.wager:.2f}"
                
                # Update stats
                user_data = self.db.get_user(user_id)
                username = user_data.get('username', 'Player')
                
                # Separate result message
                result_message = f"@{username} lost ${game.wager:.2f}"
                user_data['total_wagered'] += game.wager
                user_data['total_pnl'] -= game.wager
                user_data['games_played'] += 1
                self.db.update_user(user_id, user_data)
                
                # Record game
                self.db.record_game({
                    'type': 'mines',
                    'player_id': user_id,
                    'username': user_data.get('username', 'Unknown'),
                    'wager': game.wager,
                    'num_mines': game.num_mines,
                    'tiles_revealed': revealed,
                    'payout': 0,
                    'result': 'loss',
                    'balance_after': user_data['balance']
                })
                
                # Update house balance
                self.db.update_house_balance(game.wager)
                
            elif game.cashed_out:
                payout = game.wager * game.current_multiplier
                profit = payout - game.wager
                
                # Grid message (no result text)
                message = f"💎 **Mines**\n\n"
                message += f"**Mines:** {game.num_mines} | **Revealed:** {revealed}/{safe_tiles}\n"
                message += f"**Multiplier:** {game.current_multiplier:.2f}x\n"
                message += f"**Bet:** ${game.wager:.2f}"
                
                # Update user balance
                user_data = self.db.get_user(user_id)
                
                # Separate result message
                username = user_data.get('username', 'Unknown')
                result_message = f"@{username} won ${payout:.2f}"
                user_data['balance'] += payout
                user_data['total_wagered'] += game.wager
                user_data['total_pnl'] += profit
                user_data['games_played'] += 1
                user_data['games_won'] += 1
                self.db.update_user(user_id, user_data)
                
                # Record game
                self.db.record_game({
                    'type': 'mines',
                    'player_id': user_id,
                    'username': user_data.get('username', 'Unknown'),
                    'wager': game.wager,
                    'num_mines': game.num_mines,
                    'tiles_revealed': revealed,
                    'multiplier': game.current_multiplier,
                    'payout': payout,
                    'result': 'win',
                    'balance_after': user_data['balance']
                })
                
                # Update house balance
                self.db.update_house_balance(-profit)
            
            # Cancel timeout since game is over
            game_key = f"mines_{user_id}"
            self.cancel_game_timeout(game_key)
            
            # Remove session
            del self.mines_sessions[user_id]
        else:
            payout = game.get_potential_payout()
            message = f"💎 **Mines**\n\n"
            message += f"**Mines:** {game.num_mines} | **Revealed:** {revealed}/{safe_tiles}\n"
            message += f"**Multiplier:** {game.current_multiplier:.2f}x\n"
            message += f"**Bet:** ${game.wager:.2f}\n"
            message += f"**Current Value:** ${payout:.2f}\n\n"
            message += f"Click tiles to reveal gems 💎"
        
        reply_markup = self._build_mines_grid_keyboard(game)
        
        # Edit or send message
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if not game.game_over:
                self.button_ownership[(update.callback_query.message.chat_id, update.callback_query.message.message_id)] = user_id
            # Send separate result message after the game ends
            if result_message:
                await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=result_message, parse_mode="Markdown")
        else:
            sent_msg = await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if not game.game_over:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id

    async def baccarat_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Baccarat game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "**Usage:** `/baccarat <amount>`\n\n"
                "Bet on Player, Banker, or Tie!",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🔵 Player (2x)", callback_data=f"bacc_{user_id}_{wager:.2f}_player")],
            [InlineKeyboardButton("🔴 Banker (1.95x)", callback_data=f"bacc_{user_id}_{wager:.2f}_banker")],
            [InlineKeyboardButton("🟢 Tie (9x)", callback_data=f"bacc_{user_id}_{wager:.2f}_tie")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(
            f"🃏 **Baccarat** - Wager: ${wager:.2f}\n\n"
            f"**Choose your bet:**\n\n"
            f"• Player pays 2x\n"
            f"• Banker pays 1.95x (5% commission)\n"
            f"• Tie pays 9x",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id

    async def _play_baccarat(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, wager: float, bet_type: str):
        """Play a baccarat round"""
        query = update.callback_query
        chat_id = query.message.chat_id
        
        user_data = self.db.get_user(user_id)
        if wager > user_data['balance']:
            await query.edit_message_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        game = BaccaratGame(wager, bet_type)
        state = game.play_round()
        
        player_cards = state['player_hand']['cards']
        player_value = state['player_hand']['value']
        banker_cards = state['banker_hand']['cards']
        banker_value = state['banker_hand']['value']
        
        result_emoji = "🔵" if state['result'] == 'player' else "🔴" if state['result'] == 'banker' else "🟢"
        result_name = state['result'].capitalize()
        
        message = f"🃏 **Baccarat**\n\n"
        message += f"**Player:** {player_cards} = {player_value}\n"
        message += f"**Banker:** {banker_cards} = {banker_value}\n\n"
        message += f"**Result:** {result_emoji} {result_name} wins!\n"
        message += f"**Your bet:** {bet_type.capitalize()}\n\n"
        
        payout = state['payout']
        profit = state['profit']
        
        is_push = (payout == wager and profit == 0)
        
        if is_push:
            user_data = self.db.get_user(user_id)
            user_data['balance'] += payout
            user_data['total_wagered'] += wager
            user_data['games_played'] += 1
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
            self.db.update_user(user_id, user_data)
            
            result_text = f"Push - ${wager:.2f} returned"
        elif payout > 0:
            user_data = self.db.get_user(user_id)
            user_data['balance'] += payout
            user_data['total_wagered'] += wager
            user_data['games_played'] += 1
            user_data['games_won'] += 1
            user_data['total_pnl'] += profit
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-profit)
            
            result_text = f"@{user_data.get('username', 'Player')} won ${profit:.2f}"
        else:
            user_data = self.db.get_user(user_id)
            user_data['total_wagered'] += wager
            user_data['games_played'] += 1
            user_data['total_pnl'] -= wager
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(wager)
            
            result_text = f"@{user_data.get('username', 'Player')} lost ${wager:.2f}"
        
        outcome = 'push' if is_push else ('win' if payout > 0 else 'loss')
        self.db.record_game({
            'type': 'baccarat',
            'player_id': user_id,
            'username': user_data.get('username', 'Unknown'),
            'wager': wager,
            'bet_type': bet_type,
            'player_value': player_value,
            'banker_value': banker_value,
            'result': state['result'],
            'outcome': outcome,
            'payout': payout,
            'balance_after': user_data['balance'],
            'player_hand': f"{player_cards} ({player_value})",
            'banker_hand': f"{banker_cards} ({banker_value})"
        })
        
        self.button_ownership.pop((chat_id, query.message.message_id), None)
        
        await query.edit_message_text(message, parse_mode="Markdown")
        await context.bot.send_message(chat_id=chat_id, text=result_text, parse_mode="Markdown")

    async def keno_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Keno game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "**Usage:** `/keno <amount>`\n\n"
                "Pick up to 10 numbers from 1-40!",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        game = KenoGame(user_id, wager)
        self.keno_sessions[user_id] = game
        
        # Start 30-second timeout for the game
        chat_id = update.effective_chat.id
        game_key = f"keno_{user_id}"
        self.start_game_timeout(game_key, "keno", user_id, chat_id, wager, 
                                bot=context.bot)
        
        await self._display_keno_state(update, context, user_id, is_new=True)

    def _build_keno_grid_keyboard(self, game: KenoGame) -> InlineKeyboardMarkup:
        """Build the keno number grid keyboard"""
        user_id = game.user_id
        keyboard = []
        
        for row in range(5):
            row_buttons = []
            for col in range(8):
                num = row * 8 + col + 1
                if num > 40:
                    continue
                
                if game.game_over:
                    if num in game.picked_numbers and num in game.drawn_numbers:
                        label = f"✅{num}"
                    elif num in game.drawn_numbers:
                        label = f"🔵{num}"
                    elif num in game.picked_numbers:
                        label = f"❌{num}"
                    else:
                        label = f"{num}"
                    row_buttons.append(InlineKeyboardButton(label, callback_data="keno_noop"))
                else:
                    if num in game.picked_numbers:
                        label = f"⭐{num}"
                    else:
                        label = "\u3164"
                    row_buttons.append(InlineKeyboardButton(label, callback_data=f"keno_pick_{user_id}_{num}"))
            keyboard.append(row_buttons)
        
        if not game.game_over:
            action_row = []
            if len(game.picked_numbers) > 0:
                if game.selecting_rounds:
                    keyboard.append([
                        InlineKeyboardButton("1x", callback_data=f"keno_rounds_{user_id}_1"),
                        InlineKeyboardButton("3x", callback_data=f"keno_rounds_{user_id}_3"),
                        InlineKeyboardButton("5x", callback_data=f"keno_rounds_{user_id}_5"),
                        InlineKeyboardButton("10x", callback_data=f"keno_rounds_{user_id}_10"),
                    ])
                    keyboard.append([
                        InlineKeyboardButton("25x", callback_data=f"keno_rounds_{user_id}_25"),
                        InlineKeyboardButton("50x", callback_data=f"keno_rounds_{user_id}_50"),
                        InlineKeyboardButton("100x", callback_data=f"keno_rounds_{user_id}_100"),
                        InlineKeyboardButton("Infinite", callback_data=f"keno_rounds_{user_id}_-1"),
                    ])
                    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=f"keno_back_{user_id}")])
                elif game.is_auto_playing and game.current_round > 0:
                    action_row.append(InlineKeyboardButton("🔄 Next Draw", callback_data=f"keno_next_{user_id}"))
                    action_row.append(InlineKeyboardButton("🛑 Stop", callback_data=f"keno_stop_{user_id}"))
                    keyboard.append(action_row)
                else:
                    action_row.append(InlineKeyboardButton("🎰 Draw!", callback_data=f"keno_select_rounds_{user_id}"))
                    action_row.append(InlineKeyboardButton("🗑️ Clear", callback_data=f"keno_clear_{user_id}"))
                    keyboard.append(action_row)
        else:
            keyboard.append([
                InlineKeyboardButton("🔄 Play Again", callback_data=f"keno_again_{user_id}_{game.wager}")
            ])
        
        return InlineKeyboardMarkup(keyboard)

    async def _display_keno_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, is_new: bool = False):
        """Display the current Keno game state"""
        if user_id not in self.keno_sessions:
            return
        
        game = self.keno_sessions[user_id]
        result_message = None
        
        picks = len(game.picked_numbers)
        picked_str = ", ".join(str(n) for n in sorted(game.picked_numbers)) if picks > 0 else "None"
        
        if game.game_over:
            if game.is_auto_playing and len(game.round_results) > 1:
                summary = game.get_auto_play_summary()
                message = f"🎱 **Keno - Auto-Play Complete**\n\n"
                message += f"**Your picks:** {picked_str}\n"
                message += f"**Rounds played:** {summary['total_rounds']}\n"
                message += f"**Wins:** {summary['wins']} | **Losses:** {summary['losses']}\n"
                message += f"**Total wagered:** ${summary['total_wagered']:.2f}\n"
                message += f"**Total won:** ${summary['total_payout']:.2f}\n"
                net = summary['net_profit']
                if net >= 0:
                    message += f"**Net profit:** +${net:.2f}\n"
                else:
                    message += f"**Net loss:** -${abs(net):.2f}\n"
                
                user_data = self.db.get_user(user_id)
                result_message = f"@{user_data.get('username', 'Player')} finished {summary['total_rounds']} Keno rounds: {'won' if net >= 0 else 'lost'} ${abs(net):.2f}"
            else:
                drawn_str = ", ".join(str(n) for n in sorted(game.drawn_numbers))
                message = f"🎱 **Keno**\n\n"
                message += f"**Your picks:** {picked_str}\n"
                message += f"**Drawn:** {drawn_str}\n"
                message += f"**Hits:** {game.hits}/{picks}\n"
                message += f"**Bet:** ${game.wager:.2f}\n"
                
                if game.payout > 0:
                    user_data = self.db.get_user(user_id)
                    result_message = f"@{user_data.get('username', 'Player')} won ${game.payout:.2f} ({game.get_multiplier():.0f}x)"
                else:
                    user_data = self.db.get_user(user_id)
                    result_message = f"@{user_data.get('username', 'Player')} lost ${game.wager:.2f}"
            
            game_key = f"keno_{user_id}"
            self.cancel_game_timeout(game_key)
            
            del self.keno_sessions[user_id]
        elif game.is_auto_playing and game.current_round > 0:
            drawn_str = ", ".join(str(n) for n in sorted(game.drawn_numbers))
            rounds_display = "Infinite" if game.total_rounds == -1 else f"{game.current_round}/{game.total_rounds}"
            message = f"🎱 **Keno - Round {rounds_display}**\n\n"
            message += f"**Your picks:** {picked_str}\n"
            message += f"**Drawn:** {drawn_str}\n"
            message += f"**Hits:** {game.hits}/{picks}\n"
            message += f"**Bet:** ${game.wager:.2f}\n"
            
            if game.payout > 0:
                message += f"**Won:** ${game.payout:.2f} ({game.get_multiplier():.0f}x)\n"
            else:
                message += f"**Lost this round**\n"
            
            summary = game.get_auto_play_summary()
            net = summary['net_profit']
            if net >= 0:
                message += f"\n**Running total:** +${net:.2f}"
            else:
                message += f"\n**Running total:** -${abs(net):.2f}"
        elif game.selecting_rounds:
            message = f"🎱 **Keno** - Select number of draws\n\n"
            message += f"**Picked ({picks}/10):** {picked_str}\n"
            message += f"**Bet per draw:** ${game.wager:.2f}\n\n"
            message += f"How many draws do you want to run?"
        else:
            message = f"🎱 **Keno** - Pick up to 10 numbers\n\n"
            message += f"**Picked ({picks}/10):** {picked_str}\n"
            message += f"**Bet:** ${game.wager:.2f}\n\n"
            message += f"Tap numbers to pick, then hit Draw!"
        
        reply_markup = self._build_keno_grid_keyboard(game)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if not game.game_over:
                self.button_ownership[(update.callback_query.message.chat_id, update.callback_query.message.message_id)] = user_id
            if result_message:
                await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=result_message, parse_mode="Markdown")
        else:
            sent_msg = await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if not game.game_over:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id

    async def _run_keno_draw(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Run a single keno draw and update user balance"""
        if user_id not in self.keno_sessions:
            return
        
        game = self.keno_sessions[user_id]
        user_data = self.db.get_user(user_id)
        
        if game.current_round > 0:
            user_data['balance'] -= game.wager
            self.db.update_user(user_id, user_data)
        
        result = game.run_single_draw()
        
        if result['payout'] > 0:
            user_data['balance'] += result['payout']
            user_data['total_wagered'] += game.wager
            user_data['games_played'] += 1
            user_data['games_won'] += 1
            user_data['total_pnl'] += result['payout'] - game.wager
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + game.wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-(result['payout'] - game.wager))
        else:
            user_data['total_wagered'] += game.wager
            user_data['games_played'] += 1
            user_data['total_pnl'] -= game.wager
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + game.wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(game.wager)
        
        self.db.record_game({
            'type': 'keno',
            'player_id': user_id,
            'username': user_data.get('username', 'Unknown'),
            'wager': game.wager,
            'picks': list(game.picked_numbers),
            'drawn': result['drawn'],
            'hits': result['hits'],
            'multiplier': result['multiplier'],
            'payout': result['payout'],
            'result': 'win' if result['payout'] > 0 else 'loss',
            'balance_after': user_data['balance'],
            'auto_play_round': result['round'],
            'total_rounds': game.total_rounds
        })
        
        chat_id = update.callback_query.message.chat_id if update.callback_query else update.effective_chat.id
        game_key = f"keno_{user_id}"
        self.reset_game_timeout(game_key, "keno", user_id, chat_id, game.wager, bot=context.bot)
        
        await self._display_keno_state(update, context, user_id)
    
    async def limbo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Limbo game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if len(context.args) < 2:
            presets = get_preset_multipliers()
            preset_str = " | ".join([f"{m:.2f}x" for m in presets[:5]])
            await update.message.reply_text(
                f"**Usage:** `/limbo <amount> <target_multiplier>`\n\n"
                f"**Example:** `/limbo 1 2.00`\n"
                f"(Bet $1 that the result will be 2.00x or higher)\n\n"
                f"**Popular targets:** {preset_str}\n\n"
                f"Higher target = Higher payout but lower chance!",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
            if wager <= 0:
                await update.message.reply_text("❌ You have no balance to bet!")
                return
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        try:
            target_multiplier = round(float(context.args[1]), 2)
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Invalid target multiplier")
            return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        if target_multiplier < 1.01:
            await update.message.reply_text("❌ Minimum target multiplier is 1.01x")
            return
        
        if target_multiplier > 1000000:
            await update.message.reply_text("❌ Maximum target multiplier is 1,000,000x")
            return
        
        user_data['balance'] -= wager
        self.db.update_user(user_id, {'balance': user_data['balance']})
        
        game = LimboGame(user_id, wager, target_multiplier)
        self.limbo_sessions[user_id] = game
        
        result = game.play()
        
        win_prob = result['win_probability'] * 100
        
        if result['won']:
            user_data['balance'] += result['payout']
            user_data['total_wagered'] += wager
            user_data['games_played'] += 1
            user_data['games_won'] += 1
            user_data['total_pnl'] += result['profit']
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-result['profit'])
            
            result_emoji = "🟢"
            result_text = f"@{user_data.get('username', 'Player')} won ${result['payout']:.2f} ({target_multiplier:.2f}x)"
        else:
            user_data['total_wagered'] += wager
            user_data['games_played'] += 1
            user_data['total_pnl'] -= wager
            user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(wager)
            
            result_emoji = "🔴"
            result_text = f"@{user_data.get('username', 'Player')} lost ${wager:.2f}"
        
        self.db.record_game({
            'type': 'limbo',
            'player_id': user_id,
            'username': user_data.get('username', 'Unknown'),
            'wager': wager,
            'target_multiplier': target_multiplier,
            'result_multiplier': result['result_multiplier'],
            'won': result['won'],
            'payout': result['payout'],
            'result': 'win' if result['won'] else 'loss',
            'balance_after': user_data['balance']
        })
        
        del self.limbo_sessions[user_id]
        
        keyboard = [[InlineKeyboardButton("🔄 Play Again", callback_data=f"limbo_again_{user_id}_{wager}_{target_multiplier}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"🚀 **Limbo**\n\n"
        message += f"**Target:** {target_multiplier:.2f}x ({win_prob:.1f}% chance)\n"
        message += f"**Result:** {result['result_multiplier']:.2f}x {result_emoji}\n"
        message += f"**Bet:** ${wager:.2f}\n\n"
        message += result_text
        
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    
    async def hilo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Hi-Lo game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if not context.args:
            await update.message.reply_text(
                "**Usage:** `/hilo <amount>`\n\n"
                "Predict if the next card is higher or lower!\n"
                "• Ace is lowest (1), King is highest (13)\n"
                "• Same value counts as a win for Higher/Lower\n"
                "• Cash out anytime to secure your winnings!\n"
                "• Each correct prediction increases your multiplier",
                parse_mode="Markdown"
            )
            return
        
        using_all = context.args[0].lower() == "all"
        wager = 0.0
        if using_all:
            wager = round(user_data['balance'], 2)
            if wager <= 0:
                await update.message.reply_text("❌ You have no balance to bet!")
                return
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager < 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if not using_all and wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        user_data['balance'] -= wager
        self.db.update_user(user_id, {'balance': user_data['balance']})
        
        game = HiLoGame(user_id, wager)
        self.hilo_sessions[user_id] = game
        
        # Start 30-second timeout for the game
        chat_id = update.effective_chat.id
        game_key = f"hilo_{user_id}"
        self.start_game_timeout(game_key, "hilo", user_id, chat_id, wager, 
                                bot=context.bot)
        
        await self._display_hilo_state(update, context, user_id, is_new=True)
    
    def _build_hilo_keyboard(self, game: HiLoGame) -> InlineKeyboardMarkup:
        """Build the Hi-Lo game keyboard"""
        user_id = game.user_id
        odds = game.get_odds()
        
        if game.game_over:
            keyboard = [[InlineKeyboardButton("🔄 Play Again", callback_data=f"hilo_again_{user_id}_{game.initial_wager}")]]
        else:
            keyboard = [
                [
                    InlineKeyboardButton(f"⬆️ Higher ({odds['higher']['multiplier']:.2f}x)", callback_data=f"hilo_higher_{user_id}"),
                    InlineKeyboardButton(f"⬇️ Lower ({odds['lower']['multiplier']:.2f}x)", callback_data=f"hilo_lower_{user_id}")
                ],
                [
                    InlineKeyboardButton(f"🔄 Tie ({odds['tie']['multiplier']:.2f}x)", callback_data=f"hilo_tie_{user_id}"),
                    InlineKeyboardButton("⏭️ Skip", callback_data=f"hilo_skip_{user_id}")
                ]
            ]
            if game.round_number > 0:
                payout = game.get_potential_payout()
                keyboard.append([InlineKeyboardButton(f"💰 Cash Out ${payout:.2f}", callback_data=f"hilo_cashout_{user_id}")])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _display_hilo_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, is_new: bool = False):
        """Display the current Hi-Lo game state"""
        if user_id not in self.hilo_sessions:
            return
        
        game = self.hilo_sessions[user_id]
        state = game.get_game_state()
        result_message = None
        
        card_display = state['current_card'] if state['current_card'] else "?"
        
        if game.game_over:
            if game.won or game.cashed_out:
                payout = game.get_payout()
                profit = game.get_profit()
                
                user_data = self.db.get_user(user_id)
                user_data['balance'] += payout
                user_data['total_wagered'] += game.initial_wager
                user_data['games_played'] += 1
                user_data['games_won'] += 1
                user_data['total_pnl'] += profit
                user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + game.initial_wager
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-profit)
                
                result_message = f"@{user_data.get('username', 'Player')} won ${payout:.2f} ({game.current_multiplier:.2f}x)"
                
                message = f"🎴 **Hi-Lo** - {'Cashed Out!' if game.cashed_out else 'You Win!'}\n\n"
                message += f"**Rounds:** {game.round_number}\n"
                message += f"**Final Multiplier:** {game.current_multiplier:.2f}x\n"
                message += f"**Bet:** ${game.initial_wager:.2f}\n"
                message += f"**Payout:** ${payout:.2f} (+${profit:.2f})"
            else:
                user_data = self.db.get_user(user_id)
                user_data['total_wagered'] += game.initial_wager
                user_data['games_played'] += 1
                user_data['total_pnl'] -= game.initial_wager
                user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + game.initial_wager
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(game.initial_wager)
                
                result_message = f"@{user_data.get('username', 'Player')} lost ${game.initial_wager:.2f}"
                
                last_round = game.history[-1] if game.history else {}
                message = f"🎴 **Hi-Lo** - Bust!\n\n"
                message += f"**Current Card:** {last_round.get('current_card', '?')}\n"
                message += f"**Next Card:** {last_round.get('next_card', '?')}\n"
                message += f"**Your Prediction:** {last_round.get('prediction', '?').title()}\n"
                message += f"**Rounds Completed:** {game.round_number}\n"
                message += f"**Lost:** ${game.initial_wager:.2f}"
            
            self.db.record_game({
                'type': 'hilo',
                'player_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'wager': game.initial_wager,
                'rounds': game.round_number,
                'final_multiplier': game.current_multiplier,
                'cashed_out': game.cashed_out,
                'payout': game.get_payout(),
                'result': 'win' if (game.won or game.cashed_out) else 'loss',
                'balance_after': user_data['balance']
            })
            
            # Cancel timeout since game is over
            game_key = f"hilo_{user_id}"
            self.cancel_game_timeout(game_key)
            
            del self.hilo_sessions[user_id]
        else:
            odds = state['odds']
            message = f"🎴 **Hi-Lo**\n\n"
            message += f"**Current Card:** {card_display}"
        
        reply_markup = self._build_hilo_keyboard(game) if user_id in self.hilo_sessions else self._build_hilo_keyboard(game)
        
        if is_new or not update.callback_query:
            sent_msg = await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if user_id in self.hilo_sessions:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        else:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            if user_id in self.hilo_sessions:
                self.button_ownership[(update.callback_query.message.chat_id, update.callback_query.message.message_id)] = user_id
            if result_message:
                await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=result_message, parse_mode="Markdown")
    
    # --- CONNECT 4 GAME ---
    
    async def connect_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Connect 4 PvP game. Usage: /connect @user <amount>"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if self.user_has_active_game(user_id):
            await update.message.reply_text("only one game at a time")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/connect @user <amount>`", parse_mode="Markdown")
            return
        
        opponent_username = context.args[0].lstrip('@')
        
        try:
            wager = round(float(context.args[1]), 2)
        except ValueError:
            await update.message.reply_text("Invalid amount")
            return
        
        if wager < 0.01:
            await update.message.reply_text("Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"Balance: ${user_data['balance']:.2f}")
            return
        
        opponent_data = next((u for u in self.db.data['users'].values() if u.get('username') == opponent_username), None)
        
        if not opponent_data:
            await update.message.reply_text(f"Could not find user @{opponent_username}")
            return
        
        opponent_id = opponent_data['user_id']
        
        if opponent_id == user_id:
            await update.message.reply_text("You cannot challenge yourself")
            return
        
        if self.user_has_active_game(opponent_id):
            await update.message.reply_text(f"@{opponent_username} is already in a game")
            return
        
        if opponent_data['balance'] < wager:
            await update.message.reply_text(f"@{opponent_username} doesn't have enough balance")
            return
        
        game_id = f"c4_{user_id}_{opponent_id}_{int(datetime.now().timestamp())}"
        
        keyboard = [
            [InlineKeyboardButton("Accept Challenge", callback_data=f"connect4_accept_{game_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        self.pending_pvp[game_id] = {
            'type': 'connect4',
            'challenger': user_id,
            'challenger_username': user_data.get('username', 'Unknown'),
            'opponent': opponent_id,
            'opponent_username': opponent_username,
            'wager': wager,
            'timestamp': datetime.now().timestamp()
        }
        
        sent_msg = await update.message.reply_text(
            f"@{opponent_username}, @{user_data.get('username', 'Unknown')} challenges you to Connect 4 for ${wager:.2f}!\n\n"
            f"Click Accept to play.",
            reply_markup=reply_markup
        )
        
        async def delete_challenge_after_timeout():
            await asyncio.sleep(30)
            if game_id in self.pending_pvp:
                del self.pending_pvp[game_id]
                try:
                    await sent_msg.delete()
                except Exception:
                    pass
        
        asyncio.create_task(delete_challenge_after_timeout())
    
    async def _accept_connect4_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        """Accept a Connect 4 challenge and start the dice rolling phase."""
        query = update.callback_query
        user_id = query.from_user.id
        
        if game_id not in self.pending_pvp:
            await query.edit_message_text("Challenge expired or already accepted")
            return
        
        challenge = self.pending_pvp[game_id]
        
        if user_id != challenge['opponent']:
            await query.answer("This challenge is not for you!", show_alert=True)
            return
        
        challenger_id = challenge['challenger']
        wager = challenge['wager']
        
        challenger_data = self.db.get_user(challenger_id)
        opponent_data = self.db.get_user(user_id)
        
        if challenger_data['balance'] < wager:
            await query.edit_message_text(f"@{challenge['challenger_username']} no longer has enough balance")
            del self.pending_pvp[game_id]
            return
        
        if opponent_data['balance'] < wager:
            await query.edit_message_text("You don't have enough balance")
            del self.pending_pvp[game_id]
            return
        
        challenger_data['balance'] -= wager
        opponent_data['balance'] -= wager
        self.db.update_user(challenger_id, {'balance': challenger_data['balance']})
        self.db.update_user(user_id, {'balance': opponent_data['balance']})
        
        challenge['dice_phase'] = True
        challenge['p1_roll'] = None
        challenge['p2_roll'] = None
        
        keyboard = [[InlineKeyboardButton("🎲 Roll Dice", callback_data=f"connect4_roll_{game_id}_1")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"**Connect 4** - ${wager:.2f}\n\n"
            f"@{challenge['challenger_username']}, roll your dice!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def _handle_connect4_dice_roll(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, player_num: int):
        """Handle a player rolling their dice for Connect 4."""
        query = update.callback_query
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        
        if game_id not in self.pending_pvp:
            await query.edit_message_text("Game expired")
            return
        
        challenge = self.pending_pvp[game_id]
        challenger_id = challenge['challenger']
        opponent_id = challenge['opponent']
        wager = challenge['wager']
        
        if player_num == 1:
            if user_id != challenger_id:
                await query.answer("It's not your turn to roll!", show_alert=True)
                return
            
            roll = random.randint(1, 6)
            challenge['p1_roll'] = roll
            
            keyboard = [[InlineKeyboardButton("🎲 Roll Dice", callback_data=f"connect4_roll_{game_id}_2")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"**Connect 4** - ${wager:.2f}\n\n"
                f"🎲 @{challenge['challenger_username']} rolled: {roll}\n\n"
                f"@{challenge['opponent_username']}, roll your dice!",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            if user_id != opponent_id:
                await query.answer("It's not your turn to roll!", show_alert=True)
                return
            
            roll = random.randint(1, 6)
            challenge['p2_roll'] = roll
            p1_roll = challenge['p1_roll']
            
            while roll == p1_roll:
                roll = random.randint(1, 6)
            challenge['p2_roll'] = roll
            
            del self.pending_pvp[game_id]
            
            game = Connect4Game(challenger_id, opponent_id, wager)
            self.connect4_sessions[game_id] = game
            game.set_dice_rolls(p1_roll, roll)
            
            first_player_id = game.get_current_player_id()
            first_username = challenge['challenger_username'] if first_player_id == challenger_id else challenge['opponent_username']
            
            roll_message = f"**Connect 4** - ${wager:.2f}\n\n"
            roll_message += f"🎲 @{challenge['challenger_username']} rolled: {p1_roll}\n"
            roll_message += f"🎲 @{challenge['opponent_username']} rolled: {roll}\n\n"
            roll_message += f"@{first_username} goes first!"
            
            await query.edit_message_text(roll_message, parse_mode="Markdown")
            
            game_key = f"connect4_{game_id}"
            self.start_game_timeout(game_key, "connect4", first_player_id, chat_id, wager, 
                                    bot=context.bot, game_id=game_id, 
                                    opponent_id=challenger_id if first_player_id == opponent_id else opponent_id,
                                    is_pvp=True)
            
            await self._display_connect4_state(update, context, game_id)
    
    def _build_connect4_keyboard(self, game: Connect4Game, game_id: str) -> InlineKeyboardMarkup:
        """Build the full grid keyboard for Connect 4 with clickable invisible buttons."""
        valid_cols = game.get_valid_columns()
        keyboard = []
        
        for row in range(6):
            row_buttons = []
            for col in range(7):
                cell = game.board[row][col]
                if cell == game.EMPTY:
                    if col in valid_cols:
                        row_buttons.append(InlineKeyboardButton("\u3164", callback_data=f"connect4_drop_{game_id}_{col}"))
                    else:
                        row_buttons.append(InlineKeyboardButton("\u3164", callback_data="connect4_noop"))
                elif cell == game.PLAYER1:
                    row_buttons.append(InlineKeyboardButton("🔴", callback_data="connect4_noop"))
                else:
                    row_buttons.append(InlineKeyboardButton("🟡", callback_data="connect4_noop"))
            keyboard.append(row_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    def _build_connect4_final_board(self, game: Connect4Game) -> InlineKeyboardMarkup:
        """Build the final board display for Connect 4 (non-clickable)."""
        keyboard = []
        
        for row in range(6):
            row_buttons = []
            for col in range(7):
                cell = game.board[row][col]
                if cell == game.EMPTY:
                    row_buttons.append(InlineKeyboardButton("\u3164", callback_data="connect4_noop"))
                elif cell == game.PLAYER1:
                    row_buttons.append(InlineKeyboardButton("🔴", callback_data="connect4_noop"))
                else:
                    row_buttons.append(InlineKeyboardButton("🟡", callback_data="connect4_noop"))
            keyboard.append(row_buttons)
        
        return InlineKeyboardMarkup(keyboard)
    
    async def _display_connect4_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str, is_new: bool = True):
        """Display the current Connect 4 game state."""
        if game_id not in self.connect4_sessions:
            return
        
        game = self.connect4_sessions[game_id]
        state = game.get_game_state()
        
        p1_data = self.db.get_user(game.player1_id)
        p2_data = self.db.get_user(game.player2_id)
        p1_username = p1_data.get('username', 'Player 1')
        p2_username = p2_data.get('username', 'Player 2')
        
        current_username = p1_username if game.current_player == game.PLAYER1 else p2_username
        
        message = f"**Connect 4** - ${game.wager:.2f}\n\n"
        message += f"🔴 @{p1_username}\n"
        message += f"🟡 @{p2_username}\n"
        
        win_announcement = None
        
        if game.game_over:
            final_board = self._build_connect4_final_board(game)
            if game.is_draw:
                message += "\n**Draw!** Wagers returned."
                
                p1_data['balance'] += game.wager
                p2_data['balance'] += game.wager
                self.db.update_user(game.player1_id, {'balance': p1_data['balance']})
                self.db.update_user(game.player2_id, {'balance': p2_data['balance']})
                
                game_key = f"connect4_{game_id}"
                self.cancel_game_timeout(game_key)
                
                del self.connect4_sessions[game_id]
                reply_markup = final_board
            else:
                winner_id = state['winner_id']
                loser_id = game.player2_id if winner_id == game.player1_id else game.player1_id
                winner_username = p1_username if winner_id == game.player1_id else p2_username
                winner_emoji = "🔴" if winner_id == game.player1_id else "🟡"
                
                total_pot = game.wager * 2
                profit = game.wager
                winner_data = self.db.get_user(winner_id)
                loser_data = self.db.get_user(loser_id)
                
                winner_data['balance'] += total_pot
                winner_data['games_won'] = winner_data.get('games_won', 0) + 1
                winner_data['games_played'] += 1
                winner_data['total_wagered'] += game.wager
                winner_data['total_pnl'] += game.wager
                
                loser_data['games_played'] += 1
                loser_data['total_wagered'] += game.wager
                loser_data['total_pnl'] -= game.wager
                
                self.db.update_user(winner_id, winner_data)
                self.db.update_user(loser_id, loser_data)
                
                message += f"\n**{winner_emoji} @{winner_username} wins!**"
                win_announcement = f"{winner_emoji} @{winner_username} won ${profit:.2f}"
                
                self.db.record_game({
                    'type': 'connect4',
                    'winner_id': winner_id,
                    'loser_id': loser_id,
                    'wager': game.wager,
                    'total_pot': total_pot,
                    'result': 'win',
                    'winner_balance_after': winner_data['balance'],
                    'loser_balance_after': loser_data['balance']
                })
                
                game_key = f"connect4_{game_id}"
                self.cancel_game_timeout(game_key)
                
                del self.connect4_sessions[game_id]
                reply_markup = final_board
        else:
            current_emoji = "🔴" if game.current_player == game.PLAYER1 else "🟡"
            message += f"\n{current_emoji} @{current_username}'s turn"
            reply_markup = self._build_connect4_keyboard(game, game_id)
        
        chat_id = update.effective_chat.id
        
        if is_new:
            sent_msg = await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup, parse_mode="Markdown")
            if reply_markup and not game.game_over:
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = game.get_current_player_id()
        else:
            query = update.callback_query
            await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode="Markdown")
            if reply_markup and game_id in self.connect4_sessions:
                self.button_ownership[(query.message.chat_id, query.message.message_id)] = game.get_current_player_id()
        
        if win_announcement:
            await context.bot.send_message(chat_id=chat_id, text=win_announcement, parse_mode="Markdown")
    
    async def tip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send money to another player."""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/tip <amount> @user`", parse_mode="Markdown")
            return
        
        try:
            amount = round(float(context.args[0]), 2)
        except ValueError:
            await update.message.reply_text("❌ Invalid amount")
            return
            
        if amount <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
            
        if amount > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return

        recipient_username = context.args[1].lstrip('@')
        recipient_data = next((u for u in self.db.data['users'].values() if u.get('username') == recipient_username), None)

        if not recipient_data:
            await update.message.reply_text(f"❌ Could not find user with username @{recipient_username}.")
            return
            
        if recipient_data['user_id'] == user_id:
            await update.message.reply_text("❌ You cannot tip yourself.")
            return

        # Perform transaction
        user_data['balance'] -= amount
        recipient_data['balance'] += amount
        
        self.db.update_user(user_id, user_data)
        self.db.update_user(recipient_data['user_id'], recipient_data)
        
        self.db.add_transaction(user_id, "tip_sent", -amount, f"Tip to @{recipient_username}")
        self.db.add_transaction(recipient_data['user_id'], "tip_received", amount, f"Tip from @{update.effective_user.username or update.effective_user.first_name}")

        await update.message.reply_text(
            f"✅ Success! You tipped @{recipient_username} **${amount:.2f}**.",
            parse_mode="Markdown"
        )

    async def get_ltc_price_usd(self) -> Optional[float]:
        """Get current LTC price in USD from Plisio API, fallback to manual rate."""
        api_key = os.getenv('PLISIO_API_KEY')
        
        # Try Plisio API first for exact real-time price
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.plisio.net/api/v1/currencies/USD"
                params = {"api_key": api_key}
                
                async with session.get(url, params=params, timeout=10) as response:
                    result = await response.json()
                    logger.info(f"[PLISIO] Currencies response: {result.get('status')}")
                    
                    if result.get('status') == 'success':
                        currencies = result.get('data', [])
                        for currency in currencies:
                            if currency.get('cid') == 'LTC':
                                price = float(currency.get('price_usd', 0))
                                logger.info(f"[PLISIO] LTC price: ${price}")
                                return price
                    
                    logger.warning(f"[PLISIO] Could not get LTC price: {result}")
        except Exception as e:
            logger.warning(f"[PLISIO] Error fetching LTC price: {e}")
        
        # Fallback to manual rate if Plisio fails
        manual_rate = self.db.data.get('manual_ltc_rate')
        if manual_rate:
            logger.info(f"[LTC PRICE] Using manual fallback rate: ${manual_rate}")
            return float(manual_rate)
        
        logger.error("[LTC PRICE] Plisio failed and no manual rate set. Use /setltcrate to set one.")
        return None

    async def generate_coinremitter_address(self, user_id: int, currency: str = 'LTC') -> Optional[Dict[str, Any]]:
        """Generate a unique deposit address via Plisio API for specified currency."""
        api_key = os.getenv('PLISIO_API_KEY')
        
        if not api_key:
            logger.error("[PLISIO DEBUG] PLISIO_API_KEY not configured!")
            return None
        
        if currency not in SUPPORTED_DEPOSIT_CRYPTOS:
            logger.error(f"[PLISIO DEBUG] Unsupported currency: {currency}")
            return None
        
        webhook_url = os.getenv('WEBHOOK_URL', 'https://casino.vps.webdock.cloud')
        callback_url = f"{webhook_url}/webhook/deposit?json=true"
        
        logger.info(f"[PLISIO DEBUG] Generating {currency} deposit address for user {user_id}")
        logger.info(f"[PLISIO DEBUG] API Key (first 10 chars): {api_key[:10] if len(api_key) > 10 else 'SHORT'}...")
        logger.info(f"[PLISIO DEBUG] Callback URL: {callback_url}")
        
        url = "https://api.plisio.net/api/v1/invoices/new"
        params = {
            'source_currency': 'USD',
            'source_amount': '0.01',
            'currency': currency,
            'order_number': f'user_{user_id}_{currency}_{int(datetime.now().timestamp())}',
            'order_name': f'Deposit_User_{user_id}_{currency}',
            'callback_url': callback_url,
            'api_key': api_key,
            'expire_min': '0',
            'allowed_psys_cids': currency
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    result = await response.json()
                    logger.info(f"[PLISIO DEBUG] Invoice response: {result}")
                    if result.get('status') == 'success':
                        data = result.get('data', {})
                        logger.info(f"[PLISIO DEBUG] Full data response: {data}")
                        
                        txn_id = data.get('txn_id')
                        invoice_url = data.get('invoice_url')
                        address = data.get('wallet_hash') or data.get('wallet') or data.get('address')
                        qr_code = data.get('qr_code')
                        
                        # Use invoice_url if no direct wallet address available
                        if not address and invoice_url:
                            logger.info(f"[PLISIO DEBUG] Using invoice URL for deposit: {invoice_url}")
                            address = invoice_url  # Store invoice URL as the "address"
                        
                        logger.info(f"[PLISIO DEBUG] Generated {currency} deposit info: {address}")
                        return {
                            'address': address,
                            'qr_code': qr_code,
                            'expire_on': data.get('expire_utc'),
                            'txn_id': txn_id,
                            'invoice_url': invoice_url,
                            'currency': currency
                        }
                    else:
                        error_msg = result.get('data', {}).get('message', result.get('message', 'Unknown error'))
                        logger.error(f"[PLISIO DEBUG] API error: {error_msg} - Full response: {result}")
                        return None
        except asyncio.TimeoutError:
            logger.error(f"[PLISIO DEBUG] Request timed out after 15 seconds")
            return None
        except Exception as e:
            logger.error(f"[PLISIO DEBUG] Request failed: {e}")
            return None

    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show crypto currency selection menu for deposits."""
        user_id = update.effective_user.id
        if update.effective_chat.type != "private" and not self.is_admin(user_id):
            await update.message.reply_text("❌ Use /deposit in DMs only.")
            return
        
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        keyboard = []
        for code, info in SUPPORTED_DEPOSIT_CRYPTOS.items():
            btn = InlineKeyboardButton(info['name'], callback_data=f"deposit_crypto_{code}")
            keyboard.append([btn])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(
            f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id

    async def show_deposit_address(self, update: Update, context: ContextTypes.DEFAULT_TYPE, currency: str):
        """Show user their unique deposit address for the selected currency."""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        
        crypto_info = SUPPORTED_DEPOSIT_CRYPTOS.get(currency)
        if not crypto_info:
            await query.edit_message_text("❌ Invalid currency selected.")
            return
        
        address_key = f'{currency.lower()}_deposit_address'
        qr_key = f'{currency.lower()}_qr_code'
        
        # Always generate a fresh invoice for each deposit request
        await query.edit_message_text(f"⏳ Generating your {currency} deposit address...")
        
        address_data = await self.generate_coinremitter_address(user_id, currency)
        
        if address_data:
            user_deposit_address = address_data.get('address')
            qr_code_url = address_data.get('qr_code')
            
            user_data[address_key] = user_deposit_address
            user_data[qr_key] = qr_code_url
            user_data[f'{currency.lower()}_address_expires'] = address_data.get('expire_on')
            self.db.update_user(user_id, user_data)
            self.db.save_data()
        else:
            await query.edit_message_text(f"❌ Could not generate {currency} deposit address. Contact admin.")
            return
        
        if not user_deposit_address:
            await query.edit_message_text(f"❌ {currency} deposits temporarily unavailable. Contact admin.")
            return
        
        # Check if it's an invoice URL (Plisio payment page) or direct wallet address
        is_invoice_url = user_deposit_address.startswith('http')
        
        fee_percent = crypto_info.get('fee_percent', 0.02) * 100
        
        # Calculate expiry time (1 hour from now)
        from datetime import datetime, timedelta
        expiry_time = datetime.now() + timedelta(hours=1)
        expiry_timestamp = int(expiry_time.timestamp())
        
        # Store deposit request info for tracking
        deposit_request_key = f'{currency.lower()}_pending_deposit'
        user_data[deposit_request_key] = {
            'created_at': datetime.now().isoformat(),
            'expires_at': expiry_time.isoformat(),
            'tx_id': None
        }
        self.db.update_user(user_id, user_data)
        self.db.save_data()
        
        # Get the actual wallet address (not invoice URL)
        if is_invoice_url:
            # For invoice URLs, we still show the payment page button but with better text
            keyboard = [
                [InlineKeyboardButton(f"💳 Open {currency} Payment Page", url=user_deposit_address)],
                [InlineKeyboardButton("⬅️ Back", callback_data="deposit_back")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            deposit_text = f"""Your unique {currency} wallet address will be shown on the payment page.

Click the button below to view your deposit address.

59:59

TX ID: _waiting for deposit..._"""
        else:
            # Show direct wallet address
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="deposit_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            deposit_text = f"""Your unique {currency} deposit address:

`{user_deposit_address}`

59:59

TX ID: _waiting for deposit..._"""
        
        await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=reply_markup)

    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start withdrawal flow with payment method selection."""
        user_id = update.effective_user.id
        if update.effective_chat.type != "private" and not self.is_admin(user_id):
            await update.message.reply_text("❌ Use /withdraw in DMs only.")
            return
        
        user_data = self.ensure_user_registered(update)
        
        min_possible = min(info.get('min_withdraw', 1.00) for info in SUPPORTED_WITHDRAWAL_CRYPTOS.values())
        if user_data['balance'] < min_possible:
            await update.message.reply_text(
                f"❌ Minimum withdrawal is ${min_possible:.2f}\n\nYour balance: **${user_data['balance']:.2f}**",
                parse_mode="Markdown"
            )
            return
        
        keyboard = []
        for code, info in SUPPORTED_WITHDRAWAL_CRYPTOS.items():
            btn = InlineKeyboardButton(info['name'], callback_data=f"withdraw_method_{code.lower()}")
            keyboard.append([btn])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(
            f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        return
    
    async def process_withdrawal_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float, ltc_address: str):
        """Process the actual withdrawal after button flow."""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
        # Deduct balance immediately (hold for withdrawal)
        user_data['balance'] -= amount
        self.db.update_user(user_id, user_data)
        
        # Store pending withdrawal
        if 'pending_withdrawals' not in self.db.data:
            self.db.data['pending_withdrawals'] = []
        
        withdrawal_request = {
            'user_id': user_id,
            'username': username,
            'amount': amount,
            'ltc_address': ltc_address,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        self.db.data['pending_withdrawals'].append(withdrawal_request)
        self.db.save_data()
        
        query = update.callback_query
        await query.edit_message_text(
            f"✅ **Withdrawal Request Submitted**\n\nAmount: **${amount:.2f}**\nTo: `{ltc_address}`\n\nYour withdrawal is being processed.\n\nNew balance: ${user_data['balance']:.2f}",
            parse_mode="Markdown"
        )
        
        # Notify admins
        for admin_id in list(self.env_admin_ids) + list(self.dynamic_admin_ids):
            try:
                await self.app.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **New Withdrawal Request**\n\nUser: @{username} (ID: {user_id})\nAmount: ${amount:.2f}\nLTC Address: `{ltc_address}`\n\nUse `/processwithdraw {user_id}` after sending.",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    async def handle_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for withdrawal amount and address."""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Step 1: User is entering withdrawal amount
        if 'pending_withdraw_method' in context.user_data and 'pending_withdraw_amount' not in context.user_data:
            async def send_error_with_ownership(msg_text):
                sent_msg = await update.message.reply_text(msg_text)
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
            
            try:
                amount = round(float(text), 2)
            except ValueError:
                await send_error_with_ownership("Invalid amount. Please enter a number:")
                return
            
            user_data = self.db.get_user(user_id)
            
            if amount <= 0:
                await send_error_with_ownership("Amount must be positive. Please enter a valid amount:")
                return
            
            currency = context.user_data.get('pending_withdraw_method', 'ltc').upper()
            min_withdraw = get_crypto_min_withdraw(currency)
            if amount < min_withdraw:
                await send_error_with_ownership(f"Minimum {currency} withdrawal is ${min_withdraw:.2f}. Please enter a valid amount:")
                return
            
            if amount > user_data['balance']:
                await send_error_with_ownership(f"Insufficient balance. Your balance: ${user_data['balance']:.2f}\n\nPlease enter a valid amount:")
                return
            
            context.user_data['pending_withdraw_amount'] = amount
            
            currency = context.user_data.get('pending_withdraw_method', 'ltc').upper()
            crypto_info = SUPPORTED_WITHDRAWAL_CRYPTOS.get(currency, {'name': currency})
            fee_percent = crypto_info.get('fee_percent', 0.02) * 100
            
            keyboard = [
                [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_back_to_amount")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            sent_msg = await update.message.reply_text(
                f"Withdraw ${amount:.2f} {crypto_info['name']}\n\nFee: {fee_percent:.1f}%\n\nEnter your {currency} wallet address:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
            return
        
        # Step 2: User is entering wallet address
        if 'pending_withdraw_amount' in context.user_data:
            wallet_address = text
            amount = context.user_data.pop('pending_withdraw_amount')
            currency = context.user_data.pop('pending_withdraw_method', 'ltc').upper()
            crypto_info = SUPPORTED_WITHDRAWAL_CRYPTOS.get(currency, {'name': currency})
            
            if len(wallet_address) < 20:
                keyboard = [
                    [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_back_to_amount")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                sent_msg = await update.message.reply_text(
                    f"Invalid {currency} address. Please enter a valid address:",
                    reply_markup=reply_markup
                )
                self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                context.user_data['pending_withdraw_amount'] = amount
                context.user_data['pending_withdraw_method'] = currency.lower()
                return
            
            user_data = self.db.get_user(user_id)
            
            if amount > user_data['balance']:
                context.user_data.pop('pending_withdraw_amount', None)
                context.user_data.pop('pending_withdraw_method', None)
                await update.message.reply_text(
                    f"❌ Insufficient balance. Your balance: ${user_data['balance']:.2f}\n\nWithdrawal cancelled. Use /withdraw to try again."
                )
                return
            
            username = user_data.get('username', f'User{user_id}')
            
            user_data['balance'] -= amount
            self.db.update_user(user_id, user_data)
            
            if 'pending_withdrawals' not in self.db.data:
                self.db.data['pending_withdrawals'] = []
            
            withdrawal_request = {
                'user_id': user_id,
                'username': username,
                'amount': amount,
                'wallet_address': wallet_address,
                'currency': currency,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            self.db.data['pending_withdrawals'].append(withdrawal_request)
            self.db.save_data()
            
            await update.message.reply_text(
                f"✅ **Withdrawal Request Submitted**\n\nAmount: **${amount:.2f}**\nCurrency: **{crypto_info['name']}**\nTo: `{wallet_address}`\n\nYour withdrawal is being processed.\n\nNew balance: ${user_data['balance']:.2f}",
                parse_mode="Markdown"
            )
            
            # Send to withdrawal approval group with buttons
            withdrawal_group_id = int(os.getenv('WITHDRAWAL_GROUP_ID', '-5089646716'))
            withdraw_id = len(self.db.data['pending_withdrawals']) - 1
            
            logger.info(f"[WITHDRAWAL DEBUG] Attempting to send withdrawal notification to group {withdrawal_group_id}")
            logger.info(f"[WITHDRAWAL DEBUG] User: {username}, Amount: ${amount:.2f}, Currency: {currency}, Address: {wallet_address}")
            
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data=f"withdraw_approve_{withdraw_id}_{user_id}_{amount}_{currency}"),
                 InlineKeyboardButton("❌ Deny", callback_data=f"withdraw_deny_{withdraw_id}_{user_id}_{amount}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                result = await self.app.bot.send_message(
                    chat_id=withdrawal_group_id,
                    text=f"🔔 **New Withdrawal Request**\n\nUser: @{username} (ID: `{user_id}`)\nAmount: **${amount:.2f}**\nCurrency: **{currency}**\nAddress: `{wallet_address}`",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                logger.info(f"[WITHDRAWAL DEBUG] Successfully sent notification! Message ID: {result.message_id}")
            except Exception as e:
                logger.error(f"[WITHDRAWAL DEBUG] Failed to send to withdrawal group {withdrawal_group_id}: {e}")
                logger.error(f"[WITHDRAWAL DEBUG] Error type: {type(e).__name__}")
                await update.message.reply_text(
                    f"⚠️ Withdrawal submitted but admin notification failed.\nError: {str(e)[:100]}\n\nAdmins have been logged.",
                    parse_mode="Markdown"
                )

    async def pending_deposits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all pending deposits (Admin only)."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only.")
            return
        
        pending = self.db.data.get('pending_deposits', [])
        pending = [d for d in pending if d.get('status') == 'pending']
        
        if not pending:
            await update.message.reply_text("✅ No pending deposits.")
            return
        
        text = "📥 **Pending Deposits**\n\n"
        for i, dep in enumerate(pending[-20:], 1):
            text += f"{i}. @{dep['username']} (ID: {dep['user_id']})\n   Amount: ${dep['amount']:.2f}\n   TX: `{dep['tx_id']}`\n\n"
        
        text += "Use `/approvedeposit <user_id> <amount>` to approve."
        await update.message.reply_text(text, parse_mode="Markdown")

    async def approve_deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Approve a deposit and credit user balance (Admin only)."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/approvedeposit <user_id> <amount>`", parse_mode="Markdown")
            return
        
        try:
            target_user_id = int(context.args[0])
            amount = round(float(context.args[1]), 2)
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID or amount.")
            return
        
        user_data = self.db.get_user(target_user_id)
        deposit_fee = 0.01  # 1% deposit fee (not shown to user)
        credited_amount = round(amount * (1 - deposit_fee), 2)
        user_data['balance'] += credited_amount
        self.db.update_user(target_user_id, user_data)
        self.db.add_transaction(target_user_id, "deposit", credited_amount, "LTC Deposit (Approved)")
        self.db.record_deposit(target_user_id, user_data.get('username', f'User{target_user_id}'), amount)
        
        # Mark deposit as approved
        pending = self.db.data.get('pending_deposits', [])
        for dep in pending:
            if dep['user_id'] == target_user_id and dep.get('status') == 'pending':
                dep['status'] = 'approved'
                break
        self.db.save_data()
        
        await update.message.reply_text(
            f"✅ **Deposit Approved**\n\nUser ID: {target_user_id}\nAmount: ${amount:.2f}\nNew Balance: ${user_data['balance']:.2f}",
            parse_mode="Markdown"
        )
        
        # Notify user
        try:
            await self.app.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ **Deposit Approved!**\n\nAmount: **${amount:.2f}** has been credited.\n\nNew Balance: ${user_data['balance']:.2f}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")

    async def pending_withdraws_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all pending withdrawals (Admin only)."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only.")
            return
        
        pending = self.db.data.get('pending_withdrawals', [])
        pending = [w for w in pending if w.get('status') == 'pending']
        
        if not pending:
            await update.message.reply_text("✅ No pending withdrawals.")
            return
        
        text = "📤 **Pending Withdrawals**\n\n"
        for i, wit in enumerate(pending[-20:], 1):
            text += f"{i}. @{wit['username']} (ID: {wit['user_id']})\n   Amount: ${wit['amount']:.2f}\n   LTC: `{wit['ltc_address']}`\n\n"
        
        text += "Use `/processwithdraw <user_id>` after sending LTC."
        await update.message.reply_text(text, parse_mode="Markdown")

    async def get_crypto_price_usd(self, currency: str) -> Optional[float]:
        """Get current crypto price in USD from Plisio API."""
        api_key = os.getenv('PLISIO_API_KEY')
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.plisio.net/api/v1/currencies/USD"
                params = {"api_key": api_key}
                
                async with session.get(url, params=params) as response:
                    result = await response.json()
                    
                    if result.get('status') == 'success':
                        currencies = result.get('data', [])
                        for curr in currencies:
                            if curr.get('cid') == currency:
                                price = float(curr.get('price_usd', 0))
                                logger.info(f"[PLISIO DEBUG] {currency} price: ${price}")
                                return price
                    
                    logger.error(f"[PLISIO DEBUG] Could not get {currency} price: {result}")
                    return None
        except Exception as e:
            logger.error(f"[PLISIO DEBUG] Error fetching {currency} price: {e}")
            return None

    async def send_crypto_withdrawal(self, wallet_address: str, usd_amount: float, currency: str = 'LTC') -> dict:
        """Send crypto withdrawal via Plisio API. Converts USD to crypto first."""
        api_key = os.getenv('PLISIO_API_KEY')
        
        if not api_key:
            logger.error("[PLISIO DEBUG] PLISIO_API_KEY not configured for withdrawal!")
            return {"success": False, "error": "API key not configured"}
        
        logger.info(f"[PLISIO DEBUG] Initiating {currency} withdrawal: ${usd_amount} USD to {wallet_address}")
        
        # Get current crypto price from API
        crypto_price = await self.get_crypto_price_usd(currency)
        if not crypto_price or crypto_price <= 0:
            logger.error(f"[PLISIO DEBUG] Could not get {currency} price for conversion!")
            return {"success": False, "error": f"Could not get {currency} price"}
        logger.info(f"[PLISIO DEBUG] Using {currency} rate: ${crypto_price}")
        
        # Convert USD to crypto (USD / price per crypto = crypto amount)
        crypto_amount = usd_amount / crypto_price
        crypto_amount = round(crypto_amount, 8)
        
        logger.info(f"[PLISIO DEBUG] Converted ${usd_amount} USD to {crypto_amount} {currency} (rate: ${crypto_price})")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.plisio.net/api/v1/operations/withdraw"
                params = {
                    "api_key": api_key,
                    "currency": currency,
                    "to": wallet_address,
                    "amount": str(crypto_amount),
                    "type": "cash_out"
                }
                logger.info(f"[PLISIO DEBUG] Withdrawal params: currency={currency}, amount={crypto_amount} (${usd_amount} USD), type=cash_out")
                
                async with session.get(url, params=params) as response:
                    result = await response.json()
                    logger.info(f"[PLISIO DEBUG] Withdrawal response: {result}")
                    
                    if result.get('status') == 'success':
                        tx_id = result.get('data', {}).get('id')
                        tx_url = result.get('data', {}).get('tx_url')
                        logger.info(f"[PLISIO DEBUG] Withdrawal successful! TX ID: {tx_id}")
                        return {
                            "success": True,
                            "tx_id": tx_id,
                            "tx_url": tx_url,
                            "currency": currency,
                            "crypto_amount": crypto_amount
                        }
                    else:
                        error_msg = result.get('data', {}).get('message', 'Unknown error')
                        full_error = result.get('data', result)
                        logger.error(f"[PLISIO DEBUG] Withdrawal failed: {error_msg}")
                        logger.error(f"[PLISIO DEBUG] Full error response: {full_error}")
                        return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"[PLISIO DEBUG] Withdrawal request exception: {e}")
            return {"success": False, "error": str(e)}

    async def send_ltc_withdrawal(self, ltc_address: str, usd_amount: float) -> dict:
        """Legacy wrapper for LTC withdrawals."""
        return await self.send_crypto_withdrawal(ltc_address, usd_amount, 'LTC')

    async def process_withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process withdrawal and send LTC via Plisio (Admin only)."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Admin only.")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("Usage: `/processwithdraw <user_id>`", parse_mode="Markdown")
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID.")
            return
        
        # Find pending withdrawal
        pending = self.db.data.get('pending_withdrawals', [])
        withdrawal = None
        for wit in pending:
            if wit['user_id'] == target_user_id and wit.get('status') == 'pending':
                withdrawal = wit
                break
        
        if not withdrawal:
            await update.message.reply_text("❌ No pending withdrawal found for this user.")
            return
        
        await update.message.reply_text("⏳ Sending LTC via Plisio...")
        
        # Send via Plisio API
        result = await self.send_ltc_withdrawal(withdrawal['ltc_address'], withdrawal['amount'])
        
        if result['success']:
            withdrawal['status'] = 'processed'
            withdrawal['tx_id'] = result.get('tx_id')
            withdrawal['tx_url'] = result.get('tx_url')
            
            self.db.add_transaction(target_user_id, "withdrawal", -withdrawal['amount'], f"LTC Withdrawal to {withdrawal['ltc_address'][:20]}...")
            self.db.save_data()
            
            tx_id = result.get('tx_id', '')
            tx_url = result.get('tx_url', '')
            tx_info = f"\nTX: `{tx_id}`" if tx_id else ""
            explorer_link = f"\n[View on Blockchain]({tx_url})" if tx_url else ""
            
            if tx_id:
                if 'processed_withdrawal_txids' not in self.db.data:
                    self.db.data['processed_withdrawal_txids'] = []
                self.db.data['processed_withdrawal_txids'].append(tx_id)
                if len(self.db.data['processed_withdrawal_txids']) > 1000:
                    self.db.data['processed_withdrawal_txids'] = self.db.data['processed_withdrawal_txids'][-1000:]
                self.db.save_data()
            
            await update.message.reply_text(
                f"✅ **Withdrawal Sent!**\n\nUser ID: {target_user_id}\nAmount: ${withdrawal['amount']:.2f}\nTo: `{withdrawal['ltc_address']}`{tx_info}{explorer_link}",
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            # Notify user
            try:
                await self.app.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✅ **Withdrawal Sent!**\n\n**${withdrawal['amount']:.2f}** has been sent to your LTC address.{explorer_link}\n\nPlease allow a few minutes for blockchain confirmation.",
                    parse_mode="Markdown",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Failed to notify user {target_user_id}: {e}")
        else:
            await update.message.reply_text(
                f"❌ **Withdrawal Failed**\n\nError: {result.get('error', 'Unknown error')}\n\nThe user's balance was already deducted. Use `/givebal {target_user_id} {withdrawal['amount']}` to refund if needed.",
                parse_mode="Markdown"
            )

    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sends the database file as a backup (Admin only)."""
        if not self.is_admin(update.effective_user.id):
             await update.message.reply_text("❌ This command is for administrators only.")
             return
             
        if os.path.exists(self.db.file_path):
            await update.message.reply_document(
                document=open(self.db.file_path, 'rb'),
                filename=self.db.file_path,
                caption="Gran Tesero Database Backup"
            )
        else:
            await update.message.reply_text("❌ Database file not found.")
    
    async def save_sticker_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a sticker file_id for roulette numbers"""
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                f"Usage: `/savesticker <number> <file_id>`\nNumbers: 00, 0-36",
                parse_mode="Markdown"
            )
            return
        
        number = context.args[0]
        file_id = context.args[1]
        
        # Validate number is valid roulette number
        valid_numbers = ['00', '0'] + [str(i) for i in range(1, 37)]
        if number not in valid_numbers:
            await update.message.reply_text(f"❌ Invalid number. Must be: 00, 0, 1, 2, 3... 36")
            return
        
        # Save to database
        if 'roulette' not in self.stickers:
            self.stickers['roulette'] = {}
        
        self.stickers['roulette'][number] = file_id
        self.db.data['stickers'] = self.stickers
        self.db.save_data()
        
        await update.message.reply_text(f"✅ Sticker saved for roulette number '{number}'!")
        
    async def list_stickers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all configured stickers"""
        sticker_text = "🎨 **Roulette Stickers**\n\n"
        
        roulette_stickers = self.stickers.get('roulette', {})
        
        # Count how many are set
        all_numbers = ['00', '0'] + [str(i) for i in range(1, 37)]
        saved_count = sum(1 for num in all_numbers if num in roulette_stickers and roulette_stickers[num])
        
        sticker_text += f"Saved: {saved_count}/38"
        await update.message.reply_text(sticker_text, parse_mode="Markdown")
    
    async def save_roulette_stickers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save all 38 roulette stickers to the database"""
        # Initialize roulette stickers if not present
        if 'roulette' not in self.stickers:
            self.stickers['roulette'] = {}
        
        # Save all 38 roulette sticker IDs
        self.stickers['roulette'] = {
            "00": "CAACAgQAAxkBAAEPnjFo-TLLYpgTZExC4IIOG6PIXwsviAAC1BgAAkmhgFG_0u82E59m3DYE",
            "0": "CAACAgQAAxkBAAEPnjNo-TMFaqDdWCkRDNlus4jcuamAAwACOh0AAtQAAYBRlMLfm2ulRSM2BA",
            "1": "CAACAgQAAxkBAAEPnjRo-TMFH5o5R9ztNtTFBJmQVK_t3wACqBYAAvTrgVE4WCoxbBzVCDYE",
            "2": "CAACAgQAAxkBAAEPnjdo-TMvGdoX-f6IAuR7kpYO-hh9fwAC1RYAAob0eVF1zbcG00UjMzYE",
            "3": "CAACAgQAAxkBAAEPnjho-TMwui0CFuGEK5iwS7xMRDiPfgACSRgAAs74gVEyHQtTsRykGjYE",
            "4": "CAACAgQAAxkBAAEPnj1o-TNGYNdmhy4n5Uyp3pzWmukTgAACfBgAAg3IgFGEjdLKewti5zYE",
            "5": "CAACAgQAAxkBAAEPnj5o-TNHTKLFF2NpdxfLhHnsnFGTXgACyhYAAltygVECKXn73kUyCjYE",
            "6": "CAACAgQAAxkBAAEPnkFo-TNPGqrsJJwZNwUe_I6k4W86cwACyxoAAgutgVGyiCe4lNK2-DYE",
            "7": "CAACAgQAAxkBAAEPnkJo-TNPksXPcYnpXDWYQC68AAGlqzQAAtUYAAKU_IFRJTHChQd2yfw2BA",
            "8": "CAACAgQAAxkBAAEPnkdo-TQOIBN5WtoKKnvcthXdcy0LLgACgBQAAmlWgVFImh6M5RcAAdI2BA",
            "9": "CAACAgQAAxkBAAEPnkho-TQO92px4jOuq80nT2uWjURzSAAC4BcAAvPKeVFBx-TZycAWDzYE",
            "10": "CAACAgQAAxkBAAEPnkto-TZ8-6moW-biByRYl8J2QEPnTwAC8hgAArnAgFGen1zgHwABLPc2BA",
            "11": "CAACAgQAAxkBAAEPnkxo-TZ8ncZZ7FYYyFMJHXRv2rB0TwAC2RMAAmzdgVEao0YAAdIy41g2BA",
            "12": "CAACAgQAAxkBAAEPnk1o-TZ9z6xAxxIeccUPXoQQ9VaikQACVRgAAovngVFUjR-qYgq8LDYE",
            "13": "CAACAgQAAxkBAAEPnlFo-TbUs79Rm549dK3JK2L3P83q-QACTR0AAmc0gFHXnJ509OdiOjYE",
            "14": "CAACAgQAAxkBAAEPnlJo-TbUCpjrhSxP-x84jkBerEYB8AACQxkAAqXDeVEQ5uCH3dK9OjYE",
            "15": "CAACAgQAAxkBAAEPnlNo-TbUZokc7ubz-neSYtK9kxQ0DAACrRYAAlBWgVH9BqGde-NivjYE",
            "16": "CAACAgQAAxkBAAEPnlRo-TbUiOcqxKI6HNExFR8yT3qyvAACrxsAAkcfeVG9im0F0tuZPzYE",
            "17": "CAACAgQAAxkBAAEPnllo-TdIFRtpAW3PeDbxD2QxTgjk2QACLhgAAiuXgVHaPo1woXZEYTYE",
            "18": "CAACAgQAAxkBAAEPnlpo-TdI9Gdz2Nv3icxluy8jC3keBwACYxkAAnx7eFGsZP2AXXBKwzYE",
            "19": "CAACAgQAAxkBAAEPnlto-TdIUktLbTIhkihQz3ymy4lUIwACKRkAArDwgFH0iKqIPPiHYDYE",
            "20": "CAACAgQAAxkBAAEPnlxo-TdJVrOSPiCRuD8Jc0XGvF3B8AACcxoAAr7OeFGSuSoHyKxf5TYE",
            "21": "CAACAgQAAxkBAAEPnl1o-TdJ1jlMSjGQPO0zkaS_rOv5JQACxhcAAv1dgFF3khtGYFneYzYE",
            "22": "CAACAgQAAxkBAAEPnmNo-Te2OhfAwfprG1HfmY-UNtkEAgADGQACE8KAUSJTKzPQQQ9INgQ",
            "23": "CAACAgQAAxkBAAEPnmRo-Te3rAHmt7_CRgFp55KSNVYdKwACTBgAAundgVF6unXyM34ZYzYE",
            "24": "CAACAgQAAxkBAAEPnmVo-Te3LcVARwsUx3Akt75bruvNXAAC4RoAAnkvgFHRL4l2927wnDYE",
            "25": "CAACAgQAAxkBAAEPnmZo-Te3lY0O1JxF8tTLYJJhN1QcnAAC5hcAAiPegFFsMkNzpqfR0zYE",
            "26": "CAACAgQAAxkBAAEPnmto-TgIsR6UdO8EukNYajboFnX3mgACzSAAAn15gVG-oQ4oaJLYrzYE",
            "27": "CAACAgQAAxkBAAEPnmxo-TgIVFkyEf19Je-9awnfcm0HNAACoBcAAjK0gVFqoRMWJ0V2AjYE",
            "28": "CAACAgQAAxkBAAEPnm1o-TgIEaTKLI1hP_FD5NoPNMoRrQAC8xUAAjTtgVFbDjOI7hjkyDYE",
            "29": "CAACAgQAAxkBAAEPnm5o-TgIrfmuYVnfQps2DUcaDPJtYAACehcAAgL2eFFyvPJETxqlljYE",
            "30": "CAACAgQAAxkBAAEPnm9o-TgIumJ40cFAJ7xQVVJu8yioGQACrBUAAqMsgVEiKujpQgVfJDYE",
            "31": "CAACAgQAAxkBAAEPnndo-ThreZX7kJJpPO5idNcOeIWZpQACDhsAArW6gFENcv6I97q9xDYE",
            "32": "CAACAgQAAxkBAAEPni9o-Ssij-qcC2-pLlmtFrUQr5AUgQACWxcAAsmneVGFqOYh9w81_TYE",
            "33": "CAACAgQAAxkBAAEPnnto-Thsmi6zNRuaeXnBFpXJ-w2JnQACjBkAAo3JeFEYXOtgIzFLjTYE",
            "34": "CAACAgQAAxkBAAEPnnlo-ThrHvyKnt3O8UiLblKzGgWqzQACWBYAAvn3gVElI6JyUvoRYzYE",
            "35": "CAACAgQAAxkBAAEPnn9o-Tij1sCB1_UVenRU6QvBnfFKagACkhYAAsKTgFHHcm9rj3PDyDYE",
            "36": "CAACAgQAAxkBAAEPnoBo-Tik1zRaZMCVCaOi9J1FtVvEiAACrBcAAtbQgVFt8Uw1gyn4MDYE"
        }
        
        # Save to database
        self.db.data['stickers'] = self.stickers
        self.db.save_data()
        
        await update.message.reply_text("✅ All 38 roulette stickers have been saved to the database!")
    
    async def sticker_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming stickers silently"""
        pass
    
    # --- ADMIN COMMANDS ---
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin menu with buttons"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            is_env_admin = user_id in self.env_admin_ids
            admin_type = "Permanent Admin" if is_env_admin else "Dynamic Admin"
            
            house_balance = self.db.get_house_balance()
            total_users = len(self.db.data.get('users', {}))
            pending_withdraws = len([w for w in self.db.data.get('pending_withdrawals', []) if w.get('status') == 'pending'])
            
            admin_text = f"""🔐 **Admin Panel**

You are a **{admin_type}**

🏦 House Balance: **${house_balance:,.2f}**
👥 Total Users: **{total_users}**
💸 Pending Withdrawals: **{pending_withdraws}**

Choose an option:"""
            
            keyboard = [
                [InlineKeyboardButton("📋 Admin Commands", callback_data="admin_all_commands")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            sent_msg = await update.message.reply_text(admin_text, reply_markup=reply_markup, parse_mode="Markdown")
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        else:
            await update.message.reply_text("❌ You are not an admin.")
    
    async def givebal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Give balance to a user (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /givebal [@username or user_id] [amount]\nExample: /givebal @john 100")
            return
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount.")
            return
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive.")
            return
        
        target_user = self.find_user_by_username_or_id(context.args[0])
        if not target_user:
            await update.message.reply_text(f"❌ User '{context.args[0]}' not found.")
            return
        
        target_user_id = target_user['user_id']
        target_user['balance'] += amount
        self.db.update_user(target_user_id, target_user)
        self.db.add_transaction(target_user_id, "admin_give", amount, f"Admin grant by {update.effective_user.id}")
        
        username_display = f"@{target_user.get('username', target_user_id)}"
        await update.message.reply_text(
            f"✅ Gave ${amount:.2f} to {username_display}\n"
            f"New balance: ${target_user['balance']:.2f}"
        )
    
    async def setbal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set a user's balance (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /setbal [@username or user_id] [amount]\nExample: /setbal @john 500")
            return
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount.")
            return
        
        if amount < 0:
            await update.message.reply_text("❌ Amount cannot be negative.")
            return
        
        target_user = self.find_user_by_username_or_id(context.args[0])
        if not target_user:
            await update.message.reply_text(f"❌ User '{context.args[0]}' not found.")
            return
        
        target_user_id = target_user['user_id']
        old_balance = target_user['balance']
        target_user['balance'] = amount
        self.db.update_user(target_user_id, target_user)
        self.db.add_transaction(target_user_id, "admin_set", amount - old_balance, f"Admin set balance by {update.effective_user.id}")
        
        username_display = f"@{target_user.get('username', target_user_id)}"
        await update.message.reply_text(
            f"✅ Set balance for {username_display}\n"
            f"Old balance: ${old_balance:.2f}\n"
            f"New balance: ${amount:.2f}"
        )
    
    async def adddeposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually credit a deposit to a user (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("Usage: /adddeposit [@username or user_id] [amount]\nExample: /adddeposit @john 50")
            return
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount.")
            return
        
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be positive.")
            return
        
        target_user = self.find_user_by_username_or_id(context.args[0])
        if not target_user:
            await update.message.reply_text(f"❌ User '{context.args[0]}' not found.")
            return
        
        target_user_id = target_user['user_id']
        deposit_fee = 0.01  # 1% deposit fee (not shown to user)
        credited_amount = round(amount * (1 - deposit_fee), 2)
        target_user['balance'] += credited_amount
        self.db.update_user(target_user_id, target_user)
        self.db.add_transaction(target_user_id, "deposit", credited_amount, f"Manual deposit by admin {update.effective_user.id}")
        self.db.record_deposit(target_user_id, target_user.get('username', f'User{target_user_id}'), credited_amount)
        
        username_display = f"@{target_user.get('username', target_user_id)}"
        await update.message.reply_text(
            f"✅ Deposit credited to {username_display}\n"
            f"Amount: ${amount:.2f}\n"
            f"New balance: ${target_user['balance']:.2f}"
        )
        
        try:
            await self.app.bot.send_message(
                chat_id=target_user_id,
                text=f"✅ **Deposit Credited!**\n\nAmount: **${amount:.2f}**\n\nNew Balance: ${target_user['balance']:.2f}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
    
    async def allusers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all registered users (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        users = self.db.data['users']
        
        if not users:
            await update.message.reply_text("No users registered yet.")
            return
        
        users_text = f"👥 **All Users ({len(users)})**\n\n"
        
        for user_id_str, user_data in list(users.items())[:50]:
            username = user_data.get('username', 'N/A')
            balance = user_data.get('balance', 0)
            users_text += f"ID: `{user_id_str}` | @{username} | ${balance:.2f}\n"
        
        if len(users) > 50:
            users_text += f"\n...and {len(users) - 50} more users"
        
        await update.message.reply_text(users_text, parse_mode="Markdown")
    
    async def allbalances_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all player balances sorted by amount (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("This command is for administrators only.")
            return
        
        page = 0
        if context.args and context.args[0].isdigit():
            page = max(0, int(context.args[0]) - 1)
        
        await self.show_allbalances_page(update, page)
    
    async def show_allbalances_page(self, update: Update, page: int):
        """Display a specific page of all player balances"""
        users = self.db.data['users']
        
        if not users:
            text = "No users registered yet."
            if update.callback_query:
                await update.callback_query.edit_message_text(text)
            else:
                await update.message.reply_text(text)
            return
        
        sorted_users = sorted(
            [(uid, udata) for uid, udata in users.items()],
            key=lambda x: x[1].get('balance', 0),
            reverse=True
        )
        
        total_balance = sum(udata.get('balance', 0) for _, udata in sorted_users)
        
        items_per_page = 15
        total_pages = max(1, (len(sorted_users) + items_per_page - 1) // items_per_page)
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_data = sorted_users[start_idx:end_idx]
        
        balances_text = f"**All Player Balances** ({page + 1}/{total_pages})\n"
        balances_text += f"Total in accounts: ${total_balance:.2f}\n"
        balances_text += f"Players: {len(sorted_users)}\n\n"
        
        for idx, (user_id, user_data) in enumerate(page_data, start=start_idx + 1):
            username = user_data.get('username', 'Unknown')
            balance = user_data.get('balance', 0)
            balances_text += f"{idx}. @{username} - ${balance:.2f}\n"
        
        keyboard = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("Previous", callback_data=f"allbal_page_{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next", callback_data=f"allbal_page_{page + 1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                balances_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                balances_text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
    
    async def userinfo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View detailed user information (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /userinfo [@username or user_id]\nExample: /userinfo @john")
            return
        
        target_user = self.find_user_by_username_or_id(context.args[0])
        if not target_user:
            await update.message.reply_text(f"❌ User '{context.args[0]}' not found.")
            return
        
        target_user_id = target_user['user_id']
        
        info_text = f"""
👤 **User Info: {target_user_id}**

Username: @{target_user.get('username', 'N/A')}
Balance: ${target_user.get('balance', 0):.2f}
Playthrough: ${target_user.get('playthrough_required', 0):.2f}

**Stats:**
Games Played: {target_user.get('games_played', 0)}
Games Won: {target_user.get('games_won', 0)}
Total Wagered: ${target_user.get('total_wagered', 0):.2f}
Total P&L: ${target_user.get('total_pnl', 0):.2f}
Best Win Streak: {target_user.get('best_win_streak', 0)}

"""
        
        await update.message.reply_text(info_text, parse_mode="Markdown")
    
    async def addadmin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new admin (Admin only - requires environment admin)"""
        user_id = update.effective_user.id
        
        # Only permanent admins (from environment) can add new admins
        if user_id not in self.env_admin_ids:
            await update.message.reply_text("❌ Only permanent admins can add new admins.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /addadmin [user_id]\nExample: /addadmin 123456789")
            return
        
        try:
            new_admin_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
            return
        
        # Check if already an admin
        if self.is_admin(new_admin_id):
            admin_type = "permanent" if new_admin_id in self.env_admin_ids else "dynamic"
            await update.message.reply_text(f"❌ User {new_admin_id} is already a {admin_type} admin.")
            return
        
        # Add to dynamic admins
        self.dynamic_admin_ids.add(new_admin_id)
        self.db.data['dynamic_admins'] = list(self.dynamic_admin_ids)
        self.db.save_data()
        
        await update.message.reply_text(f"✅ User {new_admin_id} has been added as an admin!")
        
        # Notify the new admin if they exist in the system
        try:
            await self.app.bot.send_message(
                chat_id=new_admin_id,
                text="🎉 You have been granted admin privileges! Use /admin to see available commands."
            )
        except Exception as e:
            logger.info(f"Could not notify new admin {new_admin_id}: {e}")
    
    async def removeadmin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove an admin (Admin only - requires environment admin)"""
        user_id = update.effective_user.id
        
        # Only permanent admins (from environment) can remove admins
        if user_id not in self.env_admin_ids:
            await update.message.reply_text("❌ Only permanent admins can remove admins.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /removeadmin [user_id]\nExample: /removeadmin 123456789")
            return
        
        try:
            admin_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
            return
        
        # Prevent removing permanent admins
        if admin_id in self.env_admin_ids:
            await update.message.reply_text("❌ Cannot remove permanent admins from environment.")
            return
        
        # Check if they are a dynamic admin
        if admin_id not in self.dynamic_admin_ids:
            await update.message.reply_text(f"❌ User {admin_id} is not a dynamic admin.")
            return
        
        # Remove from dynamic admins
        self.dynamic_admin_ids.discard(admin_id)
        self.db.data['dynamic_admins'] = list(self.dynamic_admin_ids)
        self.db.save_data()
        
        await update.message.reply_text(f"✅ Removed admin privileges from user {admin_id}!")
        
        # Notify the user if possible
        try:
            await self.app.bot.send_message(
                chat_id=admin_id,
                text="Your admin privileges have been removed."
            )
        except Exception as e:
            logger.info(f"Could not notify removed admin {admin_id}: {e}")
    
    async def listadmins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all admins (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        admin_text = "👑 **Admin List**\n\n"
        
        if self.env_admin_ids:
            admin_text += "**Permanent Admins (from environment):**\n"
            for admin_id in sorted(self.env_admin_ids):
                user_data = self.db.data['users'].get(str(admin_id))
                username = user_data.get('username', 'N/A') if user_data else 'N/A'
                admin_text += f"• {admin_id} (@{username})\n"
            admin_text += "\n"
        
        if self.dynamic_admin_ids:
            admin_text += "**Dynamic Admins (added via commands):**\n"
            for admin_id in sorted(self.dynamic_admin_ids):
                user_data = self.db.data['users'].get(str(admin_id))
                username = user_data.get('username', 'N/A') if user_data else 'N/A'
                admin_text += f"• {admin_id} (@{username})\n"
        else:
            if not self.env_admin_ids:
                admin_text += "No admins configured."
            else:
                admin_text += "No dynamic admins added yet.\n"
                admin_text += "Use /addadmin to add more admins."
        
        await update.message.reply_text(admin_text, parse_mode="Markdown")
    
    async def addapprover_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a withdrawal approver (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Only admins can add withdrawal approvers.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /addapprover [user_id]\nExample: /addapprover 123456789")
            return
        
        try:
            new_approver_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
            return
        
        if new_approver_id in self.withdrawal_approvers:
            await update.message.reply_text(f"❌ User {new_approver_id} is already a withdrawal approver.")
            return
        
        if self.is_admin(new_approver_id):
            await update.message.reply_text(f"❌ User {new_approver_id} is an admin and already has approval permissions.")
            return
        
        self.withdrawal_approvers.add(new_approver_id)
        self.db.data['withdrawal_approvers'] = list(self.withdrawal_approvers)
        self.db.save_data()
        
        await update.message.reply_text(f"✅ User {new_approver_id} has been added as a withdrawal approver!")
        
        try:
            await self.app.bot.send_message(
                chat_id=new_approver_id,
                text="🎉 You have been granted withdrawal approval privileges! You can now approve or deny withdrawal requests in the admin group."
            )
        except Exception as e:
            logger.info(f"Could not notify new approver {new_approver_id}: {e}")
    
    async def removeapprover_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove a withdrawal approver (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Only admins can remove withdrawal approvers.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /removeapprover [user_id]\nExample: /removeapprover 123456789")
            return
        
        try:
            approver_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
            return
        
        if approver_id not in self.withdrawal_approvers:
            await update.message.reply_text(f"❌ User {approver_id} is not a withdrawal approver.")
            return
        
        self.withdrawal_approvers.discard(approver_id)
        self.db.data['withdrawal_approvers'] = list(self.withdrawal_approvers)
        self.db.save_data()
        
        await update.message.reply_text(f"✅ Removed withdrawal approval privileges from user {approver_id}!")
        
        try:
            await self.app.bot.send_message(
                chat_id=approver_id,
                text="Your withdrawal approval privileges have been removed."
            )
        except Exception as e:
            logger.info(f"Could not notify removed approver {approver_id}: {e}")
    
    async def listapprovers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all withdrawal approvers (Admin only)"""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        approver_text = "💼 **Withdrawal Approvers**\n\n"
        approver_text += "_These users can only approve/deny withdrawals._\n\n"
        
        if self.withdrawal_approvers:
            for approver_id in sorted(self.withdrawal_approvers):
                user_data = self.db.data['users'].get(str(approver_id))
                username = user_data.get('username', 'N/A') if user_data else 'N/A'
                approver_text += f"• {approver_id} (@{username})\n"
        else:
            approver_text += "No withdrawal approvers added yet.\n"
            approver_text += "Use /addapprover to add approvers."
        
        await update.message.reply_text(approver_text, parse_mode="Markdown")
    
    async def sethousebal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the house balance to a specific amount (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args:
            current_bal = self.db.get_house_balance()
            await update.message.reply_text(
                f"🏦 **Current House Balance:** ${current_bal:.2f}\n\n"
                f"Usage: /sethousebal [amount]\n"
                f"Example: /sethousebal 50000",
                parse_mode="Markdown"
            )
            return
        
        try:
            new_balance = float(context.args[0].replace(',', ''))
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please provide a valid number.")
            return
        
        if new_balance < 0:
            await update.message.reply_text("❌ House balance cannot be negative.")
            return
        
        old_balance = self.db.get_house_balance()
        self.db.data['house_balance'] = new_balance
        self.db.save_data()
        
        await update.message.reply_text(
            f"✅ **House Balance Updated**\n\n"
            f"Old Balance: ${old_balance:.2f}\n"
            f"New Balance: ${new_balance:.2f}",
            parse_mode="Markdown"
        )
        logger.info(f"Admin {user_id} set house balance from ${old_balance:.2f} to ${new_balance:.2f}")

    async def setltcrate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set the manual LTC to USD exchange rate (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args:
            current_rate = self.db.data.get('manual_ltc_rate')
            if current_rate:
                await update.message.reply_text(
                    f"💎 **Current Manual LTC Rate:** ${current_rate:.2f} per LTC\n\n"
                    f"Usage: /setltcrate [price]\n"
                    f"Example: /setltcrate 120\n\n"
                    f"This sets 1 LTC = $120 USD for all withdrawals.",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"💎 **No Manual LTC Rate Set**\n\n"
                    f"Currently using automatic rate from Plisio API.\n\n"
                    f"Usage: /setltcrate [price]\n"
                    f"Example: /setltcrate 120\n\n"
                    f"This sets 1 LTC = $120 USD for all withdrawals.",
                    parse_mode="Markdown"
                )
            return
        
        try:
            new_rate = float(context.args[0].replace(',', ''))
        except ValueError:
            await update.message.reply_text("❌ Invalid rate. Please provide a valid number.")
            return
        
        if new_rate <= 0:
            await update.message.reply_text("❌ LTC rate must be positive.")
            return
        
        old_rate = self.db.data.get('manual_ltc_rate')
        self.db.data['manual_ltc_rate'] = new_rate
        self.db.save_data()
        
        if old_rate:
            await update.message.reply_text(
                f"✅ **LTC Rate Updated**\n\n"
                f"Old Rate: ${old_rate:.2f} per LTC\n"
                f"New Rate: ${new_rate:.2f} per LTC\n\n"
                f"Example: $10 withdrawal = {10/new_rate:.8f} LTC",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                f"✅ **Manual LTC Rate Set**\n\n"
                f"Rate: ${new_rate:.2f} per LTC\n\n"
                f"Example: $10 withdrawal = {10/new_rate:.8f} LTC\n\n"
                f"_Automatic rate from Plisio API will no longer be used._",
                parse_mode="Markdown"
            )
        logger.info(f"Admin {user_id} set LTC rate to ${new_rate:.2f}")

    async def ltcrate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View the current LTC exchange rate (Admin only)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        current_rate = self.db.data.get('manual_ltc_rate')
        
        if current_rate:
            await update.message.reply_text(
                f"💎 **Current LTC Rate**\n\n"
                f"**${current_rate:.2f}** per LTC (manual)\n\n"
                f"Examples:\n"
                f"• $1 = {1/current_rate:.8f} LTC\n"
                f"• $10 = {10/current_rate:.8f} LTC\n"
                f"• $100 = {100/current_rate:.8f} LTC",
                parse_mode="Markdown"
            )
        else:
            # Try to get rate from API
            api_rate = await self.get_ltc_price_usd()
            if api_rate:
                await update.message.reply_text(
                    f"💎 **Current LTC Rate**\n\n"
                    f"**${api_rate:.2f}** per LTC (from Plisio API)\n\n"
                    f"_No manual rate set. Use /setltcrate to set one._",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    f"❌ Could not fetch LTC rate.\n\n"
                    f"_No manual rate set. Use /setltcrate to set one._",
                    parse_mode="Markdown"
                )
    
    async def matchhistory_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to view any user's match history"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ This command is for administrators only.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📜 **Match History Lookup**\n\n"
                "Usage: /matchhistory [user_id]\n"
                "Example: /matchhistory 123456789",
                parse_mode="Markdown"
            )
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")
            return
        
        target_user = self.db.data['users'].get(str(target_user_id))
        if not target_user:
            await update.message.reply_text(f"❌ User {target_user_id} not found in database.")
            return
        
        target_username = target_user.get('username', f'User{target_user_id}')
        
        all_games = self.db.data.get('games', [])
        user_games = [
            game for game in all_games 
            if game.get('player_id') == target_user_id or 
               game.get('challenger') == target_user_id or 
               game.get('opponent') == target_user_id
        ][-20:]
        
        if not user_games:
            await update.message.reply_text(f"📜 No match history found for @{target_username} (ID: {target_user_id})")
            return
        
        history_text = f"📜 **Match History for @{target_username}**\n(ID: {target_user_id}) - Last {len(user_games)} games\n\n"
        
        for game in reversed(user_games):
            game_type = game.get('type', 'unknown')
            timestamp = game.get('timestamp', '')
            wager = game.get('wager', 0)
            
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%m/%d %H:%M")
                except:
                    time_str = "Unknown"
            else:
                time_str = "Unknown"
            
            result = game.get('result', game.get('outcome', 'unknown'))
            result_emoji = "✅" if result == "win" else "❌" if result == "loss" else "🤝"
            
            if 'bot' in game_type:
                if game_type == 'dice_bot':
                    player_roll = game.get('player_roll', 0)
                    bot_roll = game.get('bot_roll', 0)
                    history_text += f"{result_emoji} Dice vs Bot - ${wager:.2f} | {player_roll} vs {bot_roll} | {time_str}\n"
                elif game_type == 'coinflip_bot':
                    choice = game.get('choice', '?')
                    flip_result = game.get('result', '?')
                    history_text += f"{result_emoji} CoinFlip vs Bot - ${wager:.2f} | {choice} | {time_str}\n"
                elif game_type == 'roulette':
                    bet_type = game.get('bet_type', '?')
                    number = game.get('winning_number', '?')
                    history_text += f"{result_emoji} Roulette - ${wager:.2f} | {bet_type} | #{number} | {time_str}\n"
                elif game_type == 'blackjack':
                    history_text += f"{result_emoji} Blackjack - ${wager:.2f} | {time_str}\n"
                else:
                    history_text += f"{result_emoji} {game_type} - ${wager:.2f} | {time_str}\n"
            else:
                opponent_id = game.get('opponent') if game.get('challenger') == target_user_id else game.get('challenger')
                opponent_user = self.db.data['users'].get(str(opponent_id), {})
                opponent_name = opponent_user.get('username', f'User{opponent_id}')
                history_text += f"{result_emoji} PvP vs @{opponent_name} - ${wager:.2f} | {time_str}\n"
        
        await update.message.reply_text(history_text, parse_mode="Markdown")
    
    async def send_sticker(self, chat_id: int, outcome: str, profit: float = 0):
        """Send a sticker based on game outcome"""
        try:
            sticker_key = None
            
            if outcome == "win":
                if profit >= 50:
                    sticker_key = "jackpot"
                elif profit >= 10:
                    sticker_key = "big_win"
                else:
                    sticker_key = "win"
            elif outcome == "loss":
                sticker_key = "loss"
            elif outcome == "draw":
                sticker_key = "draw"
            elif outcome == "bonus_claim":
                sticker_key = "bonus_claim"
            
            if sticker_key and self.stickers.get(sticker_key):
                await self.app.bot.send_sticker(
                    chat_id=chat_id,
                    sticker=self.stickers[sticker_key]
                )
        except Exception as e:
            logger.error(f"Error sending sticker: {e}")

    # --- GAME LOGIC ---

    def _update_user_stats(self, user_id: int, wager: float, profit: float, result: str):
        """Helper to update common user stats and playthrough requirements.
        Note: Balance is handled by game handlers directly, not here."""
        user_data = self.db.get_user(user_id)
        
        user_data['games_played'] += 1
        user_data['total_wagered'] += wager
        user_data['wagered_since_last_withdrawal'] += wager
        user_data['total_pnl'] += profit
        
        if result == "win":
            user_data['games_won'] += 1
            user_data['win_streak'] = user_data.get('win_streak', 0) + 1
            user_data['best_win_streak'] = max(user_data.get('best_win_streak', 0), user_data['win_streak'])
        elif result == "loss":
            user_data['win_streak'] = 0

        # Set first wager date
        if not user_data.get('first_wager_date'):
            user_data['first_wager_date'] = datetime.now().isoformat()
        
        self.db.update_user(user_id, user_data)
        


    async def dice_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play dice against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from player
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Bot sends its emoji
        bot_dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="🎲")
        await asyncio.sleep(3)
        bot_roll = bot_dice_msg.dice.value
        
        # Store pending game and wait for player emoji
        game_id = f"dice_bot_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[game_id] = {
            "type": "dice_bot",
            "player": user_id,
            "bot_roll": bot_roll,
            "wager": wager,
            "emoji": "🎲",
            "chat_id": chat_id,
            "waiting_for_emoji": True,
            "emoji_wait_started": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        await context.bot.send_message(chat_id=chat_id, text=f"@{username} your turn", parse_mode="Markdown")

    async def darts_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play darts against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from player
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Bot sends its emoji
        bot_dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="🎯")
        await asyncio.sleep(3)
        bot_roll = bot_dice_msg.dice.value
        
        # Store pending game and wait for player emoji
        game_id = f"darts_bot_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[game_id] = {
            "type": "darts_bot",
            "player": user_id,
            "bot_roll": bot_roll,
            "wager": wager,
            "emoji": "🎯",
            "chat_id": chat_id,
            "waiting_for_emoji": True,
            "emoji_wait_started": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        await context.bot.send_message(chat_id=chat_id, text=f"@{username} your turn", parse_mode="Markdown")

    async def basketball_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play basketball against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from player
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Bot sends its emoji
        bot_dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="🏀")
        await asyncio.sleep(4)
        bot_roll = bot_dice_msg.dice.value
        
        # Store pending game and wait for player emoji
        game_id = f"basketball_bot_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[game_id] = {
            "type": "basketball_bot",
            "player": user_id,
            "bot_roll": bot_roll,
            "wager": wager,
            "emoji": "🏀",
            "chat_id": chat_id,
            "waiting_for_emoji": True,
            "emoji_wait_started": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        await context.bot.send_message(chat_id=chat_id, text=f"@{username} your turn", parse_mode="Markdown")

    async def soccer_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play soccer against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from player
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Bot sends its emoji
        bot_dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="⚽")
        await asyncio.sleep(4)
        bot_roll = bot_dice_msg.dice.value
        
        # Store pending game and wait for player emoji
        game_id = f"soccer_bot_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[game_id] = {
            "type": "soccer_bot",
            "player": user_id,
            "bot_roll": bot_roll,
            "wager": wager,
            "emoji": "⚽",
            "chat_id": chat_id,
            "waiting_for_emoji": True,
            "emoji_wait_started": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        await context.bot.send_message(chat_id=chat_id, text=f"@{username} your turn", parse_mode="Markdown")

    async def bowling_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play bowling against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from player
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Bot sends its emoji
        bot_dice_msg = await context.bot.send_dice(chat_id=chat_id, emoji="🎳")
        await asyncio.sleep(4)
        bot_roll = bot_dice_msg.dice.value
        
        # Store pending game and wait for player emoji
        game_id = f"bowling_bot_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[game_id] = {
            "type": "bowling_bot",
            "player": user_id,
            "bot_roll": bot_roll,
            "wager": wager,
            "emoji": "🎳",
            "chat_id": chat_id,
            "waiting_for_emoji": True,
            "emoji_wait_started": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        await context.bot.send_message(chat_id=chat_id, text=f"@{username} your turn", parse_mode="Markdown")

    async def create_open_dice_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Create an open dice challenge for anyone to accept"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await query.answer("❌ Insufficient balance to cover the wager.", show_alert=True)
            return
        
        # Deduct wager from challenger balance immediately
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})

        chat_id = query.message.chat_id
        
        challenge_id = f"dice_open_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[challenge_id] = {
            "type": "dice",
            "challenger": user_id,
            "challenger_roll": None,
            "opponent": None,
            "wager": wager,
            "emoji": "🎲",
            "chat_id": chat_id,
            "waiting_for_challenger_emoji": False,
            "created_at": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        keyboard = [[InlineKeyboardButton("✅ Accept Challenge", callback_data=f"accept_dice_{challenge_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🎲 **Dice PvP Challenge!**\n\n"
            f"Challenger: @{username}\n"
            f"Wager: **${wager:.2f}**\n\n"
            f"Click below to accept!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def accept_dice_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, challenge_id: str):
        """Accept a pending dice challenge and resolve it."""
        query = update.callback_query

        challenge = self.pending_pvp.get(challenge_id)
        if not challenge:
            await query.edit_message_text("❌ This challenge has expired or was canceled.")
            return
        
        # Check if challenge has expired (>30 seconds old)
        if 'created_at' in challenge:
            created_at = datetime.fromisoformat(challenge['created_at'])
            time_diff = (datetime.now() - created_at).total_seconds()
            if time_diff > 30:
                await query.edit_message_text("❌ This challenge has expired after 30 seconds.")
                return

        acceptor_id = query.from_user.id
        wager = challenge['wager']
        challenger_id = challenge['challenger']
        challenger_user = self.db.get_user(challenger_id)
        acceptor_user = self.db.get_user(acceptor_id)

        if acceptor_id == challenger_id:
            await query.answer("❌ You cannot accept your own challenge.", show_alert=True)
            return

        if self.user_has_active_game(acceptor_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return

        if wager > acceptor_user['balance']:
            await query.answer(f"❌ Insufficient balance. You need ${wager:.2f} to accept.", show_alert=True)
            return
        
        # Deduct wager from acceptor balance
        self.db.update_user(acceptor_id, {'balance': acceptor_user['balance'] - wager})
        
        # Update challenge to mark acceptor and wait for challenger emoji
        challenge['opponent'] = acceptor_id
        challenge['waiting_for_challenger_emoji'] = True
        challenge['waiting_for_emoji'] = False
        challenge['emoji_wait_started'] = datetime.now().isoformat()
        self.pending_pvp[challenge_id] = challenge
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        # Show game info message with both players and wager
        await query.edit_message_text(
            f"🎲 **Dice PvP Game Started!**\n\n"
            f"💰 Wager: **${wager:.2f}**\n"
            f"🏆 Prize Pool: **${wager * 2:.2f}**\n\n"
            f"👤 Player 1: @{challenger_user['username']}\n"
            f"👤 Player 2: @{acceptor_user['username']}",
            parse_mode="Markdown"
        )
        
        # Send message telling challenger to roll
        await context.bot.send_message(
            chat_id=challenge['chat_id'],
            text=f"🎲 @{challenger_user['username']}, send your dice!",
            parse_mode="Markdown"
        )

    async def create_emoji_pvp_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float, game_type: str, emoji: str):
        """Create an emoji-based PvP challenge (darts, basketball, soccer)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
        if self.user_has_active_game(user_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > user_data['balance']:
            await query.answer("❌ Insufficient balance to cover the wager.", show_alert=True)
            return
        
        # Deduct wager from challenger balance immediately
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        chat_id = query.message.chat_id
        
        challenge_id = f"{game_type}_open_{user_id}_{int(datetime.now().timestamp())}"
        self.pending_pvp[challenge_id] = {
            "type": game_type,
            "challenger": user_id,
            "challenger_roll": None,
            "opponent": None,
            "wager": wager,
            "emoji": emoji,
            "chat_id": chat_id,
            "waiting_for_challenger_emoji": False,
            "created_at": datetime.now().isoformat()
        }
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        keyboard = [[InlineKeyboardButton("✅ Accept Challenge", callback_data=f"accept_{game_type}_{challenge_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"{emoji} **{game_type.upper()} PvP Challenge!**\n\n"
            f"Challenger: @{username}\n"
            f"Wager: **${wager:.2f}**\n\n"
            f"Click below to accept!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def accept_emoji_pvp_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, challenge_id: str):
        """Accept a pending emoji PvP challenge"""
        query = update.callback_query
        
        challenge = self.pending_pvp.get(challenge_id)
        if not challenge:
            await query.answer("❌ This challenge has expired or was canceled.", show_alert=True)
            return
        
        # Check if challenge has expired (>30 seconds old)
        if 'created_at' in challenge:
            created_at = datetime.fromisoformat(challenge['created_at'])
            time_diff = (datetime.now() - created_at).total_seconds()
            if time_diff > 30:
                await query.answer("❌ This challenge has expired after 30 seconds.", show_alert=True)
                return
        
        acceptor_id = query.from_user.id
        wager = challenge['wager']
        challenger_id = challenge['challenger']
        challenger_user = self.db.get_user(challenger_id)
        acceptor_user = self.db.get_user(acceptor_id)
        game_type = challenge['type']
        emoji = challenge['emoji']
        chat_id = challenge['chat_id']
        
        if acceptor_id == challenger_id:
            await query.answer("❌ You cannot accept your own challenge.", show_alert=True)
            return
        
        if self.user_has_active_game(acceptor_id):
            await query.answer("❌ You already have an active game. Finish it first!", show_alert=True)
            return
        
        if wager > acceptor_user['balance']:
            await query.answer(f"❌ Insufficient balance. You need ${wager:.2f} to accept.", show_alert=True)
            return
        
        # Deduct wager from acceptor balance
        self.db.update_user(acceptor_id, {'balance': acceptor_user['balance'] - wager})
        
        # Tell challenger to send their emoji first
        await query.edit_message_text(
            f"@{challenger_user['username']} your turn",
            parse_mode="Markdown"
        )
        
        # Update challenge to mark acceptor and wait for challenger emoji
        challenge['opponent'] = acceptor_id
        challenge['waiting_for_challenger_emoji'] = True
        challenge['waiting_for_emoji'] = False
        challenge['emoji_wait_started'] = datetime.now().isoformat()
        self.pending_pvp[challenge_id] = challenge
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()

    async def handle_emoji_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when a user sends a dice emoji for PvP or bot vs player"""
        if not update.message.dice:
            return
        
        user_id = update.effective_user.id
        emoji = update.message.dice.emoji
        roll_value = update.message.dice.value
        chat_id = update.message.chat_id
        
        # Reload pending_pvp from database to ensure we have the latest state
        self.pending_pvp = self.db.data.get('pending_pvp', {})
        
        logger.info(f"Received emoji {emoji} from user {user_id} in chat {chat_id}, value: {roll_value}")
        logger.info(f"Pending games: {self.pending_pvp}")
        
        # Find pending challenge waiting for this user's emoji
        challenge_id_to_resolve = None
        challenge_to_resolve = None
        
        for cid, challenge in self.pending_pvp.items():
            logger.info(f"Checking challenge {cid}: emoji={challenge.get('emoji')}, waiting_for_challenger={challenge.get('waiting_for_challenger_emoji')}, waiting={challenge.get('waiting_for_emoji')}, chat={challenge.get('chat_id')}, player={challenge.get('player')}, opponent={challenge.get('opponent')}")
            
            # Check if waiting for challenger's emoji
            if (challenge.get('waiting_for_challenger_emoji') and 
                challenge.get('emoji') == emoji and
                challenge.get('chat_id') == chat_id and
                challenge.get('challenger') == user_id):
                challenge_id_to_resolve = cid
                challenge_to_resolve = challenge
                logger.info(f"Found challenger emoji challenge: {cid}")
                
                # Wait for animation
                await asyncio.sleep(3)
                
                # Save challenger's roll and tell acceptor to go
                challenge['challenger_roll'] = roll_value
                challenge['waiting_for_challenger_emoji'] = False
                challenge['waiting_for_emoji'] = True
                challenge['emoji_wait_started'] = datetime.now().isoformat()
                self.pending_pvp[cid] = challenge
                self.db.data['pending_pvp'] = self.pending_pvp
                self.db.save_data()
                
                challenger_user = self.db.get_user(challenge['challenger'])
                acceptor_user = self.db.get_user(challenge['opponent'])
                wager = challenge['wager']
                
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=f"🎲 @{challenger_user['username']} rolled a **{roll_value}**!\n\n"
                         f"🎲 @{acceptor_user['username']}, send your dice!",
                    parse_mode="Markdown"
                )
                return
            
            # Check if waiting for acceptor's emoji (or bot vs player)
            if (challenge.get('waiting_for_emoji') and 
                challenge.get('emoji') == emoji and
                challenge.get('chat_id') == chat_id):
                # Check if it's PvP (opponent) or bot vs player (player)
                if challenge.get('opponent') == user_id or challenge.get('player') == user_id:
                    challenge_id_to_resolve = cid
                    challenge_to_resolve = challenge
                    logger.info(f"Found matching challenge: {cid}")
                    break
        
        if not challenge_to_resolve or not challenge_id_to_resolve:
            logger.info("No matching pending game found")
            return  # Not a pending emoji response
        
        # Resolve the challenge
        await asyncio.sleep(3)  # Wait for emoji animation
        
        game_type = challenge_to_resolve['type']
        wager = challenge_to_resolve['wager']
        
        # Check if it's a bot vs player game
        if game_type in ['dice_bot', 'darts_bot', 'basketball_bot', 'soccer_bot', 'bowling_bot']:
            await self.resolve_bot_vs_player_game(update, context, challenge_to_resolve, challenge_id_to_resolve, roll_value)
            return
        
        # It's a PvP game
        challenger_id = challenge_to_resolve['challenger']
        challenger_roll = challenge_to_resolve['challenger_roll']
        acceptor_roll = roll_value
        
        challenger_user = self.db.get_user(challenger_id)
        acceptor_user = self.db.get_user(user_id)
        
        # Remove challenge from pending
        del self.pending_pvp[challenge_id_to_resolve]
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        # Determine winner
        winner_id = None
        loser_id = None
        
        if challenger_roll > acceptor_roll:
            winner_id = challenger_id
            loser_id = user_id
        elif acceptor_roll > challenger_roll:
            winner_id = user_id
            loser_id = challenger_id
        else:
            # Draw: refund both wagers but still count towards wagered amounts
            self.db.update_user(challenger_id, {'balance': challenger_user['balance'] + wager})
            self.db.update_user(user_id, {'balance': acceptor_user['balance'] + wager})
            
            # Count wagered amounts for both players even on draws
            self._update_user_stats(challenger_id, wager, 0, "draw")
            self._update_user_stats(user_id, wager, 0, "draw")
            
            challenger_data = self.db.get_user(challenger_id)
            acceptor_data = self.db.get_user(user_id)
            self.db.record_game({
                "type": f"{game_type}_pvp",
                "challenger": challenger_id,
                "opponent": user_id,
                "wager": wager,
                "result": "draw",
                "challenger_balance_after": challenger_data['balance'],
                "opponent_balance_after": acceptor_data['balance']
            })
            
            result_text = (
                f"🎲 **Dice PvP Results**\n\n"
                f"👤 @{challenger_user['username']}: **{challenger_roll}**\n"
                f"👤 @{acceptor_user['username']}: **{acceptor_roll}**\n\n"
                f"🤝 **It's a tie!** Both wagers refunded."
            )
            
            keyboard = [
                [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"{game_type}_bot_{wager:.2f}")],
                [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"{game_type}_player_open_{wager:.2f}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=reply_markup, parse_mode="Markdown")
            return
        
        # Handle Win/Loss
        winnings = wager * 2
        winner_profit = wager
        
        winner_user = self.db.get_user(winner_id)
        loser_user = self.db.get_user(loser_id)
        winner_user['balance'] += winnings
        self.db.update_user(winner_id, winner_user)
        
        self._update_user_stats(winner_id, wager, winner_profit, "win")
        self._update_user_stats(loser_id, wager, -wager, "loss")
        
        self.db.add_transaction(winner_id, f"{game_type}_pvp_win", winner_profit, f"{game_type.upper()} PvP Win vs {loser_user['username']}")
        self.db.add_transaction(loser_id, f"{game_type}_pvp_loss", -wager, f"{game_type.upper()} PvP Loss vs {winner_user['username']}")
        challenger_data = self.db.get_user(challenger_id)
        opponent_data = self.db.get_user(user_id)
        self.db.record_game({
            "type": f"{game_type}_pvp",
            "challenger": challenger_id,
            "opponent": user_id,
            "wager": wager,
            "result": "win",
            "winner_id": winner_id,
            "challenger_balance_after": challenger_data['balance'],
            "opponent_balance_after": opponent_data['balance']
        })
        
        # Record for biggest dices leaderboard (only for dice games)
        if game_type == "dice":
            self.db.record_biggest_dice(winner_id, winner_user['username'], loser_id, loser_user['username'], winnings)
        
        final_text = (
            f"🎲 **Dice PvP Results**\n\n"
            f"👤 @{challenger_user['username']}: **{challenger_roll}**\n"
            f"👤 @{acceptor_user['username']}: **{acceptor_roll}**\n\n"
            f"🏆 **@{winner_user['username']} wins ${winnings:.2f}!**"
        )
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"{game_type}_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"{game_type}_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(chat_id=chat_id, text=final_text, reply_markup=reply_markup, parse_mode="Markdown")

    def _is_make(self, game_type: str, roll: int) -> bool:
        """Check if a roll is a 'make' (success) for basketball/soccer/darts"""
        if game_type == 'basketball_bot':
            return roll >= 4  # 4-5 are makes
        elif game_type == 'soccer_bot':
            return roll >= 3  # 3-5 are goals
        elif game_type == 'darts_bot':
            return roll >= 5  # 5-6 are bullseye/center hits
        return False

    async def resolve_bot_vs_player_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE, challenge: Dict, challenge_id: str, player_roll: int):
        """Resolve a bot vs player game"""
        user_id = challenge['player']
        bot_roll = challenge['bot_roll']
        wager = challenge['wager']
        game_type = challenge['type']
        emoji = challenge['emoji']
        chat_id = challenge['chat_id']
        
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
        # Remove from pending
        del self.pending_pvp[challenge_id]
        self.db.data['pending_pvp'] = self.pending_pvp
        self.db.save_data()
        
        # Determine result
        profit = 0.0
        result = "draw"
        
        # Special tie logic for basketball, soccer, darts: tie if both make or both miss
        if game_type in ['basketball_bot', 'soccer_bot', 'darts_bot']:
            player_made = self._is_make(game_type, player_roll)
            bot_made = self._is_make(game_type, bot_roll)
            
            if player_made == bot_made:
                # Both made or both missed = draw
                user_data['balance'] += wager
                self.db.update_user(user_id, user_data)
                result_text = f"@{username} - Draw, bet refunded"
                result = "draw"
            elif player_made and not bot_made:
                # Player made, bot missed = player wins
                profit = wager
                result = "win"
                result_text = f"@{username} won ${profit:.2f}"
                user_data['balance'] += wager * 2
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-wager)
            else:
                # Bot made, player missed = player loses
                profit = -wager
                result = "loss"
                result_text = f"@{username} lost ${wager:.2f}"
                self.db.update_house_balance(wager)
        else:
            # Standard dice/bowling logic: higher roll wins
            if player_roll > bot_roll:
                profit = wager
                result = "win"
                result_text = f"@{username} won ${profit:.2f}"
                user_data['balance'] += wager * 2
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-wager)
            elif player_roll < bot_roll:
                profit = -wager
                result = "loss"
                result_text = f"@{username} lost ${wager:.2f}"
                self.db.update_house_balance(wager)
            else:
                # Draw - refund wager
                user_data['balance'] += wager
                self.db.update_user(user_id, user_data)
                result_text = f"@{username} - Draw, bet refunded"
        
        # Update stats for all results (including draws - they still count towards wagered amounts)
        self._update_user_stats(user_id, wager, profit, result)
        
        self.db.add_transaction(user_id, game_type, profit, f"{game_type.upper().replace('_', ' ')} - Wager: ${wager:.2f}")
        self.db.record_game({
            "type": game_type,
            "player_id": user_id,
            "wager": wager,
            "player_roll": player_roll,
            "bot_roll": bot_roll,
            "result": result,
            "balance_after": user_data['balance']
        })
        
        # Record for biggest dices leaderboard (dice games only - record all games)
        if game_type == "dice_bot" and result != "draw":
            winnings = wager * 2
            if result == "win":
                self.db.record_biggest_dice(user_id, username, 0, "Bot", winnings, "bot")
            else:
                self.db.record_biggest_dice(0, "Bot", user_id, username, winnings, "bot")
        
        keyboard = [[InlineKeyboardButton("Play Again", callback_data=f"{game_type.replace('_bot', '_bot')}_{wager:.2f}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(chat_id, sent_msg.message_id)] = user_id

    async def coinflip_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float, choice: str):
        """Play coinflip against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager first
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        # Send coin emoji and determine result
        await context.bot.send_message(chat_id=chat_id, text="🪙")
        await asyncio.sleep(2)
        
        # Random coin flip result
        result = random.choice(['heads', 'tails'])
        
        # Determine result
        profit = 0.0
        outcome = "loss"
        
        if choice == result:
            profit = wager
            outcome = "win"
            result_text = f"@{username} won ${profit:.2f}"
            user_data['balance'] += wager * 2  # Return wager + winnings
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-wager)
        else:
            profit = -wager
            result_text = f"@{username} lost ${wager:.2f}"
            self.db.update_house_balance(wager)

        # Update user stats and database
        self._update_user_stats(user_id, wager, profit, outcome)
        self.db.add_transaction(user_id, "coinflip_bot", profit, f"CoinFlip vs Bot - Wager: ${wager:.2f}")
        self.db.record_game({
            "type": "coinflip_bot",
            "player_id": user_id,
            "wager": wager,
            "choice": choice,
            "result": result,
            "outcome": outcome,
            "balance_after": user_data['balance']
        })

        keyboard = [
            [InlineKeyboardButton("Heads again", callback_data=f"flip_bot_{wager:.2f}_heads")],
            [InlineKeyboardButton("Tails again", callback_data=f"flip_bot_{wager:.2f}_tails")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await self.send_with_buttons(chat_id, result_text, reply_markup, user_id)
        
        # Send sticker based on outcome
        await self.send_sticker(chat_id, outcome, profit)

    async def roulette_play_direct(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float, choice: str):
        """Play roulette directly from command (for specific number bets)"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = update.message.chat_id
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager first
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        blacks = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        greens = [0, 37]
        
        all_numbers = reds + blacks + greens
        result_num = random.choice(all_numbers)
        
        if result_num in reds:
            result_color = "red"
            result_emoji = "🔴"
        elif result_num in blacks:
            result_color = "black"
            result_emoji = "⚫"
        else:
            result_color = "green"
            result_emoji = "🟢"
            
        result_display = "0" if result_num == 0 else "00" if result_num == 37 else str(result_num)
        
        roulette_stickers = self.stickers.get('roulette', {})
        sticker_id = roulette_stickers.get(result_display)
        
        if sticker_id:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
        else:
            await update.message.reply_text("🎰 Spinning the wheel...")
        
        await asyncio.sleep(2.5)
        
        if choice.startswith("num_"):
            bet_num = int(choice.split("_")[1])
            bet_display = "0" if bet_num == 0 else "00" if bet_num == 37 else str(bet_num)
            
            if bet_num == result_num:
                profit = wager * 35
                outcome = "win"
                result_text = f"@{username} won ${profit:.2f}"
                user_data['balance'] += wager * 36  # Return wager + 35x winnings
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-profit)
            else:
                profit = -wager
                outcome = "loss"
                result_text = f"@{username} lost ${wager:.2f}"
                self.db.update_house_balance(wager)
            
            self._update_user_stats(user_id, wager, profit, outcome)
            self.db.add_transaction(user_id, "roulette", profit, f"Roulette - Bet: #{bet_display} - Wager: ${wager:.2f}")
            self.db.record_game({
                "type": "roulette",
                "player_id": user_id,
                "wager": wager,
                "choice": f"#{bet_display}",
                "result": result_display,
                "result_color": result_color,
                "outcome": outcome,
                "balance_after": user_data['balance']
            })
            
            await update.message.reply_text(result_text, parse_mode="Markdown")

    async def roulette_play(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float, choice: str):
        """Play roulette (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
        if wager > user_data['balance']:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager first
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
        blacks = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]
        greens = [0, 37]
        
        all_numbers = reds + blacks + greens
        result_num = random.choice(all_numbers)
        
        if result_num in reds:
            result_color = "red"
            result_emoji = "🔴"
        elif result_num in blacks:
            result_color = "black"
            result_emoji = "⚫"
        else:
            result_color = "green"
            result_emoji = "🟢"
            
        result_display = "0" if result_num == 0 else "00" if result_num == 37 else str(result_num)
        
        roulette_stickers = self.stickers.get('roulette', {})
        sticker_id = roulette_stickers.get(result_display)
        
        if sticker_id:
            await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)
        else:
            await context.bot.send_message(chat_id=chat_id, text="🎰 Spinning the wheel...")
        
        await asyncio.sleep(2.5)
        
        profit = 0.0
        outcome = "loss"
        multiplier = 0
        won = False
        bet_description = choice.upper()
        
        if choice == "red" and result_num in reds:
            won = True
            multiplier = 2
            bet_description = "RED"
        elif choice == "black" and result_num in blacks:
            won = True
            multiplier = 2
            bet_description = "BLACK"
        elif choice == "green" and result_num in greens:
            won = True
            multiplier = 14
            bet_description = "GREEN"
        elif choice == "odd" and result_num > 0 and result_num != 37 and result_num % 2 == 1:
            won = True
            multiplier = 2
            bet_description = "ODD"
        elif choice == "even" and result_num > 0 and result_num != 37 and result_num % 2 == 0:
            won = True
            multiplier = 2
            bet_description = "EVEN"
        elif choice == "low" and result_num >= 1 and result_num <= 18:
            won = True
            multiplier = 2
            bet_description = "LOW (1-18)"
        elif choice == "high" and result_num >= 19 and result_num <= 36:
            won = True
            multiplier = 2
            bet_description = "HIGH (19-36)"
        elif choice == "zero" and result_num == 0:
            won = True
            multiplier = 36
            bet_description = "0"
        elif choice == "doublezero" and result_num == 37:
            won = True
            multiplier = 36
            bet_description = "00"
        
        if won:
            profit = wager * (multiplier - 1)
            outcome = "win"
            result_text = f"@{username} won ${profit:.2f}"
            user_data['balance'] += wager * multiplier  # Return wager + winnings
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-profit)
        else:
            profit = -wager
            result_text = f"@{username} lost ${wager:.2f}"
            self.db.update_house_balance(wager)
        
        self._update_user_stats(user_id, wager, profit, outcome)
        self.db.add_transaction(user_id, "roulette", profit, f"Roulette - Bet: {bet_description} - Wager: ${wager:.2f}")
        self.db.record_game({
            "type": "roulette",
            "player_id": user_id,
            "wager": wager,
            "choice": choice,
            "result": result_display,
            "result_color": result_color,
            "outcome": outcome,
            "balance_after": user_data['balance']
        })
        
        keyboard = [
            [InlineKeyboardButton("Red (2x)", callback_data=f"roulette_{wager:.2f}_red"),
             InlineKeyboardButton("Black (2x)", callback_data=f"roulette_{wager:.2f}_black")],
            [InlineKeyboardButton("Odd (2x)", callback_data=f"roulette_{wager:.2f}_odd"),
             InlineKeyboardButton("Even (2x)", callback_data=f"roulette_{wager:.2f}_even")],
            [InlineKeyboardButton("Low (2x)", callback_data=f"roulette_{wager:.2f}_low"),
             InlineKeyboardButton("High (2x)", callback_data=f"roulette_{wager:.2f}_high")],
            [InlineKeyboardButton("0 (35x)", callback_data=f"roulette_{wager:.2f}_zero"),
             InlineKeyboardButton("00 (35x)", callback_data=f"roulette_{wager:.2f}_doublezero")],
            [InlineKeyboardButton("Green (14x)", callback_data=f"roulette_{wager:.2f}_green")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await self.send_with_buttons(chat_id, result_text, reply_markup, user_id)

    # --- CALLBACK HANDLER ---

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles all inline button presses."""
        query = update.callback_query
        
        # Ensure user is registered and username is updated
        self.ensure_user_registered(update)
        
        data = query.data
        user_id = query.from_user.id
        chat_id = query.message.chat_id
        message_id = query.message.message_id
        
        # Check if button was already clicked (prevent spam)
        button_key = (chat_id, message_id, data)
        if button_key in self.clicked_buttons:
            await query.answer("❌ This button has already been used!", show_alert=True)
            return
        
        # Check button ownership (except for public buttons like PVP accept challenges)
        # PVP accept buttons that anyone can click to accept challenges
        pvp_accept_buttons = [
            "accept_dice_", "accept_darts_", "accept_basketball_", "accept_soccer_", "accept_bowling_", "accept_coinflip_"
        ]
        # Truly public buttons (leaderboard)
        global_public_buttons = ["lb_page_", "lb_dices_week", "lb_dices_all", "lb_wagered"]
        # Mines buttons (they verify ownership internally via user_id in callback data)
        mines_buttons = ["mines_start_", "mines_reveal_", "mines_cashout_", "mines_again_", "mines_change_", "mines_noop"]
        # Blackjack buttons (they verify ownership internally via user_id in callback data)
        blackjack_buttons = ["bj_"]
        # Baccarat buttons
        baccarat_buttons = ["bacc_"]
        # Keno buttons (they verify ownership internally via user_id in callback data)
        keno_buttons = ["keno_pick_", "keno_draw_", "keno_clear_", "keno_again_", "keno_noop", "keno_select_rounds_", "keno_rounds_", "keno_back_", "keno_next_", "keno_stop_"]
        # Limbo buttons
        limbo_buttons = ["limbo_play_", "limbo_again_"]
        # Hi-Lo buttons
        hilo_buttons = ["hilo_higher_", "hilo_lower_", "hilo_tie_", "hilo_skip_", "hilo_cashout_", "hilo_again_"]
        # Connect 4 buttons
        connect4_buttons = ["connect4_accept_", "connect4_drop_", "connect4_roll_", "connect4_noop"]
        # Withdrawal approval buttons (only admins/approvers can use)
        withdrawal_buttons = ["withdraw_approve_", "withdraw_deny_"]
        
        is_pvp_accept = any(data.startswith(prefix) for prefix in pvp_accept_buttons)
        is_global_public = any(data.startswith(prefix) or data == prefix for prefix in global_public_buttons)
        is_withdrawal_button = any(data.startswith(prefix) for prefix in withdrawal_buttons)
        is_mines_button = any(data.startswith(prefix) or data == prefix for prefix in mines_buttons)
        is_blackjack_button = any(data.startswith(prefix) for prefix in blackjack_buttons)
        is_baccarat_button = any(data.startswith(prefix) for prefix in baccarat_buttons)
        is_keno_button = any(data.startswith(prefix) or data == prefix for prefix in keno_buttons)
        is_connect4_button = any(data.startswith(prefix) or data == prefix for prefix in connect4_buttons)
        
        ownership_key = (chat_id, message_id)
        # Block button if it's NOT public AND (not registered OR not owned by user)
        if not is_pvp_accept and not is_global_public and not is_mines_button and not is_blackjack_button and not is_baccarat_button and not is_keno_button and not is_connect4_button:
            # Withdrawal buttons bypass ownership but require approval permission
            if is_withdrawal_button:
                if not self.can_approve_withdrawals(user_id):
                    await query.answer("❌ You don't have permission to approve withdrawals!", show_alert=True)
                    return
            elif ownership_key not in self.button_ownership or self.button_ownership[ownership_key] != user_id:
                await query.answer("❌ This button is not for you!", show_alert=True)
                return
        
        await query.answer() # Acknowledge the button press
        
        # Mark button as clicked for game buttons (not utility buttons)
        game_buttons = [
            "dice_bot_", "darts_bot_", "basketball_bot_", "soccer_bot_", "bowling_bot_", "flip_bot_", "roulette_",
            "dice_player_open_", "darts_player_open_", "basketball_player_open_", "soccer_player_open_", "bowling_player_open_",
            "flip_player_open_", "accept_dice_", "accept_darts_", "accept_basketball_", "accept_soccer_", "accept_bowling_",
            "accept_coinflip_", "claim_daily_bonus", "claim_level_bonus_", "predict_select_", "predict_again_", "slots_"
        ]
        if any(data.startswith(prefix) for prefix in game_buttons):
            self.clicked_buttons.add(button_key)
            # Remove from pending opponent selection when user clicks a game button
            self.pending_opponent_selection.discard(user_id)
        
        try:
            # Game Callbacks (Dice vs Bot)
            if data.startswith("dice_bot_"):
                wager = float(data.split('_')[2])
                await self.dice_vs_bot(update, context, wager)
                
            # Game Callbacks (Darts vs Bot)
            elif data.startswith("darts_bot_"):
                wager = float(data.split('_')[2])
                await self.darts_vs_bot(update, context, wager)
                
            # Game Callbacks (Basketball vs Bot)
            elif data.startswith("basketball_bot_"):
                wager = float(data.split('_')[2])
                await self.basketball_vs_bot(update, context, wager)
                
            # Game Callbacks (Soccer vs Bot)
            elif data.startswith("soccer_bot_"):
                wager = float(data.split('_')[2])
                await self.soccer_vs_bot(update, context, wager)
                
            # Game Callbacks (Bowling vs Bot)
            elif data.startswith("bowling_bot_"):
                wager = float(data.split('_')[2])
                await self.bowling_vs_bot(update, context, wager)
                
            # Game Callbacks (Dice PvP)
            elif data.startswith("dice_player_open_"):
                wager = float(data.split('_')[3])
                await self.create_open_dice_challenge(update, context, wager)
                
            elif data.startswith("accept_dice_"):
                challenge_id = data.split('_', 2)[2]
                await self.accept_dice_challenge(update, context, challenge_id)
            
            # Game Callbacks (Darts PvP)
            elif data.startswith("darts_player_open_"):
                wager = float(data.split('_')[3])
                await self.create_emoji_pvp_challenge(update, context, wager, "darts", "🎯")
            
            elif data.startswith("accept_darts_"):
                challenge_id = data.split('_', 2)[2]
                await self.accept_emoji_pvp_challenge(update, context, challenge_id)
            
            # Game Callbacks (Basketball PvP)
            elif data.startswith("basketball_player_open_"):
                wager = float(data.split('_')[3])
                await self.create_emoji_pvp_challenge(update, context, wager, "basketball", "🏀")
            
            elif data.startswith("accept_basketball_"):
                challenge_id = data.split('_', 2)[2]
                await self.accept_emoji_pvp_challenge(update, context, challenge_id)
            
            # Game Callbacks (Soccer PvP)
            elif data.startswith("soccer_player_open_"):
                wager = float(data.split('_')[3])
                await self.create_emoji_pvp_challenge(update, context, wager, "soccer", "⚽")
            
            elif data.startswith("accept_soccer_"):
                challenge_id = data.split('_', 2)[2]
                await self.accept_emoji_pvp_challenge(update, context, challenge_id)
            
            # Game Callbacks (Bowling PvP)
            elif data.startswith("bowling_player_open_"):
                wager = float(data.split('_')[3])
                await self.create_emoji_pvp_challenge(update, context, wager, "bowling", "🎳")
            
            elif data.startswith("accept_bowling_"):
                challenge_id = data.split('_', 2)[2]
                await self.accept_emoji_pvp_challenge(update, context, challenge_id)
            
            # Game Callbacks (CoinFlip vs Bot)
            elif data.startswith("flip_bot_"):
                parts = data.split('_')
                wager = float(parts[2])
                choice = parts[3]
                await self.coinflip_vs_bot(update, context, wager, choice)
            
            # Game Callbacks (Roulette)
            elif data.startswith("roulette_"):
                parts = data.split('_')
                wager = float(parts[1])
                choice = parts[2]
                await self.roulette_play(update, context, wager, choice)
            
            # Game Callbacks (Predict initial selection - wager already deducted)
            elif data.startswith("predict_select_"):
                parts = data.split('_')
                wager = float(parts[2])
                predicted_number = int(parts[3])
                
                # Remove from pending predictions (cancel timeout refund)
                predict_key = f"predict_{chat_id}_{message_id}"
                if hasattr(self, 'pending_predictions') and predict_key in self.pending_predictions:
                    del self.pending_predictions[predict_key]
                
                user_data = self.db.get_user(user_id)
                
                # Edit the selection message to show prediction made
                await query.edit_message_text(f"🔮 You predicted **{predicted_number}**\n\nRolling the dice...", parse_mode="Markdown")
                
                # Send the dice emoji and wait for result
                dice_message = await context.bot.send_dice(chat_id=chat_id, emoji="🎲")
                actual_roll = dice_message.dice.value
                
                await asyncio.sleep(3)
                
                # Check if prediction matches
                if actual_roll == predicted_number:
                    payout = wager * 6
                    profit = payout - wager
                    new_balance = user_data['balance'] + payout
                    
                    self.db.update_user(user_id, {
                        'balance': new_balance,
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1,
                        'games_won': user_data['games_won'] + 1
                    })
                    self.db.update_house_balance(-profit)
                    
                    keyboard = [
                        [InlineKeyboardButton("1️⃣", callback_data=f"predict_again_{wager:.2f}_1"),
                         InlineKeyboardButton("2️⃣", callback_data=f"predict_again_{wager:.2f}_2"),
                         InlineKeyboardButton("3️⃣", callback_data=f"predict_again_{wager:.2f}_3")],
                        [InlineKeyboardButton("4️⃣", callback_data=f"predict_again_{wager:.2f}_4"),
                         InlineKeyboardButton("5️⃣", callback_data=f"predict_again_{wager:.2f}_5"),
                         InlineKeyboardButton("6️⃣", callback_data=f"predict_again_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} won ${profit:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                else:
                    self.db.update_user(user_id, {
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1
                    })
                    self.db.update_house_balance(wager)
                    
                    keyboard = [
                        [InlineKeyboardButton("1️⃣", callback_data=f"predict_again_{wager:.2f}_1"),
                         InlineKeyboardButton("2️⃣", callback_data=f"predict_again_{wager:.2f}_2"),
                         InlineKeyboardButton("3️⃣", callback_data=f"predict_again_{wager:.2f}_3")],
                        [InlineKeyboardButton("4️⃣", callback_data=f"predict_again_{wager:.2f}_4"),
                         InlineKeyboardButton("5️⃣", callback_data=f"predict_again_{wager:.2f}_5"),
                         InlineKeyboardButton("6️⃣", callback_data=f"predict_again_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} lost ${wager:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                
                self.db.record_game({
                    'type': 'dice_predict',
                    'player_id': user_id,
                    'wager': wager,
                    'predicted': predicted_number,
                    'actual_roll': actual_roll,
                    'result': 'win' if actual_roll == predicted_number else 'loss',
                    'payout': (wager * 6) if actual_roll == predicted_number else 0,
                    'balance_after': user_data['balance']
                })
            
            # Game Callbacks (Predict play again - needs to deduct wager)
            elif data.startswith("predict_again_"):
                parts = data.split('_')
                wager = float(parts[2])
                predicted_number = int(parts[3])
                
                user_data = self.db.get_user(user_id)
                
                if wager > user_data['balance']:
                    await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
                    return
                
                # Deduct wager from user balance
                self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
                
                # Send the dice emoji and wait for result
                dice_message = await context.bot.send_dice(chat_id=chat_id, emoji="🎲")
                actual_roll = dice_message.dice.value
                
                await asyncio.sleep(3)
                
                # Check if prediction matches
                if actual_roll == predicted_number:
                    payout = wager * 6
                    profit = payout - wager
                    new_balance = user_data['balance'] + payout
                    
                    self.db.update_user(user_id, {
                        'balance': new_balance,
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1,
                        'games_won': user_data['games_won'] + 1
                    })
                    self.db.update_house_balance(-profit)
                    
                    keyboard = [
                        [InlineKeyboardButton("1️⃣", callback_data=f"predict_again_{wager:.2f}_1"),
                         InlineKeyboardButton("2️⃣", callback_data=f"predict_again_{wager:.2f}_2"),
                         InlineKeyboardButton("3️⃣", callback_data=f"predict_again_{wager:.2f}_3")],
                        [InlineKeyboardButton("4️⃣", callback_data=f"predict_again_{wager:.2f}_4"),
                         InlineKeyboardButton("5️⃣", callback_data=f"predict_again_{wager:.2f}_5"),
                         InlineKeyboardButton("6️⃣", callback_data=f"predict_again_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} won ${profit:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                else:
                    self.db.update_user(user_id, {
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1
                    })
                    self.db.update_house_balance(wager)
                    
                    keyboard = [
                        [InlineKeyboardButton("1️⃣", callback_data=f"predict_again_{wager:.2f}_1"),
                         InlineKeyboardButton("2️⃣", callback_data=f"predict_again_{wager:.2f}_2"),
                         InlineKeyboardButton("3️⃣", callback_data=f"predict_again_{wager:.2f}_3")],
                        [InlineKeyboardButton("4️⃣", callback_data=f"predict_again_{wager:.2f}_4"),
                         InlineKeyboardButton("5️⃣", callback_data=f"predict_again_{wager:.2f}_5"),
                         InlineKeyboardButton("6️⃣", callback_data=f"predict_again_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} lost ${wager:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                
                self.db.record_game({
                    'type': 'dice_predict',
                    'player_id': user_id,
                    'wager': wager,
                    'predicted': predicted_number,
                    'actual_roll': actual_roll,
                    'result': 'win' if actual_roll == predicted_number else 'loss',
                    'payout': (wager * 6) if actual_roll == predicted_number else 0,
                    'balance_after': user_data['balance']
                })
            
            # Game Callbacks (Slots play again)
            elif data.startswith("slots_play_"):
                wager = float(data.split('_')[2])
                await self.slots_play(update, context, wager)

            # Leaderboard Navigation
            elif data.startswith("lb_wagered"):
                # Extract back_to from callback data (lb_wagered_menu_more_content or lb_wagered_back_to_menu)
                parts = data.split("_", 2)
                back_to = parts[2] if len(parts) > 2 else "back_to_menu"
                await self.show_leaderboard_wagered(update, back_to=back_to)
            elif data.startswith("lb_dices_week"):
                parts = data.split("_", 3)
                back_to = parts[3] if len(parts) > 3 else "back_to_menu"
                await self.show_leaderboard_dices(update, "week", back_to=back_to)
            elif data.startswith("lb_dices_all"):
                parts = data.split("_", 3)
                back_to = parts[3] if len(parts) > 3 else "back_to_menu"
                await self.show_leaderboard_dices(update, "all", back_to=back_to)
            
            # Matches Pagination
            elif data.startswith("matches_page_"):
                parts = data.split("_")
                target_user_id = int(parts[2])
                page = int(parts[3])
                target_user = self.db.get_user(target_user_id)
                target_username = target_user.get('username', f'User{target_user_id}')
                await self._show_matches_page(query.message, target_user_id, target_username, page, user_id)
            
            # History Pagination
            elif data.startswith("history_page_"):
                page = int(data.split("_")[2])
                await self._show_history_page(query.message, user_id, page, edit_message=True, show_back=True)
            
            # Levels Tier Navigation
            elif data.startswith("levels_tier_"):
                tier_index = int(data.replace("levels_tier_", ""))
                user_data = self.db.get_user(user_id)
                total_wagered = user_data.get('total_wagered', 0)
                levels_text, keyboard = self.build_tier_display(tier_index, total_wagered, user_id)
                await query.edit_message_text(levels_text, reply_markup=keyboard, parse_mode="Markdown")
            
            # All Balances Pagination (Admin)
            elif data.startswith("allbal_page_"):
                if not self.is_admin(user_id):
                    await query.answer("❌ This is for administrators only.", show_alert=True)
                    return
                page = int(data.split('_')[2])
                await self.show_allbalances_page(update, page)
                
            # Deposit Crypto Selection
            elif data.startswith("deposit_crypto_"):
                currency = data.replace("deposit_crypto_", "")
                await self.show_deposit_address(update, context, currency)
            
            # Back to Main Menu
            elif data == "back_to_main_menu":
                user_data = self.db.get_user(user_id)
                balance_text = f"🏦 **Menu**\n\nYour balance: **${user_data['balance']:.2f}**\n\nChoose the action:"
                keyboard = [
                    [InlineKeyboardButton("🎮 Play", callback_data="menu_play")],
                    [InlineKeyboardButton("💳 Deposit", callback_data="deposit_mock"),
                     InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_mock")],
                    [InlineKeyboardButton("🎁 Bonuses", callback_data="menu_bonuses"),
                     InlineKeyboardButton("📚 More Content", callback_data="menu_more_content")],
                    [InlineKeyboardButton("⚙️ Commands", callback_data="menu_commands"),
                     InlineKeyboardButton("📞 Support", callback_data="menu_support")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            # Deposit Back to Currency Selection
            elif data == "deposit_back":
                user_data = self.db.get_user(user_id)
                keyboard = []
                for code, info in SUPPORTED_DEPOSIT_CRYPTOS.items():
                    btn = InlineKeyboardButton(info['name'], callback_data=f"deposit_crypto_{code}")
                    keyboard.append([btn])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            
            # Generate New Deposit Address
            elif data == "new_deposit_address":
                await query.answer("Generating new address...")
                
                address_data = await self.generate_coinremitter_address(user_id)
                
                if address_data:
                    user_deposit_address = address_data.get('address')
                    qr_code_url = address_data.get('qr_code')
                    
                    user_data = self.db.get_user(user_id)
                    user_data['ltc_deposit_address'] = user_deposit_address
                    user_data['ltc_qr_code'] = qr_code_url
                    user_data['ltc_address_expires'] = address_data.get('expire_on')
                    self.db.update_user(user_id, user_data)
                    self.db.save_data()
                    
                    deposit_text = f"""Your NEW deposit address:

`{user_deposit_address}`

Send any amount of LTC - you will be credited the exact USD value.

59:59

TX ID: _waiting for deposit..._"""
                    
                    keyboard = [[InlineKeyboardButton("Generate New Address", callback_data="new_deposit_address")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=reply_markup)
                else:
                    master_address = os.getenv("LTC_MASTER_ADDRESS", "")
                    if master_address:
                        await query.edit_message_text(
                            f"⚠️ Could not generate unique address. Use master address:\n\n"
                            f"`{master_address}`\n\n"
                            f"**Include your User ID in memo:** `{user_id}`",
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text("❌ Could not generate new address. Contact admin.")
            
            # Utility Callbacks
            elif data == "claim_daily_bonus":
                user_data = self.db.get_user(user_id)
                bonus_amount = user_data.get('wagered_since_last_withdrawal', 0) * 0.005

                if bonus_amount < 0.01:
                     await query.edit_message_text("❌ Minimum bonus to claim is $0.01.")
                     return

                # Process claim
                user_data['balance'] += bonus_amount
                user_data['wagered_since_last_withdrawal'] = 0.0 # Reset wagered amount
                self.db.update_user(user_id, user_data)
                
                self.db.add_transaction(user_id, "bonus_claim", bonus_amount, "Bonus Claim")
                
                # Show updated rakeback view with success message
                rakeback_text = f"✅ **Bonus Claimed!** You received **${bonus_amount:.2f}**\n\n"
                rakeback_text += "💎 **Rakeback**\n\n"
                rakeback_text += f"Your current rakeback: **$0.00**\n\n"
                rakeback_text += "Play games and claim your rakeback bonus anytime!"
                
                keyboard = [
                    [InlineKeyboardButton("💸 Play to earn!", callback_data="no_rakeback")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_bonus")]
                ]
                
                await query.edit_message_text(rakeback_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

            elif data.startswith("claim_level_bonus_"):
                level_id = data.replace("claim_level_bonus_", "")
                user_data = self.db.get_user(user_id)
                total_wagered = user_data.get('total_wagered', 0)
                current_level = get_user_level(total_wagered, user_id, self.db)
                claimed_bonuses = user_data.get('claimed_level_bonuses', [])
                
                level_to_claim = None
                for level in LEVELS:
                    if level['id'] == level_id:
                        level_to_claim = level
                        break
                
                if not level_to_claim:
                    await query.edit_message_text("❌ Invalid level bonus.")
                    return
                
                if total_wagered < level_to_claim['threshold']:
                    await query.edit_message_text(f"❌ You haven't reached {level_to_claim['name']} yet!")
                    return
                
                if level_id in claimed_bonuses:
                    await query.edit_message_text(f"❌ You've already claimed the {level_to_claim['name']} bonus!")
                    return
                
                bonus_amount = level_to_claim['bonus']
                user_data['balance'] += bonus_amount
                claimed_bonuses.append(level_id)
                user_data['claimed_level_bonuses'] = claimed_bonuses
                self.db.update_user(user_id, user_data)
                
                self.db.add_transaction(user_id, "level_bonus", bonus_amount, f"Level Bonus - {level_to_claim['name']}")
                
                # Re-fetch user data and rebuild the same level bonus view
                next_level = get_next_level(total_wagered)
                
                # Get user's rank
                all_users = []
                for u_data in self.db.data['users'].values():
                    all_users.append({
                        "user_id": u_data.get('user_id'),
                        "total_wagered": u_data.get('total_wagered', 0)
                    })
                all_users.sort(key=lambda x: x['total_wagered'], reverse=True)
                user_rank = None
                for i, u in enumerate(all_users):
                    if u['user_id'] == user_id:
                        user_rank = i + 1
                        break
                
                # Find ALL unclaimed level bonuses that the user has reached (after claiming this one)
                unclaimed_levels = []
                for level in LEVELS:
                    if total_wagered >= level['threshold'] and level['id'] not in claimed_bonuses and level['bonus'] > 0:
                        unclaimed_levels.append(level)
                
                total_unclaimed = sum(level['bonus'] for level in unclaimed_levels)
                
                # Build same format as view_level_bonus
                level_text = "🌲 **Level Up Bonus**\n\n"
                level_text += "Play games, level up and get even more bonuses!\n\n"
                level_text += f"Your current level:\n{current_level['emoji']} **{current_level['name']}** - ${total_wagered:,.0f} wagered\n\n"
                
                if next_level:
                    level_text += f"Next Level:\n{next_level['emoji']} **{next_level['name']}** - ${next_level['threshold']:,.0f} wagered\n\n"
                    wager_needed = next_level['threshold'] - total_wagered
                    if user_rank:
                        level_text += f"You are ranked **#{user_rank}**.\n"
                    level_text += f"Wager **${wager_needed:,.0f}** more to upgrade your level!"
                else:
                    if user_rank:
                        level_text += f"You are ranked **#{user_rank}**.\n"
                    level_text += "You've reached the maximum level!"
                
                # Show unclaimed bonuses info
                if unclaimed_levels:
                    level_text += f"\n\n🎁 **{len(unclaimed_levels)} unclaimed bonus(es)** worth **${total_unclaimed:,.0f}** total!"
                
                # Build keyboard
                keyboard = []
                if unclaimed_levels:
                    next_bonus = unclaimed_levels[0]
                    keyboard.append([InlineKeyboardButton(f"🎁 Claim {next_bonus['emoji']} {next_bonus['name']} - ${next_bonus['bonus']:.0f}", callback_data=f"claim_level_bonus_{next_bonus['id']}")])
                keyboard.append([InlineKeyboardButton("Levels List", callback_data="show_levels_list")])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_bonus")])
                
                await query.edit_message_text(level_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

            elif data == "view_rakeback":
                user_data = self.db.get_user(user_id)
                wagered_since_withdrawal = user_data.get('wagered_since_last_withdrawal', 0)
                rakeback_amount = wagered_since_withdrawal * 0.005
                
                rakeback_text = "💎 **Rakeback**\n\n"
                rakeback_text += f"Your current rakeback: **${rakeback_amount:.2f}**\n\n"
                rakeback_text += "Play games and claim your rakeback bonus anytime!"
                
                keyboard = []
                if rakeback_amount >= 0.01:
                    keyboard.append([InlineKeyboardButton(f"💸 Claim ${rakeback_amount:.2f}", callback_data="claim_daily_bonus")])
                else:
                    keyboard.append([InlineKeyboardButton("💸 Play to earn!", callback_data="no_rakeback")])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_bonus")])
                
                await query.edit_message_text(rakeback_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
            
            elif data == "view_level_bonus":
                user_data = self.db.get_user(user_id)
                total_wagered = user_data.get('total_wagered', 0)
                current_level = get_user_level(total_wagered, user_id, self.db)
                next_level = get_next_level(total_wagered)
                claimed_bonuses = user_data.get('claimed_level_bonuses', [])
                
                # Get user's rank
                leaderboard = self.db.get_leaderboard()
                user_rank = None
                all_users = []
                for u_data in self.db.data['users'].values():
                    all_users.append({
                        "user_id": u_data.get('user_id'),
                        "total_wagered": u_data.get('total_wagered', 0)
                    })
                all_users.sort(key=lambda x: x['total_wagered'], reverse=True)
                for i, u in enumerate(all_users):
                    if u['user_id'] == user_id:
                        user_rank = i + 1
                        break
                
                # Find ALL unclaimed level bonuses that the user has reached
                unclaimed_levels = []
                for level in LEVELS:
                    if total_wagered >= level['threshold'] and level['id'] not in claimed_bonuses and level['bonus'] > 0:
                        unclaimed_levels.append(level)
                
                total_unclaimed = sum(level['bonus'] for level in unclaimed_levels)
                
                level_text = "🌲 **Level Up Bonus**\n\n"
                level_text += "Play games, level up and get even more bonuses!\n\n"
                level_text += f"Your current level:\n{current_level['emoji']} **{current_level['name']}** - ${total_wagered:,.0f} wagered\n\n"
                
                if next_level:
                    level_text += f"Next Level:\n{next_level['emoji']} **{next_level['name']}** - ${next_level['threshold']:,.0f} wagered\n\n"
                    wager_needed = next_level['threshold'] - total_wagered
                    if user_rank:
                        level_text += f"You are ranked **#{user_rank}**.\n"
                    level_text += f"Wager **${wager_needed:,.0f}** more to upgrade your level!"
                else:
                    if user_rank:
                        level_text += f"You are ranked **#{user_rank}**.\n"
                    level_text += "You've reached the maximum level!"
                
                keyboard = []
                if unclaimed_levels:
                    level_text += f"\n\n🎁 **{len(unclaimed_levels)} unclaimed bonus(es)** worth **${total_unclaimed:,.0f}** total!"
                    # Single button to claim bonuses one by one
                    next_bonus = unclaimed_levels[0]
                    keyboard.append([InlineKeyboardButton(f"🎁 Claim {next_bonus['emoji']} {next_bonus['name']} - ${next_bonus['bonus']:.0f}", callback_data=f"claim_level_bonus_{next_bonus['id']}")])
                else:
                    keyboard.append([InlineKeyboardButton("No bonus available", callback_data="no_level_bonus")])
                keyboard.append([InlineKeyboardButton("Levels List", callback_data="show_levels_list")])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_bonus")])
                
                await query.edit_message_text(level_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return
            
            elif data == "back_to_bonus":
                # Show the main bonus screen again
                bonus_text = "🎁 **Bonus**\n\n"
                bonus_text += "In this section you can find bonuses that you can get by playing games!\n\n"
                bonus_text += "💎 **Rakeback**\n"
                bonus_text += "Play games and claim your rakeback bonus anytime!\n\n"
                bonus_text += "💎 **Level Up Bonus**\n"
                bonus_text += "Play games, level up and earn money!"
                
                keyboard = [
                    [
                        InlineKeyboardButton("🎁 Rakeback", callback_data="view_rakeback"),
                        InlineKeyboardButton("🎁 Level Up Bonus", callback_data="view_level_bonus")
                    ],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
                ]
                
                await query.edit_message_text(bonus_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
                return

            elif data == "no_rakeback":
                await query.answer("💸 Play games to earn rakeback!", show_alert=True)
                return
            
            elif data == "no_level_bonus":
                await query.answer("⬆️ Reach a new level to unlock level bonuses!", show_alert=True)
                return
            
            elif data == "show_levels_list":
                user_data = self.db.get_user(user_id)
                total_wagered = user_data.get('total_wagered', 0)
                current_level = get_user_level(total_wagered, user_id, self.db)
                
                current_tier_name = current_level.get('tier_name', 'Bronze')
                if current_tier_name == 'Unranked':
                    current_tier_name = 'Bronze'
                
                tier_index = get_tier_index(current_tier_name)
                levels_text, keyboard = self.build_tier_display(tier_index, total_wagered, user_id)
                
                await query.edit_message_text(levels_text, reply_markup=keyboard, parse_mode="Markdown")
                return

            elif data == "back_to_menu":
                user_data = self.db.get_user(user_id)
                balance_text = f"🏦 **Menu**\n\nYour balance: **${user_data['balance']:.2f}**\n\nChoose the action:"
                
                keyboard = [
                    [InlineKeyboardButton("🎮 Play", callback_data="menu_play")],
                    [InlineKeyboardButton("💳 Deposit", callback_data="deposit_mock"),
                     InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_mock")],
                    [InlineKeyboardButton("🎁 Bonuses", callback_data="menu_bonuses"),
                     InlineKeyboardButton("📚 More Content", callback_data="menu_more_content")],
                    [InlineKeyboardButton("⚙️ Commands", callback_data="menu_commands"),
                     InlineKeyboardButton("📞 Support", callback_data="menu_support")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "menu_commands":
                commands_text = """⚙️ **Commands**

**Games:**
/dice - Roll dice 🎲
/darts - Play darts 🎯
/basketball - Shoot hoops 🏀
/soccer - Play soccer ⚽
/bowling - Go bowling 🎳
/flip - Flip a coin 🪙
/predict - Dice prediction 🔮
/roulette - Play roulette 🎡
/slots - Play slots 🎰
/blackjack - Play blackjack ♠️
/mines - Play mines 💣
/baccarat - Play baccarat 🃏
/keno - Play keno 🎱
/limbo - Play limbo 🚀
/hilo - Play hi-lo 📈
/connect - Connect 4 🔴

**Account:**
/bal - Check your balance
/bonus - Get your bonuses
/stats - View your stats
/levels - View level rewards
/history - View game history
/deposit - Deposit funds
/withdraw - Withdraw funds
/tip @user amount - Tip another player

**Info:**
/leaderboard - View top players
/housebal - View house balance
"""
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(commands_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "menu_play":
                game_menu_text = "🎮 **Game Menu**\n\nChoose the game you want to play:"
                
                keyboard = [
                    [InlineKeyboardButton("🎲 Dice", callback_data="game_info_dice")],
                    [InlineKeyboardButton("🎰 Slots", callback_data="game_info_slots")],
                    [InlineKeyboardButton("🔮 Dice Prediction", callback_data="game_info_predict")],
                    [InlineKeyboardButton("🎡 Roulette", callback_data="game_info_roulette")],
                    [InlineKeyboardButton("🪙 Coinflip", callback_data="game_info_coinflip")],
                    [InlineKeyboardButton("🎯 Darts", callback_data="game_info_darts")],
                    [InlineKeyboardButton("🏀 Basketball", callback_data="game_info_basketball")],
                    [InlineKeyboardButton("⚽ Soccer", callback_data="game_info_soccer")],
                    [InlineKeyboardButton("🎳 Bowling", callback_data="game_info_bowling")],
                    [InlineKeyboardButton("♠️ Blackjack", callback_data="game_info_blackjack")],
                    [InlineKeyboardButton("💣 Mines", callback_data="game_info_mines")],
                    [InlineKeyboardButton("🃏 Baccarat", callback_data="game_info_baccarat")],
                    [InlineKeyboardButton("🎱 Keno", callback_data="game_info_keno")],
                    [InlineKeyboardButton("🚀 Limbo", callback_data="game_info_limbo")],
                    [InlineKeyboardButton("📈 Hi-Lo", callback_data="game_info_hilo")],
                    [InlineKeyboardButton("🔴 Connect 4", callback_data="game_info_connect4")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(game_menu_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "menu_more_content":
                more_content_text = "📚 **More Content**"
                
                keyboard = [
                    [InlineKeyboardButton("📊 Your Statistics", callback_data="more_stats"),
                     InlineKeyboardButton("📅 Matches History", callback_data="more_history")],
                    [InlineKeyboardButton("🏆 Leaderboard", callback_data="more_leaderboard")],
                    [InlineKeyboardButton("🎟️ Raffle", callback_data="more_raffle")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(more_content_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "menu_bonuses":
                user_data = self.db.get_user(user_id)
                bonus_text = "🎁 **Bonus**\n\n"
                bonus_text += "In this section you can find bonuses that you can get by playing games!\n\n"
                bonus_text += "💎 **Rakeback**\n"
                bonus_text += "Play games and claim your rakeback bonus anytime!\n\n"
                bonus_text += "💎 **Level Up Bonus**\n"
                bonus_text += "Play games, level up and earn money!"
                
                keyboard = [
                    [
                        InlineKeyboardButton("🎁 Rakeback", callback_data="view_rakeback"),
                        InlineKeyboardButton("🎁 Level Up Bonus", callback_data="view_level_bonus")
                    ],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(bonus_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "menu_support":
                support_text = """📞 **Support**

Need help? Contact our support team:

🔹 Telegram: @GranTeseroSupport
🔹 Issues with deposits/withdrawals
🔹 Questions about games
🔹 Report bugs or problems

We're here to help 24/7!"""
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(support_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            # --- ADMIN MENU CALLBACKS ---
            elif data == "back_to_admin_menu":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                is_env_admin = user_id in self.env_admin_ids
                admin_type = "Permanent Admin" if is_env_admin else "Dynamic Admin"
                
                house_balance = self.db.get_house_balance()
                total_users = len(self.db.data.get('users', {}))
                pending_withdraws = len([w for w in self.db.data.get('pending_withdrawals', []) if w.get('status') == 'pending'])
                
                admin_text = f"""🔐 **Admin Panel**

You are a **{admin_type}**

🏦 House Balance: **${house_balance:,.2f}**
👥 Total Users: **{total_users}**
💸 Pending Withdrawals: **{pending_withdraws}**

Choose an option:"""
                
                keyboard = [
                    [InlineKeyboardButton("📋 Admin Commands", callback_data="admin_all_commands")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(admin_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_balance_mgmt":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                balance_text = """💰 **Balance Management**

Commands to manage user balances:

• `/givebal @user amount` - Give money to user
• `/setbal @user amount` - Set user's balance
• `/adddeposit @user amount` - Credit a deposit
• `/sethousebal amount` - Set house balance

Examples:
`/givebal @john 100`
`/setbal 123456789 500`"""
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(balance_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_user_mgmt":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                total_users = len(self.db.data.get('users', {}))
                total_balance = sum(u.get('balance', 0) for u in self.db.data.get('users', {}).values())
                
                user_text = f"""👥 **User Management**

📊 **Stats:**
Total Users: **{total_users}**
Total Balances: **${total_balance:,.2f}**

Commands:
• `/allusers` - View all registered users
• `/allbalances` - View all player balances
• `/userinfo @user` - View detailed user info
• `/userid @user` - Get user's ID
• `/userhistory @user` - View user's game history"""
                
                keyboard = [
                    [InlineKeyboardButton("📋 View All Users", callback_data="admin_view_all_users")],
                    [InlineKeyboardButton("💰 View All Balances", callback_data="admin_view_all_balances")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(user_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_view_all_users":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                users = list(self.db.data.get('users', {}).values())[:20]
                if not users:
                    text = "👥 **All Users**\n\nNo users registered yet."
                else:
                    text = "👥 **All Users** (Top 20)\n\n"
                    for i, u in enumerate(users, 1):
                        username = u.get('username', f"User{u['user_id']}")
                        text += f"{i}. @{username} (ID: `{u['user_id']}`)\n"
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_user_mgmt")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_view_all_balances":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                users = sorted(self.db.data.get('users', {}).values(), key=lambda x: x.get('balance', 0), reverse=True)[:20]
                if not users:
                    text = "💰 **All Balances**\n\nNo users registered yet."
                else:
                    text = "💰 **All Balances** (Top 20)\n\n"
                    for i, u in enumerate(users, 1):
                        username = u.get('username', f"User{u['user_id']}")
                        balance = u.get('balance', 0)
                        text += f"{i}. @{username}: **${balance:,.2f}**\n"
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_user_mgmt")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_withdrawals":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                pending = [w for w in self.db.data.get('pending_withdrawals', []) if w.get('status') == 'pending']
                
                if pending:
                    text = f"💸 **Pending Withdrawals** ({len(pending)})\n\n"
                    for i, w in enumerate(pending[:10], 1):
                        username = w.get('username', f"User{w['user_id']}")
                        amount = w.get('amount', 0)
                        currency = w.get('currency', 'LTC')
                        text += f"{i}. @{username}: **${amount:.2f}** ({currency})\n"
                    if len(pending) > 10:
                        text += f"\n... and {len(pending) - 10} more"
                else:
                    text = "💸 **Pending Withdrawals**\n\nNo pending withdrawals."
                
                text += "\n\nCommands:\n• `/pendingwithdraws` - Detailed view"
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_deposits":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                deposits = self.db.get_biggest_deposits("week")[:10]
                
                if deposits:
                    text = "💳 **Recent Deposits** (This Week)\n\n"
                    for i, d in enumerate(deposits, 1):
                        username = d.get('username', f"User{d['user_id']}")
                        amount = d.get('amount', 0)
                        text += f"{i}. @{username}: **${amount:,.2f}**\n"
                else:
                    text = "💳 **Recent Deposits**\n\nNo deposits this week."
                
                text += "\n\nCommands:\n• `/pendingdeposits` - View pending deposits\n• `/biggestdeposits` - All-time biggest"
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_admin_mgmt":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                env_count = len(self.env_admin_ids)
                dyn_count = len(self.dynamic_admin_ids)
                approver_count = len(self.withdrawal_approvers)
                
                text = f"""👑 **Admin Management**

📊 **Current Admins:**
Permanent Admins: **{env_count}**
Dynamic Admins: **{dyn_count}**
Withdrawal Approvers: **{approver_count}**

Commands:
• `/addadmin user_id` - Add new admin
• `/removeadmin user_id` - Remove admin
• `/listadmins` - List all admins
• `/addapprover user_id` - Add withdrawal approver
• `/removeapprover user_id` - Remove approver
• `/listapprovers` - List all approvers"""
                
                keyboard = [
                    [InlineKeyboardButton("📋 List Admins", callback_data="admin_list_admins")],
                    [InlineKeyboardButton("📋 List Approvers", callback_data="admin_list_approvers")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_list_admins":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                text = "👑 **All Admins**\n\n"
                
                if self.env_admin_ids:
                    text += "**Permanent Admins:**\n"
                    for aid in sorted(self.env_admin_ids):
                        text += f"• `{aid}`\n"
                
                if self.dynamic_admin_ids:
                    text += "\n**Dynamic Admins:**\n"
                    for aid in sorted(self.dynamic_admin_ids):
                        text += f"• `{aid}`\n"
                
                if not self.env_admin_ids and not self.dynamic_admin_ids:
                    text += "No admins configured."
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_admin_mgmt")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_list_approvers":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                text = "💼 **Withdrawal Approvers**\n\n"
                
                if self.withdrawal_approvers:
                    for aid in sorted(self.withdrawal_approvers):
                        text += f"• `{aid}`\n"
                else:
                    text += "No approvers configured."
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_admin_mgmt")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_system":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                house_balance = self.db.get_house_balance()
                
                text = f"""🛠️ **System**

🏦 House Balance: **${house_balance:,.2f}**

Commands:
• `/backup` - Download database backup
• `/sethousebal amount` - Set house balance
• `/housebal` - View house balance
• `/saveroulette` - Save roulette stickers
• `/ltcrate` - View LTC rate
• `/setltcrate price` - Set manual LTC rate"""
                
                keyboard = [
                    [InlineKeyboardButton("💾 Create Backup", callback_data="admin_backup")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "admin_backup":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                await query.answer("Creating backup... Use /backup command for file download.", show_alert=True)
            
            elif data == "admin_all_commands":
                if not self.is_admin(user_id):
                    await query.answer("❌ Admin only.", show_alert=True)
                    return
                
                text = """📋 **All Admin Commands**

**Balance:**
• `/givebal @user amount`
• `/setbal @user amount`
• `/adddeposit @user amount`
• `/sethousebal amount`

**Users:**
• `/allusers` • `/allbalances`
• `/userinfo @user` • `/userid @user`
• `/userhistory @user`

**Admins:**
• `/addadmin ID` • `/removeadmin ID`
• `/listadmins`

**Approvers:**
• `/addapprover ID` • `/removeapprover ID`
• `/listapprovers`

**Transactions:**
• `/pendingdeposits`
• `/pendingwithdraws`
• `/biggestdeposits`
• `/walletbal`

**System:**
• `/backup` • `/housebal`
• `/ltcrate` • `/setltcrate price`
• `/saveroulette`"""
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="back_to_admin_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "more_stats":
                user_data = self.db.get_user(user_id)
                username = user_data.get('username', f"User{user_id}")
                balance = user_data.get('balance', 0)
                games_played = user_data.get('games_played', 0)
                games_won = user_data.get('games_won', 0)
                win_rate = (games_won / games_played * 100) if games_played > 0 else 0
                total_wagered = user_data.get('total_wagered', 0)
                total_pnl = user_data.get('total_pnl', 0)
                total_won = total_wagered + total_pnl if total_pnl > 0 else total_wagered
                
                current_level = get_user_level(total_wagered, user_id, self.db)
                
                stats_text = f"""ℹ️ Stats of {username}

💰 Balance: ${balance:.2f}

Level: {current_level['emoji']} {current_level['name']}
Games Played: {games_played}
Wins: {games_won} ({win_rate:.2f}%)
Total Wagered: ${total_wagered:,.2f}
Total Won: ${total_won:,.2f}"""
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_more_content")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "more_history":
                await self._show_history_page(query.message, user_id, 0, edit_message=True, show_back=True)
            
            elif data == "more_leaderboard":
                await self.show_leaderboard_wagered(update, back_to="menu_more_content")
            
            elif data == "more_raffle":
                raffle_text = "🎟️ **Raffle**\n\nThere are no active raffles right now. Come back later!"
                keyboard = [
                    [InlineKeyboardButton("ℹ️ Rules", callback_data="raffle_rules"),
                     InlineKeyboardButton("ℹ️ Event History", callback_data="raffle_history")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="menu_more_content")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(raffle_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "raffle_rules":
                rules_text = """🎟️ **Raffle Rules**

1. Raffles are held periodically with exciting prizes
2. Each ticket costs a set amount to enter
3. Winners are selected randomly
4. Prizes are credited directly to your balance
5. Stay tuned for announcements!"""
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="more_raffle")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(rules_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data == "raffle_history":
                history_text = "🎟️ **Event History**\n\nNo past raffles yet. Check back after the first raffle ends!"
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="more_raffle")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(history_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            elif data.startswith("game_info_"):
                game_name = data.replace("game_info_", "")
                game_usage = {
                    "dice": "Usage: `/dice <amount|all>`",
                    "slots": "Usage: `/slots <amount|all>`",
                    "predict": "🔮 **Dice Prediction**\n\nPredict the dice roll and win **6x** your wager!\n\n**Usage:** `/predict <amount|all>`",
                    "roulette": "Usage: `/roulette <amount|all>`",
                    "coinflip": "Usage: `/flip <amount|all>`",
                    "darts": "Usage: `/darts <amount|all>`",
                    "basketball": "Usage: `/basketball <amount|all>`",
                    "soccer": "Usage: `/soccer <amount|all>`",
                    "bowling": "Usage: `/bowling <amount|all>`",
                    "blackjack": "Usage: `/blackjack <amount|all>`",
                    "mines": "Usage: `/mines <amount|all>`",
                    "baccarat": "🃏 **Baccarat**\n\nBet on Player, Banker, or Tie!\n\n**Usage:** `/baccarat <amount|all>`",
                    "keno": "🎱 **Keno**\n\nPick up to 10 numbers and match the draw!\n\n**Usage:** `/keno <amount|all>`",
                    "limbo": "🚀 **Limbo**\n\nSet a target multiplier and hope the roll beats it!\n\n**Usage:** `/limbo <amount|all>`",
                    "hilo": "📈 **Hi-Lo**\n\nPredict if the next card is higher or lower!\n\n**Usage:** `/hilo <amount|all>`",
                    "connect4": "🔴 **Connect 4**\n\nChallenge another player to Connect 4!\n\n**Usage:** `/connect @user <amount>`"
                }
                
                usage_text = game_usage.get(game_name, "Game not found.")
                
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="menu_play")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(usage_text, reply_markup=reply_markup, parse_mode="Markdown")

            # Deposit/Withdrawal buttons
            elif data == "deposit_mock":
                if query.message.chat.type != "private" and not self.is_admin(user_id):
                    await query.answer("❌ Use deposit in DMs only.", show_alert=True)
                    return
                # Show currency selection menu
                await query.answer()
                user_data = self.db.get_user(user_id)
                
                keyboard = []
                for code, info in SUPPORTED_DEPOSIT_CRYPTOS.items():
                    btn = InlineKeyboardButton(info['name'], callback_data=f"deposit_crypto_{code}")
                    keyboard.append([btn])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            
            elif data == "withdraw_mock":
                if query.message.chat.type != "private" and not self.is_admin(user_id):
                    await query.answer("❌ Use withdraw in DMs only.", show_alert=True)
                    return
                user_data = self.db.get_user(user_id)
                min_possible = min(info.get('min_withdraw', 1.00) for info in SUPPORTED_WITHDRAWAL_CRYPTOS.values())
                if user_data['balance'] < min_possible:
                    await query.edit_message_text(f"❌ Minimum withdrawal is ${min_possible:.2f}\n\nYour balance: **${user_data['balance']:.2f}**", parse_mode="Markdown")
                else:
                    keyboard = []
                    for code, info in SUPPORTED_WITHDRAWAL_CRYPTOS.items():
                        btn = InlineKeyboardButton(info['name'], callback_data=f"withdraw_method_{code.lower()}")
                        keyboard.append([btn])
                    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
            
            elif data.startswith("withdraw_method_"):
                currency = data.replace("withdraw_method_", "").upper()
                crypto_info = SUPPORTED_WITHDRAWAL_CRYPTOS.get(currency)
                if not crypto_info:
                    await query.answer("❌ Invalid currency.", show_alert=True)
                    return
                
                user_data = self.db.get_user(user_id)
                balance = user_data['balance']
                fee_percent = crypto_info.get('fee_percent', 0.02) * 100
                min_withdraw = crypto_info.get('min_withdraw', 1.00)
                
                context.user_data['pending_withdraw_method'] = currency.lower()
                
                keyboard = [
                    [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_back_to_currency")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"Your balance: **${balance:.2f}**\nFee: **{fee_percent:.1f}%**\nMinimum: **${min_withdraw:.2f}**\n\nEnter the amount you want to withdraw:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            
            elif data == "withdraw_cancel":
                await query.edit_message_text("❌ Withdrawal cancelled.")
            
            elif data == "withdraw_cancel_flow":
                # Clear any pending withdrawal state
                context.user_data.pop('pending_withdraw_method', None)
                context.user_data.pop('pending_withdraw_amount', None)
                await query.edit_message_text("Withdraw cancelled.")
            
            elif data == "withdraw_back_to_currency":
                # Clear pending state and go back to currency selection
                context.user_data.pop('pending_withdraw_method', None)
                context.user_data.pop('pending_withdraw_amount', None)
                
                user_data = self.db.get_user(user_id)
                keyboard = []
                for code, info in SUPPORTED_WITHDRAWAL_CRYPTOS.items():
                    btn = InlineKeyboardButton(info['name'], callback_data=f"withdraw_method_{code.lower()}")
                    keyboard.append([btn])
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"Your balance: **${user_data['balance']:.2f}**\n\nSelect a cryptocurrency:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            
            elif data == "withdraw_back_to_amount":
                # Clear amount and go back to entering amount
                context.user_data.pop('pending_withdraw_amount', None)
                currency = context.user_data.get('pending_withdraw_method', 'ltc').upper()
                crypto_info = SUPPORTED_WITHDRAWAL_CRYPTOS.get(currency, {'name': currency})
                fee_percent = crypto_info.get('fee_percent', 0.02) * 100
                min_withdraw = crypto_info.get('min_withdraw', 1.00)
                
                user_data = self.db.get_user(user_id)
                balance = user_data['balance']
                
                keyboard = [
                    [InlineKeyboardButton("⬅️ Back", callback_data="withdraw_back_to_currency")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"Your balance: **${balance:.2f}**\nFee: **{fee_percent:.1f}%**\nMinimum: **${min_withdraw:.2f}**\n\nEnter the amount you want to withdraw:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            
            elif data.startswith("withdraw_approve_"):
                parts = data.split('_')
                withdraw_id = int(parts[2])
                target_user_id = int(parts[3])
                amount = float(parts[4])
                currency = parts[5] if len(parts) > 5 else 'LTC'
                
                pending = self.db.data.get('pending_withdrawals', [])
                if withdraw_id < len(pending) and pending[withdraw_id]['status'] == 'pending':
                    withdrawal = pending[withdraw_id]
                    username = withdrawal.get('username', f'User{target_user_id}')
                    wallet_address = withdrawal.get('wallet_address') or withdrawal.get('ltc_address', '')
                    currency = withdrawal.get('currency', currency)
                    crypto_info = SUPPORTED_WITHDRAWAL_CRYPTOS.get(currency, {'name': currency})
                    
                    await query.edit_message_text(
                        f"⏳ **Sending {currency} via Plisio...**\n\nUser: @{username} (ID: `{target_user_id}`)\nAmount: **${amount:.2f}**",
                        parse_mode="Markdown"
                    )
                    
                    # Send crypto via Plisio API
                    result = await self.send_crypto_withdrawal(wallet_address, amount, currency)
                    
                    if result['success']:
                        withdrawal['status'] = 'processed'
                        withdrawal['tx_id'] = result.get('tx_id')
                        withdrawal['tx_url'] = result.get('tx_url')
                        self.db.add_transaction(target_user_id, "withdrawal", -amount, f"{currency} Withdrawal to {wallet_address[:20]}...")
                        
                        tx_id = result.get('tx_id', '')
                        tx_url = result.get('tx_url', '')
                        if tx_id:
                            if 'processed_withdrawal_txids' not in self.db.data:
                                self.db.data['processed_withdrawal_txids'] = []
                            self.db.data['processed_withdrawal_txids'].append(tx_id)
                            if len(self.db.data['processed_withdrawal_txids']) > 1000:
                                self.db.data['processed_withdrawal_txids'] = self.db.data['processed_withdrawal_txids'][-1000:]
                        self.db.save_data()
                        
                        tx_info = f"\nTX: `{tx_id}`" if tx_id else ""
                        explorer_link = f"\n[View on Blockchain]({tx_url})" if tx_url else ""
                        await query.edit_message_text(
                            f"✅ **Withdrawal Sent!**\n\nUser: @{username} (ID: `{target_user_id}`)\nAmount: **${amount:.2f}**\nCurrency: **{currency}**\nTo: `{wallet_address}`{tx_info}{explorer_link}\n\nApproved by @{update.effective_user.username or update.effective_user.first_name}",
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                        
                        # Notify the user
                        try:
                            await self.app.bot.send_message(
                                chat_id=target_user_id,
                                text=f"✅ **Withdrawal Sent!**\n\n**${amount:.2f}** in {crypto_info['name']} has been sent to your address.{explorer_link}\n\nPlease allow a few minutes for blockchain confirmation.",
                                parse_mode="Markdown",
                                disable_web_page_preview=True
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify user {target_user_id}: {e}")
                    else:
                        await query.edit_message_text(
                            f"❌ **Withdrawal Failed**\n\nUser: @{username} (ID: `{target_user_id}`)\nAmount: **${amount:.2f}**\nError: {result.get('error', 'Unknown')}\n\nUser balance was already deducted. Use /givebal to refund if needed.",
                            parse_mode="Markdown"
                        )
                else:
                    await query.answer("❌ This withdrawal was already processed.", show_alert=True)
            
            elif data.startswith("withdraw_deny_"):
                parts = data.split('_')
                withdraw_id = int(parts[2])
                target_user_id = int(parts[3])
                amount = float(parts[4])
                
                pending = self.db.data.get('pending_withdrawals', [])
                if withdraw_id < len(pending) and pending[withdraw_id]['status'] == 'pending':
                    # Refund the user silently
                    target_user_data = self.db.get_user(target_user_id)
                    target_user_data['balance'] += amount
                    self.db.update_user(target_user_id, target_user_data)
                    self.db.save_data()
                    
                    # Just show a toast, keep buttons visible for re-approval if needed
                    await query.answer(f"Refunded ${amount:.2f} to user. Player not notified.", show_alert=True)
                else:
                    await query.answer("❌ This withdrawal was already processed.", show_alert=True)
            
            elif data.startswith("copy_addr_"):
                address = data.replace("copy_addr_", "")
                await query.answer("Address copied! Tap the message to copy.", show_alert=True)
                await self.app.bot.send_message(
                    chat_id=user_id,
                    text=f"📋 **Your Deposit Address:**\n\n`{address}`\n\n_(Tap above to copy)_",
                    parse_mode="Markdown"
                )

            elif data == "transactions_history":
                user_transactions = self.db.data['transactions'].get(str(user_id), [])[-10:] # Last 10
                
                if not user_transactions:
                    await query.edit_message_text("📜 No transaction history found.")
                    return
                
                history_text = "📜 **Last 10 Transactions**\n\n"
                for tx in reversed(user_transactions):
                    time_str = datetime.fromisoformat(tx['timestamp']).strftime("%m/%d %H:%M")
                    sign = "+" if tx['amount'] >= 0 else ""
                    history_text += f"*{time_str}* | `{sign}{tx['amount']:.2f}`: {tx['description']}\n"
                
                await query.edit_message_text(history_text, parse_mode="Markdown")

            # Handle decline of PvP (general)
            elif data.startswith("decline_"):
                challenge_id = data.split('_', 1)[1]
                if challenge_id in self.pending_pvp and self.pending_pvp[challenge_id]['challenger'] == user_id:
                     await query.edit_message_text("✅ Challenge canceled.")
                     del self.pending_pvp[challenge_id]
                     self.db.data['pending_pvp'] = self.pending_pvp
                     self.db.save_data()
                else:
                    await query.answer("❌ Only the challenger can cancel this game.", show_alert=True)
            
            # Blackjack button handlers
            elif data.startswith("bj_"):
                parts = data.split('_')
                game_user_id = int(parts[1])
                action = parts[2]
                
                # Verify this is the correct user's game
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                # Handle Play Again separately (session already deleted)
                if action == "playagain":
                    wager = float(parts[3])
                    user_data = self.db.get_user(user_id)
                    
                    # Check if user has another active game
                    if self.user_has_active_game(user_id):
                        await query.answer("❌ You already have an active game!", show_alert=True)
                        return
                    
                    if user_data['balance'] < wager:
                        await query.answer(f"❌ Insufficient balance! You have ${user_data['balance']:.2f}", show_alert=True)
                        return
                    
                    # Remove the Play Again button from the old message
                    try:
                        old_text = query.message.text
                        await query.edit_message_text(old_text, parse_mode="Markdown")
                    except:
                        pass
                    
                    # Deduct wager
                    user_data['balance'] -= wager
                    self.db.update_user(user_id, user_data)
                    
                    # Create new game
                    new_game = BlackjackGame(bet_amount=wager)
                    new_game.start_game()
                    self.blackjack_sessions[user_id] = new_game
                    
                    # Start 30-second timeout for the game
                    chat_id = query.message.chat_id
                    game_key = f"blackjack_{user_id}"
                    self.start_game_timeout(game_key, "blackjack", user_id, chat_id, wager, 
                                            bot=context.bot)
                    
                    # Send a NEW message for the new game (not editing)
                    await self._display_blackjack_state_new_message(update, context, user_id)
                    return
                
                if game_user_id not in self.blackjack_sessions:
                    await query.edit_message_text("❌ Game session expired. Start a new game with /blackjack")
                    return
                
                game = self.blackjack_sessions[game_user_id]
                
                # Execute the action
                if action == "hit":
                    game.hit()
                elif action == "stand":
                    game.stand()
                elif action == "double":
                    # Check if user has enough balance for double down
                    user_data = self.db.get_user(user_id)
                    current_hand = game.player_hands[game.current_hand_index]
                    additional_bet = current_hand['bet']
                    
                    if user_data['balance'] < additional_bet:
                        await query.answer("❌ Insufficient balance to double down!", show_alert=True)
                        return
                    
                    # Deduct additional bet
                    user_data['balance'] -= additional_bet
                    self.db.update_user(user_id, user_data)
                    
                    game.double_down()
                elif action == "split":
                    # Check if user has enough balance for split
                    user_data = self.db.get_user(user_id)
                    current_hand = game.player_hands[game.current_hand_index]
                    additional_bet = current_hand['bet']
                    
                    if user_data['balance'] < additional_bet:
                        await query.answer("❌ Insufficient balance to split!", show_alert=True)
                        return
                    
                    # Deduct additional bet
                    user_data['balance'] -= additional_bet
                    self.db.update_user(user_id, user_data)
                    
                    game.split()
                    # After split, cancel timeout if game ended (e.g., split aces both get 21)
                    game_state_after_split = game.get_game_state()
                    if game_state_after_split['game_over']:
                        game_key = f"blackjack_{user_id}"
                        self.cancel_game_timeout(game_key)
                elif action == "insurance":
                    # Check if user has enough balance for insurance
                    user_data = self.db.get_user(user_id)
                    insurance_cost = game.initial_bet / 2
                    
                    if user_data['balance'] < insurance_cost:
                        await query.answer("❌ Insufficient balance for insurance!", show_alert=True)
                        return
                    
                    # Deduct insurance cost
                    user_data['balance'] -= insurance_cost
                    self.db.update_user(user_id, user_data)
                    
                    game.take_insurance()
                
                # Reset or cancel timeout after each action
                if game_user_id in self.blackjack_sessions:
                    game_state = game.get_game_state()
                    game_key = f"blackjack_{user_id}"
                    if not game_state['game_over']:
                        # Game still active - reset the timeout
                        chat_id = query.message.chat_id
                        wager = sum(h['bet'] for h in game.player_hands)
                        self.reset_game_timeout(game_key, "blackjack", user_id, chat_id, wager,
                                                bot=context.bot)
                    else:
                        # Game ended - cancel the timeout immediately
                        self.cancel_game_timeout(game_key)
                
                # Update the display with new game state
                await self._display_blackjack_state(update, context, user_id)
            
            # Mines Game Callbacks
            elif data.startswith("mines_start_"):
                try:
                    # mines_start_<wager>_<num_mines>
                    parts = data.split('_')
                    wager = float(parts[2])
                    num_mines = int(parts[3])
                    
                    # Remove from pending selection
                    if user_id in self.pending_opponent_selection:
                        self.pending_opponent_selection.discard(user_id)
                    
                    # Check balance again
                    user_data = self.db.get_user(user_id)
                    if wager > user_data['balance']:
                        await query.edit_message_text(f"❌ Insufficient balance. You have ${user_data['balance']:.2f}")
                        return
                    
                    # Deduct wager
                    user_data['balance'] -= wager
                    self.db.update_user(user_id, user_data)
                    
                    # Create new game
                    game = MinesGame(user_id=user_id, wager=wager, num_mines=num_mines)
                    self.mines_sessions[user_id] = game
                    
                    # Start 30-second timeout for the game
                    chat_id = query.message.chat_id
                    game_key = f"mines_{user_id}"
                    self.start_game_timeout(game_key, "mines", user_id, chat_id, wager, 
                                            bot=context.bot)
                    
                    # Display game grid
                    await self._display_mines_state(update, context, user_id, is_new=True)
                except Exception as mines_error:
                    logger.error(f"Mines start error: {mines_error}")
                    await query.edit_message_text(f"❌ Error starting mines: {str(mines_error)[:100]}")
            
            elif data.startswith("mines_reveal_"):
                # mines_reveal_<user_id>_<position>
                parts = data.split('_')
                game_user_id = int(parts[2])
                position = int(parts[3])
                
                # Verify this is the correct user
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if game_user_id not in self.mines_sessions:
                    await query.edit_message_text("❌ Game session expired. Start a new game with /mines")
                    return
                
                game = self.mines_sessions[game_user_id]
                
                # Reveal the tile
                is_safe, game_over, multiplier, already_revealed = game.reveal_tile(position)
                
                # If already revealed, just acknowledge and do nothing
                if already_revealed:
                    await query.answer()
                    return
                
                # Reset timeout if game is still active
                if not game_over and user_id in self.mines_sessions:
                    chat_id = query.message.chat_id
                    game_key = f"mines_{user_id}"
                    self.reset_game_timeout(game_key, "mines", user_id, chat_id, game.wager,
                                            bot=context.bot)
                
                # Update display
                await self._display_mines_state(update, context, user_id)
            
            elif data.startswith("mines_cashout_"):
                # mines_cashout_<user_id>
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                # Verify this is the correct user
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if game_user_id not in self.mines_sessions:
                    await query.edit_message_text("❌ Game session expired. Start a new game with /mines")
                    return
                
                game = self.mines_sessions[game_user_id]
                
                # Cash out
                game.cash_out()
                
                # Update display
                await self._display_mines_state(update, context, user_id)
            
            elif data.startswith("mines_again_"):
                # mines_again_<user_id>_<wager>_<num_mines> - Play again with same settings
                parts = data.split('_')
                game_user_id = int(parts[2])
                wager = float(parts[3])
                num_mines = int(parts[4])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                # Check if user has enough balance
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < wager:
                    await query.answer(f"❌ Insufficient balance! Need ${wager:.2f}", show_alert=True)
                    return
                
                # Deduct wager
                user_data['balance'] -= wager
                self.db.update_user(user_id, user_data)
                
                # Start new game with same settings
                self.mines_sessions[user_id] = MinesGame(user_id=user_id, wager=wager, num_mines=num_mines)
                
                await query.answer("🎮 New game started!")
                await self._display_mines_state(update, context, user_id, is_new=True)
            
            elif data.startswith("mines_change_"):
                # mines_change_<user_id>_<wager> - Pick new mines count
                parts = data.split('_')
                game_user_id = int(parts[2])
                wager = float(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                # Check if user has enough balance
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < wager:
                    await query.answer(f"❌ Insufficient balance! Need ${wager:.2f}", show_alert=True)
                    return
                
                # Show mines selection keyboard (same format as /mines command)
                keyboard = [
                    [InlineKeyboardButton("3 Mines (Low Risk)", callback_data=f"mines_start_{wager:.2f}_3")],
                    [InlineKeyboardButton("5 Mines (Medium)", callback_data=f"mines_start_{wager:.2f}_5")],
                    [InlineKeyboardButton("10 Mines (High Risk)", callback_data=f"mines_start_{wager:.2f}_10")],
                    [InlineKeyboardButton("15 Mines (Very High)", callback_data=f"mines_start_{wager:.2f}_15")],
                    [InlineKeyboardButton("20 Mines (Extreme)", callback_data=f"mines_start_{wager:.2f}_20")],
                    [InlineKeyboardButton("24 Mines (Max Risk)", callback_data=f"mines_start_{wager:.2f}_24")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    f"💣 **Mines** - Wager: ${wager:.2f}\n\n"
                    f"**Select difficulty (number of mines):**\n\n"
                    f"More mines = Higher risk = Bigger multipliers!\n"
                    f"• 3 mines: Up to 2.23x\n"
                    f"• 5 mines: Up to 7.42x\n"
                    f"• 10 mines: Up to 113.85x\n"
                    f"• 15 mines: Up to 9,176x\n"
                    f"• 24 mines: Up to 24,750x",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            
            elif data == "mines_noop":
                # Just acknowledge the click but do nothing (for revealed/disabled tiles)
                await query.answer()
            
            # Baccarat callbacks
            elif data.startswith("bacc_"):
                parts = data.split('_')
                game_user_id = int(parts[1])
                wager = float(parts[2])
                bet_type = parts[3]
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                await self._play_baccarat(update, context, user_id, wager, bet_type)
            
            # Keno callbacks
            elif data.startswith("keno_pick_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                number = int(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                success, msg = game.pick_number(number)
                
                # Reset timeout since player is still active
                if not game.game_over and user_id in self.keno_sessions:
                    chat_id = query.message.chat_id
                    game_key = f"keno_{user_id}"
                    self.reset_game_timeout(game_key, "keno", user_id, chat_id, game.wager,
                                            bot=context.bot)
                
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_draw_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                game.start_draw()
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_clear_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                game.picked_numbers.clear()
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_again_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                wager = float(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < wager:
                    await query.answer(f"❌ Insufficient balance! Need ${wager:.2f}", show_alert=True)
                    return
                
                user_data['balance'] -= wager
                self.db.update_user(user_id, user_data)
                
                self.keno_sessions[user_id] = KenoGame(user_id, wager)
                await query.answer("🎮 New game started!")
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_select_rounds_"):
                parts = data.split('_')
                game_user_id = int(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                game.selecting_rounds = True
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_back_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                game.selecting_rounds = False
                await self._display_keno_state(update, context, user_id)
            
            elif data.startswith("keno_rounds_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                rounds = int(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                user_data = self.db.get_user(user_id)
                
                if rounds == -1:
                    await query.answer("Starting infinite auto-play!")
                else:
                    total_cost = game.wager * (rounds - 1)
                    if user_data['balance'] < total_cost:
                        await query.answer(f"❌ Need ${total_cost + game.wager:.2f} for {rounds} draws", show_alert=True)
                        return
                    await query.answer(f"Starting {rounds} draws!")
                
                game.set_rounds(rounds)
                await self._run_keno_draw(update, context, user_id)
            
            elif data.startswith("keno_next_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                user_data = self.db.get_user(user_id)
                
                if user_data['balance'] < game.wager:
                    game.game_over = True
                    await query.answer("❌ Insufficient balance! Stopping auto-play.", show_alert=True)
                    await self._display_keno_state(update, context, user_id)
                    return
                
                await self._run_keno_draw(update, context, user_id)
            
            elif data.startswith("keno_stop_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.keno_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.keno_sessions[user_id]
                game.game_over = True
                await query.answer("Stopping auto-play!")
                await self._display_keno_state(update, context, user_id)
            
            elif data == "keno_noop":
                await query.answer()
            
            # Limbo callbacks
            elif data.startswith("limbo_again_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                wager = float(parts[3])
                target_multiplier = float(parts[4])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < wager:
                    await query.answer(f"❌ Insufficient balance! Need ${wager:.2f}", show_alert=True)
                    return
                
                user_data['balance'] -= wager
                self.db.update_user(user_id, {'balance': user_data['balance']})
                
                game = LimboGame(user_id, wager, target_multiplier)
                self.limbo_sessions[user_id] = game
                result = game.play()
                
                win_prob = result['win_probability'] * 100
                
                if result['won']:
                    user_data['balance'] += result['payout']
                    user_data['total_wagered'] += wager
                    user_data['games_played'] += 1
                    user_data['games_won'] += 1
                    user_data['total_pnl'] += result['profit']
                    user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
                    self.db.update_user(user_id, user_data)
                    self.db.update_house_balance(-result['profit'])
                    result_emoji = "🟢"
                    result_text = f"@{user_data.get('username', 'Player')} won ${result['payout']:.2f} ({target_multiplier:.2f}x)"
                else:
                    user_data['total_wagered'] += wager
                    user_data['games_played'] += 1
                    user_data['total_pnl'] -= wager
                    user_data['wagered_since_last_withdrawal'] = user_data.get('wagered_since_last_withdrawal', 0) + wager
                    self.db.update_user(user_id, user_data)
                    self.db.update_house_balance(wager)
                    result_emoji = "🔴"
                    result_text = f"@{user_data.get('username', 'Player')} lost ${wager:.2f}"
                
                self.db.record_game({
                    'type': 'limbo',
                    'player_id': user_id,
                    'username': user_data.get('username', 'Unknown'),
                    'wager': wager,
                    'target_multiplier': target_multiplier,
                    'result_multiplier': result['result_multiplier'],
                    'won': result['won'],
                    'payout': result['payout'],
                    'result': 'win' if result['won'] else 'loss',
                    'balance_after': user_data['balance']
                })
                
                del self.limbo_sessions[user_id]
                
                keyboard = [[InlineKeyboardButton("🔄 Play Again", callback_data=f"limbo_again_{user_id}_{wager}_{target_multiplier}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"🚀 **Limbo**\n\n"
                message += f"**Target:** {target_multiplier:.2f}x ({win_prob:.1f}% chance)\n"
                message += f"**Result:** {result['result_multiplier']:.2f}x {result_emoji}\n"
                message += f"**Bet:** ${wager:.2f}\n\n"
                message += result_text
                
                await query.edit_message_text(message, reply_markup=reply_markup, parse_mode="Markdown")
            
            # Hi-Lo callbacks
            elif data.startswith("hilo_higher_") or data.startswith("hilo_lower_") or data.startswith("hilo_tie_"):
                parts = data.split('_')
                action = parts[1]
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.hilo_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.hilo_sessions[user_id]
                game.make_prediction(action)
                
                # Reset timeout if game is still active
                if not game.game_over and user_id in self.hilo_sessions:
                    chat_id = query.message.chat_id
                    game_key = f"hilo_{user_id}"
                    self.reset_game_timeout(game_key, "hilo", user_id, chat_id, game.initial_wager,
                                            bot=context.bot)
                
                await self._display_hilo_state(update, context, user_id)
            
            elif data.startswith("hilo_skip_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.hilo_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.hilo_sessions[user_id]
                game.skip_card()
                
                # Reset timeout since player is still active
                if not game.game_over and user_id in self.hilo_sessions:
                    chat_id = query.message.chat_id
                    game_key = f"hilo_{user_id}"
                    self.reset_game_timeout(game_key, "hilo", user_id, chat_id, game.initial_wager,
                                            bot=context.bot)
                await query.answer("⏭️ Card skipped!")
                await self._display_hilo_state(update, context, user_id)
            
            elif data.startswith("hilo_cashout_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                if user_id not in self.hilo_sessions:
                    await query.answer("❌ No active game!", show_alert=True)
                    return
                
                game = self.hilo_sessions[user_id]
                result = game.cash_out()
                if 'error' in result:
                    await query.answer(f"❌ {result['error']}", show_alert=True)
                    return
                
                await query.answer("💰 Cashing out!")
                await self._display_hilo_state(update, context, user_id)
            
            elif data.startswith("hilo_again_"):
                parts = data.split('_')
                game_user_id = int(parts[2])
                wager = float(parts[3])
                
                if user_id != game_user_id:
                    await query.answer("❌ This is not your game!", show_alert=True)
                    return
                
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < wager:
                    await query.answer(f"❌ Insufficient balance! Need ${wager:.2f}", show_alert=True)
                    return
                
                user_data['balance'] -= wager
                self.db.update_user(user_id, {'balance': user_data['balance']})
                
                game = HiLoGame(user_id, wager)
                self.hilo_sessions[user_id] = game
                
                # Start 30-second timeout for the game
                chat_id = query.message.chat_id
                game_key = f"hilo_{user_id}"
                self.start_game_timeout(game_key, "hilo", user_id, chat_id, wager, 
                                        bot=context.bot)
                
                await query.answer("🎮 New game started!")
                await self._display_hilo_state(update, context, user_id)
            
            # Connect 4 callbacks
            elif data.startswith("connect4_accept_"):
                game_id = data.replace("connect4_accept_", "")
                await self._accept_connect4_challenge(update, context, game_id)
            
            elif data.startswith("connect4_roll_"):
                parts = data.split('_')
                player_num = int(parts[-1])
                game_id = '_'.join(parts[2:-1])
                await self._handle_connect4_dice_roll(update, context, game_id, player_num)
            
            elif data.startswith("connect4_drop_"):
                prefix_len = len("connect4_drop_")
                rest = data[prefix_len:]
                last_underscore = rest.rfind('_')
                game_id = rest[:last_underscore]
                col = int(rest[last_underscore + 1:])
                
                if game_id not in self.connect4_sessions:
                    await query.answer("Game not found!", show_alert=True)
                    return
                
                game = self.connect4_sessions[game_id]
                
                if user_id != game.get_current_player_id():
                    await query.answer("Not your turn!", show_alert=True)
                    return
                
                result = game.make_move(user_id, col)
                
                if 'error' in result:
                    await query.answer(result['error'], show_alert=True)
                    return
                
                # Reset timeout for the next player if game is still active
                if not game.game_over and game_id in self.connect4_sessions:
                    chat_id = query.message.chat_id
                    game_key = f"connect4_{game_id}"
                    next_player_id = game.get_current_player_id()
                    opponent_player_id = game.player1_id if next_player_id == game.player2_id else game.player2_id
                    self.reset_game_timeout(game_key, "connect4", next_player_id, chat_id, game.wager,
                                            bot=context.bot, game_id=game_id, opponent_id=opponent_player_id,
                                            is_pvp=True)
                
                await query.answer()
                await self._display_connect4_state(update, context, game_id, is_new=False)
            
            elif data == "connect4_noop":
                await query.answer("Column is full!", show_alert=True)
            
            else:
                await query.edit_message_text("Something went wrong or this button is for a different command!")
            
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text="An unexpected error occurred. Please try the command again.")


    def run(self):
        """Start the bot."""
        # Schedule task to check for expired challenges every 5 seconds
        job_queue = self.app.job_queue
        job_queue.run_repeating(self.check_expired_challenges, interval=5, first=5)
        
        self.app.run_polling(poll_interval=1.0)


async def main():
    print("DEBUG: main() function started")
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    USE_POLLING = os.getenv("USE_POLLING", "true").lower() == "true"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://casino.vps.webdock.cloud")
    
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        raise ValueError("TELEGRAM_BOT_TOKEN is required to run the bot")
    
    print(f"DEBUG: BOT_TOKEN={'SET' if BOT_TOKEN else 'NOT SET'}, USE_POLLING={USE_POLLING}")
    logger.info("Starting Gran Tesero Casino Bot...")
    logger.info(f"USE_POLLING={USE_POLLING}, WEBHOOK_URL={WEBHOOK_URL}")
    
    bot = GranTeseroCasinoBot(token=BOT_TOKEN)
    
    await bot.app.initialize()
    await bot.app.start()
    
    # Set up the bot menu commands (hamburger menu / 3 bars panel)
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Open main menu"),
        BotCommand("balance", "Check your balance"),
        BotCommand("deposit", "Deposit funds"),
        BotCommand("withdraw", "Withdraw funds"),
        BotCommand("bonus", "View bonuses"),
        BotCommand("dice", "Play Dice"),
        BotCommand("slots", "Play Slots"),
        BotCommand("blackjack", "Play Blackjack"),
        BotCommand("roulette", "Play Roulette"),
        BotCommand("mines", "Play Mines"),
        BotCommand("flip", "Play Coinflip"),
        BotCommand("baccarat", "Play Baccarat"),
        BotCommand("keno", "Play Keno"),
        BotCommand("limbo", "Play Limbo"),
        BotCommand("hilo", "Play Hi-Lo"),
        BotCommand("connect", "Play Connect 4"),
        BotCommand("levels", "View level progress"),
        BotCommand("stats", "View your statistics"),
        BotCommand("history", "View game history"),
        BotCommand("referral", "View referral program"),
        BotCommand("admin", "Admin panel (admins only)"),
    ]
    await bot.app.bot.set_my_commands(commands)
    logger.info("Bot menu commands set successfully")
    
    if USE_POLLING:
        logger.info("Polling mode active - using long-polling for updates (webhook server disabled)")
        job_queue = bot.app.job_queue
        job_queue.run_repeating(bot.check_expired_challenges, interval=5, first=5)
        
        await bot.app.updater.start_polling(poll_interval=1.0)
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await bot.app.updater.stop()
            await bot.app.stop()
            await bot.app.shutdown()
    else:
        from webhook_server import WebhookServer
        webhook_server = WebhookServer(bot, port=5000)
        await webhook_server.start()
        logger.info("Webhook server started on port 5000")
        
        webhook_full_url = f"{WEBHOOK_URL.rstrip('/')}/webhook/telegram"
        logger.info(f"Setting up Telegram webhook at: {webhook_full_url}")
        await bot.app.bot.set_webhook(url=webhook_full_url)
        logger.info("Webhook mode active - bot will receive updates via HTTP")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await bot.app.bot.delete_webhook()
            await bot.app.stop()
            await bot.app.shutdown()

if __name__ == '__main__':
    print("DEBUG: Script starting...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"DEBUG: Fatal error: {e}")
        import traceback
        traceback.print_exc()
