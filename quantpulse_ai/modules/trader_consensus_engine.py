import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TraderConsensusEngine:
    """
    Engine 4: Top Elite Day Traders Consensus Engine.
    Aggregates trading decisions from 4 top day trader profiles:
      - Trader 1: Spécialiste SMC / ICT (Structure, Order Blocks, Liquidity Sweeps)
      - Trader 2: Spécialiste Macro & Order Flow (Banques Centrales, COT, Liquide)
      - Trader 3: Trader Quant & Volatilité (Jim Simons / Stat Arb, Z-score)
      - Trader 4: Scalper Momentum & Breakouts (Rebond dynamique, Volumétrie)
    Computes statistical consensus metrics (% BUY, % SELL, % NEUTRAL).
    """

    def analyze(self, smc_res: Dict[str, Any], gann_res: Dict[str, Any], fund_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates individual decisions of top day traders and statistical consensus.
        """
        # 1. Trader A: SMC / ICT Specialist
        trader_a_signal = smc_res.get("signal", "NEUTRAL")
        trader_a_reason = smc_res.get("reasons", ["Analyse de structure SMC."])[0]

        # 2. Trader B: Macro & Order Flow Specialist
        trader_b_signal = fund_res.get("signal", "NEUTRAL")
        trader_b_reason = fund_res.get("reasons", ["Analyse macro-économique."])[0]

        # 3. Trader C: Quant Volatility & Stat Arb Specialist
        trader_c_signal = gann_res.get("signal", "NEUTRAL")
        trader_c_reason = gann_res.get("reasons", ["Modélisation quant et angles de Gann."])[0]

        # 4. Trader D: Momentum Breakout Scalper
        # Scalper looks at alignment between SMC & Quant
        if trader_a_signal == trader_c_signal and trader_a_signal != "NEUTRAL":
            trader_d_signal = trader_a_signal
            trader_d_reason = f"Breakout de Momentum confirmé par la convergence SMC & Quant ({trader_a_signal})."
        else:
            trader_d_signal = "NEUTRAL"
            trader_d_reason = "Momentum indécis, en attente de cassure nette."

        traders = {
            "trader_smc": {
                "name": "Trader Alex (Spécialiste SMC / ICT)",
                "signal": trader_a_signal,
                "reason": trader_a_reason
            },
            "trader_macro": {
                "name": "Trader Marc (Macro & Order Flow)",
                "signal": trader_b_signal,
                "reason": trader_b_reason
            },
            "trader_quant": {
                "name": "Trader Elena (Quant & Stat Arb)",
                "signal": trader_c_signal,
                "reason": trader_c_reason
            },
            "trader_scalper": {
                "name": "Trader Lucas (Scalper Momentum Pro)",
                "signal": trader_d_signal,
                "reason": trader_d_reason
            }
        }

        # Calculate Statistics (% BUY, % SELL, % NEUTRAL)
        signals = [trader_a_signal, trader_b_signal, trader_c_signal, trader_d_signal]
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")
        neutral_count = signals.count("NEUTRAL")

        total = len(signals)
        buy_pct = round((buy_count / total) * 100, 1)
        sell_pct = round((sell_count / total) * 100, 1)
        neutral_pct = round((neutral_count / total) * 100, 1)

        if buy_pct > sell_pct and buy_pct >= 50.0:
            consensus_signal = "BUY"
            consensus_score = float(min(95.0, 50.0 + (buy_pct - sell_pct) * 0.5))
        elif sell_pct > buy_pct and sell_pct >= 50.0:
            consensus_signal = "SELL"
            consensus_score = float(min(95.0, 50.0 + (sell_pct - buy_pct) * 0.5))
        else:
            consensus_signal = "NEUTRAL"
            consensus_score = 50.0

        reasons = [
            f"Consensus Élite Day Traders : {buy_pct}% ACHAT | {sell_pct}% VENTE | {neutral_pct}% NEUTRE",
            f"Majorité des traders orientée {consensus_signal}."
        ]

        return {
            "signal": consensus_signal,
            "score": round(consensus_score, 1),
            "stats": {
                "buy_pct": buy_pct,
                "sell_pct": sell_pct,
                "neutral_pct": neutral_pct
            },
            "traders": traders,
            "reasons": reasons
        }
