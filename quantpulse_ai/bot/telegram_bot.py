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

class QuantPulseBot:
    """
    Telegram Bot with Interactive MetaTrader 5 Auto-Trader Setup Flow & Multi-Strategy Intelligence.
    """

    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.strategy_engine = StrategyEngine()
        self.gann_quant_engine = GannQuantEngine()
        self.fundamental_engine = FundamentalEngine()
        self.trader_consensus_engine = TraderConsensusEngine()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.decision_engine = DecisionEngine()
        self.chart_generator = ChartGenerator()
        self.mt5_executor = MT5Executor()

        self.app: Optional[Application] = None
        self.cached_evaluations: Dict[str, Dict[str, Any]] = {}
        self.user_autotrader_configs: Dict[int, Dict[str, Any]] = {}

    def build_application(self) -> Application:
        """Build python-telegram-bot Application with ConversationHandler for MT5 Auto-Trader."""
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("TELEGRAM_BOT_TOKEN non fourni ! Le bot fonctionnera sans interface Telegram.")
            return None

        request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
        self.app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).request(request).build()

        # MT5 Auto-Trader Setup Conversation Handler
        mt5_conv_handler = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_autotrader_setup, pattern="^btn_setup_autotrader$")
            ],
            states={
                STATE_MT5_SERVER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_mt5_server)],
                STATE_MT5_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_mt5_login)],
                STATE_MT5_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_mt5_password)],
            },
            fallbacks=[CommandHandler("start", self.cmd_start)]
        )

        self.app.add_handler(mt5_conv_handler)

        # Commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("analyse", self.cmd_analyse))
        self.app.add_handler(CommandHandler("spacex", self.cmd_spacex))
        self.app.add_handler(CommandHandler("signals_on", self.cmd_signals_on))
        self.app.add_handler(CommandHandler("signals_off", self.cmd_signals_off))
        self.app.add_handler(CommandHandler("autotrader_off", self.cmd_autotrader_off))
        self.app.add_handler(CommandHandler("autotrader_on", self.cmd_autotrader_on))

        # Callbacks
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

        return self.app

    def get_start_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Welcome Menu with Auto-Trader Choice."""
        keyboard = [
            [
                InlineKeyboardButton("🚀 Activer l'Auto-Trader MetaTrader", callback_data="btn_setup_autotrader")
            ],
            [
                InlineKeyboardButton("📊 Mode Signaux Telegram Uniquement", callback_data="back_main")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        """Main Menu Keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🥇 Or (XAU)", callback_data="asset_XAU"),
                InlineKeyboardButton("🥈 Argent (XAG)", callback_data="asset_XAG")
            ],
            [
                InlineKeyboardButton("₿ Bitcoin", callback_data="asset_BTC"),
                InlineKeyboardButton("🚗 Tesla", callback_data="asset_TSLA")
            ],
            [
                InlineKeyboardButton("🚀 Actu SpaceX & Impact TSLA", callback_data="btn_SPACEX")
            ],
            [
                InlineKeyboardButton("📊 Diagnostic Global du Marché", callback_data="btn_GLOBAL")
            ],
            [
                InlineKeyboardButton("🛑 Stopper l'Auto-Trader MetaTrader", callback_data="btn_stop_autotrader")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_asset_sub_menu_keyboard(self, asset_key: str) -> InlineKeyboardMarkup:
        """Sub-menu keyboard with dedicated strategy choices."""
        keyboard = [
            [InlineKeyboardButton("📉 SMC, ICT & Technique Avancée", callback_data=f"smc_{asset_key}")],
            [InlineKeyboardButton("📐 Gann & Math Quant (Simons, Wyckoff, Elliott)", callback_data=f"gann_{asset_key}")],
            [InlineKeyboardButton("🏛️ Fondamental & Banques Centrales / Baleines", callback_data=f"fund_{asset_key}")],
            [InlineKeyboardButton("👥 Consensus Élite Day Traders (% Buy/Sell)", callback_data=f"traders_{asset_key}")],
            [InlineKeyboardButton("🔥 Diagnostic Multi-Stratégies Combiné", callback_data=f"combined_{asset_key}")],
            [InlineKeyboardButton("↩️ Retour au Menu Principal", callback_data="back_main")]
        ]
        return InlineKeyboardMarkup(keyboard)

    def get_signal_keyboard(self, asset_key: str) -> InlineKeyboardMarkup:
        """Interactive Alert Action Buttons (Chart, IA Explanation, Dismiss)."""
        keyboard = [
            [
                InlineKeyboardButton("📊 Voir Graphique", callback_data=f"chart_{asset_key}"),
                InlineKeyboardButton("❓ Explication IA", callback_data=f"explain_{asset_key}")
            ],
            [
                InlineKeyboardButton("🔕 Ignorer", callback_data="dismiss_alert")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    # --- Interactive MT5 Auto-Trader Conversation Flow ---

    async def start_autotrader_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Step 1: Ask user for MetaTrader Server Name."""
        query = update.callback_query
        await query.answer()

        msg = (
            "🌐 **CONFIGURATION AUTOMATIQUE METATRADER 5**\n\n"
            "Veuillez entrer le **nom de votre SERVEUR MetaTrader**\n"
            "*(Exemples : `MetaQuotes-Demo`, `Exness-Trial5`, `Deriv-Demo`, `XMGlobal-Demo`, `ICMarkets-Demo`)* :"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")
        return STATE_MT5_SERVER

    async def process_mt5_server(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Step 2: Save Server Name and Ask for MT5 Login Number."""
        server_name = update.message.text.strip()
        context.user_data['mt5_server'] = server_name

        msg = (
            f"✅ Serveur enregistré : `{server_name}`\n\n"
            "🔢 **ÉTAPE 2 / 3 : NUMÉRO DE LOGIN**\n"
            "Veuillez entrer votre **numéro de compte Login MetaTrader** *(ex: `50192834`)* :"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return STATE_MT5_LOGIN

    async def process_mt5_login(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Step 3: Save Login Number and Ask for Password."""
        login_str = update.message.text.strip()
        if not login_str.isdigit():
            await update.message.reply_text("❌ Le numéro de login doit contenir uniquement des chiffres. Veuillez réessayer :")
            return STATE_MT5_LOGIN

        context.user_data['mt5_login'] = int(login_str)

        msg = (
            f"✅ Login enregistré : `{login_str}`\n\n"
            "🔑 **ÉTAPE 3 / 3 : MOT DE PASSE**\n"
            "Veuillez entrer votre **mot de passe MetaTrader** :"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return STATE_MT5_PASSWORD

    async def process_mt5_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Step 4: Authenticate on MT5 and Start Auto-Trader."""
        password = update.message.text.strip()
        server = context.user_data.get('mt5_server')
        login = context.user_data.get('mt5_login')

        await update.message.reply_text("🔄 **Connexion en cours à MetaTrader 5... Veuillez patienter.**", parse_mode="Markdown")

        # Test MT5 Connection
        if MT5_AVAILABLE and mt5:
            try:
                init_res = mt5.initialize(login=login, password=password, server=server)
                if init_res:
                    acc = mt5.account_info()
                    balance = acc.balance if acc else 0.0
                    currency = acc.currency if acc else "USD"

                    user_id = update.effective_user.id
                    self.user_autotrader_configs[user_id] = {
                        "server": server,
                        "login": login,
                        "password": password,
                        "active": True
                    }

                    success_msg = (
                        f"🎉 **CONNEXION METATRADER 5 ÉTABLIE AVEC SUCCÈS !**\n\n"
                        f"• **Serveur :** `{server}`\n"
                        f"• **Compte Login :** `{login}`\n"
                        f"• **Solde Démo :** `{balance:.2f} {currency}`\n\n"
                        f"🤖 **L'Auto-Trader est 100% ACTIVE en Pilote Automatique !**\n"
                        f"QuantPulse AI contrôlera et exécutera désormais automatiquement les transactions d'élite (Ratio 1:3) directement sur votre compte MetaTrader."
                    )
                    await update.message.reply_text(success_msg, reply_markup=self.get_main_menu_keyboard(), parse_mode="Markdown")
                    return ConversationHandler.END
                else:
                    err = mt5.last_error()
                    err_msg = (
                        f"❌ **ÉCHEC DE CONNEXION METATRADER**\n\n"
                        f"Raison : `Code d'erreur {err}`\n"
                        f"Veuillez vérifier votre nom de serveur, login et mot de passe, puis retapez `/start` pour réessayez."
                    )
                    await update.message.reply_text(err_msg, parse_mode="Markdown")
                    return ConversationHandler.END
            except Exception as e:
                await update.message.reply_text(f"❌ Erreur lors de la tentative d'initialisation : {e}")
                return ConversationHandler.END

        await update.message.reply_text(
            "⚠️ **Remarque :** MetaTrader 5 n'est pas ouvert sur le serveur local. Vos identifiants ont été enregistrés et l'Auto-Trader s'exécutera dès l'ouverture du terminal MT5 !",
            reply_markup=self.get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # --- Command Handlers ---

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for `/start` - Prompts Auto-Trader Setup."""
        welcome_text = (
            "🤖 **BIENVENUE SUR QUANTPULSE AI MARKET INTELLIGENCE !**\n\n"
            "Voulez-vous activer le **Mode AUTO-TRADER (Trading Automatique 100% Autonome sur MetaTrader 5)** ?"
        )
        await update.message.reply_text(welcome_text, reply_markup=self.get_start_menu_keyboard(), parse_mode="Markdown")

    async def cmd_autotrader_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable MT5 Auto-Trader."""
        user_id = update.effective_user.id
        if user_id in self.user_autotrader_configs:
            self.user_autotrader_configs[user_id]["active"] = False
        await update.message.reply_text(
            "🛑 **MODE AUTO-TRADER METATRADER DÉSACTIVÉ !**\n\n"
            "Le bot n'exécutera plus aucun ordre automatique sur votre compte MT5 jusqu'à la réactivation (`/autotrader_on` ou `/start`).",
            parse_mode="Markdown"
        )

    async def cmd_autotrader_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable MT5 Auto-Trader."""
        user_id = update.effective_user.id
        if user_id in self.user_autotrader_configs:
            self.user_autotrader_configs[user_id]["active"] = True
        await update.message.reply_text(
            "✅ **MODE AUTO-TRADER METATRADER RÉACTIVÉ !**\n\n"
            "Le bot reprend l'exécution automatique des ordres d'élite en Pilote Automatique sur votre compte MT5.",
            parse_mode="Markdown"
        )

    async def cmd_signals_on(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable automated market signals."""
        settings.AUTO_SIGNALS_ENABLED = True
        await update.message.reply_text("✅ **Alertes de trading automatiques ACTIVÉES.**", parse_mode="Markdown")

    async def cmd_signals_off(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable automated market signals."""
        settings.AUTO_SIGNALS_ENABLED = False
        await update.message.reply_text("🔴 **Alertes de trading automatiques DÉSACTIVÉES.**", parse_mode="Markdown")

    async def cmd_spacex(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for `/spacex`."""
        news = await self.data_fetcher.fetch_rss_news()
        spacex_res = await self.sentiment_analyzer.analyze_spacex_impact(news)
        text = MessageFormatter.format_spacex_report(spacex_res)
        await update.message.reply_text(text, parse_mode="Markdown")

    async def cmd_analyse(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for `/analyse [ACTIF]`."""
        args = context.args
        if not args:
            await update.message.reply_text("⚠️ Veuillez spécifier un actif, ex: `/analyse XAU`", parse_mode="Markdown")
            return

        raw_asset = args[0].upper()
        asset_key = "BTC" if "BTC" in raw_asset else "XAU" if "XAU" in raw_asset or "OR" in raw_asset else "XAG" if "XAG" in raw_asset else "TSLA" if "TSLA" in raw_asset else None

        if not asset_key:
            await update.message.reply_text("❌ Actif non reconnu. Choisissez parmi `XAU`, `XAG`, `BTC`, `TSLA`.", parse_mode="Markdown")
            return

        eval_data = await self.run_single_asset_analysis(asset_key)
        if eval_data:
            text = MessageFormatter.format_multi_strategy_diagnostic(eval_data)
            await update.message.reply_text(text, reply_markup=self.get_asset_sub_menu_keyboard(asset_key), parse_mode="Markdown")

    # --- Callback Query Handler ---

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process inline keyboard button clicks."""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data == "back_main":
            text = MessageFormatter.format_start_welcome()
            await query.message.edit_text(text, reply_markup=self.get_main_menu_keyboard(), parse_mode="Markdown")

        elif data.startswith("asset_"):
            asset_key = data.split("_")[1]
            text = MessageFormatter.format_asset_sub_menu(asset_key)
            await query.message.reply_text(text, reply_markup=self.get_asset_sub_menu_keyboard(asset_key), parse_mode="Markdown")

        # Specific Strategy Button Callbacks
        elif data.startswith("smc_"):
            asset_key = data.split("_")[1]
            eval_data = await self._get_or_run_eval(asset_key)
            if eval_data:
                text = MessageFormatter.format_smc_ict_analysis(eval_data)
                await query.message.reply_text(text, reply_markup=self.get_signal_keyboard(asset_key), parse_mode="Markdown")

        elif data.startswith("gann_"):
            asset_key = data.split("_")[1]
            eval_data = await self._get_or_run_eval(asset_key)
            if eval_data:
                text = MessageFormatter.format_gann_quant_analysis(eval_data)
                await query.message.reply_text(text, reply_markup=self.get_signal_keyboard(asset_key), parse_mode="Markdown")

        elif data.startswith("fund_"):
            asset_key = data.split("_")[1]
            eval_data = await self._get_or_run_eval(asset_key)
            if eval_data:
                text = MessageFormatter.format_fundamental_analysis(eval_data)
                await query.message.reply_text(text, reply_markup=self.get_signal_keyboard(asset_key), parse_mode="Markdown")

        elif data.startswith("traders_"):
            asset_key = data.split("_")[1]
            eval_data = await self._get_or_run_eval(asset_key)
            if eval_data:
                text = MessageFormatter.format_trader_consensus_analysis(eval_data)
                await query.message.reply_text(text, reply_markup=self.get_signal_keyboard(asset_key), parse_mode="Markdown")

        elif data.startswith("combined_"):
            asset_key = data.split("_")[1]
            eval_data = await self._get_or_run_eval(asset_key)
            if eval_data:
                text = MessageFormatter.format_multi_strategy_diagnostic(eval_data)
                await query.message.reply_text(text, reply_markup=self.get_signal_keyboard(asset_key), parse_mode="Markdown")

        elif data == "btn_SPACEX":
            news = await self.data_fetcher.fetch_rss_news()
            spacex_res = await self.sentiment_analyzer.analyze_spacex_impact(news)
            text = MessageFormatter.format_spacex_report(spacex_res)
            await query.message.reply_text(text, parse_mode="Markdown", reply_markup=self.get_main_menu_keyboard())

        elif data == "btn_GLOBAL":
            await self._reply_global_diagnostic(query)

        elif data == "btn_stop_autotrader":
            user_id = update.effective_user.id
            if user_id in self.user_autotrader_configs:
                self.user_autotrader_configs[user_id]["active"] = False
            await query.message.reply_text(
                "🛑 **AUTO-TRADER METATRADER STOPPÉ !**\n\n"
                "Le trading automatique est désormais suspendu. Vous pouvez le réactiver à tout moment via `/autotrader_on` ou `/start`.",
                parse_mode="Markdown"
            )

        # Alert Actions
        elif data.startswith("chart_"):
            asset_key = data.split("_")[1]
            await self._send_chart_image(query, asset_key)
        elif data.startswith("explain_"):
            asset_key = data.split("_")[1]
            await self._send_ia_explanation(query, asset_key)
        elif data == "dismiss_alert":
            await query.message.delete()

    async def _get_or_run_eval(self, asset_key: str) -> Optional[Dict[str, Any]]:
        """Always execute fresh pipeline to fetch live real-time market data."""
        return await self.run_single_asset_analysis(asset_key)

    async def _reply_global_diagnostic(self, query):
        """Run global multi-asset overview."""
        results = []
        for key in ["XAU", "XAG", "BTC", "TSLA"]:
            eval_data = await self.run_single_asset_analysis(key)
            if eval_data:
                results.append(eval_data)
        text = MessageFormatter.format_global_diagnostic(results)
        await query.message.reply_text(text, parse_mode="Markdown", reply_markup=self.get_main_menu_keyboard())

    async def _send_chart_image(self, query, asset_key: str):
        """Generate and send candlestick chart image."""
        eval_data = await self._get_or_run_eval(asset_key)
        if not eval_data:
            await query.message.reply_text("❌ Impossible de générer le graphique.")
            return

        df = await self.data_fetcher.fetch_ohlcv(asset_key, period="10d", interval="1h")
        if df is not None:
            df['rsi'] = self.strategy_engine._calculate_rsi(df['close'])
            chart_buf = self.chart_generator.generate_signal_chart(
                df,
                TARGET_ASSETS[asset_key].name,
                eval_data["tp1"],
                eval_data["tp2"],
                eval_data["sl"],
                eval_data["final_action"]
            )
            if chart_buf:
                await query.message.reply_photo(
                    photo=chart_buf,
                    caption=f"📈 **Graphique Analyse Technique QuantPulse — {asset_key}**",
                    parse_mode="Markdown"
                )
                return

        await query.message.reply_text("❌ Données graphiques indisponibles.")

    async def _send_ia_explanation(self, query, asset_key: str):
        """Provide detailed AI multi-strategy explanation."""
        eval_data = await self._get_or_run_eval(asset_key)
        if not eval_data:
            await query.message.reply_text("❌ Information indisponible.")
            return

        explanation = (
            f"🧠 **EXPLICATION DU MOTEUR MULTI-STRATÉGIES ({asset_key})**\n\n"
            f"1️⃣ **Calcul du Score Combiné ({eval_data['combined_score']}%) :**\n"
            f"   • SMC/ICT Score (35%) : `{eval_data['smc_res']['score']}%`\n"
            f"   • Gann & Quant Score (25%) : `{eval_data['gann_res']['score']}%`\n"
            f"   • Fondamental Score (20%) : `{eval_data['fund_res']['score']}%`\n"
            f"   • Consensus Day Traders (20%) : `{eval_data['trader_res']['score']}%`\n\n"
            f"2️⃣ **Day Trading Risk & Rules :**\n"
            f"   Le Stop-Loss ({eval_data['sl']}) et les TP1 ({eval_data['tp1']}) / TP2 ({eval_data['tp2']}) sont calibrés dynamiquement à partir de la volatilité ATR(14) et de la structure SMC des Order Blocks."
        )
        await query.message.reply_text(explanation, parse_mode="Markdown")

    # --- Multi-Strategy Pipeline Run ---

    async def run_single_asset_analysis(self, asset_key: str) -> Optional[Dict[str, Any]]:
        """Executes all 4 strategy engines for an asset."""
        try:
            df = await self.data_fetcher.fetch_ohlcv(asset_key, period="14d", interval="1h")
            if df is None or df.empty:
                return None

            news = await self.data_fetcher.fetch_rss_news()

            # Run 4 engines
            smc_res = self.strategy_engine.analyze(df, asset_key)
            gann_res = self.gann_quant_engine.analyze(df, asset_key)
            fund_res = await self.fundamental_engine.analyze(asset_key, news)
            trader_res = self.trader_consensus_engine.analyze(smc_res, gann_res, fund_res)

            # Fuse decisions
            eval_data = self.decision_engine.evaluate_all(asset_key, smc_res, gann_res, fund_res, trader_res)
            self.cached_evaluations[asset_key] = eval_data
            return eval_data

        except Exception as e:
            logger.error(f"Error in multi-strategy pipeline for {asset_key}: {e}", exc_info=True)
            return None
