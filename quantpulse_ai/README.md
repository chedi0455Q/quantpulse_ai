# 🤖 QuantPulse AI — Bot Telegram de Signaux & Intelligence de Marché

QuantPulse AI est un bot Telegram d'intelligence quantitative et de signaux de trading automatisés en temps réel pour **l'Or (XAU/USD)**, **l'Argent (XAG/USD)**, le **Bitcoin (BTC/USDT)**, **Tesla (TSLA)** et **SpaceX (Flux Privé)**.

Il est propulsé par une architecture hybride de **Score de Confiance Multi-Modal (0% à 100%)** combinant :
- **Score Technique (60%)** : RSI, Croisements MACD, Smart Money Concepts (Order Blocks, Change of Character / ChoCh) et Stop-Loss / Take-Profit dynamiques calculés via l'ATR.
- **Score Sentiment & Actualités (40%)** : Scraping de flux RSS (Boursorama, Reuters, Bloomberg, Cointelegraph) et analyse contextuelle IA via OpenAI GPT (avec fallback automatique VADER).
- **Moteur de Décision & Risk Warning** : Détection des divergences entre la technique et les actualités pour éviter les faux signaux.

---

## 🎯 Périmètre des Actifs

| Actif | Ticker / Source | Type | Description |
| :--- | :--- | :--- | :--- |
| 🥇 **Or (XAU/USD)** | `GC=F` / MetaTrader5 / yfinance | Commodity | Niveaux clés, macroéconomie FED, ATR. |
| 🥈 **Argent (XAG/USD)** | `SI=F` / MetaTrader5 / yfinance | Commodity | Corrélation avec les métaux précieux. |
| ₿ **Bitcoin (BTC/USDT)** | `BTC/USDT` (CCXT / Binance) | Crypto | RSI, zones de liquidité & divergences. |
| 🚗 **Tesla (TSLA)** | `TSLA` (yfinance / Alpaca) | Stock | Résultats financiers, tech & sentiment Elon Musk. |
| 🚀 **SpaceX** | Flux Privé RSS & IA | Private Feed | Suivi des valorisations privées, lancements Starship/Starlink et impact indirect sur TSLA. |

---

## 🚀 Fonctionnalités & Modèle d'Alerte

### 📲 Interface Telegram 100% en Français
- **Boutons Inline Interactifs** :
  - `[🥇 Or (XAU)]` | `[🥈 Argent (XAG)]`
  - `[₿ Bitcoin]` | `[🚗 Tesla]`
  - `[🚀 Actu SpaceX & Impact TSLA]`
  - `[📊 Diagnostic Global du Marché]`
- **Modèle d'Alerte Automatique** :
  ```text
  🚨 SIGNAL DE TRADING DÉTECTÉ : Or (XAU/USD)

  • Type : 🟢 ACHAT (BUY)
  • Prix Actuel : 2385.50
  • Score de Confiance : 88% (Technique : 90% | Sentiment News : 85%)
  • Niveau de Risque : EXCELLENT / SIGNAL FORT 🚀
  • Objectifs : TP1 : 2410.20 | TP2 : 2435.00
  • Stop-Loss : 2368.00 (Calculé via ATR / Order Block)

  💡 Analyse Rapide : RSI en survente (<30) + Cassure de Structure (ChoCh) + Croisement MACD haussier récent
  ```
- **Boutons sous chaque alerte** : `[📊 Voir Graphique]` `[❓ Explication IA]` `[🔕 Ignorer]`

---

## 🛠️ Guide d'Installation & Déploiement

### 1️⃣ PRÉREQUIS & CONFIGURATION DU BOT TELEGRAM

1. Créez votre bot Telegram via `@BotFather` :
   - Tapez `/newbot` dans Telegram et suivez les instructions.
   - Copiez le **Token d'API HTTP** fourni.
2. Récupérez votre **Chat ID** (Channel ou Chat personnel) :
   - Ajoutez le bot à votre canal ou envoyez un message au bot `@userinfobot`.
   - Copiez votre ID numérique (ex: `123456789` ou `-100123456789` pour un canal).

---

### 2️⃣ INSTALLATION EN LOCAL (PYTHON 3.11+)

#### Étape A : Cloner et préparer l'environnement
```bash
git clone https://github.com/votre-repo/quantpulse_ai.git
cd quantpulse_ai

# Créer un environnement virtuel Python
python -m venv venv

# Activer l'environnement
# Sur Windows :
venv\Scripts\activate
# Sur Linux/macOS :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

#### Étape B : Configurer le fichier `.env`
Copiez le fichier `.env.example` en `.env` :
```bash
cp .env.example .env
```
Éditez `.env` avec vos clés :
```env
TELEGRAM_BOT_TOKEN="VOTRE_TOKEN_BOTFATHER"
TELEGRAM_CHAT_ID="VOTRE_CHAT_ID"
OPENAI_API_KEY="sk-proj-xxxxxxxx" # Optionnel mais recommandé
SCAN_INTERVAL_SECONDS=120
CONFIDENCE_THRESHOLD=70.0
```

#### Étape C : Lancer l'application
```bash
python main.py
```
Le bot initialise l'API FastAPI sur `http://localhost:8000`, lance le scanner de marché en arrière-plan et active l'écoute Telegram.

---

### 3️⃣ DÉPLOIEMENT SUR UN VPS AVEC DOCKER & DOCKER COMPOSE (RECOMMANDÉ)

#### Étape A : Transférer les fichiers sur le VPS
```bash
scp -r . root@votre-vps-ip:/opt/quantpulse_ai
cd /opt/quantpulse_ai
```

#### Étape B : Créer le fichier `.env` sur le VPS
```bash
nano .env
```
Inscrivez-y vos variables d'environnement.

#### Étape C : Démarrer le conteneur Docker
```bash
docker-compose up -d --build
```
Vérifiez que le conteneur fonctionne :
```bash
docker-compose logs -f
```

---

### 4️⃣ DÉPLOIEMENT SYSTEMD SUR UBUNTU / DEBIAN (SANS DOCKER)

Si vous préférez exécuter le service directement sous Linux :

1. Créez un fichier de service systemd :
   ```bash
   sudo nano /etc/systemd/system/quantpulse.service
   ```
2. Ajoutez la configuration suivante :
   ```ini
   [Unit]
   Description=QuantPulse AI Trading Bot
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/opt/quantpulse_ai
   ExecStart=/opt/quantpulse_ai/venv/bin/python main.py
   Restart=always
   RestartSec=10
   EnvironmentFile=/opt/quantpulse_ai/.env

   [Install]
   WantedBy=multi-user.target
   ```
3. Activez et démarrez le service :
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable quantpulse
   sudo systemctl start quantpulse
   sudo systemctl status quantpulse
   ```

---

## 💻 Structure du Projet

```text
quantpulse_ai/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration globale Pydantic
├── modules/
│   ├── __init__.py
│   ├── data_fetcher.py      # Adaptateur asynchrone CCXT, yfinance, RSS
│   ├── strategy_engine.py   # Calculs TA (RSI, MACD, ATR) & SMC (ChoCh, OB)
│   ├── sentiment_analyzer.py# Analyse du sentiment RSS & SpaceX via OpenAI / VADER
│   ├── decision_engine.py   # Score de Confiance Hybride (0-100%) & Risques
│   └── chart_generator.py   # Génération de graphiques PNG (mplfinance/matplotlib)
├── bot/
│   ├── __init__.py
│   ├── telegram_bot.py      # Handlers Telegram async v20+ & Keyboards FR
│   └── formatters.py        # Formateurs de messages HTML/Markdown (FR)
├── main.py                  # Point d'entrée principal (FastAPI + Asyncio Loop)
├── .env.example             # Modèle de variables d'environnement
├── requirements.txt         # Dépendances Python
├── Dockerfile               # Image Docker de production
├── docker-compose.yml       # Orchestration Docker
└── README.md                # Documentation complète
```

---

## ⚡ Commandes Telegram Disponibles

- `/start` : Lance le menu interactif principal en français.
- `/analyse [ACTIF]` : Analyse instantanée (ex: `/analyse XAU` ou `/analyse BTC`).
- `/spacex` : Rapport sur la valorisation SpaceX et son impact estimé sur TSLA.
- `/signals_on` : Active le scan automatique du marché et les alertes.
- `/signals_off` : Désactive temporairement le scan automatique.

---

## 📄 Licence & Disclaimer

**Avertissement sur les risques** : *QuantPulse AI est un outil informatique d'intelligence de marché et de démonstration technique. Les analyses et signaux générés ne constituent en aucun cas un conseil en investissement financier. Le trading d'actifs comporte des risques élevés de perte en capital.*
