import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class StrategyEngine:
    """
    Engine 1: SMC (Smart Money Concepts), ICT (Inner Circle Trader) & Advanced Technical Analysis.
    Detects Fair Value Gaps (FVG), Liquidity Pools (BSL/SSL), Optimal Trade Entry (OTE), Order Blocks (OB),
    Market Structure Shift (MSS), Change of Character (ChoCh), RSI, MACD, and ATR dynamic SL/TP for Day Trading.
    """

    def analyze(self, df: pd.DataFrame, asset_key: str) -> Dict[str, Any]:
        """
        Runs full SMC / ICT & Technical strategy analysis on an OHLCV DataFrame.
        Returns a dict containing signal type, SMC/ICT score (0-100), key prices, TP/SL, and detailed breakdown.
        """
        if df is None or len(df) < 30:
            return {
                "signal": "NEUTRAL",
                "score": 50.0,
                "current_price": 0.0,
                "tp1": 0.0,
                "tp2": 0.0,
                "sl": 0.0,
                "details": {"error": "Données de marché insuffisantes."}
            }

        df = df.copy()

        # 1. Technical Indicators
        df['rsi'] = self._calculate_rsi(df['close'], period=14)
        df['macd'], df['macd_signal'], df['macd_hist'] = self._calculate_macd(df['close'])
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['ema200'] = df['close'].ewm(span=200, adjust=False).mean() if len(df) >= 200 else df['close'].ewm(span=len(df), adjust=False).mean()
        df['atr'] = self._calculate_atr(df, period=14)

        current_price = float(df['close'].iloc[-1])
        current_rsi = float(df['rsi'].iloc[-1])
        current_macd_hist = float(df['macd_hist'].iloc[-1])
        current_atr = float(df['atr'].iloc[-1]) if not np.isnan(df['atr'].iloc[-1]) else current_price * 0.01

        # 2. ICT / SMC Core Modules
        fvg_info = self._detect_fair_value_gaps(df)
        liquidity_info = self._detect_liquidity_pools(df)
        ote_info = self._calculate_ote_fibonacci(df)
        choch_info = self._detect_choch_mss(df)
        order_blocks = self._detect_order_blocks(df)

        # 3. Scoring System (0 - 100%)
        bullish_points = 0
        bearish_points = 0
        reasons = []

        # A. ICT Fair Value Gaps (Weight: 20)
        if fvg_info.get("bullish_fvg"):
            bullish_points += 20
            reasons.append(f"FVG Haussier actif (Fair Value Gap entre {fvg_info['bullish_fvg'][0]:.2f} et {fvg_info['bullish_fvg'][1]:.2f})")
        elif fvg_info.get("bearish_fvg"):
            bearish_points += 20
            reasons.append(f"FVG Baissier actif (Fair Value Gap entre {fvg_info['bearish_fvg'][0]:.2f} et {fvg_info['bearish_fvg'][1]:.2f})")

        # B. ICT Liquidity Sweeps (Weight: 20)
        if liquidity_info.get("ssl_swept"):
            bullish_points += 20
            reasons.append("Chasse aux liquidités vendedrices (SSL Swept) -> Balayage sous les bas récents")
        elif liquidity_info.get("bsl_swept"):
            bearish_points += 20
            reasons.append("Chasse aux liquidités acheteuses (BSL Swept) -> Balayage sous les hauts récents")

        # C. ICT OTE Zone (Optimal Trade Entry 61.8% - 78.6%) (Weight: 20)
        if ote_info.get("in_bullish_ote"):
            bullish_points += 20
            reasons.append(f"Zone OTE Haussière ICT atteinte (Fib 61.8%-78.6% à {ote_info['ote_low']:.2f}-{ote_info['ote_high']:.2f})")
        elif ote_info.get("in_bearish_ote"):
            bearish_points += 20
            reasons.append(f"Zone OTE Baissière ICT atteinte (Fib 61.8%-78.6% à {ote_info['ote_low']:.2f}-{ote_info['ote_high']:.2f})")

        # D. SMC Order Blocks & ChoCh/MSS (Weight: 25)
        if choch_info == "BULLISH_MSS":
            bullish_points += 25
            reasons.append("Market Structure Shift (MSS) Haussier / ChoCh validé")
        elif choch_info == "BEARISH_MSS":
            bearish_points += 25
            reasons.append("Market Structure Shift (MSS) Baissier / ChoCh validé")

        if order_blocks.get("bullish_ob") and abs(current_price - order_blocks["bullish_ob"]) / current_price < 0.015:
            bullish_points += 15
            reasons.append("Support sur Order Block Haussier SMC")
        elif order_blocks.get("bearish_ob") and abs(current_price - order_blocks["bearish_ob"]) / current_price < 0.015:
            bearish_points += 15
            reasons.append("Résistance sur Order Block Baissier SMC")

        # E. Technical Confluence (RSI & MACD) (Weight: 15)
        if current_rsi < 35:
            bullish_points += 15
            reasons.append(f"RSI en survente ({current_rsi:.1f})")
        elif current_rsi > 65:
            bearish_points += 15
            reasons.append(f"RSI en surachat ({current_rsi:.1f})")

        if current_macd_hist > 0:
            bullish_points += 10
        elif current_macd_hist < 0:
            bearish_points += 10

        # Signal & Score Calculation
        if bullish_points > bearish_points and bullish_points >= 35:
            signal = "BUY"
            score = float(min(98.0, 50.0 + (bullish_points - bearish_points) * 0.65))
        elif bearish_points > bullish_points and bearish_points >= 35:
            signal = "SELL"
            score = float(min(98.0, 50.0 + (bearish_points - bullish_points) * 0.65))
        else:
            signal = "NEUTRAL"
            score = 50.0

        if not reasons:
            reasons.append("Structure de marché en consolidation neutre.")

        # Day Trading TP / SL calculation via ATR & Order Blocks / Key Swings
        if signal == "BUY":
            sl = current_price - (1.5 * current_atr)
            if order_blocks.get("bullish_ob") and order_blocks["bullish_ob"] < current_price:
                sl = max(sl, order_blocks["bullish_ob"] - (0.2 * current_atr))
            tp1 = current_price + (1.5 * current_atr)
            tp2 = current_price + (3.0 * current_atr)
        elif signal == "SELL":
            sl = current_price + (1.5 * current_atr)
            if order_blocks.get("bearish_ob") and order_blocks["bearish_ob"] > current_price:
                sl = min(sl, order_blocks["bearish_ob"] + (0.2 * current_atr))
            tp1 = current_price - (1.5 * current_atr)
            tp2 = current_price - (3.0 * current_atr)
        else:
            sl = current_price - (1.0 * current_atr)
            tp1 = current_price + (1.0 * current_atr)
            tp2 = current_price + (2.0 * current_atr)

        return {
            "signal": signal,
            "score": round(score, 1),
            "current_price": round(current_price, 4 if current_price < 10 else 2),
            "tp1": round(tp1, 4 if tp1 < 10 else 2),
            "tp2": round(tp2, 4 if tp2 < 10 else 2),
            "sl": round(sl, 4 if sl < 10 else 2),
            "rsi": round(current_rsi, 1),
            "atr": round(current_atr, 4),
            "reasons": reasons,
            "details": {
                "fvg": fvg_info,
                "liquidity": liquidity_info,
                "ote": ote_info,
                "choch_mss": choch_info,
                "order_blocks": order_blocks,
                "ema20": round(float(df['ema20'].iloc[-1]), 2),
                "ema50": round(float(df['ema50'].iloc[-1]), 2),
                "ema200": round(float(df['ema200'].iloc[-1]), 2)
            }
        }

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        """Standard RSI calculation."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss.replace(0, 1e-9))
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Standard MACD calculation."""
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Average True Range calculation."""
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _detect_fair_value_gaps(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        ICT Fair Value Gap (FVG) detection over recent candles.
        Bullish FVG: High of candle 1 < Low of candle 3.
        Bearish FVG: Low of candle 1 > High of candle 3.
        """
        bullish_fvg = None
        bearish_fvg = None

        if len(df) < 5:
            return {"bullish_fvg": bullish_fvg, "bearish_fvg": bearish_fvg}

        for i in range(len(df) - 2, len(df) - 10, -1):
            if i < 2:
                break
            c1_high = df['high'].iloc[i-2]
            c1_low = df['low'].iloc[i-2]
            c3_high = df['high'].iloc[i]
            c3_low = df['low'].iloc[i]

            # Bullish FVG
            if c3_low > c1_high:
                bullish_fvg = (round(float(c1_high), 2), round(float(c3_low), 2))
                break

            # Bearish FVG
            if c3_high < c1_low:
                bearish_fvg = (round(float(c3_high), 2), round(float(c1_low), 2))
                break

        return {"bullish_fvg": bullish_fvg, "bearish_fvg": bearish_fvg}

    def _detect_liquidity_pools(self, df: pd.DataFrame) -> Dict[str, bool]:
        """
        ICT Liquidity Sweeps (BSL - Buy Side Liquidity, SSL - Sell Side Liquidity).
        Detects if current bar swept previous swing high/low and closed back inside.
        """
        if len(df) < 15:
            return {"bsl_swept": False, "ssl_swept": False}

        swing_highs = df['high'].iloc[-15:-2].max()
        swing_lows = df['low'].iloc[-15:-2].min()

        curr_high = df['high'].iloc[-1]
        curr_low = df['low'].iloc[-1]
        curr_close = df['close'].iloc[-1]

        # BSL Swept: High breaks swing high but Close closes below swing high
        bsl_swept = bool(curr_high > swing_highs and curr_close < swing_highs)

        # SSL Swept: Low breaks swing low but Close closes above swing low
        ssl_swept = bool(curr_low < swing_lows and curr_close > swing_lows)

        return {"bsl_swept": bsl_swept, "ssl_swept": ssl_swept}

    def _calculate_ote_fibonacci(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        ICT Optimal Trade Entry (OTE) Fib Retracement 61.8% to 78.6%.
        """
        if len(df) < 20:
            return {"in_bullish_ote": False, "in_bearish_ote": False, "ote_low": 0, "ote_high": 0}

        recent = df.iloc[-25:]
        min_price = float(recent['low'].min())
        max_price = float(recent['high'].max())
        curr_price = float(df['close'].iloc[-1])
        diff = max_price - min_price

        if diff == 0:
            return {"in_bullish_ote": False, "in_bearish_ote": False, "ote_low": 0, "ote_high": 0}

        # Fib levels from low to high (Bullish Retracement)
        fib_618 = max_price - (diff * 0.618)
        fib_786 = max_price - (diff * 0.786)

        in_bullish_ote = bool(fib_786 <= curr_price <= fib_618)

        # Fib levels from high to low (Bearish Retracement)
        bear_fib_618 = min_price + (diff * 0.618)
        bear_fib_786 = min_price + (diff * 0.786)

        in_bearish_ote = bool(bear_fib_618 <= curr_price <= bear_fib_786)

        return {
            "in_bullish_ote": in_bullish_ote,
            "in_bearish_ote": in_bearish_ote,
            "ote_low": round(fib_786, 2),
            "ote_high": round(fib_618, 2)
        }

    def _detect_choch_mss(self, df: pd.DataFrame) -> str:
        """Detect Change of Character (ChoCh) / Market Structure Shift (MSS)."""
        if len(df) < 20:
            return "NONE"

        recent_highs = df['high'].iloc[-20:-3].max()
        recent_lows = df['low'].iloc[-20:-3].min()
        curr_close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]

        if curr_close > recent_highs and prev_close <= recent_highs:
            return "BULLISH_MSS"
        elif curr_close < recent_lows and prev_close >= recent_lows:
            return "BEARISH_MSS"

        return "NONE"

    def _detect_order_blocks(self, df: pd.DataFrame) -> Dict[str, Optional[float]]:
        """Identify recent SMC Bullish and Bearish Order Blocks."""
        bullish_ob = None
        bearish_ob = None

        if len(df) < 15:
            return {"bullish_ob": bullish_ob, "bearish_ob": bearish_ob}

        for i in range(len(df) - 3, len(df) - 12, -1):
            c_open = df['open'].iloc[i]
            c_close = df['close'].iloc[i]
            c_low = df['low'].iloc[i]
            c_high = df['high'].iloc[i]

            if c_close < c_open and (df['close'].iloc[i+2] - c_close) / c_close > 0.01:
                bullish_ob = float(c_low)
                break

            if c_close > c_open and (c_close - df['close'].iloc[i+2]) / c_close > 0.01:
                bearish_ob = float(c_high)
                break

        return {"bullish_ob": bullish_ob, "bearish_ob": bearish_ob}
