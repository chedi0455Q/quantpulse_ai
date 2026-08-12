import io
import logging
from typing import Optional
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Generates customized candlestick and technical indicator chart images
    with TP1, TP2, and Stop-Loss overlays and prominent LONG / SHORT badges for Telegram.
    """

    @staticmethod
    def generate_signal_chart(
        df: pd.DataFrame, 
        asset_name: str, 
        tp1: float, 
        tp2: float, 
        sl: float, 
        signal_type: str = "BUY"
    ) -> Optional[io.BytesIO]:
        """
        Generates a dark-themed chart with Price action, dynamic TP/SL levels, RSI panel,
        and LONG (BUY) / SHORT (SELL) signal badge.
        Returns a BytesIO buffer containing PNG image data.
        """
        if df is None or len(df) < 20:
            return None

        try:
            # Use last 50 candles for clear visualization
            subset = df.iloc[-50:].copy()

            # Styling setup
            plt.style.use('dark_background')
            fig, (ax1, ax2) = plt.subplots(
                2, 1, 
                figsize=(10, 6), 
                gridspec_kw={'height_ratios': [3, 1]}, 
                sharex=True
            )
            fig.patch.set_facecolor('#0d1117')
            ax1.set_facecolor('#161b22')
            ax2.set_facecolor('#161b22')

            # Price Plotting (Candlesticks approximation via High-Low & Open-Close lines)
            dates = subset.index
            for i in range(len(subset)):
                date = dates[i]
                open_p = subset['open'].iloc[i]
                high_p = subset['high'].iloc[i]
                low_p = subset['low'].iloc[i]
                close_p = subset['close'].iloc[i]

                color = '#00c853' if close_p >= open_p else '#ff5252'
                ax1.plot([date, date], [low_p, high_p], color=color, linewidth=1)
                ax1.plot([date, date], [open_p, close_p], color=color, linewidth=3.5)

            # Draw TP1, TP2, SL Horizontal Lines
            cur_price = float(subset['close'].iloc[-1])
            ax1.axhline(cur_price, color='#ffffff', linestyle='--', alpha=0.7, label=f"Prix: {cur_price:.2f}")
            ax1.axhline(tp1, color='#00e676', linestyle='-', linewidth=1.5, label=f"TP1: {tp1:.2f}")
            ax1.axhline(tp2, color='#00b0ff', linestyle='-', linewidth=1.5, label=f"TP2: {tp2:.2f}")
            ax1.axhline(sl, color='#ff1744', linestyle='-', linewidth=1.5, label=f"SL: {sl:.2f}")

            # Prominent Signal Badge (LONG vs SHORT)
            sig_badge = "🟢 LONG (ACHAT)" if signal_type == "BUY" else "🔴 SHORT (VENTE)" if signal_type == "SELL" else "⚪ NEUTRE"
            badge_color = "#00c853" if signal_type == "BUY" else "#ff5252" if signal_type == "SELL" else "#757575"
            ax1.text(
                0.98, 0.93, 
                f"SIGNAL: {sig_badge}", 
                transform=ax1.transAxes, 
                fontsize=11, 
                fontweight='bold', 
                color='white', 
                ha='right', 
                va='top', 
                bbox=dict(boxstyle="round,pad=0.5", fc=badge_color, ec="white", lw=1.5, alpha=0.9)
            )

            ax1.set_title(f"QuantPulse AI — Graphique {asset_name}", fontsize=14, color='#00e5ff', pad=10)
            ax1.set_ylabel("Prix", color='#8b949e')
            ax1.legend(loc='upper left', facecolor='#21262d', edgecolor='#30363d', labelcolor='#c9d1d9')
            ax1.grid(True, linestyle=':', alpha=0.3, color='#30363d')

            # RSI Subplot
            if 'rsi' in subset.columns:
                ax2.plot(dates, subset['rsi'], color='#ab47bc', linewidth=1.5, label='RSI (14)')
                ax2.axhline(70, color='#ff5252', linestyle=':', alpha=0.7)
                ax2.axhline(30, color='#00c853', linestyle=':', alpha=0.7)
                ax2.fill_between(dates, 70, 30, color='#ab47bc', alpha=0.1)
                ax2.set_ylabel("RSI", color='#8b949e')
                ax2.set_ylim(0, 100)
                ax2.grid(True, linestyle=':', alpha=0.3, color='#30363d')
                ax2.legend(loc='upper left', facecolor='#21262d', edgecolor='#30363d', labelcolor='#c9d1d9')

            # Date Formatting
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            fig.autofmt_xdate()
            plt.tight_layout()

            # Save to buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor=fig.get_facecolor())
            plt.close(fig)
            buf.seek(0)
            return buf

        except Exception as e:
            logger.error(f"Error generating chart for {asset_name}: {e}")
            plt.close('all')
            return None
