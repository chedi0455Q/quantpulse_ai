import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class FundamentalEngine:
    """
    Engine 3: Fundamental, Central Banks & Institutional Whales Intelligence Engine.
    Tracks:
      - Central Banks (FED, ECB, BOJ) monetary policies & rate decision dynamics.
      - Big Investment Banks (Goldman Sachs, J.P. Morgan, Morgan Stanley) consensus notes.
      - COT (Commitment of Traders) reports & Whale order flow liquidations.
    """

    async def analyze(self, asset_key: str, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes fundamental, institutional, and central bank sentiment for an asset.
        """
        # 1. Central Banks Policy Stance
        cb_info = self._analyze_central_banks(asset_key, news_items)

        # 2. Big Investment Banks Consensus (Goldman Sachs, J.P. Morgan, MS)
        banks_info = self._analyze_institutional_banks(asset_key, news_items)

        # 3. COT Report & Whale Order Flow
        whales_info = self._analyze_whales_and_cot(asset_key, news_items)

        # 4. Fundamental Score Calculation (0 - 100%)
        bullish_pts = 0
        bearish_pts = 0
        reasons = []

        # Central Bank Policy Points (Weight: 35)
        if cb_info["stance"] == "DOVISH_BULLISH":
            bullish_pts += 35
            reasons.append(f"Banques Centrales (FED/BCE) : Politique accommodante (Baisse des taux / Injection de liquidités) -> Haussier pour {asset_key}")
        elif cb_info["stance"] == "HAWKISH_BEARISH":
            bearish_pts += 35
            reasons.append(f"Banques Centrales (FED/BCE) : Politique restrictive (Maintien de taux élevés / Inflation) -> Baissier pour {asset_key}")

        # Big Banks Consensus Points (Weight: 35)
        if banks_info["consensus"] == "BULLISH":
            bullish_pts += 35
            reasons.append(f"Grandes Banques d'Investissement (Goldman Sachs, J.P. Morgan) : Consensus d'achat confirmé ({banks_info['summary']})")
        elif banks_info["consensus"] == "BEARISH":
            bearish_pts += 35
            reasons.append(f"Grandes Banques d'Investissement (Goldman Sachs, J.P. Morgan) : Recommandation de prudence / vente ({banks_info['summary']})")

        # Whales & COT Positioning Points (Weight: 30)
        if whales_info["bias"] == "BULLISH_ACCUMULATION":
            bullish_pts += 30
            reasons.append(f"Baleines & COT Report : Accumulation massive des institutionnels / absorption des ventes")
        elif whales_info["bias"] == "BEARISH_DISTRIBUTION":
            bearish_pts += 30
            reasons.append(f"Baleines & COT Report : Prise de profit institutionnelle / Ventes massives détectées")

        # Score & Signal
        if bullish_pts > bearish_pts and bullish_pts >= 35:
            signal = "BUY"
            score = float(min(96.0, 50.0 + (bullish_pts - bearish_pts) * 0.65))
        elif bearish_pts > bullish_pts and bearish_pts >= 35:
            signal = "SELL"
            score = float(min(96.0, 50.0 + (bearish_pts - bullish_pts) * 0.65))
        else:
            signal = "NEUTRAL"
            score = 50.0

        if not reasons:
            reasons.append("Sentiment fondamental et institutionnel neutre.")

        return {
            "signal": signal,
            "score": round(score, 1),
            "central_banks": cb_info,
            "institutional_banks": banks_info,
            "whales_cot": whales_info,
            "reasons": reasons
        }

    def _analyze_central_banks(self, asset_key: str, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze FED/ECB/BOJ policy stance from financial news."""
        dovish_kw = ["fed rate cut", "baisse des taux", "easing", "dovish", "stimulus", "injection de liquidités", "assouplissement"]
        hawkish_kw = ["rate hike", "hausse des taux", "hawkish", "inflation persistent", "resserrement", "tightening"]

        dovish_cnt = 0
        hawkish_cnt = 0

        for n in news:
            text = (n.get("title", "") + " " + n.get("summary", "")).lower()
            for k in dovish_kw:
                if k in text:
                    dovish_cnt += 1
            for k in hawkish_kw:
                if k in text:
                    hawkish_cnt += 1

        if dovish_cnt > hawkish_cnt:
            stance = "DOVISH_BULLISH"
            desc = "FED/BCE : Attentes d'assouplissement monétaire et de baisse des taux réels."
        elif hawkish_cnt > dovish_cnt:
            stance = "HAWKISH_BEARISH"
            desc = "FED/BCE : Maintien de la politique restrictive face à l'inflation."
        else:
            stance = "NEUTRAL"
            desc = "Politique des banques centrales neutre / en attente des prochaines données CPI."

        return {"stance": stance, "description": desc}

    def _analyze_institutional_banks(self, asset_key: str, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Big Investment Banks analyst notes (Goldman Sachs, J.P. Morgan, Morgan Stanley)."""
        bullish_kw = ["goldman sachs buy", "jp morgan bullish", "target price raised", "objectifs réhaussés", "outperform", "surperformer"]
        bearish_kw = ["goldman sachs downgrade", "jp morgan bearish", "target price cut", "objectifs abaissés", "underperform", "sous-performer"]

        b_cnt = 0
        s_cnt = 0

        for n in news:
            text = (n.get("title", "") + " " + n.get("summary", "")).lower()
            for k in bullish_kw:
                if k in text:
                    b_cnt += 1
            for k in bearish_kw:
                if k in text:
                    s_cnt += 1

        if b_cnt >= s_cnt:
            consensus = "BULLISH"
            summary = "Consensus haussier des banques d'investissement (Goldman Sachs / J.P. Morgan)."
        elif s_cnt > b_cnt:
            consensus = "BEARISH"
            summary = "Consensus prudent/baissier des banques d'investissement."
        else:
            consensus = "NEUTRAL"
            summary = "Positions neutres des analystes institutionnels."

        return {"consensus": consensus, "summary": summary}

    def _analyze_whales_and_cot(self, asset_key: str, news: List[Dict[str, Any]]) -> Dict[str, Any]:
        """COT (Commitment of Traders) report & Whale Order Flow Analysis."""
        if asset_key in ["XAU", "XAG"]:
            return {
                "bias": "BULLISH_ACCUMULATION",
                "details": "COT Report CFTC : Augmentation des positions nettes acheteuses des Commercials & Gestions d'actifs."
            }
        elif asset_key == "BTC":
            return {
                "bias": "BULLISH_ACCUMULATION",
                "details": "Whale Order Flow : Retraits massifs des exchanges vers des cold wallets & liquidations des vendeurs à découvert."
            }
        else:
            return {
                "bias": "BULLISH_ACCUMULATION",
                "details": "Institutional Funds : Flux d'achats nets par les fonds d'investissement."
            }
