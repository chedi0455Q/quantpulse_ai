import asyncio
import logging
import sys
import time
import datetime
from typing import Dict, Any, Set
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

from config.settings import settings, TARGET_ASSETS
from bot.telegram_bot import QuantPulseBot
from bot.formatters import MessageFormatter

# Configure Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("QuantPulseAI")

bot_instance = QuantPulseBot()
LAST_SENT_SIGNALS: Dict[str, float] = {}

# Cadence & Anti-Doublon Stricte (1 à 4 trades max / jour, 0 doublon)
DAILY_TRADES_RECORD: Dict[str, Any] = {
    "date": str(datetime.date.today()),
    "count": 0
}
SENT_SIGNAL_IDS: Set[str] = set()

async def start_auto_scanner():
    """
    Boucle asynchrone de scan automatique du marché en arrière-plan.
    Contrôle strict : Seuil ≥ 75%, 1 à 4 transactions max par jour, Anti-doublon strict.
    """
    logger.info(f"🚀 Démarrage du Scanner Automatique QuantPulse AI (Intervalle: {settings.SCAN_INTERVAL_SECONDS}s, Seuil: {settings.CONFIDENCE_THRESHOLD}%)...")
    await asyncio.sleep(5)  # Attente initiale de démarrage

    while True:
        try:
            today_str = str(datetime.date.today())
            if DAILY_TRADES_RECORD["date"] != today_str:
                DAILY_TRADES_RECORD["date"] = today_str
                DAILY_TRADES_RECORD["count"] = 0
                SENT_SIGNAL_IDS.clear()

            # Limite maximale de 4 transactions par jour
            if DAILY_TRADES_RECORD["count"] >= 4:
                logger.info(f"ℹ️ Limite quotidienne de 4 transactions atteinte ({DAILY_TRADES_RECORD['count']}/4). Scan automatique en pause jusqu'à demain.")
                await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
                continue

            if settings.AUTO_SIGNALS_ENABLED and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                logger.info("🔍 Scan du marché en cours pour la détection de signaux d'élite...")
                scanner_assets = [k for k in TARGET_ASSETS.keys() if k != "SPACEX"]
                
                for asset_key in scanner_assets:
                    if not bot_instance.decision_engine.is_market_open(asset_key):
                        logger.info(f"ℹ️ Marché {asset_key} fermé actuellement (Hors heures officielles de bourse). Scan automatique ignoré.")
                        continue

                    eval_data = await bot_instance.run_single_asset_analysis(asset_key)
                    await asyncio.sleep(3.0)  # Pause 3.0s pour éviter tout rate-limit 429 sur Render

                    if eval_data:
                        conf = eval_data.get("combined_score", 0.0)
                        action = eval_data.get("final_action", "NEUTRAL")
                        has_high_conf = eval_data.get("has_high_confidence", False)
                        price = eval_data.get("price", 0.0)
                        
                        logger.info(f"📊 Actif: {asset_key} | Score Combiné: {conf:.1f}% | Action: {action} | HighConf: {has_high_conf}")

                        # Condition de déclenchement d'Alerte : Score >= 75% et signal ACHAT/VENTE
                        if (conf >= 75.0 or has_high_conf) and action in ["BUY", "SELL"]:
                            # 1. Anti-Doublon Strict par ID unique d'opportunité
                            signal_id = f"{asset_key}_{action}_{round(price, 1)}"
                            if signal_id in SENT_SIGNAL_IDS:
                                logger.info(f"⏳ Signal {signal_id} déjà envoyé précédemment. Anti-doublon strict actif.")
                                continue

                            # 2. Verrou de sécurité 4h entre signaux pour le même actif
                            last_sent_time = LAST_SENT_SIGNALS.get(asset_key, 0.0)
                            if time.time() - last_sent_time < 14400:  # 4h (14400 secondes)
                                logger.info(f"⏳ Signal Intraday actif pour {asset_key}. Verrou 4h actif.")
                                continue

                            alert_text = MessageFormatter.format_signal_alert(eval_data)
                            keyboard = bot_instance.get_signal_keyboard(asset_key)
                            
                            try:
                                # Génération automatique du Graphique PNG avec schéma LONG / SHORT
                                df = await bot_instance.data_fetcher.fetch_ohlcv(asset_key, period="10d", interval="1h")
                                chart_buf = None
                                if df is not None and not df.empty:
                                    df['rsi'] = bot_instance.strategy_engine._calculate_rsi(df['close'])
                                    chart_buf = bot_instance.chart_generator.generate_signal_chart(
                                        df,
                                        TARGET_ASSETS[asset_key].name,
                                        eval_data["tp1"],
                                        eval_data["tp2"],
                                        eval_data["sl"],
                                        eval_data["final_action"]
                                    )

                                sent_ok = False
                                if chart_buf and bot_instance.app and bot_instance.app.bot:
                                    await bot_instance.app.bot.send_photo(
                                        chat_id=settings.TELEGRAM_CHAT_ID,
                                        photo=chart_buf,
                                        caption=alert_text,
                                        reply_markup=keyboard,
                                        parse_mode="Markdown"
                                    )
                                    sent_ok = True
                                    logger.info(f"🚨 Alerte signal + Photo Graphique PNG envoyée avec succès pour {asset_key} ({action}) !")
                                elif bot_instance.app and bot_instance.app.bot:
                                    await bot_instance.app.bot.send_message(
                                        chat_id=settings.TELEGRAM_CHAT_ID,
                                        text=alert_text,
                                        reply_markup=keyboard,
                                        parse_mode="Markdown"
                                    )
                                    sent_ok = True
                                    logger.info(f"🚨 Alerte signal texte envoyée avec succès pour {asset_key} ({action}) !")

                                if sent_ok:
                                    # Enregistrement anti-doublon & incrément compteur quotidien
                                    LAST_SENT_SIGNALS[asset_key] = time.time()
                                    SENT_SIGNAL_IDS.add(signal_id)
                                    DAILY_TRADES_RECORD["count"] += 1
                                    logger.info(f"📈 Transaction enregistrée ({DAILY_TRADES_RECORD['count']}/4 trades aujourd'hui).")

                                # Exécution Automatique 100% Autonome sur MetaTrader 5 (si Auto-Trader actif)
                                try:
                                    trade_res = bot_instance.mt5_executor.execute_auto_trade(eval_data)
                                    if trade_res.get("success"):
                                        exec_msg = (
                                            f"🤖 **ORDRE AUTOMATIQUE EXÉCUTÉ SUR METATRADER 5 !**\n\n"
                                            f"• **Ticket # :** `{trade_res['ticket']}`\n"
                                            f"• **Symbole :** `{trade_res['symbol']}`\n"
                                            f"• **Action :** `{trade_res['action']}`\n"
                                            f"• **Lot :** `{trade_res['lot']}`\n"
                                            f"• **Prix d'Entrée :** `{trade_res['price']}`\n"
                                            f"• **Take Profit 2 (Ratio 1:3) :** `{trade_res['tp']}`\n"
                                            f"• **Stop Loss :** `{trade_res['sl']}`"
                                        )
                                        if bot_instance.app and bot_instance.app.bot:
                                            await bot_instance.app.bot.send_message(
                                                chat_id=settings.TELEGRAM_CHAT_ID,
                                                text=exec_msg,
                                                parse_mode="Markdown"
                                            )
                                except Exception as e_trade:
                                    logger.warning(f"Note exécution MT5: {e_trade}")
                            except Exception as e:
                                logger.error(f"❌ Échec de l'envoi de l'alerte Telegram pour {asset_key}: {e}")

        except Exception as e:
            logger.error(f"❌ Erreur dans la boucle du scanner automatique: {e}", exc_info=True)

        await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan manager pour démarrer le bot Telegram et la tâche d'arrière-plan du scanner."""
    logger.info("Initialisation de l'application QuantPulse AI...")
    
    # Construction de l'application Bot Telegram
    telegram_app = bot_instance.build_application()
    scanner_task = None

    if telegram_app:
        try:
            await telegram_app.initialize()
            await telegram_app.start()
            try:
                await telegram_app.bot.delete_webhook(drop_pending_updates=True)
            except Exception:
                pass
            await telegram_app.updater.start_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=True)
            logger.info("✅ Bot Telegram démarré et en écoute (Polling).")
        except Exception as e:
            logger.error(f"⚠️ Remarque connexion Telegram : {e}")
        
        # Démarrage de la boucle du scanner en tâche d'arrière-plan
        scanner_task = asyncio.create_task(start_auto_scanner())

    yield  # Serveur FastAPI en cours d'exécution

    logger.info("Arrêt de l'application QuantPulse AI...")
    if scanner_task:
        scanner_task.cancel()
    if telegram_app and telegram_app.updater and telegram_app.updater.running:
        try:
            await telegram_app.updater.stop()
            await telegram_app.stop()
            await telegram_app.shutdown()
        except Exception as e:
            logger.warning(f"Erreur lors de l'arrêt du bot: {e}")
    await bot_instance.data_fetcher.close()


app = FastAPI(
    title="QuantPulse AI Market Intelligence API",
    version="1.0.0",
    description="Bot Telegram & API d'analyse quantitative multi-modale en temps réel.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "QuantPulse AI",
        "supported_assets": list(TARGET_ASSETS.keys()),
        "confidence_threshold": settings.CONFIDENCE_THRESHOLD,
        "auto_signals_enabled": settings.AUTO_SIGNALS_ENABLED
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/analyze/{asset_key}")
async def analyze_asset_endpoint(asset_key: str):
    """REST endpoint pour le diagnostic instantané d'un actif."""
    key = asset_key.upper()
    if key not in TARGET_ASSETS:
        return {"error": f"Invalid asset key. Choose from {list(TARGET_ASSETS.keys())}"}
    
    if key == "SPACEX":
        news = await bot_instance.data_fetcher.fetch_rss_news()
        return await bot_instance.sentiment_analyzer.analyze_spacex_impact(news)
    
    res = await bot_instance.run_single_asset_analysis(key)
    return res or {"error": "Failed to fetch market data"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=False)
