import asyncio
import logging
import sys
import time
from typing import Dict
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
