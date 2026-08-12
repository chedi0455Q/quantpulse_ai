import logging
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class GannQuantEngine:
    """
    Engine 2: Mathematical Analysis, W.D. Gann Strategies & Famous Quantitative Researchers.
    Evaluates:
      - W.D. Gann Angles (1x1 45°, 2x1, 1x2) & Gann Square of 9.
      - Jim Simons (Renaissance Technologies / Quant Stat Arb): Z-Score Mean Reversion & Stationarity.
      - Richard Wyckoff: Accumulation / Distribution Schematic (Spring vs UTAD).
      - Ralph Nelson Elliott: Elliott Wave Impulse & Corrective Phase Detection.
    """

    def analyze(self, df: pd.DataFrame, asset_key: str) -> Dict[str, Any]:
        """
        Runs mathematical & quantitative researcher analysis on an OHLCV DataFrame.
        """
        if df is None or len(df) < 30:
            return {
                "signal": "NEUTRAL",
                "score": 50.0,
                "gann_angles": {},
                "researchers": {},
                "reasons": ["Données insuffisantes pour les modèles mathématiques."]
            }

        df = df.copy()
        current_price = float(df['close'].iloc[-1])

        # 1. W.D. Gann Angle & Square of 9 Analysis
        gann_res = self._calculate_gann_square_and_angles(df)

        # 2. Jim Simons Quant Model (Z-Score & Mean Reversion)
        simons_res = self._jim_simons_quant_model(df)

        # 3. Richard Wyckoff Structural Model
        wyckoff_res = self._wyckoff_model(df)

        # 4. Ralph Nelson Elliott Wave Model
        elliott_res = self._elliott_wave_model(df)

        # 5. Composite Quantitative Score (0 - 100%)
        bullish_score = 0
        bearish_score = 0
        reasons = []

        # Gann Scoring
        if gann_res["bias"] == "BULLISH":
            bullish_score += 25
            reasons.append(f"Gann Angle 1x1 (45°) franchi à la hausse (Support à {gann_res['gann_1x1_support']:.2f})")
        elif gann_res["bias"] == "BEARISH":
            bearish_score += 25
            reasons.append(f"Gann Angle 1x1 (45°) franchi à la baisse (Résistance à {gann_res['gann_1x1_resistance']:.2f})")

        # Jim Simons Scoring
        if simons_res["signal"] == "BUY":
            bullish_score += 25
            reasons.append(f"Jim Simons Quant : Déviation Z-Score en survente ({simons_res['z_score']:.2f}) -> Signal d'arbitrage statistique haussier")
        elif simons_res["signal"] == "SELL":
            bearish_score += 25
            reasons.append(f"Jim Simons Quant : Déviation Z-Score en surachat ({simons_res['z_score']:.2f}) -> Signal d'arbitrage statistique baissier")

        # Wyckoff Scoring
        if wyckoff_res["phase"] in ["ACCUMULATION", "MARKUP"]:
            bullish_score += 25
            reasons.append(f"Richard Wyckoff : Phase d'Accumulation / Markup ({wyckoff_res['details']})")
        elif wyckoff_res["phase"] in ["DISTRIBUTION", "MARKDOWN"]:
            bearish_score += 25
            reasons.append(f"Richard Wyckoff : Phase de Distribution / Markdown ({wyckoff_res['details']})")

        # Elliott Wave Scoring
        if elliott_res["wave_type"] == "IMPULSE_WAVE_3":
            bullish_score += 25
            reasons.append("Ralph Nelson Elliott : Détection de la Vague 3 Impulsive Haussière (Phase la plus puissante)")
        elif elliott_res["wave_type"] == "CORRECTIVE_WAVE_C":
            bearish_score += 25
            reasons.append("Ralph Nelson Elliott : Vague C Corrective Baissière en cours")

        # Final Signal Determination
        if bullish_score > bearish_score and bullish_score >= 35:
            signal = "BUY"
            score = float(min(97.0, 50.0 + (bullish_score - bearish_score) * 0.7))
        elif bearish_score > bullish_score and bearish_score >= 35:
            signal = "SELL"
            score = float(min(97.0, 50.0 + (bearish_score - bullish_score) * 0.7))
        else:
            signal = "NEUTRAL"
            score = 50.0

        if not reasons:
            reasons.append("Consolidation selon la géométrie de Gann et les modèles quantitatifs.")

        return {
            "signal": signal,
            "score": round(score, 1),
            "current_price": round(current_price, 4 if current_price < 10 else 2),
            "gann_angles": gann_res,
            "researchers": {
                "jim_simons": simons_res,
                "wyckoff": wyckoff_res,
                "elliott_wave": elliott_res
            },
            "reasons": reasons
        }

    def _calculate_gann_square_and_angles(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        W.D. Gann Square of 9 & 1x1 45° Angle calculation.
        """
        recent = df.iloc[-30:]
        low_swing = float(recent['low'].min())
        high_swing = float(recent['high'].max())
        curr_price = float(df['close'].iloc[-1])

        # Gann 1x1 angle rate estimation
        time_elapsed = len(recent)
        angle_unit = (high_swing - low_swing) / (time_elapsed * 2)

        gann_1x1_support = low_swing + (angle_unit * time_elapsed)
        gann_1x1_resistance = high_swing - (angle_unit * time_elapsed)

        # Gann Square of 9 angles (90 deg = +sqrt(P)+0.5)^2, 180 deg = +1.0)^2
        sqrt_price = math.sqrt(curr_price)
        sq9_target_up = (sqrt_price + 0.5) ** 2
        sq9_target_down = (sqrt_price - 0.5) ** 2

        bias = "BULLISH" if curr_price >= gann_1x1_support else "BEARISH"

        return {
            "bias": bias,
            "gann_1x1_support": round(gann_1x1_support, 2),
            "gann_1x1_resistance": round(gann_1x1_resistance, 2),
            "sq9_target_up": round(sq9_target_up, 2),
            "sq9_target_down": round(sq9_target_down, 2)
        }

    def _jim_simons_quant_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Jim Simons / Renaissance Tech Stat Arb Z-Score Model.
        Calculates Z-score of price relative to 20-period SMA & StdDev.
        """
        sma20 = df['close'].rolling(20).mean()
        std20 = df['close'].rolling(20).std()
        z_score = float((df['close'].iloc[-1] - sma20.iloc[-1]) / (std20.iloc[-1] + 1e-9))

        if z_score < -1.8:
            signal = "BUY"
            desc = "Survente extrême statistique (Z < -1.8), retour à la moyenne haussier imminent."
        elif z_score > 1.8:
            signal = "SELL"
            desc = "Surachat extrême statistique (Z > +1.8), retour à la moyenne baissier imminent."
        else:
            signal = "NEUTRAL"
            desc = f"Z-score dans la zone normale ({z_score:.2f})."

        return {
            "signal": signal,
            "z_score": round(z_score, 2),
            "description": desc
        }

    def _wyckoff_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Richard Wyckoff Accumulation vs Distribution Phase Detection.
        """
        recent = df.iloc[-20:]
        vol_mean = recent['volume'].mean()
        last_vol = recent['volume'].iloc[-1]
        close_change = (recent['close'].iloc[-1] - recent['close'].iloc[-10]) / recent['close'].iloc[-10]

        if close_change < -0.02 and last_vol > vol_mean * 1.3:
            phase = "ACCUMULATION"
            details = "Chasse aux stop-loss & Accumulation institutionnelle sous fort volume (Spring)."
        elif close_change > 0.02 and last_vol > vol_mean * 1.3:
            phase = "MARKUP"
            details = "Phase d'Impulsion Haussière (Markup)."
        elif close_change > 0.02 and last_vol < vol_mean:
            phase = "DISTRIBUTION"
            details = "Distribution sous faible volume (UTAD / Épuisement)."
        else:
            phase = "CONSOLIDATION"
            details = "Équilibre entre offre et demande."

        return {
            "phase": phase,
            "details": details
        }

    def _elliott_wave_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Ralph Nelson Elliott Wave Pattern Estimation.
        """
        closes = df['close'].iloc[-15:].values
        diffs = np.diff(closes)

        up_moves = np.sum(diffs > 0)
        down_moves = np.sum(diffs < 0)

        if up_moves >= 10:
            wave_type = "IMPULSE_WAVE_3"
            desc = "Vague 3 Haussière (Impulsion maximale)"
        elif down_moves >= 10:
            wave_type = "CORRECTIVE_WAVE_C"
            desc = "Vague C Baissière (Correction en cours)"
        else:
            wave_type = "WAVE_CONSOLIDATION"
            desc = "Phase de construction d'onde de Elliott"

        return {
            "wave_type": wave_type,
            "description": desc
        }
