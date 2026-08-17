import logging
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from config.settings import settings, TARGET_ASSETS
from bot.formatters import MessageFormatter
from modules.data_fetcher import DataFetcher
from modules.strategy_engine import StrategyEngine
from modules.gann_quant_engine import GannQuantEngine
from modules.fundamental_engine import FundamentalEngine
from modules.trader_consensus_engine import TraderConsensusEngine
from modules.sentiment_analyzer import SentimentAnalyzer
from modules.decision_engine import DecisionEngine
from modules.chart_generator import ChartGenerator
from modules.mt5_executor import MT5Executor, mt5, MT5_AVAILABLE
from telegram.request import HTTPXRequest
logger = logging.getLogger(__name__)
# Conversation States for Interactive MT5 Setup
STATE_MT5_SERVER, STATE_MT5_LOGIN, STATE_MT5_PASSWORD = range(3)
