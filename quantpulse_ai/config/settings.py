import os
from typing import Dict, List, Any
from pydantic_settings import BaseSettings, SettingsConfigDict

class AssetConfig:
    """Structure for asset configuration metadata."""
    def __init__(self, key: str, name: str, emoji: str, asset_type: str, yf_ticker: str, ccxt_symbol: str = None):
        self.key = key
        self.name = name
        self.emoji = emoji
        self.asset_type = asset_type  # 'commodity', 'crypto', 'stock', 'private'
        self.yf_ticker = yf_ticker
        self.ccxt_symbol = ccxt_symbol

# Symboles optimisés pour MetaTrader 5 et Binance CCXT
TARGET_ASSETS: Dict[str, AssetConfig] = {
    "XAU": AssetConfig("XAU", "Or (XAU/USD)", "🥇", "commodity", "XAUUSD"),
    "XAG": AssetConfig("XAG", "Argent (XAG/USD)", "🥈", "commodity", "XAGUSD"),
    "BTC": AssetConfig("BTC", "Bitcoin (BTC/USDT)", "₿", "crypto", "BTCUSD", "BTC/USDT"),
    "TSLA": AssetConfig("TSLA", "Tesla (TSLA)", "🚗", "stock", "TSLA"),
    "SPACEX": AssetConfig("SPACEX", "SpaceX (Flux Privé)", "🚀", "private", "TSLA"),
}

DEFAULT_RSS_FEEDS: List[str] = [
    "https://www.boursorama.com/rss/actualites/marches/",
    "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    "https://cointelegraph.com/rss",
    "https://news.google.com/rss/search?q=SpaceX+Tesla&hl=fr&gl=FR&ceid=FR:fr",
    "https://news.google.com/rss/search?q=Gold+XAU+Fed&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Bitcoin+USDT+liquidation&hl=en-US&gl=US&ceid=US:en",
]

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""  # ID de ton compte/canal Telegram pour recevoir les alertes directes
    
    # AI APIs
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Market APIs
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    
    # Scanner & Automated Signal Settings
    SCAN_INTERVAL_SECONDS: int = 60       # Intervalle de scan automatique (en secondes)
    CONFIDENCE_THRESHOLD: float = 70.0    # Seuil minimal de confiance pour envoyer une alerte (%)
    AUTO_SIGNALS_ENABLED: bool = True     # Activation du moteur de signaux automatiques
    
    # RSS News Feeds
    RSS_FEEDS: List[str] = DEFAULT_RSS_FEEDS
    
    # App Settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()