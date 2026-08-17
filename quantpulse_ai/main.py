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
