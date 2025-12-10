from flask import Flask, render_template, jsonify, request
import os
import sys
import json
import hmac
import hashlib
import random
import requests
from urllib.parse import parse_qsl

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sql_database import SQLDatabaseManager

app = Flask(__name__, static_folder='static', template_folder='templates')

db = SQLDatabaseManager()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = set()
if ADMIN_IDS_STR:
    try:
        ADMIN_IDS = set(int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip())
    except ValueError:
        pass

def load_dynamic_admins():
    try:
        return set(db.get_dynamic_admins())
    except:
        pass
    return set()

def is_admin(user_id):
    dynamic_admins = load_dynamic_admins()
    return user_id in ADMIN_IDS or user_id in dynamic_admins

def get_user_profile_photo_url(user_id):
    if not BOT_TOKEN or not user_id:
        return None
    try:
        photos_response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/getUserProfilePhotos",
            params={"user_id": user_id, "limit": 1},
            timeout=5
        )
        photos_data = photos_response.json()
        if photos_data.get("ok") and photos_data.get("result", {}).get("total_count", 0) > 0:
            photos = photos_data["result"]["photos"]
            if photos and len(photos) > 0 and len(photos[0]) > 0:
                file_id = photos[0][-1]["file_id"]
                file_response = requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                    params={"file_id": file_id},
                    timeout=5
                )
                file_data = file_response.json()
                if file_data.get("ok"):
                    file_path = file_data["result"]["file_path"]
                    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"Error fetching profile photo: {e}")
    return None

def validate_init_data(init_data):
    if not init_data or not BOT_TOKEN:
        return None
    try:
        parsed = dict(parse_qsl(init_data))
        check_hash = parsed.pop('hash', None)
        if not check_hash:
            return None
        data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if calculated_hash == check_hash:
            user_data = json.loads(parsed.get('user', '{}'))
            return user_data
    except:
        pass
    return None

LEVEL_TIERS = [
    {"name": "Bronze", "emoji": "🥉", "thresholds": [100, 500, 1000, 2500, 5000]},
    {"name": "Silver", "emoji": "🥈", "thresholds": [10000, 15200, 20500, 26000, 32000]},
    {"name": "Gold", "emoji": "🏆", "thresholds": [39000, 48000, 58000, 69000, 81000]},
    {"name": "Platinum", "emoji": "💎", "thresholds": [94000, 107500, 122000, 138000, 155000]},
    {"name": "Diamond", "emoji": "💠", "thresholds": [173000, 192000, 211500, 232000, 253000]},
    {"name": "Emerald", "emoji": "💚", "thresholds": [275000, 298000, 322000, 347000, 373000]},
    {"name": "Ruby", "emoji": "❤️", "thresholds": [400000, 428000, 457000, 487000, 518000]},
    {"name": "Sapphire", "emoji": "💙", "thresholds": [550000, 583000, 617000, 652000, 688000]},
    {"name": "Amethyst", "emoji": "💜", "thresholds": [725000, 763000, 802000, 842000, 883000]},
    {"name": "Obsidian", "emoji": "🖤", "thresholds": [925000, 968000, 1012000, 1058000, 1107000]},
    {"name": "Mythic", "emoji": "🔮", "thresholds": [1159000, 1213000, 1270000, 1330000, 1393000]},
    {"name": "Legendary", "emoji": "👑", "thresholds": [1458000, 1525000, 1595000, 1668000, 1743000]},
    {"name": "Ethereal", "emoji": "✨", "thresholds": [1850000, 2000000, 2175000, 2400000, 2650000]},
]

def get_user_level(total_wagered):
    current_level = {"name": "Unranked", "emoji": "⚪", "threshold": 0}
    next_level = None
    
    all_levels = []
    for tier in LEVEL_TIERS:
        for i, threshold in enumerate(tier["thresholds"]):
            all_levels.append({
                "name": f"{tier['name']} {['I', 'II', 'III', 'IV', 'V'][i]}",
                "emoji": tier["emoji"],
                "threshold": threshold
            })
    
    for i, level in enumerate(all_levels):
        if total_wagered >= level["threshold"]:
            current_level = level
            if i + 1 < len(all_levels):
                next_level = all_levels[i + 1]
            else:
                next_level = None
        else:
            if current_level["name"] == "Unranked":
                next_level = level
            break
    
    return current_level, next_level

def get_user_from_db(user_id):
    try:
        user = db.get_user(user_id)
        if user:
            total_wagered = user.get('total_wagered', 0)
            games_played = user.get('games_played', 0)
            games_won = user.get('games_won', 0)
            win_rate = round((games_won / games_played * 100) if games_played > 0 else 0, 1)
            level, next_level = get_user_level(total_wagered)
            return {
                "balance": user.get('balance', 0),
                "level_emoji": level["emoji"],
                "level_name": level["name"],
                "total_wagered": total_wagered,
                "total_won": user.get('total_pnl', 0) if user.get('total_pnl', 0) > 0 else 0,
                "games_played": games_played,
                "win_rate": win_rate
            }
    except Exception as e:
        print(f"Error getting user from db: {e}")
    return None

def get_full_user_from_db(user_id):
    try:
        user = db.get_user(user_id)
        if user:
            total_wagered = user.get('total_wagered', 0)
            games_played = user.get('games_played', 0)
            games_won = user.get('games_won', 0)
            win_rate = round((games_won / games_played * 100) if games_played > 0 else 0, 1)
            level, next_level = get_user_level(total_wagered)
            return {
                "balance": user.get('balance', 0),
                "level_emoji": level["emoji"],
                "level_name": level["name"],
                "current_threshold": level["threshold"],
                "total_wagered": total_wagered,
                "total_pnl": user.get('total_pnl', 0),
                "games_played": games_played,
                "games_won": games_won,
                "win_rate": win_rate,
                "best_win_streak": user.get('best_win_streak', 0),
                "join_date": user.get('join_date'),
                "next_level": next_level
            }
    except Exception as e:
        print(f"Error getting full user from db: {e}")
    return None

def get_leaderboard_data():
    try:
        users = db.get_leaderboard()
        leaderboard = []
        for user in users:
            total_wagered = user.get('total_wagered', 0)
            if total_wagered > 0:
                level, _ = get_user_level(total_wagered)
                leaderboard.append({
                    "username": user.get('username', f'User{user.get("user_id")}'),
                    "total_wagered": total_wagered,
                    "level_emoji": level["emoji"],
                    "level_name": level["name"]
                })
        return leaderboard[:50]
    except Exception as e:
        print(f"Error getting leaderboard: {e}")
    return []

def get_user_history(user_id):
    try:
        return db.get_user_history(user_id, limit=50)
    except Exception as e:
        print(f"Error getting user history: {e}")
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/blackjack')
def blackjack():
    return render_template('blackjack.html')

@app.route('/slots')
def slots():
    return render_template('slots.html')

@app.route('/mines')
def mines():
    return render_template('mines.html')

@app.route('/limbo')
def limbo():
    return render_template('limbo.html')

@app.route('/keno')
def keno():
    return render_template('keno.html')

@app.route('/hilo')
def hilo():
    return render_template('hilo.html')

@app.route('/baccarat')
def baccarat():
    return render_template('baccarat.html')

@app.route('/roulette')
def roulette():
    return render_template('roulette.html')

@app.route('/coinflip')
def coinflip():
    return render_template('coinflip.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/profile', methods=['POST'])
def get_profile():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if user_id:
            profile = get_full_user_from_db(user_id)
            if profile:
                return jsonify({"success": True, "profile": profile})
        
        return jsonify({
            "success": True, 
            "profile": {
                "balance": 0,
                "level_emoji": "⚪",
                "level_name": "Unranked",
                "current_threshold": 0,
                "total_wagered": 0,
                "total_pnl": 0,
                "games_played": 0,
                "games_won": 0,
                "win_rate": 0,
                "best_win_streak": 0,
                "next_level": {"name": "Bronze I", "emoji": "🥉", "threshold": 100}
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/leaderboard')
def get_leaderboard():
    try:
        leaderboard = get_leaderboard_data()
        return jsonify({"success": True, "leaderboard": leaderboard})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/history', methods=['POST'])
def get_history():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if user_id:
            history = get_user_history(user_id)
            return jsonify({"success": True, "history": history})
        
        return jsonify({"success": True, "history": []})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/user', methods=['POST'])
def get_user():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        user_data = None
        admin_status = False
        photo_url = None
        
        if user_id:
            user_data = get_user_from_db(user_id)
            admin_status = is_admin(user_id)
            photo_url = get_user_profile_photo_url(user_id)
        
        if not user_data:
            user_data = {
                "balance": 0.00,
                "level_emoji": "⚪",
                "level_name": "Unranked",
                "total_wagered": 0,
                "total_won": 0,
                "games_played": 0,
                "win_rate": 0
            }
        
        user_data["is_admin"] = admin_status
        user_data["photo_url"] = photo_url
        
        bot_username = os.getenv("BOT_USERNAME", "GildTesoroCasinoBot")
        
        return jsonify({
            "success": True,
            "user": user_data,
            "bot_username": bot_username
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/deposit')
def deposit_page():
    return render_template('deposit.html')

@app.route('/withdraw')
def withdraw_page():
    return render_template('withdraw.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/deposit-info', methods=['POST'])
def get_deposit_info():
    try:
        ltc_address = os.getenv("LTC_MASTER_ADDRESS", "")
        sol_address = os.getenv("SOL_MASTER_ADDRESS", "")
        return jsonify({
            "success": True,
            "addresses": {
                "ltc": ltc_address,
                "sol": sol_address or "Coming Soon"
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/withdraw', methods=['POST'])
def request_withdraw():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id:
            return jsonify({"success": False, "error": "Authentication required"})
        
        amount = data.get('amount', 0)
        crypto = data.get('crypto', 'LTC')
        address = data.get('address', '')
        
        if amount < 2:
            return jsonify({"success": False, "error": "Minimum withdrawal is $2.00"})
        
        if not address:
            return jsonify({"success": False, "error": "Wallet address required"})
        
        user = db.get_user(user_id)
        if not user or user.get('balance', 0) < amount:
            return jsonify({"success": False, "error": "Insufficient balance"})
        
        db.update_balance(user_id, -amount)
        db.add_pending_withdrawal(user_id, amount, crypto, address)
        
        return jsonify({"success": True, "message": "Withdrawal request submitted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/check', methods=['POST'])
def check_admin():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if user_id and is_admin(user_id):
            return jsonify({"success": True, "is_admin": True})
        return jsonify({"success": True, "is_admin": False})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/stats', methods=['POST'])
def get_admin_stats():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id or not is_admin(user_id):
            return jsonify({"success": False, "error": "Unauthorized"})
        
        stats = db.get_bot_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/pending', methods=['POST'])
def get_pending_withdrawals():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id or not is_admin(user_id):
            return jsonify({"success": False, "error": "Unauthorized"})
        
        pending = db.get_pending_withdrawals()
        return jsonify({"success": True, "pending": pending})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/user-search', methods=['POST'])
def admin_user_search():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id or not is_admin(user_id):
            return jsonify({"success": False, "error": "Unauthorized"})
        
        query = data.get('query', '')
        user = db.search_user(query)
        
        if user:
            return jsonify({"success": True, "user": user})
        return jsonify({"success": False, "error": "User not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/modify-balance', methods=['POST'])
def admin_modify_balance():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        admin_id = user_info.get('id') if user_info else None
        
        if not admin_id or not is_admin(admin_id):
            return jsonify({"success": False, "error": "Unauthorized"})
        
        target_user_id = data.get('user_id')
        amount = data.get('amount', 0)
        action = data.get('action', 'add')
        
        if action == 'remove':
            amount = -amount
        
        db.update_balance(target_user_id, amount)
        return jsonify({"success": True, "message": "Balance updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/admin/handle-withdrawal', methods=['POST'])
def admin_handle_withdrawal():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        admin_id = user_info.get('id') if user_info else None
        
        if not admin_id or not is_admin(admin_id):
            return jsonify({"success": False, "error": "Unauthorized"})
        
        withdrawal_id = data.get('id')
        action = data.get('action')
        
        if action == 'approve':
            db.approve_withdrawal(withdrawal_id)
        elif action == 'reject':
            db.reject_withdrawal(withdrawal_id)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

RED_NUMBERS = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
BLACK_NUMBERS = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]

@app.route('/api/roulette/play', methods=['POST'])
def play_roulette():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id:
            return jsonify({"success": False, "error": "Authentication required"})
        
        bet = float(data.get('bet', 0))
        bet_type = data.get('betType', '')
        
        if bet <= 0:
            return jsonify({"success": False, "error": "Invalid bet amount"})
        
        if not bet_type:
            return jsonify({"success": False, "error": "Select a bet type"})
        
        user = db.get_user(user_id)
        if not user or user.get('balance', 0) < bet:
            return jsonify({"success": False, "error": "Insufficient balance"})
        
        result = random.randint(0, 37)
        if result == 37:
            result = 0
        
        color = 'green'
        if result in RED_NUMBERS:
            color = 'red'
        elif result in BLACK_NUMBERS:
            color = 'black'
        
        win = False
        multiplier = 0
        
        if bet_type == 'red' and color == 'red':
            win = True
            multiplier = 2
        elif bet_type == 'black' and color == 'black':
            win = True
            multiplier = 2
        elif bet_type == 'green' and color == 'green':
            win = True
            multiplier = 14
        elif bet_type == 'odd' and result > 0 and result % 2 == 1:
            win = True
            multiplier = 2
        elif bet_type == 'even' and result > 0 and result % 2 == 0:
            win = True
            multiplier = 2
        elif bet_type == 'low' and 1 <= result <= 18:
            win = True
            multiplier = 2
        elif bet_type == 'high' and 19 <= result <= 36:
            win = True
            multiplier = 2
        
        payout = 0
        if win:
            payout = bet * multiplier
            db.update_balance(user_id, payout - bet)
        else:
            db.update_balance(user_id, -bet)
        
        db.record_game(user_id, 'roulette', bet, payout - bet if win else -bet, win)
        
        new_balance = db.get_user(user_id).get('balance', 0)
        
        return jsonify({
            "success": True,
            "result": result,
            "color": color,
            "win": win,
            "payout": payout,
            "newBalance": new_balance
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/coinflip/play', methods=['POST'])
def play_coinflip():
    try:
        data = request.get_json()
        init_data = data.get('initData', '')
        user_info = validate_init_data(init_data)
        user_id = user_info.get('id') if user_info else None
        
        if not user_id:
            return jsonify({"success": False, "error": "Authentication required"})
        
        bet = float(data.get('bet', 0))
        choice = data.get('choice', '')
        
        if bet <= 0:
            return jsonify({"success": False, "error": "Invalid bet amount"})
        
        if choice not in ['heads', 'tails']:
            return jsonify({"success": False, "error": "Select heads or tails"})
        
        user = db.get_user(user_id)
        if not user or user.get('balance', 0) < bet:
            return jsonify({"success": False, "error": "Insufficient balance"})
        
        result = random.choice(['heads', 'tails'])
        win = result == choice
        
        multiplier = 1.98
        payout = 0
        
        if win:
            payout = bet * multiplier
            db.update_balance(user_id, payout - bet)
        else:
            db.update_balance(user_id, -bet)
        
        db.record_game(user_id, 'coinflip', bet, payout - bet if win else -bet, win)
        
        new_balance = db.get_user(user_id).get('balance', 0)
        
        return jsonify({
            "success": True,
            "result": result,
            "win": win,
            "payout": payout,
            "newBalance": new_balance
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
