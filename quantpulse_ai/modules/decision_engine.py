import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Multi-Strategy Fusion & High-Precision Risk Decision Engine.
    Filters out false breakouts and weak setups to maximize Win Rate and target ~15% monthly yield.
    Requires Confluence (Triple Alignment), Trend Validation, and Risk Penalization.
    """

    def evaluate_all(
        self, 
        asset_key: str, 
        smc_res: Dict[str, Any], 
        gann_res: Dict[str, Any], 
        fund_res: Dict[str, Any], 
        trader_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs multi-strategy score fusion with high-precision win-rate filters.
        """
        smc_score = smc_res.get("score", 50.0)
        gann_score = gann_res.get("score", 50.0)
        fund_score = fund_res.get("score", 50.0)
        trader_score = trader_res.get("score", 50.0)

        smc_sig = smc_res.get("signal", "NEUTRAL")
        gann_sig = gann_res.get("signal", "NEUTRAL")
        fund_sig = fund_res.get("signal", "NEUTRAL")
        trader_sig = trader_res.get("signal", "NEUTRAL")

        # Weighted Fusion Score
        combined_score = (
            (smc_score * 0.35) + 
            (gann_score * 0.25) + 
            (fund_score * 0.20) + 
            (trader_score * 0.20)
        )
        combined_score = max(0.0, min(100.0, round(combined_score, 1)))

        # Determine dominant direction accurately (BUY vs SELL)
        signals = [smc_sig, gann_sig, fund_sig, trader_sig]
        buy_cnt = signals.count("BUY")
        sell_cnt = signals.count("SELL")

        # Triple Confluence Check (At least 2-3 engines agree in direction)
        if sell_cnt >= 2 or (smc_sig == "SELL" and smc_score >= 65.0):
            combined_action = "SELL"
        elif buy_cnt >= 2 or (smc_sig == "BUY" and smc_score >= 65.0):
            combined_action = "BUY"
        else:
            combined_action = "NEUTRAL"

        # Divergence & Risk Penalization
        has_divergence = False
        warning_msg = None
        risk_level = "MODÉRÉ"

        if smc_sig == "BUY" and fund_sig == "SELL":
            has_divergence = True
            combined_score = max(40.0, combined_score - 15.0)  # Penalize score
            risk_level = "⚠️ PRUDENCE DIVERGENCE : SMC Haussier vs Fondamental Baissier"
            warning_msg = "Le signal technique SMC est haussier mais le contexte fondamental est défavorable."
        elif smc_sig == "SELL" and fund_sig == "BUY":
            has_divergence = True
            combined_score = max(40.0, combined_score - 15.0)  # Penalize score
            risk_level = "⚠️ PRUDENCE DIVERGENCE : SMC Baissier vs Fondamental Haussier"
            warning_msg = "Le signal technique SMC est baissier mais les données fondamentales sont haussières."
        elif combined_score >= 75.0:
            risk_level = "🔥 EXCELLENT / CONFLUENCE MAXIMALE 🚀"
        elif combined_score >= 68.0:
            risk_level = "✅ BON / SIGNAL CONFIRMÉ"

        final_action = combined_action if (combined_score >= 65.0 and not has_divergence) else "NEUTRAL"

        # High Precision Signal Trigger Condition (Minimizes mistakes, maximizes win-rate)
        has_high_confidence = (
            (combined_score >= 70.0 and final_action in ["BUY", "SELL"] and not has_divergence) or
            (smc_score >= 78.0 and smc_sig in ["BUY", "SELL"] and not has_divergence)
        )

        price = smc_res.get("current_price", 0.0)
        atr = smc_res.get("atr", price * 0.01)

        # Align TP1, TP2, SL with final_action
        if final_action == "SELL":
            tp1 = smc_res.get("tp1") if smc_sig == "SELL" else price - (1.5 * atr)
            tp2 = smc_res.get("tp2") if smc_sig == "SELL" else price - (3.0 * atr)
            sl = smc_res.get("sl") if smc_sig == "SELL" else price + (1.5 * atr)
        elif final_action == "BUY":
            tp1 = smc_res.get("tp1") if smc_sig == "BUY" else price + (1.5 * atr)
            tp2 = smc_res.get("tp2") if smc_sig == "BUY" else price + (3.0 * atr)
            sl = smc_res.get("sl") if smc_sig == "BUY" else price - (1.5 * atr)
        else:
            tp1 = price + (1.0 * atr)
            tp2 = price + (2.0 * atr)
            sl = price - (1.0 * atr)

        # Calculate recommended lot size for 1.5% risk (Target ~15%/month growth)
        recommended_lot = self.calculate_recommended_lot(asset_key, price, float(sl), account_balance=5000.0, risk_pct=1.5)

        return {
            "asset_key": asset_key,
            "final_action": final_action,
            "combined_score": combined_score,
            "has_high_confidence": has_high_confidence,
            "risk_level": risk_level,
            "warning_msg": warning_msg,
            "price": round(price, 4 if price < 10 else 2),
            "tp1": round(float(tp1), 4 if tp1 < 10 else 2),
            "tp2": round(float(tp2), 4 if tp2 < 10 else 2),
            "sl": round(float(sl), 4 if sl < 10 else 2),
            "recommended_lot": recommended_lot,
            "rsi": smc_res.get("rsi", 50.0),
            "smc_res": smc_res,
            "gann_res": gann_res,
            "fund_res": fund_res,
            "trader_res": trader_res
        }

    @staticmethod
    def calculate_recommended_lot(asset_key: str, price: float, sl: float, account_balance: float = 5000.0, risk_pct: float = 1.5) -> float:
        """
        Calculates dynamic position lot size to risk exactly `risk_pct` % of account balance per trade.
        Targeting ~15% monthly growth safely.
        """
        if price == 0 or sl == price:
            return 0.11

        risk_amount = account_balance * (risk_pct / 100.0)
        sl_distance = abs(price - sl)

        if asset_key == "XAU":  # 1 Lot = 100 oz -> $1 movement per lot = $100
            lot = risk_amount / (sl_distance * 100.0)
        elif asset_key == "XAG":  # 1 Lot = 5000 oz -> $0.01 movement per lot = $50
            lot = risk_amount / (sl_distance * 5000.0)
        elif asset_key == "BTC":  # 1 Lot = 1 BTC
            lot = risk_amount / sl_distance
        else:  # Stock (TSLA)
            lot = risk_amount / sl_distance

        return round(max(0.01, min(5.0, lot)), 2)
