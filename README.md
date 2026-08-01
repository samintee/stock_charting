# stock_charting

Download stock OHLCV from yfinance and chart it in Streamlit (candles, volume, SMA/EMA, Bollinger, RSI).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Chart app (recommended)

```bash
streamlit run chart_app.py
```

In the sidebar:

1. **Fetch online** — enter a ticker, history preset (or custom dates), and interval (`1d` / `1wk` / `1mo`), then click Fetch.
2. Or **Upload CSV** — use a file previously saved under `data/`.
3. Toggle overlays (SMA/EMA), Bollinger Bands, RSI, chart theme, and the weekly panel.

Indicators are computed on the full loaded series, then the chart window filter is applied, so longer MAs stay correct on short views.

## Optional CLI fetcher

```bash
# Interactive prompts
python fetch_stock_data.py

# Non-interactive (writes to data/)
python fetch_stock_data.py AAPL --preset 1Y
python fetch_stock_data.py NOK --start 2020-01-01 --end 2024-12-31 --interval 1wk
```

CSV files are saved under `data/` (gitignored).

## Event markers

Sidebar **Event markers** (all default off):

1. MA crosses (SMA 20/50, 50/200, EMA 12/26) — triangles under/over the candle  
2. RSI exits — diamonds when RSI reclaims 70 / 30  
3. Bollinger breakout / squeeze exit — dots on close + faint band on squeeze exit  
4. MACD pane + MACD cross circles  
5. Volume spikes — markers on the volume pane + faint band  

Markers are capped (slider), deduplicated per bar, vertically offset when several fire on one date, and labeled with mechanical rule text on hover only.

## Dependencies

See `requirements.txt` (streamlit, plotly, pandas, yfinance).
