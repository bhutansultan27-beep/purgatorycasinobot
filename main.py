import os
import asyncio
import random
import hashlib
import json
import logging
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Import Blackjack game logic
from blackjack import BlackjackGame

# External dependencies (assuming they are installed via pip install python-telegram-bot)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    {"name": "Top Tier", "emoji": "🌟", "levels": [
        {"id": "top_tier", "name": "Top Tier", "threshold": 3000000, "bonus": 1750},
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

def get_user_level(total_wagered: float) -> dict:
    """Returns the current level data based on total wagered amount."""
    current_level = LEVELS[0]
    for level in LEVELS:
        if total_wagered >= level["threshold"]:
            current_level = level
        else:
            break
    return current_level

def get_next_level(total_wagered: float) -> dict:
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

# --- 1. Database Manager (Simulated File Storage) ---
# This class handles loading and saving the bot's state to a local JSON file.
class DatabaseManager:
    def __init__(self, file_path: str = 'casino_data.json'):
        self.file_path = file_path
        self.data: Dict[str, Any] = self.load_data()
        
    def load_data(self) -> Dict[str, Any]:
        """Loads data from the JSON file or returns a default structure."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading database file: {e}. Starting with default data.")
        
        # Default starting data structure
        return {
            "users": {},
            "games": [],
            "transactions": {},
            "pending_pvp": {},
            "house_balance": 10000.00, # Initial house seed money
            "dynamic_admins": [],  # Additional admins added via commands
            "stickers": {
                "roulette": {}  # Will store stickers for roulette numbers: "00", "0", "1", "2", ... "36"
            }
        }

    def save_data(self):
        """Saves the current state back to the JSON file."""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
        except IOError as e:
            logger.error(f"Error saving database file: {e}")

    def get_user(self, user_id: int) -> Dict[str, Any]:
        """Retrieves user data, initializing a new user if necessary."""
        user_id_str = str(user_id)
        if user_id_str not in self.data['users']:
            # New player default: $0 starting balance
            new_user = {
                "user_id": user_id,
                "username": f"User{user_id}",
                "balance": 0.0,
                "playthrough_required": 0.0,
                "last_bonus_claim": None,
                "total_wagered": 0.0,
                "total_pnl": 0.0,
                "games_played": 0,
                "games_won": 0,
                "win_streak": 0,
                "best_win_streak": 0,
                "wagered_since_last_withdrawal": 0.0,
                "first_wager_date": None,
                "join_date": datetime.now().isoformat(),
                "last_game_date": None,
                "claimed_level_bonuses": [],
                "referral_code": None,
                "referred_by": None,
                "referral_count": 0,
                "referral_earnings": 0.0,
                "unclaimed_referral_earnings": 0.0,
                "achievements": []
            }
            self.data['users'][user_id_str] = new_user
            self.save_data()
        return self.data['users'][user_id_str]

    def update_user(self, user_id: int, updates: Dict[str, Any]):
        """Updates specific fields for a user."""
        user_id_str = str(user_id)
        if user_id_str in self.data['users']:
            self.data['users'][user_id_str].update(updates)
            self.save_data()

    def get_house_balance(self) -> float:
        """Retrieves the current house balance."""
        return self.data['house_balance']

    def update_house_balance(self, change: float):
        """Adds or subtracts from the house balance."""
        self.data['house_balance'] += change
        self.save_data()
        
    def add_transaction(self, user_id: int, type: str, amount: float, description: str):
        """Records a transaction for historical purposes."""
        user_id_str = str(user_id)
        if user_id_str not in self.data['transactions']:
            self.data['transactions'][user_id_str] = []
        
        transaction = {
            "type": type,
            "amount": amount,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
        self.data['transactions'][user_id_str].append(transaction)
        # Note: Transaction save is implicitly handled by self.save_data() called in update_user/update_house_balance

    def record_game(self, game_data: Dict[str, Any]):
        """Records a completed game to the global history."""
        game_data['timestamp'] = datetime.now().isoformat()
        self.data['games'].append(game_data)
        # We only keep the last 500 games to prevent the file from getting too large
        if len(self.data['games']) > 500:
            self.data['games'] = self.data['games'][-500:]
        self.save_data()

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Returns top players by total wagered."""
        leaderboard_data = []
        for user_data in self.data['users'].values():
            leaderboard_data.append({
                "username": user_data.get('username', f'User{user_data["user_id"]}'),
                "total_wagered": user_data.get('total_wagered', 0.0)
            })
        
        # Sort by total_wagered descending
        leaderboard_data.sort(key=lambda x: x['total_wagered'], reverse=True)
        return leaderboard_data[:50] # Limit to top 50

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
        if 'dynamic_admins' not in self.db.data:
            self.db.data['dynamic_admins'] = []
            self.db.save_data()
        
        self.dynamic_admin_ids = set(self.db.data.get('dynamic_admins', []))
        if self.dynamic_admin_ids:
            logger.info(f"Loaded {len(self.dynamic_admin_ids)} dynamic admin(s) from database")
        
        # Initialize bot application
        self.app = Application.builder().token(token).build()
        self.setup_handlers()
        
        # Dictionary to store ongoing PvP challenges
        self.pending_pvp: Dict[str, Any] = self.db.data.get('pending_pvp', {})
        
        # Track button ownership: (chat_id, message_id) -> user_id mapping
        self.button_ownership: Dict[tuple, int] = {}
        # Track clicked buttons to prevent re-use: (chat_id, message_id, callback_data)
        self.clicked_buttons: set = set()
        
        # Sticker configuration - Load from database or initialize with defaults
        if 'stickers' not in self.db.data:
            self.db.data['stickers'] = {
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
            self.db.save_data()
        
        self.stickers = self.db.data['stickers']
        
        # Dictionary to store active Blackjack games: user_id -> BlackjackGame instance
        self.blackjack_sessions: Dict[int, BlackjackGame] = {}

    def setup_handlers(self):
        """Setup all command and callback handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.start_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("bal", self.balance_command))
        self.app.add_handler(CommandHandler("bonus", self.bonus_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("levels", self.levels_command))
        self.app.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        self.app.add_handler(CommandHandler("global", self.leaderboard_command))
        self.app.add_handler(CommandHandler("referral", self.referral_command))
        self.app.add_handler(CommandHandler("ref", self.referral_command))
        self.app.add_handler(CommandHandler("housebal", self.housebal_command))
        self.app.add_handler(CommandHandler("userid", self.userid_command))
        self.app.add_handler(CommandHandler("history", self.history_command))
        self.app.add_handler(CommandHandler("dice", self.dice_command))
        self.app.add_handler(CommandHandler("darts", self.darts_command))
        self.app.add_handler(CommandHandler("basketball", self.basketball_command))
        self.app.add_handler(CommandHandler("bball", self.basketball_command))
        self.app.add_handler(CommandHandler("soccer", self.soccer_command))
        self.app.add_handler(CommandHandler("football", self.soccer_command))
        self.app.add_handler(CommandHandler("bowling", self.bowling_command))
        self.app.add_handler(CommandHandler("predict", self.predict_command))
        self.app.add_handler(CommandHandler("coinflip", self.coinflip_command))
        self.app.add_handler(CommandHandler("flip", self.coinflip_command))
        self.app.add_handler(CommandHandler("roulette", self.roulette_command))
        self.app.add_handler(CommandHandler("blackjack", self.blackjack_command))
        self.app.add_handler(CommandHandler("bj", self.blackjack_command))
        self.app.add_handler(CommandHandler("tip", self.tip_command))
        self.app.add_handler(CommandHandler("deposit", self.deposit_command))
        self.app.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.app.add_handler(CommandHandler("backup", self.backup_command))
        self.app.add_handler(CommandHandler("savesticker", self.save_sticker_command))
        self.app.add_handler(CommandHandler("stickers", self.list_stickers_command))
        self.app.add_handler(CommandHandler("saveroulette", self.save_roulette_stickers_command))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", self.admin_command))
        self.app.add_handler(CommandHandler("givebal", self.givebal_command))
        self.app.add_handler(CommandHandler("setbal", self.setbal_command))
        self.app.add_handler(CommandHandler("adddeposit", self.adddeposit_command))
        self.app.add_handler(CommandHandler("allusers", self.allusers_command))
        self.app.add_handler(CommandHandler("allbalances", self.allbalances_command))
        self.app.add_handler(CommandHandler("userinfo", self.userinfo_command))
        self.app.add_handler(CommandHandler("addadmin", self.addadmin_command))
        self.app.add_handler(CommandHandler("removeadmin", self.removeadmin_command))
        self.app.add_handler(CommandHandler("listadmins", self.listadmins_command))
        self.app.add_handler(CommandHandler("sethousebal", self.sethousebal_command))
        self.app.add_handler(CommandHandler("matchhistory", self.matchhistory_command))
        self.app.add_handler(CommandHandler("pendingdeposits", self.pending_deposits_command))
        self.app.add_handler(CommandHandler("creditdeposit", self.creditdeposit_command))
        self.app.add_handler(CommandHandler("approvedeposit", self.approve_deposit_command))
        self.app.add_handler(CommandHandler("pendingwithdraws", self.pending_withdraws_command))
        self.app.add_handler(CommandHandler("processwithdraw", self.process_withdraw_command))
        
        self.app.add_handler(MessageHandler(filters.Sticker.ALL, self.sticker_handler))
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
        credited_amount = round(ltc_amount, 2)
        
        target_data['balance'] += credited_amount
        self.db.update_user(target_user_id, target_data)
        
        self.db.add_transaction(target_user_id, "deposit", credited_amount, f"LTC Deposit (Manual) - TX: {tx_id[:16]}...")
        
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
                     f"Received: {ltc_amount:.8f} LTC\n"
                     f"Credited: **${credited_amount:.2f}**\n\n"
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
                                    text=f"⏰ @{challenger_data['username']} didn't send their emoji within 30 seconds and forfeited ${wager:.2f} to the house. @{acceptor_data['username']} has been refunded ${wager:.2f}.",
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
                                        text=f"⏰ @{opponent_data['username']} didn't send their emoji within 30 seconds and forfeited ${wager:.2f} to the house. @{challenger_data['username']} has been refunded ${wager:.2f}.",
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
                                        text=f"⏰ @{player_data['username']} didn't send their emoji within 30 seconds and forfeited ${wager:.2f} to the house.",
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
        
        # Check for referral link in /start arguments
        if context.args and context.args[0].startswith('ref_'):
            ref_code = context.args[0].split('_', 1)[1]
            if user_data.get('referred_by') is None:
                referrer_data = self.db.data['users'].get(self.db.data['users'].get(ref_code))
                if referrer_data and referrer_data['user_id'] != user.id:
                    self.db.update_user(user.id, {'referred_by': ref_code})
                    self.db.update_user(referrer_data['user_id'], {'referral_count': referrer_data.get('referral_count', 0) + 1})
                    await context.bot.send_message(
                        chat_id=referrer_data['user_id'],
                        text=f"🎉 **New Referral!** Your link brought in @{user.username or user.first_name}.",
                        parse_mode="Markdown"
                    )
        
        welcome_text = f"""
🎰 **Gran Tesero**
💰 Balance: ${user_data['balance']:.2f}

**Games:**
/dice 10 - Dice 🎲
/darts 10 - Darts 🎯
/basketball 10 - Basketball 🏀
/soccer 10 - Soccer ⚽
/bowling 10 - Bowling 🎳
/flip 10 - Coin Flip 🪙
/predict 10 #6 - Predict 🔮
/roulette 10 - Roulette 🎡

**Menu:**
/bal - Balance
/bonus - Get bonus
/stats - Your stats
"""
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show balance with deposit/withdraw buttons"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        balance_text = f"💰 **Balance: ${user_data['balance']:.2f}**"
        
        keyboard = [
            [InlineKeyboardButton("💵 Deposit", callback_data="deposit_mock"),
             InlineKeyboardButton("💸 Withdraw", callback_data="withdraw_mock")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(balance_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    async def bonus_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bonus status"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        wagered_since_withdrawal = user_data.get('wagered_since_last_withdrawal', 0)
        bonus_amount = wagered_since_withdrawal * 0.005
        
        if bonus_amount < 0.01:
            await update.message.reply_text("🎁 No bonus available yet\n\nPlay games to earn bonus!", parse_mode="Markdown")
            return
        
        bonus_text = f"🎁 **Bonus Available: ${bonus_amount:.2f}**\n\nClaim it below!"
        
        keyboard = [[InlineKeyboardButton("💰 Claim Now", callback_data="claim_daily_bonus")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(bonus_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show player statistics"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        games_played = user_data.get('games_played', 0)
        games_won = user_data.get('games_won', 0)
        win_rate = (games_won / games_played * 100) if games_played > 0 else 0
        total_wagered = user_data.get('total_wagered', 0)
        total_pnl = user_data.get('total_pnl', 0)
        total_won = total_wagered + total_pnl if total_pnl > 0 else total_wagered
        
        current_level = get_user_level(total_wagered)
        next_level = get_next_level(total_wagered)
        
        join_date = user_data.get('join_date')
        first_game = user_data.get('first_wager_date')
        last_game = user_data.get('last_game_date')
        
        def format_date(date_str):
            if not date_str:
                return "N/A"
            try:
                dt = datetime.fromisoformat(date_str)
                return dt.strftime("%b %d, %Y")
            except:
                return "N/A"
        
        stats_text = f"""{current_level['emoji']} **Level: {current_level['name']}**

📊 **Your Stats**

🎮 Games Played: {games_played}
🏆 Win Rate: {win_rate:.0f}%
💵 Total Wagered: ${total_wagered:.2f}
💰 Total Won: ${total_won:.2f}

📅 Joined: {format_date(join_date)}
🎰 First Game: {format_date(first_game)}
🕐 Last Game: {format_date(last_game)}"""

        if next_level:
            progress = total_wagered / next_level['threshold'] * 100
            remaining = next_level['threshold'] - total_wagered
            stats_text += f"\n\n📈 **Next: {next_level['emoji']} {next_level['name']}**\nProgress: {progress:.1f}% (${remaining:.2f} more)"
        
        keyboard = []
        
        claimed_bonuses = user_data.get('claimed_level_bonuses', [])
        if current_level['bonus'] > 0 and current_level['id'] not in claimed_bonuses:
            keyboard.append([InlineKeyboardButton(f"🎁 Claim ${current_level['bonus']} Level Bonus!", callback_data=f"claim_level_bonus_{current_level['id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def levels_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show levels with tier navigation"""
        user_id = update.effective_user.id
        user_data = self.ensure_user_registered(update)
        total_wagered = user_data.get('total_wagered', 0)
        current_level = get_user_level(total_wagered)
        
        current_tier_name = current_level.get('tier_name', 'Bronze')
        if current_tier_name == 'Unranked':
            current_tier_name = 'Bronze'
        
        tier_index = get_tier_index(current_tier_name)
        
        levels_text, keyboard = self.build_tier_display(tier_index, total_wagered)
        
        sent_msg = await update.message.reply_text(levels_text, reply_markup=keyboard, parse_mode="Markdown")
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    def build_tier_display(self, tier_index: int, total_wagered: float):
        """Build the display for a specific tier with navigation buttons."""
        tier_index = max(0, min(tier_index, len(LEVEL_TIERS) - 1))
        tier = LEVEL_TIERS[tier_index]
        current_level = get_user_level(total_wagered)
        
        levels_text = f"⬆️ **Levels**\n\n"
        
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
            
            levels_text += f"{tier['emoji']} **{level['name']}**\n"
            levels_text += f"Wager to Reach: ${threshold:,}\n"
            levels_text += f"Level Up Bonus: {bonus_text}\n\n"
        
        keyboard = []
        nav_buttons = []
        
        if tier_index > 0:
            prev_tier = LEVEL_TIERS[tier_index - 1]
            nav_buttons.append(InlineKeyboardButton(f"⬅ {prev_tier['name']}", callback_data=f"levels_tier_{tier_index - 1}"))
        
        if tier_index < len(LEVEL_TIERS) - 1:
            next_tier = LEVEL_TIERS[tier_index + 1]
            nav_buttons.append(InlineKeyboardButton(f"{next_tier['name']} ➡", callback_data=f"levels_tier_{tier_index + 1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("⬅ Back", callback_data="back_to_menu")])
        
        return levels_text, InlineKeyboardMarkup(keyboard)
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show leaderboard with pagination"""
        page = 0
        if context.args and context.args[0].isdigit():
            page = max(0, int(context.args[0]) - 1)
        
        await self.show_leaderboard_page(update, page)
    
    async def show_leaderboard_page(self, update: Update, page: int):
        """Display a specific leaderboard page"""
        leaderboard = self.db.get_leaderboard()
        items_per_page = 10
        total_pages = (len(leaderboard) + items_per_page - 1) // items_per_page
        
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        page_data = leaderboard[start_idx:end_idx]
        
        leaderboard_text = f"🏆 **Leaderboard** ({page + 1}/{total_pages})\n\n"
        
        if not leaderboard:
            leaderboard_text += "No players yet"
        
        for idx, player in enumerate(page_data, start=start_idx + 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            leaderboard_text += f"{medal} **{player['username']}**\n"
            leaderboard_text += f"   💰 Wagered: ${player['total_wagered']:.2f}\n\n"
        
        keyboard = []
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"lb_page_{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"lb_page_{page + 1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Removed "Go to Page" button for simplicity in single file
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
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
    
    async def referral_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show referral link and earnings"""
        user_id = update.effective_user.id
        user_data = self.db.get_user(user_id)
        
        if not user_data.get('referral_code'):
            # Generate a simple, unique referral code
            referral_code = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
            self.db.update_user(user_id, {'referral_code': referral_code})
            user_data['referral_code'] = referral_code
        
        bot_username = (await context.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_data['referral_code']}"
        
        referral_text = f"""
👥 **Referral**

Link: `{referral_link}`

Referrals: {user_data.get('referral_count', 0)}
Earned: ${user_data.get('referral_earnings', 0):.2f}
Unclaimed: ${user_data.get('unclaimed_referral_earnings', 0):.2f}
"""
        
        keyboard = []
        if user_data.get('unclaimed_referral_earnings', 0) >= 0.01:
            keyboard.append([InlineKeyboardButton("💰 Claim Earnings", callback_data="claim_referral")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.message.reply_text(referral_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    async def housebal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show house balance"""
        house_balance = self.db.get_house_balance()
        
        housebal_text = f"🏦 House: ${house_balance:.2f}"
        
        await update.message.reply_text(housebal_text, parse_mode="Markdown")
    
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
        """Show match history"""
        user_id = update.effective_user.id
        user_games = self.db.data.get('games', [])
        
        # Filter games involving the user (player_id, challenger, or opponent) and get the last 15
        user_games_filtered = [
            game for game in user_games 
            if game.get('player_id') == user_id or 
               game.get('challenger') == user_id or 
               game.get('opponent') == user_id
        ][-15:]
        
        if not user_games_filtered:
            await update.message.reply_text("📜 No history yet")
            return
        
        history_text = "🎮 **History** (Last 15)\n\n"
        
        for game in reversed(user_games_filtered):
            game_type = game.get('type', 'unknown')
            timestamp = game.get('timestamp', '')
            
            if timestamp:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
            else:
                time_str = "Unknown"
            
            if 'bot' in game_type:
                result = game.get('result', 'unknown')
                wager = game.get('wager', 0)
                
                if game_type == 'dice_bot':
                    player_roll = game.get('player_roll', 0)
                    bot_roll = game.get('bot_roll', 0)
                    result_emoji = "✅ Win" if result == "win" else "❌ Loss" if result == "loss" else "🤝 Draw"
                    history_text += f"{result_emoji} **Dice vs Bot** - ${wager:.2f}\n"
                    history_text += f"   You: {player_roll} | Bot: {bot_roll} | {time_str}\n\n"
                elif game_type == 'coinflip_bot':
                    choice = game.get('choice', 'unknown')
                    flip_result = game.get('result', 'unknown')
                    outcome = game.get('outcome', 'unknown')
                    result_emoji = "✅ Win" if outcome == "win" else "❌ Loss"
                    history_text += f"{result_emoji} **CoinFlip vs Bot** - ${wager:.2f}\n"
                    history_text += f"   Chose: {choice.capitalize()} | Result: {flip_result.capitalize()} | {time_str}\n\n"
            else:
                # PvP games are just generic matches for history view
                opponent_id = game.get('opponent') if game.get('challenger') == user_id else game.get('challenger')
                opponent_user = self.db.get_user(opponent_id)
                opponent_username = opponent_user.get('username', f'User{opponent_id}')
                
                history_text += f"🎲 **{game_type.replace('_', ' ').title()}**\n"
                history_text += f"   PvP Match vs @{opponent_username} | {time_str}\n\n"
        
        await update.message.reply_text(history_text, parse_mode="Markdown")
    
    async def dice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play dice game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("Usage: `/dice <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"dice_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"dice_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        if not context.args:
            await update.message.reply_text("Usage: `/darts <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"darts_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"darts_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        if not context.args:
            await update.message.reply_text("Usage: `/basketball <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"basketball_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"basketball_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        if not context.args:
            await update.message.reply_text("Usage: `/soccer <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"soccer_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"soccer_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        if not context.args:
            await update.message.reply_text("Usage: `/bowling <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        keyboard = [
            [InlineKeyboardButton("🤖 Play vs Bot", callback_data=f"bowling_bot_{wager:.2f}")],
            [InlineKeyboardButton("👥 Create PvP Challenge", callback_data=f"bowling_player_open_{wager:.2f}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
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
        
        if len(context.args) < 2:
            await update.message.reply_text("Usage: `/predict <amount|all> #<number>`\nExample: `/predict 5 #6`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        # Parse the predicted number
        predicted_str = context.args[1]
        if not predicted_str.startswith('#'):
            await update.message.reply_text("❌ Prediction must start with # (e.g., #6)")
            return
        
        try:
            predicted_number = int(predicted_str[1:])
        except ValueError:
            await update.message.reply_text("❌ Invalid number")
            return
        
        if predicted_number < 1 or predicted_number > 6:
            await update.message.reply_text("❌ Prediction must be between #1 and #6")
            return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from user balance
        self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
        
        # Send the dice emoji and wait for result
        dice_message = await update.message.reply_dice(emoji="🎲")
        actual_roll = dice_message.dice.value
        
        await asyncio.sleep(3)
        
        # Check if prediction matches
        if actual_roll == predicted_number:
            # Win! 6x payout (since odds are 1/6)
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
            
            # Add 6 play-again buttons for each number
            keyboard = [
                [InlineKeyboardButton("#1", callback_data=f"predict_{wager:.2f}_1"),
                 InlineKeyboardButton("#2", callback_data=f"predict_{wager:.2f}_2"),
                 InlineKeyboardButton("#3", callback_data=f"predict_{wager:.2f}_3")],
                [InlineKeyboardButton("#4", callback_data=f"predict_{wager:.2f}_4"),
                 InlineKeyboardButton("#5", callback_data=f"predict_{wager:.2f}_5"),
                 InlineKeyboardButton("#6", callback_data=f"predict_{wager:.2f}_6")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await update.message.reply_text(f"✅ Won ${profit:.2f}!", reply_markup=reply_markup)
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        else:
            # Loss
            self.db.update_user(user_id, {
                'total_wagered': user_data['total_wagered'] + wager,
                'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                'games_played': user_data['games_played'] + 1
            })
            self.db.update_house_balance(wager)
            
            # Add 6 play-again buttons for each number
            keyboard = [
                [InlineKeyboardButton("#1", callback_data=f"predict_{wager:.2f}_1"),
                 InlineKeyboardButton("#2", callback_data=f"predict_{wager:.2f}_2"),
                 InlineKeyboardButton("#3", callback_data=f"predict_{wager:.2f}_3")],
                [InlineKeyboardButton("#4", callback_data=f"predict_{wager:.2f}_4"),
                 InlineKeyboardButton("#5", callback_data=f"predict_{wager:.2f}_5"),
                 InlineKeyboardButton("#6", callback_data=f"predict_{wager:.2f}_6")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_msg = await update.message.reply_text(f"❌ Lost ${wager:.2f}", reply_markup=reply_markup)
            self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
        
        # Record game
        self.db.record_game({
            'type': 'dice_predict',
            'player_id': user_id,
            'wager': wager,
            'predicted': predicted_number,
            'actual_roll': actual_roll,
            'result': 'win' if actual_roll == predicted_number else 'loss',
            'payout': (wager * 6) if actual_roll == predicted_number else 0
        })
    
    async def coinflip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Play coinflip game setup"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("Usage: `/flip <amount|all>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
            
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
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
        
        if not context.args:
            await update.message.reply_text("Usage: `/roulette <amount|all>` or `/roulette <amount> #<number>`", parse_mode="Markdown")
            return
        
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
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
            [InlineKeyboardButton("Green (14x)", callback_data=f"roulette_{wager:.2f}_green")],
            [InlineKeyboardButton("Odd (2x)", callback_data=f"roulette_{wager:.2f}_odd"),
             InlineKeyboardButton("Even (2x)", callback_data=f"roulette_{wager:.2f}_even")],
            [InlineKeyboardButton("Low (2x)", callback_data=f"roulette_{wager:.2f}_low"),
             InlineKeyboardButton("High (2x)", callback_data=f"roulette_{wager:.2f}_high")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        sent_msg = await update.message.reply_text(
            f"🎰 **Roulette** - Wager: ${wager:.2f}\n\n"
            f"**Choose your bet:**\n"
            f"• Red/Black: 2x payout\n"
            f"• Odd/Even: 2x payout\n"
            f"• Green (0/00): 14x payout\n"
            f"• Low (1-18)/High (19-36): 2x payout\n\n"
            f"*Tip: Bet on a specific number with `/roulette <amount> #<number>` for 36x payout!*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
    
    async def blackjack_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start a Blackjack game"""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        # Check if user already has an active game
        if user_id in self.blackjack_sessions:
            await update.message.reply_text("❌ You already have an active Blackjack game. Finish it first or use /stand to end it.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "🃏 **Blackjack Rules**\n\n"
                "Get as close to 21 as possible without going over!\n\n"
                "**Card Values:**\n"
                "• 2-10: Face value\n"
                "• J, Q, K: 10 points\n"
                "• Ace: 1 or 11 points\n\n"
                "**Payouts:**\n"
                "• Blackjack (Ace + 10): 3:2 (1.5x)\n"
                "• Regular Win: 1:1\n"
                "• Push (tie): Bet returned\n\n"
                "**Actions:**\n"
                "• Hit: Take another card\n"
                "• Stand: Keep current hand\n"
                "• Double: Double bet, get 1 card\n"
                "• Split: Split pairs into 2 hands\n"
                "• Surrender: Forfeit and lose half bet\n\n"
                "**Usage:** `/blackjack <amount|all>`",
                parse_mode="Markdown"
            )
            return
        
        # Parse wager
        wager = 0.0
        if context.args[0].lower() == "all":
            wager = user_data['balance']
        else:
            try:
                wager = round(float(context.args[0]), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount")
                return
        
        if wager <= 0.01:
            await update.message.reply_text("❌ Min: $0.01")
            return
        
        if wager > user_data['balance']:
            await update.message.reply_text(f"❌ Balance: ${user_data['balance']:.2f}")
            return
        
        # Deduct wager from balance
        user_data['balance'] -= wager
        self.db.update_user(user_id, user_data)
        
        # Create new Blackjack game
        game = BlackjackGame(bet_amount=wager)
        game.start_game()
        self.blackjack_sessions[user_id] = game
        
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
            
            hand_status += f"{hand['cards']} (Value: {hand['value']}) "
            hand_status += f"- Bet: ${hand['bet']:.2f}"
            
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
            message += f"\n**Final Result:**\n"
            if state['dealer']['final_status'] == 'Bust':
                message += f"Dealer busts with {state['dealer']['value']}!\n\n"
            elif state['dealer']['is_blackjack']:
                message += "Dealer has Blackjack!\n\n"
            
            total_payout = state['total_payout']
            if total_payout > 0:
                message += f"✅ **You won ${total_payout:.2f}!**"
            elif total_payout < 0:
                message += f"❌ **You lost ${abs(total_payout):.2f}**"
            else:
                message += "🤝 **Push** - Bet returned"
            
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
                'game_type': 'blackjack',
                'user_id': user_id,
                'username': user_data.get('username', 'Unknown'),
                'wager': sum(h['bet'] for h in state['player_hands']),
                'payout': total_payout,
                'result': 'win' if total_payout > 0 else ('loss' if total_payout < 0 else 'push')
            })
            
            # Remove session
            del self.blackjack_sessions[user_id]
            
            await update.effective_message.reply_text(message, parse_mode="Markdown")
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
            
            # Surrender button
            if actions.get('can_surrender'):
                keyboard.append([InlineKeyboardButton("Surrender", callback_data=f"bj_{user_id}_surrender")])
        
        # Insurance button
        if state['is_insurance_available']:
            keyboard.append([InlineKeyboardButton("Take Insurance", callback_data=f"bj_{user_id}_insurance")])
        
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        
        await update.effective_message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")
    
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

    async def generate_coinremitter_address(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Generate a unique LTC deposit address via Plisio API."""
        api_key = "wMlExjlEV0Gu2AXHuheIclaWDkDQj14wWNqpLz1p8dIt60uDyhA-ZmTKWVCntlj0"
        
        webhook_url = os.getenv('WEBHOOK_URL', 'https://replit-casino-bot--stugbak2.replit.app')
        callback_url = f"{webhook_url}/webhook/deposit?json=true"
        
        url = "https://plisio.net/api/v1/invoices/new"
        params = {
            'source_currency': 'USD',
            'source_amount': '1',
            'currency': 'LTC',
            'order_number': f'user_{user_id}_{int(datetime.now().timestamp())}',
            'order_name': f'Deposit_User_{user_id}',
            'callback_url': callback_url,
            'api_key': api_key,
            'expire_min': '0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    result = await response.json()
                    if result.get('status') == 'success':
                        data = result.get('data', {})
                        return {
                            'address': data.get('wallet_hash'),
                            'qr_code': data.get('qr_code'),
                            'expire_on': data.get('expire_utc'),
                            'txn_id': data.get('txn_id')
                        }
                    else:
                        logger.error(f"Plisio API error: {result}")
                        return None
        except Exception as e:
            logger.error(f"Plisio API request failed: {e}")
            return None

    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user their unique deposit address for automatic deposits."""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        user_deposit_address = user_data.get('ltc_deposit_address')
        qr_code_url = user_data.get('ltc_qr_code')
        
        if not user_deposit_address:
            await update.message.reply_text("⏳ Generating your unique deposit address...")
            
            address_data = await self.generate_coinremitter_address(user_id)
            
            if address_data:
                user_deposit_address = address_data.get('address')
                qr_code_url = address_data.get('qr_code')
                
                user_data['ltc_deposit_address'] = user_deposit_address
                user_data['ltc_qr_code'] = qr_code_url
                user_data['ltc_address_expires'] = address_data.get('expire_on')
                self.db.update_user(user_id, user_data)
                self.db.save_data()
            else:
                master_address = os.getenv("LTC_MASTER_ADDRESS", "")
                if master_address:
                    user_deposit_address = master_address
                    await update.message.reply_text(
                        f"⚠️ Could not generate unique address. Use master address:\n\n"
                        f"`{master_address}`\n\n"
                        f"**Include your User ID in memo:** `{user_id}`",
                        parse_mode="Markdown"
                    )
                    return
                else:
                    await update.message.reply_text("❌ Deposits not configured. Contact admin.")
                    return
        
        if not user_deposit_address:
            master_address = os.getenv("LTC_MASTER_ADDRESS", "")
            if master_address:
                await update.message.reply_text(
                    f"⚠️ Could not generate unique address. Use master address:\n\n"
                    f"`{master_address}`\n\n"
                    f"👆 **Tap address to copy**\n\n"
                    f"**Include your User ID in memo:** `{user_id}`",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Deposits temporarily unavailable. Contact admin.")
            return
        
        deposit_text = f"""💰 **LTC Deposit**

Your unique deposit address:

`{user_deposit_address}`

👆 **Tap address to copy**

Send any amount of LTC - you will be credited the exact USD value.

Your balance will be credited automatically after confirmations."""
        
        await update.message.reply_text(deposit_text, parse_mode="Markdown")

    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start withdrawal flow with payment method selection."""
        user_data = self.ensure_user_registered(update)
        user_id = update.effective_user.id
        
        if user_data['balance'] < 1.00:
            await update.message.reply_text(
                f"❌ Minimum withdrawal is $1.00\n\nYour balance: **${user_data['balance']:.2f}**",
                parse_mode="Markdown"
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("💎 LTC (Litecoin)", callback_data="withdraw_method_ltc")],
            [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"💸 **Withdraw Funds**\n\nYour balance: **${user_data['balance']:.2f}**\n\nSelect payment method:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
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
            try:
                amount = round(float(text), 2)
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a number.")
                return
            
            user_data = self.db.get_user(user_id)
            
            if amount <= 0:
                await update.message.reply_text("❌ Amount must be positive.")
                return
            
            if amount < 1.00:
                await update.message.reply_text("❌ Minimum withdrawal is $1.00")
                return
            
            if amount > user_data['balance']:
                await update.message.reply_text(f"❌ Insufficient balance. You have ${user_data['balance']:.2f}")
                return
            
            context.user_data['pending_withdraw_amount'] = amount
            await update.message.reply_text(
                f"💸 **Withdraw ${amount:.2f} LTC**\n\nEnter your LTC wallet address:",
                parse_mode="Markdown"
            )
            return
        
        # Step 2: User is entering LTC address
        if 'pending_withdraw_amount' in context.user_data:
            ltc_address = text
            amount = context.user_data.pop('pending_withdraw_amount')
            context.user_data.pop('pending_withdraw_method', None)
            
            if len(ltc_address) < 20:
                await update.message.reply_text("❌ Invalid LTC address. Please enter a valid address.")
                context.user_data['pending_withdraw_amount'] = amount
                context.user_data['pending_withdraw_method'] = 'ltc'
                return
            
            user_data = self.db.get_user(user_id)
            
            if amount > user_data['balance']:
                await update.message.reply_text(f"❌ Insufficient balance. You have ${user_data['balance']:.2f}")
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
                'ltc_address': ltc_address,
                'timestamp': datetime.now().isoformat(),
                'status': 'pending'
            }
            
            self.db.data['pending_withdrawals'].append(withdrawal_request)
            self.db.save_data()
            
            await update.message.reply_text(
                f"✅ **Withdrawal Request Submitted**\n\nAmount: **${amount:.2f}**\nTo: `{ltc_address}`\n\nYour withdrawal is being processed.\n\nNew balance: ${user_data['balance']:.2f}",
                parse_mode="Markdown"
            )
            
            # Send to withdrawal approval group with buttons
            withdrawal_group_id = int(os.getenv('WITHDRAWAL_GROUP_ID', '-1003381398107'))
            withdraw_id = len(self.db.data['pending_withdrawals']) - 1
            
            keyboard = [
                [InlineKeyboardButton("✅ Approve", callback_data=f"withdraw_approve_{withdraw_id}_{user_id}_{amount}"),
                 InlineKeyboardButton("❌ Deny", callback_data=f"withdraw_deny_{withdraw_id}_{user_id}_{amount}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await self.app.bot.send_message(
                    chat_id=withdrawal_group_id,
                    text=f"🔔 **New Withdrawal Request**\n\nUser: @{username} (ID: `{user_id}`)\nAmount: **${amount:.2f}**\nLTC Address: `{ltc_address}`",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to send to withdrawal group: {e}")

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
        user_data['balance'] += amount
        self.db.update_user(target_user_id, user_data)
        self.db.add_transaction(target_user_id, "deposit", amount, "LTC Deposit (Approved)")
        
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

    async def send_ltc_withdrawal(self, ltc_address: str, usd_amount: float) -> dict:
        """Send LTC withdrawal via Plisio API."""
        api_key = "wMlExjlEV0Gu2AXHuheIclaWDkDQj14wWNqpLz1p8dIt60uDyhA-ZmTKWVCntlj0"
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://plisio.net/api/v1/operations/withdraw"
                params = {
                    "api_key": api_key,
                    "currency": "LTC",
                    "to": ltc_address,
                    "amount": str(usd_amount),
                    "type": "cash_out"
                }
                async with session.get(url, params=params) as response:
                    result = await response.json()
                    if result.get('status') == 'success':
                        return {
                            "success": True,
                            "tx_id": result.get('data', {}).get('id'),
                            "tx_url": result.get('data', {}).get('tx_url')
                        }
                    else:
                        error_msg = result.get('data', {}).get('message', 'Unknown error')
                        logger.error(f"Plisio withdrawal error: {error_msg}")
                        return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"Plisio withdrawal request failed: {e}")
            return {"success": False, "error": str(e)}

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
            
            tx_info = f"\nTX: `{result.get('tx_id', 'N/A')}`" if result.get('tx_id') else ""
            await update.message.reply_text(
                f"✅ **Withdrawal Sent!**\n\nUser ID: {target_user_id}\nAmount: ${withdrawal['amount']:.2f}\nTo: `{withdrawal['ltc_address']}`{tx_info}",
                parse_mode="Markdown"
            )
            
            # Notify user
            try:
                await self.app.bot.send_message(
                    chat_id=target_user_id,
                    text=f"✅ **Withdrawal Sent!**\n\n**${withdrawal['amount']:.2f}** has been sent to your LTC address.\n\nPlease allow a few minutes for blockchain confirmation.",
                    parse_mode="Markdown"
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
        """Check if user is an admin"""
        user_id = update.effective_user.id
        
        if self.is_admin(user_id):
            is_env_admin = user_id in self.env_admin_ids
            admin_type = "Permanent Admin" if is_env_admin else "Dynamic Admin"
            
            admin_text = f"""✅ You are a {admin_type}!

Admin Commands:
• /givebal [@username or ID] [amount] - Give money to a user
• /setbal [@username or ID] [amount] - Set a user's balance
• /adddeposit [@username or ID] [amount] - Credit a deposit
• /allbalances - View all player balances
• /allusers - View all registered users
• /userinfo [@username or ID] - View detailed user info
• /backup - Download database backup
• /addadmin [user_id] - Make someone an admin
• /removeadmin [user_id] - Remove admin access
• /listadmins - List all admins

Examples:
/givebal @john 100
/adddeposit @john 50
/setbal 123456789 500"""
            await update.message.reply_text(admin_text)
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
        target_user['balance'] += amount
        self.db.update_user(target_user_id, target_user)
        self.db.add_transaction(target_user_id, "deposit", amount, f"Manual deposit by admin {update.effective_user.id}")
        
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

**Referrals:**
Referred By: {target_user.get('referred_by', 'None')}
Referral Count: {target_user.get('referral_count', 0)}
Referral Earnings: ${target_user.get('referral_earnings', 0):.2f}
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
        
        # Handle referral earnings (1% of wager)
        referrer_code = user_data.get('referred_by')
        if referrer_code:
            referrer_data = next((u for u in self.db.data['users'].values() if u.get('referral_code') == referrer_code), None)
            if referrer_data:
                referral_commission = wager * 0.01
                referrer_data['referral_earnings'] += referral_commission
                referrer_data['unclaimed_referral_earnings'] += referral_commission
                self.db.update_user(referrer_data['user_id'], referrer_data)


    async def dice_vs_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float):
        """Play dice against the bot (called from button)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        chat_id = query.message.chat_id
        
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

    async def create_emoji_pvp_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, wager: float, game_type: str, emoji: str):
        """Create an emoji-based PvP challenge (darts, basketball, soccer)"""
        query = update.callback_query
        user_id = query.from_user.id
        user_data = self.db.get_user(user_id)
        username = user_data.get('username', f'User{user_id}')
        
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
                
                acceptor_user = self.db.get_user(challenge['opponent'])
                await context.bot.send_message(chat_id=chat_id, text=f"@{acceptor_user['username']} your turn", parse_mode="Markdown")
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
        result_text = ""
        
        if challenger_roll > acceptor_roll:
            winner_id = challenger_id
            loser_id = user_id
            result_text = f"✅ @{challenger_user['username']} won ${wager:.2f}!"
        elif acceptor_roll > challenger_roll:
            winner_id = user_id
            loser_id = challenger_id
            result_text = f"✅ @{acceptor_user['username']} won ${wager:.2f}!"
        else:
            # Draw: refund both wagers
            self.db.update_user(challenger_id, {'balance': challenger_user['balance'] + wager})
            self.db.update_user(user_id, {'balance': acceptor_user['balance'] + wager})
            result_text = "🤝 Draw! Refunded"
            
            self._update_user_stats(challenger_id, wager, 0.0, "draw")
            self._update_user_stats(user_id, wager, 0.0, "draw")
            
            self.db.record_game({"type": f"{game_type}_pvp", "challenger": challenger_id, "opponent": user_id, "wager": wager, "result": "draw"})
            
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
        winner_user['balance'] += winnings
        self.db.update_user(winner_id, winner_user)
        
        self._update_user_stats(winner_id, wager, winner_profit, "win")
        self._update_user_stats(loser_id, wager, -wager, "loss")
        
        self.db.add_transaction(winner_id, f"{game_type}_pvp_win", winner_profit, f"{game_type.upper()} PvP Win vs {self.db.get_user(loser_id)['username']}")
        self.db.add_transaction(loser_id, f"{game_type}_pvp_loss", -wager, f"{game_type.upper()} PvP Loss vs {self.db.get_user(winner_id)['username']}")
        self.db.record_game({"type": f"{game_type}_pvp", "challenger": challenger_id, "opponent": user_id, "wager": wager, "result": "win"})
        
        final_text = f"✅ @{winner_user['username']} won ${wager:.2f}!"
        
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
                result_text = f"✅ Won ${profit:.2f}!"
                user_data['balance'] += wager * 2
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-wager)
            else:
                # Bot made, player missed = player loses
                profit = -wager
                result = "loss"
                result_text = f"❌ Lost ${wager:.2f}"
                self.db.update_house_balance(wager)
        else:
            # Standard dice/bowling logic: higher roll wins
            if player_roll > bot_roll:
                profit = wager
                result = "win"
                result_text = f"✅ Won ${profit:.2f}!"
                user_data['balance'] += wager * 2
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-wager)
            elif player_roll < bot_roll:
                profit = -wager
                result = "loss"
                result_text = f"❌ Lost ${wager:.2f}"
                self.db.update_house_balance(wager)
            else:
                # Draw - refund wager
                user_data['balance'] += wager
                self.db.update_user(user_id, user_data)
                result_text = f"@{username} - Draw, bet refunded"
        
        # Update stats (unless draw, which already refunded)
        if result != "draw":
            self._update_user_stats(user_id, wager, profit, result)
        
        self.db.add_transaction(user_id, game_type, profit, f"{game_type.upper().replace('_', ' ')} - Wager: ${wager:.2f}")
        self.db.record_game({
            "type": game_type,
            "player_id": user_id,
            "wager": wager,
            "player_roll": player_roll,
            "bot_roll": bot_roll,
            "result": result
        })
        
        keyboard = [[InlineKeyboardButton("Play Again", callback_data=f"{game_type.replace('_bot', '_bot')}_{wager:.2f}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(chat_id=chat_id, text=result_text, reply_markup=reply_markup, parse_mode="Markdown")

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
            user_display = f"@{username}" if user_data.get('username') else username
            result_text = f"{user_display} won ${profit:.2f}"
            user_data['balance'] += wager * 2  # Return wager + winnings
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-wager)
        else:
            profit = -wager
            user_display = f"@{username}" if user_data.get('username') else username
            result_text = f"{user_display} lost ${wager:.2f}"
            self.db.update_house_balance(wager)

        # Update user stats and database
        self._update_user_stats(user_id, wager, profit, outcome)
        self.db.add_transaction(user_id, "coinflip_bot", profit, f"CoinFlip vs Bot - Wager: ${wager:.2f}")
        self.db.record_game({
            "type": "coinflip_bot",
            "player_id": user_id,
            "wager": wager,
            "choice": choice,
            "result": result, # The actual flip result
            "outcome": outcome # win or loss
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
                user_display = f"@{username}" if user_data.get('username') else username
                result_text = f"✅ Won ${profit:.2f}!"
                user_data['balance'] += wager * 36  # Return wager + 35x winnings
                self.db.update_user(user_id, user_data)
                self.db.update_house_balance(-profit)
            else:
                profit = -wager
                outcome = "loss"
                user_display = f"@{username}" if user_data.get('username') else username
                result_text = f"❌ Lost ${wager:.2f}"
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
                "outcome": outcome
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
        
        if won:
            profit = wager * (multiplier - 1)
            outcome = "win"
            user_display = f"@{username}" if user_data.get('username') else username
            result_text = f"{user_display} won ${profit:.2f}"
            user_data['balance'] += wager * multiplier  # Return wager + winnings
            self.db.update_user(user_id, user_data)
            self.db.update_house_balance(-profit)
        else:
            profit = -wager
            user_display = f"@{username}" if user_data.get('username') else username
            result_text = f"{user_display} lost ${wager:.2f}"
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
            "outcome": outcome
        })
        
        keyboard = [
            [InlineKeyboardButton("Red (2x)", callback_data=f"roulette_{wager:.2f}_red"),
             InlineKeyboardButton("Black (2x)", callback_data=f"roulette_{wager:.2f}_black")],
            [InlineKeyboardButton("Green (14x)", callback_data=f"roulette_{wager:.2f}_green")],
            [InlineKeyboardButton("Odd (2x)", callback_data=f"roulette_{wager:.2f}_odd"),
             InlineKeyboardButton("Even (2x)", callback_data=f"roulette_{wager:.2f}_even")],
            [InlineKeyboardButton("Low (2x)", callback_data=f"roulette_{wager:.2f}_low"),
             InlineKeyboardButton("High (2x)", callback_data=f"roulette_{wager:.2f}_high")]
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
        
        # Check button ownership (except for public buttons like challenges and leaderboard)
        public_buttons = ["accept_dice_", "accept_darts_", "accept_basketball_", "accept_soccer_", "accept_bowling_", "accept_coinflip_", "lb_page_", "transactions_history", "deposit_mock", "withdraw_mock"]
        is_public = any(data.startswith(prefix) or data == prefix for prefix in public_buttons)
        
        ownership_key = (chat_id, message_id)
        if not is_public and ownership_key in self.button_ownership:
            if self.button_ownership[ownership_key] != user_id:
                await query.answer("❌ This button is not for you!", show_alert=True)
                return
        
        await query.answer() # Acknowledge the button press
        
        # Mark button as clicked for game buttons (not utility buttons)
        if any(data.startswith(prefix) for prefix in ["dice_bot_", "darts_bot_", "basketball_bot_", "soccer_bot_", "bowling_bot_", "flip_bot_", "roulette_", "dice_player_open_", "darts_player_open_", "basketball_player_open_", "soccer_player_open_", "bowling_player_open_", "accept_darts_", "accept_basketball_", "accept_soccer_", "accept_bowling_", "claim_daily_bonus", "claim_referral", "claim_level_bonus_"]):
            self.clicked_buttons.add(button_key)
        
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
            
            # Game Callbacks (Predict play again)
            elif data.startswith("predict_"):
                parts = data.split('_')
                wager = float(parts[1])
                predicted_number = int(parts[2])
                
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
                    # Win! 6x payout (since odds are 1/6)
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
                    
                    # Add 6 play-again buttons for each number
                    keyboard = [
                        [InlineKeyboardButton("#1", callback_data=f"predict_{wager:.2f}_1"),
                         InlineKeyboardButton("#2", callback_data=f"predict_{wager:.2f}_2"),
                         InlineKeyboardButton("#3", callback_data=f"predict_{wager:.2f}_3")],
                        [InlineKeyboardButton("#4", callback_data=f"predict_{wager:.2f}_4"),
                         InlineKeyboardButton("#5", callback_data=f"predict_{wager:.2f}_5"),
                         InlineKeyboardButton("#6", callback_data=f"predict_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} won ${profit:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                else:
                    # Loss
                    self.db.update_user(user_id, {
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1
                    })
                    self.db.update_house_balance(wager)
                    
                    # Add 6 play-again buttons for each number
                    keyboard = [
                        [InlineKeyboardButton("#1", callback_data=f"predict_{wager:.2f}_1"),
                         InlineKeyboardButton("#2", callback_data=f"predict_{wager:.2f}_2"),
                         InlineKeyboardButton("#3", callback_data=f"predict_{wager:.2f}_3")],
                        [InlineKeyboardButton("#4", callback_data=f"predict_{wager:.2f}_4"),
                         InlineKeyboardButton("#5", callback_data=f"predict_{wager:.2f}_5"),
                         InlineKeyboardButton("#6", callback_data=f"predict_{wager:.2f}_6")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} lost ${wager:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                
                # Record game
                self.db.record_game({
                    'type': 'dice_predict',
                    'player_id': user_id,
                    'wager': wager,
                    'predicted': predicted_number,
                    'actual_roll': actual_roll,
                    'result': 'win' if actual_roll == predicted_number else 'loss',
                    'payout': (wager * 6) if actual_roll == predicted_number else 0
                })
            
            # Game Callbacks (Slots play again)
            elif data.startswith("slots_"):
                wager = float(data.split('_')[1])
                
                user_data = self.db.get_user(user_id)
                
                if wager > user_data['balance']:
                    await context.bot.send_message(chat_id=chat_id, text=f"❌ Balance: ${user_data['balance']:.2f}")
                    return
                
                # Deduct wager from user balance
                self.db.update_user(user_id, {'balance': user_data['balance'] - wager})
                
                # Send the slot machine emoji and wait for result
                dice_message = await context.bot.send_dice(chat_id=chat_id, emoji="🎰")
                slot_value = dice_message.dice.value
                
                # Slot machine values range from 1-64
                double_match_values = [2, 3, 4, 5, 6, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 37, 38, 39, 40, 41, 44, 45, 46, 47, 48, 51, 52, 53, 54, 55, 58, 59, 60, 61, 62]
                
                await asyncio.sleep(3)
                
                payout_multiplier = 0
                
                if slot_value == 64:
                    payout_multiplier = 10
                elif slot_value in [1, 22, 43]:
                    payout_multiplier = 5
                elif slot_value in double_match_values:
                    payout_multiplier = 2
                
                payout = wager * payout_multiplier
                profit = payout - wager
                
                # Add play-again button
                keyboard = [[InlineKeyboardButton("Play Again", callback_data=f"slots_{wager:.2f}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Update user balance and stats
                if payout > 0:
                    new_balance = user_data['balance'] + payout
                    self.db.update_user(user_id, {
                        'balance': new_balance,
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1,
                        'games_won': user_data['games_won'] + 1
                    })
                    self.db.update_house_balance(-profit)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} won ${profit:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                else:
                    self.db.update_user(user_id, {
                        'total_wagered': user_data['total_wagered'] + wager,
                        'wagered_since_last_withdrawal': user_data.get('wagered_since_last_withdrawal', 0) + wager,
                        'games_played': user_data['games_played'] + 1
                    })
                    self.db.update_house_balance(wager)
                    sent_msg = await context.bot.send_message(chat_id=chat_id, text=f"@{user_data['username']} lost ${wager:.2f}", reply_markup=reply_markup)
                    self.button_ownership[(sent_msg.chat_id, sent_msg.message_id)] = user_id
                
                # Record game
                self.db.record_game({
                    'type': 'slots_bot',
                    'player_id': user_id,
                    'wager': wager,
                    'slot_value': slot_value,
                    'result': 'win' if profit > 0 else 'loss',
                    'payout': profit
                })

            # Leaderboard Pagination
            elif data.startswith("lb_page_"):
                page = int(data.split('_')[2])
                await self.show_leaderboard_page(update, page)
            
            # All Balances Pagination (Admin)
            elif data.startswith("allbal_page_"):
                if not self.is_admin(user_id):
                    await query.answer("❌ This is for administrators only.", show_alert=True)
                    return
                page = int(data.split('_')[2])
                await self.show_allbalances_page(update, page)
                
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
                    
                    deposit_text = f"""💰 **LTC Deposit**

Your NEW deposit address:
`{user_deposit_address}`

Send any amount of LTC - you will be credited the exact USD value.

Your balance will be credited automatically after confirmations.

⚠️ Only send LTC to this address!"""
                    
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
                
                await query.edit_message_text(f"✅ **Bonus Claimed!**\nYou received **${bonus_amount:.2f}**.\n\nYour new balance is ${user_data['balance']:.2f}.", parse_mode="Markdown")

            elif data == "claim_referral":
                user_data = self.db.get_user(user_id)
                claim_amount = user_data.get('unclaimed_referral_earnings', 0)
                
                if claim_amount < 0.01:
                    await query.edit_message_text("❌ Minimum unclaimed earnings to claim is $0.01.")
                    return
                
                # Process claim
                user_data['balance'] += claim_amount
                user_data['unclaimed_referral_earnings'] = 0.0
                self.db.update_user(user_id, user_data)
                
                self.db.add_transaction(user_id, "referral_claim", claim_amount, "Referral Earnings Claim")
                
                await query.edit_message_text(f"✅ **Referral Earnings Claimed!**\nYou received **${claim_amount:.2f}**.\n\nYour new balance is ${user_data['balance']:.2f}.", parse_mode="Markdown")

            elif data.startswith("claim_level_bonus_"):
                level_id = data.replace("claim_level_bonus_", "")
                user_data = self.db.get_user(user_id)
                total_wagered = user_data.get('total_wagered', 0)
                current_level = get_user_level(total_wagered)
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
                
                await query.edit_message_text(
                    f"🎉 **Level Bonus Claimed!**\n\n"
                    f"{level_to_claim['emoji']} You reached **{level_to_claim['name']}**!\n"
                    f"Bonus: **+${bonus_amount:.2f}**\n\n"
                    f"New Balance: ${user_data['balance']:.2f}",
                    parse_mode="Markdown"
                )

            elif data == "back_to_menu":
                await query.edit_message_text("Use /start to see the main menu.", parse_mode="Markdown")

            # Deposit/Withdrawal buttons
            elif data == "deposit_mock":
                user_data = self.db.get_user(user_id)
                user_deposit_address = user_data.get('ltc_deposit_address')
                
                if not user_deposit_address:
                    await query.edit_message_text("⏳ Generating your unique deposit address...")
                    
                    address_data = await self.generate_coinremitter_address(user_id)
                    
                    if address_data:
                        user_deposit_address = address_data.get('address')
                        user_data['ltc_deposit_address'] = user_deposit_address
                        user_data['ltc_qr_code'] = address_data.get('qr_code')
                        user_data['ltc_address_expires'] = address_data.get('expire_on')
                        self.db.update_user(user_id, user_data)
                        self.db.save_data()
                    else:
                        master_address = os.getenv("LTC_MASTER_ADDRESS", "")
                        if master_address:
                            await query.edit_message_text(
                                f"⚠️ Could not generate unique address. Use master address:\n\n"
                                f"`{master_address}`\n\n"
                                f"**Include your User ID in memo:** `{user_id}`",
                                parse_mode="Markdown"
                            )
                            return
                        else:
                            await query.edit_message_text("❌ Deposits not configured. Contact admin.", parse_mode="Markdown")
                            return
                
                deposit_text = f"""💰 **LTC Deposit**

Your unique deposit address:

`{user_deposit_address}`

Send any amount of LTC - you will be credited the exact USD value.

Your balance will be credited automatically after confirmations."""
                
                keyboard = [[InlineKeyboardButton("📋 Copy Address", callback_data=f"copy_addr_{user_deposit_address}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(deposit_text, parse_mode="Markdown", reply_markup=reply_markup)
            
            elif data == "withdraw_mock":
                user_data = self.db.get_user(user_id)
                if user_data['balance'] < 1.00:
                    await query.edit_message_text(f"❌ Minimum withdrawal is $1.00\n\nYour balance: **${user_data['balance']:.2f}**", parse_mode="Markdown")
                else:
                    keyboard = [
                        [InlineKeyboardButton("💎 LTC (Litecoin)", callback_data="withdraw_method_ltc")],
                        [InlineKeyboardButton("❌ Cancel", callback_data="withdraw_cancel")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        f"💸 **Withdraw Funds**\n\nYour balance: **${user_data['balance']:.2f}**\n\nSelect payment method:",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
            
            elif data == "withdraw_method_ltc":
                user_data = self.db.get_user(user_id)
                balance = user_data['balance']
                
                context.user_data['pending_withdraw_method'] = 'ltc'
                
                await query.edit_message_text(
                    f"💸 **Withdraw LTC**\n\nYour balance: **${balance:.2f}**\n\nEnter the amount you want to withdraw:",
                    parse_mode="Markdown"
                )
            
            elif data == "withdraw_cancel":
                await query.edit_message_text("❌ Withdrawal cancelled.")
            
            elif data.startswith("withdraw_approve_"):
                parts = data.split('_')
                withdraw_id = int(parts[2])
                target_user_id = int(parts[3])
                amount = float(parts[4])
                
                pending = self.db.data.get('pending_withdrawals', [])
                if withdraw_id < len(pending) and pending[withdraw_id]['status'] == 'pending':
                    withdrawal = pending[withdraw_id]
                    username = withdrawal.get('username', f'User{target_user_id}')
                    
                    await query.edit_message_text(
                        f"⏳ **Sending LTC via Plisio...**\n\nUser: @{username} (ID: `{target_user_id}`)\nAmount: **${amount:.2f}**",
                        parse_mode="Markdown"
                    )
                    
                    # Send LTC via Plisio API
                    result = await self.send_ltc_withdrawal(withdrawal['ltc_address'], amount)
                    
                    if result['success']:
                        withdrawal['status'] = 'processed'
                        withdrawal['tx_id'] = result.get('tx_id')
                        self.db.add_transaction(target_user_id, "withdrawal", -amount, f"LTC Withdrawal to {withdrawal['ltc_address'][:20]}...")
                        self.db.save_data()
                        
                        tx_info = f"\nTX: `{result.get('tx_id', 'N/A')}`" if result.get('tx_id') else ""
                        await query.edit_message_text(
                            f"✅ **Withdrawal Sent!**\n\nUser: @{username} (ID: `{target_user_id}`)\nAmount: **${amount:.2f}**\nTo: `{withdrawal['ltc_address']}`{tx_info}\n\nApproved by @{update.effective_user.username or update.effective_user.first_name}",
                            parse_mode="Markdown"
                        )
                        
                        # Notify the user
                        try:
                            await self.app.bot.send_message(
                                chat_id=target_user_id,
                                text=f"✅ **Withdrawal Sent!**\n\n**${amount:.2f}** has been sent to your LTC address.\n\nPlease allow a few minutes for blockchain confirmation.",
                                parse_mode="Markdown"
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
                elif action == "surrender":
                    game.surrender()
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
                
                # Update the display with new game state
                await self._display_blackjack_state(update, context, user_id)
            
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
    BOT_TOKEN = "8575155625:AAFd40dO3bjJ6b6P74QcjH3mHUzuN7MilEA"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    USE_POLLING = os.getenv("USE_POLLING", "false").lower() == "true"
    
    logger.info("Starting Gran Tesero Casino Bot...")
    bot = GranTeseroCasinoBot(token=BOT_TOKEN)
    
    from webhook_server import WebhookServer
    webhook_server = WebhookServer(bot, port=5000)
    await webhook_server.start()
    logger.info("Webhook server started on port 5000")
    
    await bot.app.initialize()
    await bot.app.start()
    
    if WEBHOOK_URL and WEBHOOK_URL.startswith("https://") and not USE_POLLING:
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
    else:
        logger.info("Polling mode active - using long-polling for updates")
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

if __name__ == '__main__':
    asyncio.run(main())
