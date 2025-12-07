import os
import json
import logging
import hmac
import hashlib
import asyncio
from datetime import datetime
from aiohttp import web
from telegram import Update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self, bot, port=None):
        self.bot = bot
        self.port = port or int(os.getenv("PORT", "5000"))
        self.app = web.Application()
        self.last_challenge_check = datetime.now()
        self.setup_routes()
        
    def setup_routes(self):
        self.app.router.add_post('/webhook/deposit', self.handle_deposit_webhook)
        self.app.router.add_get('/webhook/deposit', self.webhook_validation)
        self.app.router.add_post('/webhook/telegram', self.handle_telegram_webhook)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/', self.home)
        
    async def home(self, request):
        await self.periodic_challenge_check()
        return web.Response(text="Casino Bot Webhook Server", status=200)
    
    async def periodic_challenge_check(self):
        now = datetime.now()
        if (now - self.last_challenge_check).total_seconds() >= 5:
            self.last_challenge_check = now
            try:
                await self.bot.check_expired_challenges(None)
            except Exception as e:
                logger.error(f"Error checking expired challenges: {e}")
    
    async def handle_telegram_webhook(self, request):
        try:
            await self.periodic_challenge_check()
            data = await request.json()
            logger.info(f"Received Telegram update: {json.dumps(data)[:500]}")
            update = Update.de_json(data, self.bot.app.bot)
            logger.info(f"Processing update - chat_type: {update.effective_chat.type if update.effective_chat else 'unknown'}, message: {update.effective_message.text if update.effective_message else 'no message'}")
            await self.bot.app.process_update(update)
            return web.Response(text="OK", status=200)
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}", exc_info=True)
            return web.Response(text="Error", status=500)
        
    async def webhook_validation(self, request):
        return web.json_response({"status": "ok", "message": "Webhook endpoint ready"})
        
    async def health_check(self, request):
        return web.json_response({"status": "ok"})
    
    async def handle_deposit_webhook(self, request):
        try:
            content_type = request.content_type
            if 'multipart/form-data' in content_type or 'application/x-www-form-urlencoded' in content_type:
                data = await request.post()
                data = dict(data)
            else:
                data = await request.json()
            logger.info(f"Received deposit webhook: {data}")
            
            address = data.get('wallet_hash') or data.get('address')
            amount = float(data.get('amount', 0))
            tx_id = data.get('txn_id') or data.get('txid') or data.get('tx_id') or data.get('id')
            status = data.get('status', '')
            order_number = data.get('order_number', '')
            source_amount = data.get('source_amount')
            
            if status not in ['completed', 'mismatch']:
                logger.info(f"Webhook status: {status} - waiting for completed")
                return web.json_response({"status": "pending", "message": f"Status: {status}"})
            
            user_id = None
            if order_number and order_number.startswith('user_'):
                try:
                    user_id = int(order_number.split('_')[1])
                except (IndexError, ValueError):
                    pass
            
            if not user_id:
                user_id = self.find_user_by_deposit_address(address)
            
            if not user_id:
                logger.warning(f"No user found for deposit address: {address}")
                return web.json_response({"status": "error", "message": "Unknown address"}, status=400)
            
            if self.is_deposit_processed(tx_id):
                logger.info(f"Deposit already processed: {tx_id}")
                return web.json_response({"status": "ok", "message": "Already processed"})
            
            if source_amount:
                credited_amount = round(float(source_amount), 2)
            else:
                logger.warning("No source_amount from Plisio, using LTC amount as USD")
                credited_amount = round(amount, 2)
            
            user_data = self.bot.db.get_user(user_id)
            user_data['balance'] += credited_amount
            self.bot.db.update_user(user_id, user_data)
            
            tx_display = tx_id[:16] if tx_id and len(tx_id) > 16 else tx_id
            self.bot.db.add_transaction(user_id, "deposit", credited_amount, f"LTC Deposit (Auto) - TX: {tx_display}...")
            
            self.mark_deposit_processed(tx_id, user_id, amount, credited_amount)
            
            try:
                await self.bot.app.bot.send_message(
                    chat_id=user_id,
                    text=f"✅ **Deposit Confirmed!**\n\nReceived: {amount:.8f} LTC\nCredited: **${credited_amount:.2f}**\n\nNew Balance: ${user_data['balance']:.2f}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to notify user {user_id}: {e}")
            
            await self.generate_new_address_for_user(user_id)
            
            logger.info(f"Deposit processed: User {user_id}, Amount ${credited_amount:.2f}")
            return web.json_response({"status": "ok", "credited": credited_amount})
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)
    
    def find_user_by_deposit_address(self, address):
        for user_id, user_data in self.bot.db.data['users'].items():
            if user_data.get('ltc_deposit_address') == address:
                return int(user_id)
        return None
    
    def is_deposit_processed(self, tx_id):
        processed = self.bot.db.data.get('processed_deposits', [])
        return tx_id in processed
    
    def mark_deposit_processed(self, tx_id, user_id, ltc_amount, usd_amount):
        if 'processed_deposits' not in self.bot.db.data:
            self.bot.db.data['processed_deposits'] = []
        if 'deposit_history' not in self.bot.db.data:
            self.bot.db.data['deposit_history'] = []
            
        self.bot.db.data['processed_deposits'].append(tx_id)
        self.bot.db.data['deposit_history'].append({
            'tx_id': tx_id,
            'user_id': user_id,
            'ltc_amount': ltc_amount,
            'usd_amount': usd_amount,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.bot.db.data['processed_deposits']) > 1000:
            self.bot.db.data['processed_deposits'] = self.bot.db.data['processed_deposits'][-1000:]
        
        self.bot.db.save_data()
    
    async def generate_new_address_for_user(self, user_id):
        """Generate a new deposit address for the user after their deposit was processed."""
        try:
            address_data = await self.bot.generate_coinremitter_address(user_id)
            
            if address_data:
                user_data = self.bot.db.get_user(user_id)
                user_data['ltc_deposit_address'] = address_data.get('address')
                user_data['ltc_qr_code'] = address_data.get('qr_code')
                user_data['ltc_address_expires'] = address_data.get('expire_on')
                self.bot.db.update_user(user_id, user_data)
                self.bot.db.save_data()
                
                logger.info(f"Generated new deposit address for user {user_id}: {user_data['ltc_deposit_address']}")
            else:
                logger.warning(f"Could not generate new address for user {user_id}")
        except Exception as e:
            logger.error(f"Error generating new address for user {user_id}: {e}")
    
    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        logger.info(f"Webhook server started on port {self.port}")
