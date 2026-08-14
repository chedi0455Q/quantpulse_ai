import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
import pandas as pd
import ccxt.async_support as ccxt
import feedparser
import aiohttp

try:
    from tradingview_ta import TA_Handler, Interval
    TV_AVAILABLE = True
except (ImportError, ModuleNotFoundError, Exception):
    TV_AVAILABLE = False

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, ModuleNotFoundError, Exception):
    mt5 = None
    MT5_AVAILABLE = False

from config.settings import TARGET_ASSETS, settings

logger = logging.getLogger(__name__)

class DataFetcher:
    """Asynchronous data fetcher connected directly to TradingView, MetaTrader 5, CCXT & yfinance."""
    
    def __init__(self):
        self._ohlcv_cache: Dict[str, Any] = {}

        # 1. Initialize MetaTrader 5 if available (Windows OS)
        if MT5_AVAILABLE and mt5:
            try:
                if not mt5.initialize():
                    logger.error(f"Échec de l'initialisation de MetaTrader5: {mt5.last_error()}")
                else:
                    logger.info("MetaTrader 5 connecté avec succès!")
            except Exception as e:
                logger.warning(f"Erreur d'initialisation MT5: {e}")

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
        Fetch OHLCV dataframe directly connected to TradingView, MetaTrader 5, CCXT, or Yahoo Finance.
        """
        asset = TARGET_ASSETS.get(asset_key)
        if not asset:
            logger.error(f"Actif inconnu: {asset_key}")
            return None

        # 0. In-Memory Cache (15-second TTL for live real-time updates)
        cache_key = f"{asset_key}_{interval}"
        now = time.time()
        if cache_key in self._ohlcv_cache:
            cached_time, cached_df = self._ohlcv_cache[cache_key]
            if now - cached_time < 3:  # 3 seconds max TTL for ultra-low latency live ticks
                return cached_df.copy()

        # 1. DIRECT TRADINGVIEW SERVERS (Tous les 4 actifs : XAU, XAG, BTC, TSLA)
        tv_price = 0.0
        if TV_AVAILABLE:
            try:
                tv_map = {
                    "XAU": {"symbol": "GOLD", "screener": "cfd", "exchange": "TVC"},
                    "XAG": {"symbol": "SILVER", "screener": "cfd", "exchange": "TVC"},
                    "BTC": {"symbol": "BTCUSDT", "screener": "crypto", "exchange": "BINANCE"},
                    "TSLA": {"symbol": "TSLA", "screener": "america", "exchange": "NASDAQ"}
                }
                tv_cfg = tv_map.get(asset_key)
                if tv_cfg:
                    loop = asyncio.get_event_loop()
                    handler = TA_Handler(
                        symbol=tv_cfg["symbol"],
                        screener=tv_cfg["screener"],
                        exchange=tv_cfg["exchange"],
                        interval=Interval.INTERVAL_1_HOUR
                    )
                    analysis = await loop.run_in_executor(None, handler.get_analysis)
                    tv_price = float(analysis.indicators.get("close", 0.0))
            except Exception as e:
                logger.warning(f"Tentative TradingView directe échouée pour {asset_key}: {e}")

        # Fallback to historical fetchers
        df = await self._fetch_background_history(asset_key, period, interval)

        # Application du VRAI PRIX TRADINGVIEW EN DIRECT sur la bougie pour TOUS les actifs
        if df is not None and not df.empty and tv_price > 0:
            df.iloc[-1, df.columns.get_loc('close')] = tv_price
            logger.info(f"⚡ Prix TradingView Direct en direct appliqué pour {asset_key}: Prix = {tv_price}")

        if df is not None:
            self._ohlcv_cache[cache_key] = (now, df)
            return df
        return None

    async def _fetch_background_history(self, asset_key: str, period: str = "30d", interval: str = "1h") -> Optional[pd.DataFrame]:
        """Fetch historical candles from MT5, CCXT, or yfinance."""
        asset = TARGET_ASSETS.get(asset_key)

        # A. Crypto (BTC) via Binance CCXT
        if asset and asset.asset_type == "crypto" and asset.ccxt_symbol:
            try:
                timeframe_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
                tf = timeframe_map.get(interval, "1h")
                ohlcv = await self.binance.fetch_ohlcv(asset.ccxt_symbol, timeframe=tf, limit=150)
                if ohlcv:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df.set_index('timestamp', inplace=True)
                    return df
            except Exception:
                pass

        # B. Commodities & Stocks via MetaTrader 5 if available
        mt5_symbol_aliases = {
            "XAU": ["XAUUSD", "GOLD", "XAUUSD.a", "XAUUSD.m", "XAUUSD.ecn", "XAUUSD_i", "XAUUSD.r"],
            "XAG": ["XAGUSD", "SILVER", "XAGUSD.a", "XAGUSD.m"],
            "TSLA": ["TSLA"],
            "BTC": ["BTCUSD", "BTCUSDT"]
        }
        possible_symbols = mt5_symbol_aliases.get(asset_key, [asset_key])

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
                            return df[['open', 'high', 'low', 'close', 'volume']]
            except Exception as e:
                logger.warning(f"MT5 fallback warning: {e}")

        # C. Yahoo Finance Fallback
        yf_ticker_map = {
            "XAU": ["PAXG-USD", "GC=F"],
            "XAG": ["KAG-USD", "SI=F"],
            "BTC": ["BTC-USD", "BTC-USDT"],
            "TSLA": ["TSLA"]
        }
        yf_candidates = yf_ticker_map.get(asset_key, [asset_key])
        
        import yfinance as yf
        loop = asyncio.get_event_loop()

        for yf_symbol in yf_candidates:
            try:
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
                        return df
            except Exception:
                pass

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
