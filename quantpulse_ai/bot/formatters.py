from typing import Dict, Any, List
from config.settings import TARGET_ASSETS

class MessageFormatter:
    """Formats Telegram messages in French for each dedicated strategy analysis."""

    @staticmethod
    def format_start_welcome() -> str:
        """Format `/start` welcome message in French."""
        return (
            "🤖 **Bienvenue sur QuantPulse AI — Terminal d'Intelligence Quantitative Multi-Stratégies**\n\n"
            "Je suis votre bot autonome de signaux de Day Trading et d'analyse multi-modale.\n"
            "Chaque actif est analysé séparément selon **4 Piliers d'Analyse Indépendants** :\n\n"
            "1️⃣ 📉 **SMC / ICT & Technique Avancée** (FVG, Order Blocks, Liquidity Sweeps, OTE)\n"
            "2️⃣ 📐 **Gann & Math Quant** (Angles 1x1, Square of 9, Jim Simons, Wyckoff, Elliott)\n"
            "3️⃣ 🏛️ **Fondamental & Baleines** (Banques Centrales FED/BCE, COT, Goldman Sachs)\n"
            "4️⃣ 👥 **Consensus Élite Day Traders** (% BUY, % SELL, % NEUTRE)\n\n"
            "📌 **Périmètre des Actifs :**\n"
            "• 🥇 **Or (XAU/USD)** | 🥈 **Argent (XAG/USD)**\n"
            "• ₿ **Bitcoin (BTC/USDT)** | 🚗 **Tesla (TSLA)**\n"
            "• 🚀 **Flux SpaceX** (Impact indirect sur TSLA)\n\n"
            "👇 *Choisissez un actif ci-dessous pour ouvrir son menu d'analyse :*"
        )

    @staticmethod
    def format_asset_sub_menu(asset_key: str) -> str:
        """Sub-menu title for choosing specific strategy analysis."""
        asset_cfg = TARGET_ASSETS.get(asset_key)
        name = asset_cfg.name if asset_cfg else asset_key
        return (
            f"🎯 **MENU D'ANALYSE : {name}**\n\n"
            f"Veuillez sélectionner le type d'analyse que vous souhaitez consulter :"
        )

    @staticmethod
    def format_smc_ict_analysis(eval_data: Dict[str, Any]) -> str:
        """1. Format SMC, ICT & Technical Analysis Report."""
        smc = eval_data.get("smc_res", {})
        price = smc.get("current_price", 0.0)
        score = smc.get("score", 50.0)
        signal = smc.get("signal", "NEUTRAL")
        reasons = smc.get("reasons", [])
        details = smc.get("details", {})

        sig_icon = "🟢 ACHAT (BUY / LONG)" if signal == "BUY" else "🔴 VENTE (SELL / SHORT)" if signal == "SELL" else "⚪ NEUTRE"
        reasons_str = "\n".join([f"  • {r}" for r in reasons])

        fvg = details.get("fvg", {})
        fvg_str = "Aucun FVG actif"
        if fvg.get("bullish_fvg"):
            fvg_str = f"Bullish FVG [{fvg['bullish_fvg'][0]} - {fvg['bullish_fvg'][1]}]"
        elif fvg.get("bearish_fvg"):
            fvg_str = f"Bearish FVG [{fvg['bearish_fvg'][0]} - {fvg['bearish_fvg'][1]}]"

        return (
            f"📉 **1. RAPPORT D'ANALYSE SMC, ICT & TECHNIQUE AVANCÉE**\n\n"
            f"💰 **Prix Actuel :** `{price}`\n"
            f"🎯 **Score SMC/ICT :** **{score:.0f}%**\n"
            f"⚡ **Signal Stratégie :** **{sig_icon}**\n\n"
            f"🔍 **Concepts ICT & SMC Détectés :**\n"
            f"• **Fair Value Gap (FVG) :** `{fvg_str}`\n"
            f"• **Chasse aux Liquidités (BSL/SSL) :** `{details.get('liquidity', {}).get('bsl_swept', False)} (BSL) | {details.get('liquidity', {}).get('ssl_swept', False)} (SSL)`\n"
            f"• **Market Structure Shift (MSS) :** `{details.get('choch_mss', 'NONE')}`\n"
            f"• **Zone OTE (Optimal Trade Entry) :** `61.8% - 78.6% Fib`\n\n"
            f"💡 **Justifications Techniques & SMC :**\n"
            f"{reasons_str}\n\n"
            f"📍 **Niveaux Day Trading Recommandés :**\n"
            f"• **TP1 :** `{eval_data.get('tp1')}` | **TP2 :** `{eval_data.get('tp2')}`\n"
            f"• **Stop-Loss (ATR) :** `{eval_data.get('sl')}`"
        )

    @staticmethod
    def format_gann_quant_analysis(eval_data: Dict[str, Any]) -> str:
        """2. Format Gann & Mathematical Quantitative Analysis Report."""
        gann_res = eval_data.get("gann_res", {})
        price = gann_res.get("current_price", 0.0)
        score = gann_res.get("score", 50.0)
        signal = gann_res.get("signal", "NEUTRAL")
        reasons = gann_res.get("reasons", [])
        researchers = gann_res.get("researchers", {})
        angles = gann_res.get("gann_angles", {})

        sig_icon = "🟢 ACHAT (BUY / LONG)" if signal == "BUY" else "🔴 VENTE (SELL / SHORT)" if signal == "SELL" else "⚪ NEUTRE"
        reasons_str = "\n".join([f"  • {r}" for r in reasons])

        simons = researchers.get("jim_simons", {})
        wyckoff = researchers.get("wyckoff", {})
        elliott = researchers.get("elliott_wave", {})

        return (
            f"📐 **2. RAPPORT D'ANALYSE MATHÉMATIQUE & GANN / CHERCHEURS**\n\n"
            f"💰 **Prix Actuel :** `{price}`\n"
            f"🎯 **Score Math & Quant :** **{score:.0f}%**\n"
            f"⚡ **Signal Stratégie :** **{sig_icon}**\n\n"
            f"📐 **W.D. Gann Angles & Square of 9 :**\n"
            f"• Angle 1x1 Support : `{angles.get('gann_1x1_support', 0)}` | Résistance : `{angles.get('gann_1x1_resistance', 0)}`\n"
            f"• Gann Square of 9 Cibles : `{angles.get('sq9_target_down', 0)}` ⬅️ Prix ➡️ `{angles.get('sq9_target_up', 0)}`\n\n"
            f"🧬 **Avis des Grands Chercheurs Quantitatifs :**\n"
            f"• **Jim Simons (Quant / Stat Arb) :** `{simons.get('signal')}` (Z-Score: `{simons.get('z_score')}`)\n"
            f"   _{simons.get('description')}_\n"
            f"• **Richard Wyckoff :** Phase `{wyckoff.get('phase')}`\n"
            f"   _{wyckoff.get('details')}_\n"
            f"• **Ralph Nelson Elliott :** `{elliott.get('wave_type')}`\n"
            f"   _{elliott.get('description')}_\n\n"
            f"💡 **Synthèse des Calculs Mathématiques :**\n"
            f"{reasons_str}"
        )

    @staticmethod
    def format_fundamental_analysis(eval_data: Dict[str, Any]) -> str:
        """3. Format Fundamental & Central Banks / Whales Analysis Report."""
        fund = eval_data.get("fund_res", {})
        score = fund.get("score", 50.0)
        signal = fund.get("signal", "NEUTRAL")
        reasons = fund.get("reasons", [])
        cb = fund.get("central_banks", {})
        banks = fund.get("institutional_banks", {})
        whales = fund.get("whales_cot", {})

        sig_icon = "🟢 ACHAT (BUY / LONG)" if signal == "BUY" else "🔴 VENTE (SELL / SHORT)" if signal == "SELL" else "⚪ NEUTRE"
        reasons_str = "\n".join([f"  • {r}" for r in reasons])

        return (
            f"🏛️ **3. RAPPORT FONDAMENTAL, BANQUES CENTRALES & BALEINES**\n\n"
            f"🎯 **Score Fondamental :** **{score:.0f}%**\n"
            f"⚡ **Biais Institutionnel :** **{sig_icon}**\n\n"
            f"🏦 **Politique des Banques Centrales (FED / BCE / BOJ) :**\n"
            f"• Posture : `{cb.get('stance')}`\n"
            f"   _{cb.get('description')}_\n\n"
            f"📊 **Grandes Banques d'Investissement (Goldman Sachs, JP Morgan) :**\n"
            f"• Consensus : `{banks.get('consensus')}`\n"
            f"   _{banks.get('summary')}_\n\n"
            f"🐋 **Rapport COT & Order Flow des Baleines :**\n"
            f"• Flux Institutionnels : `{whales.get('bias')}`\n"
            f"   _{whales.get('details')}_\n\n"
            f"💡 **Analyse synthétique :**\n"
            f"{reasons_str}"
        )

    @staticmethod
    def format_trader_consensus_analysis(eval_data: Dict[str, Any]) -> str:
        """4. Format Elite Day Traders Consensus & Statistics Report."""
        trader_res = eval_data.get("trader_res", {})
        score = trader_res.get("score", 50.0)
        signal = trader_res.get("signal", "NEUTRAL")
        stats = trader_res.get("stats", {})
        traders = trader_res.get("traders", {})

        sig_icon = "🟢 ACHAT (BUY / LONG)" if signal == "BUY" else "🔴 VENTE (SELL / SHORT)" if signal == "SELL" else "⚪ NEUTRE"

        traders_str = ""
        for k, t in traders.items():
            s_icon = "🟢 BUY" if t['signal'] == "BUY" else "🔴 SELL" if t['signal'] == "SELL" else "⚪ NEUTRE"
            traders_str += f"• **{t['name']}** : {s_icon}\n  _{t['reason']}_\n"

        return (
            f"👥 **4. RAPPORT DU CONSENSUS DES ÉLITES DAY TRADERS**\n\n"
            f"🎯 **Score de Consensus :** **{score:.0f}%**\n"
            f"⚡ **Orientation Majoritaire :** **{sig_icon}**\n\n"
            f"📊 **Statistiques de Répartition des Day Traders Pro :**\n"
            f"🟢 **Pour le BUY (LONG) :** `{stats.get('buy_pct', 0)}%`\n"
            f"🔴 **Pour le SELL (SHORT) :** `{stats.get('sell_pct', 0)}%`\n"
            f"⚪ **NEUTRE / Attente :** `{stats.get('neutral_pct', 0)}%`\n\n"
            f"👨‍💻 **Positions & Avis Individuels des Traders Élite :**\n"
            f"{traders_str}"
        )

    @staticmethod
    def format_multi_strategy_diagnostic(eval_data: Dict[str, Any]) -> str:
        """Format Global Multi-Strategy Diagnostic."""
        conf = eval_data.get("combined_score", 50.0)
        price = eval_data.get("price", 0.0)
        risk = eval_data.get("risk_level", "MODÉRÉ")
        warning = eval_data.get("warning_msg")

        smc_score = eval_data.get("smc_res", {}).get("score", 50.0)
        gann_score = eval_data.get("gann_res", {}).get("score", 50.0)
        fund_score = eval_data.get("fund_res", {}).get("score", 50.0)
        trader_score = eval_data.get("trader_res", {}).get("score", 50.0)

        action = eval_data.get("final_action", "NEUTRAL")
        action_str = "🟢 **ACHAT (BUY / LONG)**" if action == "BUY" else "🔴 **VENTE (SELL / SHORT)**" if action == "SELL" else "⚪ **NEUTRE**"

        msg = (
            f"🔥 **DIAGNOSTIC MULTI-STRATÉGIES COMBINÉ : {eval_data.get('asset_key')}**\n\n"
            f"💰 **Prix Actuel :** `{price}`\n"
            f"📊 **Score de Confiance Hybride Global :** **{conf:.0f}%**\n"
            f"🎯 **Décision Finale Day Trading :** {action_str}\n"
            f"⚠️ **Profil de Risque :** {risk}\n\n"
            f"🧩 **Répartition des Scores par Stratégie :**\n"
            f"• 📉 **SMC / ICT & Technique :** `{smc_score:.0f}%`\n"
            f"• 📐 **Gann & Math Quant :** `{gann_score:.0f}%`\n"
            f"• 🏛️ **Fondamental & Banques :** `{fund_score:.0f}%`\n"
            f"• 👥 **Consensus Day Traders Pro :** `{trader_score:.0f}%`\n\n"
            f"📍 **Niveaux de Prix Clés :**\n"
            f"• **TP1 :** `{eval_data.get('tp1')}` | **TP2 :** `{eval_data.get('tp2')}`\n"
            f"• **Stop-Loss (ATR) :** `{eval_data.get('sl')}`"
        )
        if warning:
            msg += f"\n\n⚠️ **Avertissement :** {warning}"
        return msg

    @staticmethod
    def format_signal_alert(eval_data: Dict[str, Any]) -> str:
        """Format automated high confidence Telegram alert (> 70%)."""
        asset_key = eval_data.get("asset_key", "ACTIF")
        asset_cfg = TARGET_ASSETS.get(asset_key)
        asset_name = asset_cfg.name if asset_cfg else asset_key

        action = eval_data.get("final_action", "NEUTRAL")
        if action == "SELL":
            action_str = "🔴 **VENTE (SELL / SHORT)**"
        elif action == "BUY":
            action_str = "🟢 **ACHAT (BUY / LONG)**"
        else:
            action_str = "⚪ **NEUTRE**"

        conf = eval_data.get("combined_score", 75.0)
        smc_score = eval_data.get("smc_res", {}).get("score", 50.0)
        gann_score = eval_data.get("gann_res", {}).get("score", 50.0)

        # Bold & Colored Score Badge
        if conf >= 80.0:
            score_badge = f"🔥 🟢 **{conf:.0f}% [ÉLITE / CONFLUENCE MAXIMALE 🚀]**"
        elif conf >= 72.0:
            score_badge = f"🟢 **{conf:.0f}% [SIGNAL CONFIRMÉ ✅]**"
        else:
            score_badge = f"🟡 **{conf:.0f}% [MODÉRÉ]**"

        price = eval_data.get("price", 0.0)
        tp1 = eval_data.get("tp1", 0.0)
        tp2 = eval_data.get("tp2", 0.0)
        sl = eval_data.get("sl", 0.0)

        smc_reasons = eval_data.get("smc_res", {}).get("reasons", [])
        quick_analysis = " + ".join(smc_reasons[:2]) if smc_reasons else "Confluence multi-stratégies."

        lot_2k = eval_data.get("lot_2k", 0.04)
        lot_5k = eval_data.get("lot_5k", 0.11)
        lot_10k = eval_data.get("lot_10k", 0.22)
        lot_25k = eval_data.get("lot_25k", 0.55)
        lot_50k = eval_data.get("lot_50k", 1.10)
        lot_100k = eval_data.get("lot_100k", 2.20)

        return (
            f"🚨 **SIGNAL DE DAY TRADING DÉTECTÉ : {asset_name}**\n\n"
            f"🎯 **SCORE DE CONFIANCE HYBRIDE :** {score_badge}\n"
            f"• **Direction :** {action_str}\n"
            f"• **Prix d'Entrée en Direct :** `{price}`\n\n"
            f"📍 **NIVEAUX D'EXÉCUTION (RATIO RISK/REWARD 1:3 MINIMUM) :**\n"
            f"• **TP1 (Sécurisation 50%) :** `{tp1}` (Ratio 1:1.5)\n"
            f"• **TP2 (Objectif Final Intraday) :** `{tp2}` (Ratio 1:3.0 Strict)\n"
            f"• **Stop-Loss (ATR / Order Block) :** `{sl}`\n\n"
            f"💰 **TABLEAU D'ALLOCATION DES LOTS (RISQUE D'ÉLITE 1.5%) :**\n"
            f"• Compte 2 000 $ ➔ `{lot_2k} Lot`\n"
            f"• Compte 5 000 $ ➔ `{lot_5k} Lot` *(Votre Compte)*\n"
            f"• Compte 10 000 $ ➔ `{lot_10k} Lot`\n"
            f"• Compte 25 000 $ ➔ `{lot_25k} Lot`\n"
            f"• Compte 50 000 $ ➔ `{lot_50k} Lot`\n"
            f"• Compte 100 000 $ ➔ `{lot_100k} Lot`\n\n"
            f"💡 **Analyse Rapide :** {quick_analysis}"
        )
