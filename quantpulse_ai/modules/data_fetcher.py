import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
import pandas as pd
import ccxt.async_support as ccxt
import feedparser
import aiohttp

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, ModuleNotFoundError, Exception):
    mt5 = None
    MT5_AVAILABLE = False

from config.settings import TARGET_ASSETS, settings

logger = logging.getLogger(__name__)

class DataFetcher:
    """Asynchronous data fetcher using MetaTrader 5 for Spot Assets, CCXT & yfinance with 3-min cache."""
    
    def __init__(self):
        self._ohlcv_cache: Dict[str, Any] = {}

        # 1. Initialize MetaTrader 5 if available (Windows OS)
        if MT5_AVAILABLE and mt5:
            try:
                if not mt5.initialize():
                    logger.error(f"Échec de l'initialisation de MetaTrader5, code d'erreur: {mt5.last_error()}")
                else:
                    logger.info("MetaTrader 5 connecté avec succès!")
            except Exception as e:
                logger.warning(f"Erreur d'initialisation MT5: {e}")
        else:
            logger.info("MetaTrader5 non disponible sur cet environnement (Linux/Cloud). Activation du secours automatique yfinance & CCXT.")

        # 2. Initialize Binance CCXT
        self.binance = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })

    async def close(self):
        """Close external clients and MetaTrader 5 connection."""
        try:
            await self.binance.close()
            if MT5_AVAILABLE and mt5:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
            logger.info("Connexions MT5 et CCXT fermées.")
        except Exception as e:
            logger.warning(f"Erreur lors de la fermeture des clients: {e}")

    async def fetch_ohlcv(self, asset_key: str, period: str = "30d", interval: str = "1h") -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV dataframe from MetaTrader 5, CCXT, or Yahoo Finance with 3-min cache.
        """
        asset = TARGET_ASSETS.get(asset_key)
        if not asset:
            logger.error(f"Actif inconnu: {asset_key}")
            return None

        # 0. In-Memory Cache (3-minute TTL to eliminate Rate Limiting)
        cache_key = f"{asset_key}_{interval}"
        now = time.time()
        if cache_key in self._ohlcv_cache:
            cached_time, cached_df = self._ohlcv_cache[cache_key]
            if now - cached_time < 180:  # 3 minutes
                return cached_df.copy()

        # A. Crypto (BTC) via Binance CCXT
        if asset.asset_type == "crypto" and asset.ccxt_symbol:
            try:
                timeframe_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
                tf = timeframe_map.get(interval, "1h")
                ohlcv = await self.binance.fetch_ohlcv(asset.ccxt_symbol, timeframe=tf, limit=150)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    self._ohlcv_cache[cache_key] = (now, df)
                    return df
            except Exception:
                logger.info(f"Passage automatique sur yfinance pour {asset_key} (Environnement Cloud).")

        # B. Commodities & Stocks (XAU, XAG, TSLA) via MetaTrader 5 (si disponible) + yfinance Fallback
        mt5_symbol_aliases = {
            "XAU": ["XAUUSD", "GOLD", "XAUUSD.a", "XAUUSD.m", "XAUUSD.ecn", "XAUUSD_i", "XAUUSD.r"],
            "XAG": ["XAGUSD", "SILVER", "XAGUSD.a", "XAGUSD.m"],
            "TSLA": ["TSLA"],
            "BTC": ["BTCUSD", "BTCUSDT"]
        }
        
        possible_symbols = mt5_symbol_aliases.get(asset_key, [asset_key])

        # 1. Try MT5 with Symbol Aliases if MT5 is available
        if MT5_AVAILABLE and mt5:
            try:
                tf_map = {
                    "15m": mt5.TIMEFRAME_M15,
                    "1h": mt5.TIMEFRAME_H1,
                    "4h": mt5.TIMEFRAME_H4,
                    "1d": mt5.TIMEFRAME_D1
                }
                timeframe = tf_map.get(interval, mt5.TIMEFRAME_H1)
                loop = asyncio.get_event_loop()
                for sym in possible_symbols:
                    if mt5.symbol_select(sym, True):
                        rates = await loop.run_in_executor(
                            None, 
                            lambda s=sym: mt5.copy_rates_from_pos(s, timeframe, 0, 150)
                        )
                        if rates is not None and len(rates) > 0:
                            df = pd.DataFrame(rates)
                            df['timestamp'] = pd.to_datetime(df['time'], unit='s')
                            df.set_index('timestamp', inplace=True)
                            df = df.rename(columns={'tick_volume': 'volume'})
                            df = df[['open', 'high', 'low', 'close', 'volume']]
                            logger.info(f"✅ Données récupérées avec succès sur MT5 pour {asset_key} (Symbole: {sym})")
                            self._ohlcv_cache[cache_key] = (now, df)
                            return df
            except Exception as e:
                logger.warning(f"Erreur lors de la tentative MT5 pour {asset_key}: {e}")

        # 2. Secours Automatique multi-tickers via yfinance
        yf_ticker_map = {
            "XAU": ["GC=F", "GLD", "IAU", "XAUUSD=X"],
            "XAG": ["SI=F", "SLV", "XAGUSD=X"],
            "BTC": ["BTC-USD", "BTC-USDT"],
            "TSLA": ["TSLA"]
        }
        yf_candidates = yf_ticker_map.get(asset_key, [asset_key])
        
        import yfinance as yf
        loop = asyncio.get_event_loop()

        for yf_symbol in yf_candidates:
            try:
                logger.info(f"🔄 Recours yfinance pour {asset_key} (Ticker: {yf_symbol})...")
                ticker_obj = yf.Ticker(yf_symbol)
                df = await loop.run_in_executor(
                    None, 
                    lambda s=ticker_obj: s.history(period=period, interval=interval)
                )
                if df is not None and not df.empty:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df = df.rename(columns={
                        'Open': 'open', 'High': 'high', 'Low': 'low', 
                        'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
                    })
                    df = df[['open', 'high', 'low', 'close', 'volume']].dropna()
                    if not df.empty and len(df) >= 10:
                        logger.info(f"✅ Données récupérées avec succès via yfinance pour {asset_key} ({yf_symbol})")
                        self._ohlcv_cache[cache_key] = (now, df)
                        return df
            except Exception as e:
                logger.warning(f"Ticker yfinance {yf_symbol} indisponible: {e}")

        logger.error(f"❌ Échec total de la récupération des données de marché pour {asset_key}")
        return None

    async def fetch_rss_news(self, custom_urls: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch and aggregate RSS news items."""
        urls = custom_urls or settings.RSS_FEEDS
        articles = []
        
        async with aiohttp.ClientSession(headers={"User-Agent": "QuantPulseAI/1.0"}) as session:
            tasks = [self._fetch_feed(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, list):
                    articles.extend(res)

        return articles[:30]

    async def _fetch_feed(self, session: aiohttp.ClientSession, url: str) -> List[Dict[str, Any]]:
        """Fetch a single RSS feed asynchronously."""
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as response:
                if response.status == 200:
                    text = await response.text()
                    feed = feedparser.parse(text)
                    items = []
                    for entry in feed.entries[:10]:
                        items.append({
                            "title": entry.get("title", ""),
                            "summary": entry.get("summary", entry.get("description", "")),
                            "link": entry.get("link", ""),
                            "published": entry.get("published", entry.get("updated", "")),
                            "source": feed.feed.get("title", url)
                        })
                    return items
        except Exception as e:
            logger.debug(f"Failed to fetch RSS feed {url}: {e}")
        return []
