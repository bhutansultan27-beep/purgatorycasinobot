import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    balance = Column(Float, default=0.0)
    playthrough_required = Column(Float, default=0.0)
    total_wagered = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    win_streak = Column(Integer, default=0)
    best_win_streak = Column(Integer, default=0)
    wagered_since_last_withdrawal = Column(Float, default=0.0)
    first_wager_date = Column(DateTime, nullable=True)
    last_bonus_claim = Column(DateTime, nullable=True)
    last_game_date = Column(DateTime, nullable=True)
    join_date = Column(DateTime, default=datetime.now)
    referral_code = Column(String(50), nullable=True)
    referred_by = Column(BigInteger, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    unclaimed_referral_earnings = Column(Float, default=0.0)
    achievements = Column(JSON, default=list)
    claimed_level_bonuses = Column(JSON, default=list)

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    game_type = Column(String(50), nullable=False)
    wager = Column(Float, default=0.0)
    payout = Column(Float, default=0.0)
    result = Column(String(20))
    multiplier = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    game_snapshot = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

class HouseConfig(Base):
    __tablename__ = "house_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    role = Column(String(50), default="admin")
    added_at = Column(DateTime, default=datetime.now)

class BiggestDice(Base):
    __tablename__ = "biggest_dices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    winner_id = Column(BigInteger, nullable=False)
    winner_username = Column(String(255), nullable=True)
    loser_id = Column(BigInteger, nullable=False)
    loser_username = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    game_mode = Column(String(20), default="pvp")
    timestamp = Column(DateTime, default=datetime.now)

class DepositRecord(Base):
    __tablename__ = "deposit_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    amount = Column(Float, nullable=False)
    ltc_amount = Column(Float, default=0.0)
    tx_id = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        house_balance = session.query(HouseConfig).filter_by(key="house_balance").first()
        if not house_balance:
            session.add(HouseConfig(key="house_balance", value="10000.0"))
            session.commit()
    finally:
        session.close()

class CompatibilityDataProxy:
    def __init__(self, db_manager):
        self._db = db_manager
        self._cache = {}
    
    def __contains__(self, key):
        return True
    
    def get(self, key, default=None):
        if key == 'users':
            return self._get_all_users()
        elif key == 'games':
            return self._get_all_games()
        elif key == 'house_balance':
            return self._db.get_house_balance()
        elif key == 'dynamic_admins':
            return self._db.get_dynamic_admins()
        else:
            val = self._db.get_config(key, None)
            if val is None:
                return default
            try:
                return json.loads(val)
            except:
                return val
    
    def __getitem__(self, key):
        return self.get(key, {})
    
    def __setitem__(self, key, value):
        if key == 'house_balance':
            current = self._db.get_house_balance()
            self._db.update_house_balance(value - current)
        elif key == 'dynamic_admins':
            pass
        else:
            self._db.set_config(key, json.dumps(value) if not isinstance(value, str) else value)
    
    def _get_all_users(self):
        session = self._db.get_session()
        try:
            users = session.query(User).all()
            return {str(u.user_id): {
                "user_id": u.user_id,
                "username": u.username,
                "balance": u.balance,
                "playthrough_required": u.playthrough_required,
                "total_wagered": u.total_wagered,
                "total_pnl": u.total_pnl,
                "games_played": u.games_played,
                "games_won": u.games_won,
                "win_streak": u.win_streak,
                "best_win_streak": u.best_win_streak,
                "wagered_since_last_withdrawal": u.wagered_since_last_withdrawal,
                "first_wager_date": u.first_wager_date.isoformat() if u.first_wager_date else None,
                "last_bonus_claim": u.last_bonus_claim.isoformat() if u.last_bonus_claim else None,
                "last_game_date": u.last_game_date.isoformat() if u.last_game_date else None,
                "join_date": u.join_date.isoformat() if u.join_date else None,
                "referral_code": u.referral_code,
                "referred_by": u.referred_by,
                "referral_count": u.referral_count,
                "referral_earnings": u.referral_earnings,
                "unclaimed_referral_earnings": u.unclaimed_referral_earnings,
                "achievements": u.achievements or [],
                "claimed_level_bonuses": u.claimed_level_bonuses or []
            } for u in users}
        finally:
            session.close()
    
    def _get_all_games(self):
        session = self._db.get_session()
        try:
            games = session.query(Game).order_by(Game.timestamp.desc()).limit(500).all()
            return [{
                "id": g.id,
                "user_id": g.user_id,
                "username": g.username,
                "game_type": g.game_type,
                "game": g.game_type,
                "wager": g.wager,
                "bet": g.wager,
                "payout": g.payout,
                "result": g.result,
                "multiplier": g.multiplier or 0.0,
                "timestamp": g.timestamp.isoformat() if g.timestamp else None,
                **(g.details or {})
            } for g in games]
        finally:
            session.close()


class SQLDatabaseManager:
    def __init__(self):
        init_db()
        self._data_proxy = None
    
    @property
    def data(self):
        if self._data_proxy is None:
            self._data_proxy = CompatibilityDataProxy(self)
        return self._data_proxy
    
    def get_session(self):
        return SessionLocal()
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if not user:
                user = User(
                    user_id=user_id,
                    username=f"User{user_id}",
                    balance=0.0,
                    join_date=datetime.now(),
                    achievements=[],
                    claimed_level_bonuses=[]
                )
                session.add(user)
                session.commit()
                session.refresh(user)
            
            return {
                "user_id": user.user_id,
                "username": user.username,
                "balance": user.balance,
                "playthrough_required": user.playthrough_required,
                "total_wagered": user.total_wagered,
                "total_pnl": user.total_pnl,
                "games_played": user.games_played,
                "games_won": user.games_won,
                "win_streak": user.win_streak,
                "best_win_streak": user.best_win_streak,
                "wagered_since_last_withdrawal": user.wagered_since_last_withdrawal,
                "first_wager_date": user.first_wager_date.isoformat() if user.first_wager_date else None,
                "last_bonus_claim": user.last_bonus_claim.isoformat() if user.last_bonus_claim else None,
                "last_game_date": user.last_game_date.isoformat() if user.last_game_date else None,
                "join_date": user.join_date.isoformat() if user.join_date else None,
                "referral_code": user.referral_code,
                "referred_by": user.referred_by,
                "referral_count": user.referral_count,
                "referral_earnings": user.referral_earnings,
                "unclaimed_referral_earnings": user.unclaimed_referral_earnings,
                "achievements": user.achievements or [],
                "claimed_level_bonuses": user.claimed_level_bonuses or []
            }
        finally:
            session.close()
    
    def update_user(self, user_id: int, updates: Dict[str, Any]):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                for key, value in updates.items():
                    if hasattr(user, key):
                        if key in ['first_wager_date', 'last_bonus_claim', 'last_game_date'] and isinstance(value, str):
                            value = datetime.fromisoformat(value)
                        setattr(user, key, value)
                session.commit()
        finally:
            session.close()
    
    def add_transaction(self, user_id: int, type: str, amount: float, description: str):
        session = self.get_session()
        try:
            transaction = Transaction(
                user_id=user_id,
                type=type,
                amount=amount,
                description=description,
                timestamp=datetime.now()
            )
            session.add(transaction)
            session.commit()
        finally:
            session.close()
    
    def record_game(self, game_data: Dict[str, Any]):
        session = self.get_session()
        try:
            wager = game_data.get("wager", game_data.get("bet", 0))
            payout = game_data.get("payout", 0)
            multiplier = (payout / wager) if wager > 0 else 0.0
            
            game = Game(
                user_id=game_data.get("user_id"),
                username=game_data.get("username"),
                game_type=game_data.get("game_type", game_data.get("game", "unknown")),
                wager=wager,
                payout=payout,
                result=game_data.get("result", ""),
                multiplier=multiplier,
                details=game_data,
                game_snapshot=game_data.get("game_snapshot"),
                timestamp=datetime.now()
            )
            session.add(game)
            session.commit()
            return game.id
        finally:
            session.close()
    
    def get_live_bets(self, limit: int = 20, after_id: int = None) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            query = session.query(Game).order_by(Game.id.desc())
            if after_id:
                query = query.filter(Game.id > after_id)
            games = query.limit(limit).all()
            return [
                {
                    "id": g.id,
                    "user_id": g.user_id,
                    "username": g.username or f"User{str(g.user_id)[-4:]}",
                    "game_type": g.game_type,
                    "wager": g.wager,
                    "payout": g.payout,
                    "result": g.result,
                    "multiplier": g.multiplier or 0.0,
                    "timestamp": g.timestamp.isoformat() if g.timestamp else None,
                }
                for g in games
            ]
        finally:
            session.close()
    
    def get_bet_details(self, bet_id: int) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            game = session.query(Game).filter_by(id=bet_id).first()
            if not game:
                return None
            return {
                "id": game.id,
                "user_id": game.user_id,
                "username": game.username or f"User{str(game.user_id)[-4:]}",
                "game_type": game.game_type,
                "wager": game.wager,
                "payout": game.payout,
                "result": game.result,
                "multiplier": game.multiplier or 0.0,
                "details": game.details or {},
                "game_snapshot": game.game_snapshot,
                "timestamp": game.timestamp.isoformat() if game.timestamp else None,
            }
        finally:
            session.close()
    
    def get_house_balance(self) -> float:
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key="house_balance").first()
            if config:
                return float(config.value)
            return 10000.0
        finally:
            session.close()
    
    def update_house_balance(self, change: float):
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key="house_balance").first()
            if config:
                current = float(config.value)
                config.value = str(current + change)
            else:
                session.add(HouseConfig(key="house_balance", value=str(10000.0 + change)))
            session.commit()
        finally:
            session.close()
    
    def get_leaderboard(self, sort_by: str = "total_wagered", limit: int = 50) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            users = session.query(User).filter(User.total_wagered > 0).order_by(User.total_wagered.desc()).limit(limit).all()
            return [
                {
                    "user_id": str(u.user_id),
                    "username": u.username or f"User{u.user_id}",
                    "balance": u.balance,
                    "total_wagered": u.total_wagered,
                    "total_pnl": u.total_pnl,
                    "games_played": u.games_played
                }
                for u in users
            ]
        finally:
            session.close()
    
    def get_user_history(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            games = session.query(Game).filter_by(user_id=user_id).order_by(Game.timestamp.desc()).limit(limit).all()
            return [
                {
                    "user_id": g.user_id,
                    "game_type": g.game_type,
                    "game": g.game_type,
                    "wager": g.wager,
                    "bet": g.wager,
                    "payout": g.payout,
                    "result": g.result,
                    "timestamp": g.timestamp.isoformat() if g.timestamp else None,
                    **(g.details or {})
                }
                for g in games
            ]
        finally:
            session.close()
    
    def record_biggest_dice(self, winner_id: int, winner_username: str, loser_id: int, loser_username: str, amount: float, game_mode: str = "pvp"):
        session = self.get_session()
        try:
            record = BiggestDice(
                winner_id=winner_id,
                winner_username=winner_username,
                loser_id=loser_id,
                loser_username=loser_username,
                amount=amount,
                game_mode=game_mode,
                timestamp=datetime.now()
            )
            session.add(record)
            session.commit()
        finally:
            session.close()
    
    def get_biggest_dices(self, time_filter: str = "all") -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            from datetime import timedelta
            query = session.query(BiggestDice)
            if time_filter == "week":
                one_week_ago = datetime.now() - timedelta(days=7)
                query = query.filter(BiggestDice.timestamp > one_week_ago)
            
            dices = query.order_by(BiggestDice.amount.desc()).limit(10).all()
            return [
                {
                    "winner_id": d.winner_id,
                    "winner_username": d.winner_username,
                    "loser_id": d.loser_id,
                    "loser_username": d.loser_username,
                    "amount": d.amount,
                    "game_mode": d.game_mode,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None
                }
                for d in dices
            ]
        finally:
            session.close()
    
    def record_deposit(self, user_id: int, username: str, amount: float, ltc_amount: float = 0.0, tx_id: str = ""):
        session = self.get_session()
        try:
            record = DepositRecord(
                user_id=user_id,
                username=username,
                amount=amount,
                ltc_amount=ltc_amount,
                tx_id=tx_id,
                timestamp=datetime.now()
            )
            session.add(record)
            session.commit()
        finally:
            session.close()
    
    def get_biggest_deposits(self, time_filter: str = "all") -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            from datetime import timedelta
            query = session.query(DepositRecord)
            if time_filter == "week":
                one_week_ago = datetime.now() - timedelta(days=7)
                query = query.filter(DepositRecord.timestamp > one_week_ago)
            
            deposits = query.order_by(DepositRecord.amount.desc()).limit(10).all()
            return [
                {
                    "user_id": d.user_id,
                    "username": d.username,
                    "amount": d.amount,
                    "ltc_amount": d.ltc_amount,
                    "tx_id": d.tx_id,
                    "timestamp": d.timestamp.isoformat() if d.timestamp else None
                }
                for d in deposits
            ]
        finally:
            session.close()
    
    def get_dynamic_admins(self) -> List[int]:
        session = self.get_session()
        try:
            admins = session.query(Admin).all()
            return [a.user_id for a in admins]
        finally:
            session.close()
    
    def add_dynamic_admin(self, user_id: int):
        session = self.get_session()
        try:
            existing = session.query(Admin).filter_by(user_id=user_id).first()
            if not existing:
                session.add(Admin(user_id=user_id))
                session.commit()
        finally:
            session.close()
    
    def remove_dynamic_admin(self, user_id: int):
        session = self.get_session()
        try:
            session.query(Admin).filter_by(user_id=user_id).delete()
            session.commit()
        finally:
            session.close()
    
    def get_config(self, key: str, default: str = "") -> str:
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key=key).first()
            return config.value if config else default
        finally:
            session.close()
    
    def set_config(self, key: str, value: str):
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key=key).first()
            if config:
                config.value = value
            else:
                session.add(HouseConfig(key=key, value=value))
            session.commit()
        finally:
            session.close()
    
    def update_balance(self, user_id: int, amount: float):
        session = self.get_session()
        try:
            user = session.query(User).filter_by(user_id=user_id).first()
            if user:
                user.balance = max(0, user.balance + amount)
                session.commit()
        finally:
            session.close()
    
    def add_pending_withdrawal(self, user_id: int, amount: float, crypto: str, address: str):
        session = self.get_session()
        try:
            import time
            unique_id = int(time.time() * 1000) % 1000000000
            
            withdrawal_data = {
                "id": unique_id,
                "user_id": user_id,
                "amount": amount,
                "crypto": crypto,
                "address": address,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
            config = session.query(HouseConfig).filter_by(key="pending_withdrawals").first()
            if config:
                pending = json.loads(config.value) if config.value else []
            else:
                pending = []
                config = HouseConfig(key="pending_withdrawals", value="[]")
                session.add(config)
            
            pending.append(withdrawal_data)
            config.value = json.dumps(pending)
            session.commit()
        finally:
            session.close()
    
    def get_pending_withdrawals(self) -> List[Dict[str, Any]]:
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key="pending_withdrawals").first()
            if config and config.value:
                pending = json.loads(config.value)
                result = []
                for p in pending:
                    if p.get("status") == "pending":
                        user = session.query(User).filter_by(user_id=p.get("user_id")).first()
                        p["username"] = user.username if user else "Unknown"
                        result.append(p)
                return result
            return []
        finally:
            session.close()
    
    def approve_withdrawal(self, withdrawal_id: int):
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key="pending_withdrawals").first()
            if config and config.value:
                pending = json.loads(config.value)
                new_pending = []
                for p in pending:
                    if p.get("id") == withdrawal_id and p.get("status") == "pending":
                        amount = p.get("amount", 0)
                        house_config = session.query(HouseConfig).filter_by(key="house_balance").first()
                        if house_config:
                            current_balance = float(house_config.value)
                            house_config.value = str(current_balance - amount)
                        self.add_transaction(p.get("user_id"), "withdrawal_approved", -amount, f"Withdrawal approved: ${amount}")
                    else:
                        new_pending.append(p)
                config.value = json.dumps(new_pending)
                session.commit()
        finally:
            session.close()
    
    def reject_withdrawal(self, withdrawal_id: int):
        session = self.get_session()
        try:
            config = session.query(HouseConfig).filter_by(key="pending_withdrawals").first()
            if config and config.value:
                pending = json.loads(config.value)
                new_pending = []
                for p in pending:
                    if p.get("id") == withdrawal_id and p.get("status") == "pending":
                        user_id = p.get("user_id")
                        amount = p.get("amount", 0)
                        user = session.query(User).filter_by(user_id=user_id).first()
                        if user:
                            user.balance += amount
                        self.add_transaction(user_id, "withdrawal_rejected", amount, f"Withdrawal rejected, refunded: ${amount}")
                    else:
                        new_pending.append(p)
                config.value = json.dumps(new_pending)
                session.commit()
        finally:
            session.close()
    
    def search_user(self, query: str) -> Optional[Dict[str, Any]]:
        session = self.get_session()
        try:
            user = None
            if query.isdigit():
                user = session.query(User).filter_by(user_id=int(query)).first()
            else:
                clean_query = query.lstrip('@')
                user = session.query(User).filter(User.username.ilike(f"%{clean_query}%")).first()
            
            if user:
                return {
                    "user_id": user.user_id,
                    "username": user.username,
                    "balance": user.balance,
                    "total_wagered": user.total_wagered,
                    "games_played": user.games_played
                }
            return None
        finally:
            session.close()
    
    def get_bot_stats(self) -> Dict[str, Any]:
        session = self.get_session()
        try:
            total_users = session.query(User).count()
            total_wagered = session.query(User).with_entities(
                session.query(User.total_wagered).as_scalar()
            ).scalar() or 0
            
            users = session.query(User).all()
            total_wagered = sum(u.total_wagered for u in users)
            total_pnl = sum(u.total_pnl for u in users)
            
            house_config = session.query(HouseConfig).filter_by(key="house_balance").first()
            house_balance = float(house_config.value) if house_config else 10000.0
            
            return {
                "total_users": total_users,
                "total_wagered": total_wagered,
                "house_balance": house_balance,
                "house_profit": -total_pnl
            }
        finally:
            session.close()
    
    def save_data(self):
        pass


def migrate_json_to_sql(json_file: str = "casino_data.json"):
    if not os.path.exists(json_file):
        print(f"No {json_file} found, skipping migration")
        return
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {json_file}: {e}")
        return
    
    db = SQLDatabaseManager()
    session = db.get_session()
    
    try:
        existing_users = session.query(User).count()
        if existing_users > 0:
            print(f"Database already has {existing_users} users, skipping migration")
            return
        
        users_data = data.get("users", {})
        for user_id_str, user_data in users_data.items():
            try:
                user_id = int(user_id_str)
                join_date = None
                if user_data.get("join_date"):
                    try:
                        join_date = datetime.fromisoformat(user_data["join_date"])
                    except:
                        pass
                
                first_wager_date = None
                if user_data.get("first_wager_date"):
                    try:
                        first_wager_date = datetime.fromisoformat(user_data["first_wager_date"])
                    except:
                        pass
                
                last_bonus_claim = None
                if user_data.get("last_bonus_claim"):
                    try:
                        last_bonus_claim = datetime.fromisoformat(user_data["last_bonus_claim"])
                    except:
                        pass
                
                user = User(
                    user_id=user_id,
                    username=user_data.get("username", f"User{user_id}"),
                    balance=user_data.get("balance", 0.0),
                    playthrough_required=user_data.get("playthrough_required", 0.0),
                    total_wagered=user_data.get("total_wagered", 0.0),
                    total_pnl=user_data.get("total_pnl", 0.0),
                    games_played=user_data.get("games_played", 0),
                    games_won=user_data.get("games_won", 0),
                    win_streak=user_data.get("win_streak", 0),
                    best_win_streak=user_data.get("best_win_streak", 0),
                    wagered_since_last_withdrawal=user_data.get("wagered_since_last_withdrawal", 0.0),
                    first_wager_date=first_wager_date,
                    last_bonus_claim=last_bonus_claim,
                    join_date=join_date or datetime.now(),
                    referral_code=user_data.get("referral_code"),
                    referred_by=user_data.get("referred_by"),
                    referral_count=user_data.get("referral_count", 0),
                    referral_earnings=user_data.get("referral_earnings", 0.0),
                    unclaimed_referral_earnings=user_data.get("unclaimed_referral_earnings", 0.0),
                    achievements=user_data.get("achievements", []),
                    claimed_level_bonuses=user_data.get("claimed_level_bonuses", [])
                )
                session.add(user)
            except Exception as e:
                print(f"Error migrating user {user_id_str}: {e}")
        
        games_data = data.get("games", [])
        for game_data in games_data[-500:]:
            try:
                timestamp = None
                if game_data.get("timestamp"):
                    try:
                        timestamp = datetime.fromisoformat(game_data["timestamp"])
                    except:
                        pass
                
                game = Game(
                    user_id=game_data.get("user_id", 0),
                    game_type=game_data.get("game_type", game_data.get("game", "unknown")),
                    wager=game_data.get("wager", game_data.get("bet", 0)),
                    payout=game_data.get("payout", 0),
                    result=game_data.get("result", ""),
                    details=game_data,
                    timestamp=timestamp or datetime.now()
                )
                session.add(game)
            except Exception as e:
                print(f"Error migrating game: {e}")
        
        house_balance = data.get("house_balance", 10000.0)
        session.add(HouseConfig(key="house_balance", value=str(house_balance)))
        
        dynamic_admins = data.get("dynamic_admins", [])
        for admin_id in dynamic_admins:
            session.add(Admin(user_id=admin_id))
        
        session.commit()
        print(f"Successfully migrated {len(users_data)} users and {len(games_data)} games to SQL")
        
    except Exception as e:
        session.rollback()
        print(f"Migration error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    migrate_json_to_sql()
