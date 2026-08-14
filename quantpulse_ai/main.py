import asyncio
import logging
import sys
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

async def start_auto_scanner():
    """
    Boucle asynchrone de scan automatique du marché en arrière-plan.
    Surveille en continu les actifs et envoie une alerte Telegram directe avec la photo du graphique PNG
    dès qu'un signal d'achat (LONG) ou de vente (SHORT) dépasse le seuil de confiance de 70%.
    """
    logger.info(f"🚀 Démarrage du Scanner Automatique QuantPulse AI (Intervalle: {settings.SCAN_INTERVAL_SECONDS}s, Seuil: {settings.CONFIDENCE_THRESHOLD}%)...")
    await asyncio.sleep(5)  # Attente initiale de démarrage

    while True:
        try:
            if settings.AUTO_SIGNALS_ENABLED and settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                logger.info("🔍 Scan du marché en cours pour la détection de signaux...")
                scanner_assets = [k for k in TARGET_ASSETS.keys() if k != "SPACEX"]
                
                for asset_key in scanner_assets:
                    if not bot_instance.decision_engine.is_market_open(asset_key):
                        logger.info(f"ℹ️ Marché {asset_key} fermé actuellement (Hors heures officielles de bourse). Scan automatique ignoré.")
                        continue

                    eval_data = await bot_instance.run_single_asset_analysis(asset_key)
                    await asyncio.sleep(1.5)  # Pause anti rate-limit Yahoo Finance
                    if eval_data:
                        conf = eval_data.get("combined_score", 0.0)
                        action = eval_data.get("final_action", "NEUTRAL")
                        has_high_conf = eval_data.get("has_high_confidence", False)
                        
                        logger.info(f"📊 Actif: {asset_key} | Score Combiné: {conf:.1f}% | Action: {action} | HighConf: {has_high_conf}")

                        # Envoi de l'alerte Telegram avec PHOTO du Graphique si score >= 75% et signal ACHAT/VENTE
                        if (conf >= 75.0 or has_high_conf) and action in ["BUY", "SELL"]:
                            # Verrou de Signal Intraday (Attente 4h entre chaque alerte automatique pour éviter tout spam)
                            last_sent_time = LAST_SENT_SIGNALS.get(asset_key, 0.0)
                            if time.time() - last_sent_time < 14400:  # 4h (14400 secondes)
                                logger.info(f"⏳ Signal Intraday actif pour {asset_key}. Verrou 4h actif (Aucun spam de TP/SL).")
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

                                if chart_buf and bot_instance.app and bot_instance.app.bot:
                                    await bot_instance.app.bot.send_photo(
                                        chat_id=settings.TELEGRAM_CHAT_ID,
                                        photo=chart_buf,
                                        caption=alert_text,
                                        reply_markup=keyboard,
                                        parse_mode="Markdown"
                                    )
                                    LAST_SENT_SIGNALS[asset_key] = time.time()
                                    logger.info(f"🚨 Alerte signal + Photo Graphique PNG envoyée avec succès sur Telegram pour {asset_key} ({action}) !")
                                elif bot_instance.app and bot_instance.app.bot:
                                    await bot_instance.app.bot.send_message(
                                        chat_id=settings.TELEGRAM_CHAT_ID,
                                        text=alert_text,
                                        reply_markup=keyboard,
                                        parse_mode="Markdown"
                                    )
                                    LAST_SENT_SIGNALS[asset_key] = time.time()
                                    logger.info(f"🚨 Alerte signal texte envoyée avec succès pour {asset_key} ({action}) !")
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

