# Stock Charting Manual

A plain-language guide to installing the app, using every control, understanding chart jargon, and learning the technical indicators this project supports.

This manual is written for beginners. You do not need prior trading experience. Where a concept is technical, it is explained with everyday analogies first, then with how it appears in this software.

---

## Table of contents

1. [What this program is](#1-what-this-program-is)
2. [Important disclaimer](#2-important-disclaimer)
3. [What you need before you start](#3-what-you-need-before-you-start)
4. [Installation](#4-installation)
5. [Quick start (first chart in five minutes)](#5-quick-start-first-chart-in-five-minutes)
6. [Using the chart app in detail](#6-using-the-chart-app-in-detail)
7. [Optional: downloading data from the command line](#7-optional-downloading-data-from-the-command-line)
8. [Reading a candlestick chart](#8-reading-a-candlestick-chart)
9. [Glossary of terminology](#9-glossary-of-terminology)
10. [Technical indicators tutorial](#10-technical-indicators-tutorial)
11. [Event markers explained](#11-event-markers-explained)
12. [Suggested learning path inside the app](#12-suggested-learning-path-inside-the-app)
13. [Common problems and fixes](#13-common-problems-and-fixes)
14. [Project files (for the curious)](#14-project-files-for-the-curious)

---

## 1. What this program is

**stock_charting** is a small desktop/browser tool that:

1. Downloads historical stock prices from the internet (via Yahoo Finance, through a library called `yfinance`).
2. Draws interactive **candlestick charts** (the classic Japanese candle price charts used by many traders).
3. Optionally overlays **technical indicators** — mathematical summaries of past price and volume.
4. Optionally places **event markers** when simple mechanical rules fire (for example: “the 20-day average crossed above the 50-day average”).

You use it mainly through a web page that opens on your computer when you run:

```bash
streamlit run chart_app.py
```

There is also an optional command-line script (`fetch_stock_data.py`) that only downloads CSV files into a `data/` folder, if you prefer that workflow.

---

## 2. Important disclaimer

This software is an **educational charting tool**.

- It is **not** financial advice.
- Marker labels describe **mechanical rules** (math conditions), not “buy” or “sell” recommendations.
- Past patterns on a chart do **not** guarantee future results.
- Stock markets involve risk of loss. If you trade with real money, that is your own decision and responsibility.

Think of the app like a microscope for price history: it helps you *see* and *measure*, not *promise* outcomes.

---

## 3. What you need before you start

| Requirement | Notes |
|-------------|--------|
| A computer | Linux, macOS, or Windows (this project is often used under WSL on Windows). |
| Python 3 | Roughly 3.10+ recommended. |
| Internet | Needed to fetch live data. CSV upload works offline once you already have files. |
| Basic comfort with a terminal | You will type a few commands. Copy-paste is enough. |

Useful concepts (explained later in detail):

- **Ticker symbol** — short code for a company or fund (example: `AAPL` for Apple, `NOK` for Nokia).
- **OHLCV** — Open, High, Low, Close, Volume for each time period (day, week, etc.).

---

## 4. Installation

Open a terminal in the project folder (`stock_charting`).

### 4.1 Create a virtual environment

A virtual environment is a private Python sandbox so this project’s libraries do not interfere with other projects.

```bash
python -m venv .venv
```

Activate it:

```bash
# Linux / macOS / WSL
source .venv/bin/activate

# Windows (Command Prompt / PowerShell, if not using WSL)
.venv\Scripts\activate
```

When it is active, your prompt often shows `(.venv)` at the beginning.

### 4.2 Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

- **streamlit** — the web UI framework
- **plotly** — interactive charts
- **pandas** — data tables
- **yfinance** — market data download

### 4.3 Confirm it runs

```bash
streamlit run chart_app.py
```

Your browser should open a page titled something like **Stock Candlestick Chart**. If it does not open automatically, the terminal prints a local URL (often `http://localhost:8501`) — open that in a browser.

To stop the app later, go back to the terminal and press `Ctrl+C`.

---

## 5. Quick start (first chart in five minutes)

1. Start the app (`streamlit run chart_app.py`).
2. In the **left sidebar**, under **Data**, leave **Source** on **Fetch online**.
3. In **Ticker**, type a familiar symbol, for example `AAPL`.
4. Under **History to download**, choose `1Y` (one year of history).
5. Leave **Interval** on `1d` (one bar = one trading day).
6. Click **Fetch**.
7. Wait a moment. The main area should show a candlestick chart with volume underneath.
8. Hover your mouse over candles to see prices for that day.
9. Try the dark/light **Chart theme** switch near the bottom of the sidebar.

You now have a working chart. Everything else in this manual is optional depth.

---

## 6. Using the chart app in detail

The screen has two main regions:

- **Sidebar (left)** — settings: where data comes from, which window of history to show, which indicators and markers to draw.
- **Main panel (center/right)** — the chart(s), a short status line, and summary statistics.

### 6.1 Data source

#### Fetch online

This is the normal path.

| Control | What it means |
|---------|----------------|
| **Ticker** | The symbol to download (`MSFT`, `TSLA`, `SPY`, etc.). Use the exchange’s symbol format that Yahoo Finance understands. |
| **History to download** | How far back to pull when you click Fetch: `1M`, `3M`, `6M`, `1Y`, `2Y`, `5Y`, or **Custom** dates. |
| **Interval** | Size of each candle: `1d` (daily), `1wk` (weekly), `1mo` (monthly). |
| **Fetch** | Actually downloads (or reloads from cache) and updates the chart. |
| **Also save CSV to data/** | If checked, writes a file under `data/` when you fetch, so you can reopen it later offline. |

**Tip:** Changing ticker or dates does nothing until you click **Fetch** again. The app remembers the last successful fetch during the session.

#### Upload CSV

Use this if you already have a file (for example from the command-line fetcher).

1. Choose **Upload CSV**.
2. Pick a `.csv` file that has columns: `Date`, `Open`, `High`, `Low`, `Close`, `Volume`.
3. Optionally edit **Ticker label** (used in the chart title). The app guesses from the filename when possible (for example `AAPL_2025-01-01_2026-01-01.csv` → `AAPL`).

If required columns are missing, you will see a clear error instead of a broken chart.

### 6.2 Chart window (what portion you look at)

Downloading five years of data and *looking at* only the last three months are different ideas.

| Control | Meaning |
|---------|---------|
| **Timeframe** | How much of the loaded data to show: `1M` … `5Y`, **All**, or **Custom**. |
| **From / To** | Appears when Timeframe is Custom. |

**Why this matters for indicators:** Moving averages need warm-up history. This app calculates indicators on the **full loaded series**, then applies the chart window. So if you downloaded five years but view one year, a 200-day average can still be valid at the left edge of the one-year view.

### 6.3 Overlays (lines drawn on the price chart)

| Checkbox | Meaning |
|----------|---------|
| **SMA 20 / 50 / 200** | Simple moving averages of the closing price over 20, 50, or 200 bars. |
| **EMA 12 / 26** | Exponential moving averages (react faster to recent prices). |

These are lines drawn **on top of** the candles.

### 6.4 Bands and oscillators

| Checkbox | What you get |
|----------|----------------|
| **Bollinger Bands (20, 2σ)** | A middle average line plus upper/lower bands based on volatility. |
| **RSI (14)** | A separate pane from 0–100 measuring recent up vs down strength. |
| **MACD (12, 26, 9)** | A separate pane with MACD line, signal line, and histogram. |

### 6.5 Event markers

All marker options are **off by default** so the chart stays clean for beginners.

| Option | What appears |
|--------|----------------|
| **MA crosses** | Triangles when a faster average crosses a slower one. Sub-options: SMA 20/50, SMA 50/200, EMA 12/26. |
| **RSI exits** | Diamonds when RSI comes back from above 70 or below 30. |
| **Bollinger breakout / squeeze exit** | Dots when price closes outside a band; open dots plus a faint vertical band when a “squeeze” ends. |
| **MACD crosses** | Circles when MACD crosses its signal line. |
| **Volume spikes** | Markers on the volume pane when volume is unusually large vs its recent average. |
| **Max marker dates in view** | Limits clutter by keeping only the most recent N event dates. |

**How to read a marker:** hover it. The popup text is a mechanical description such as:

> SMA 20 crossed above SMA 50

It does **not** say “buy now.”

If several rules fire on the same day, markers are slightly stacked, and the hover text may combine the rules with a middle dot (`·`).

### 6.6 Display options

| Control | Effect |
|---------|--------|
| **Chart theme** | `dark` or `light` color palette for the Plotly chart. |
| **Show weekly chart** | Below the main chart, builds weekly candles from the data currently in view, with the same indicator/marker settings when there is enough weekly history. |

### 6.7 Stats strip

Under the charts you will see four summary numbers for the **visible** window:

- **Last Close** — most recent closing price in view
- **Period High** — highest high in view
- **Period Low** — lowest low in view
- **Period Return** — percent change from first close to last close in view

---

## 7. Optional: downloading data from the command line

You do not need this if you use **Fetch online** in the app. It is useful for scripting, saving files ahead of time, or working offline later.

### 7.1 Interactive mode

```bash
source .venv/bin/activate
python fetch_stock_data.py
```

The script asks for:

1. Ticker
2. Timeframe (1 month … 5 years, or custom dates)
3. Interval (`1d`, `1wk`, `1mo`)

Files are saved under `data/`, for example:

```text
data/AAPL_2025-08-01_2026-08-01.csv
```

### 7.2 Non-interactive examples

```bash
python fetch_stock_data.py AAPL --preset 1Y
python fetch_stock_data.py NOK --start 2020-01-01 --end 2024-12-31 --interval 1wk
python fetch_stock_data.py MSFT --preset 5Y --interval 1d
```

Presets (`1M`, `3M`, `6M`, `1Y`, `2Y`, `5Y`) use the same calendar math as the chart app.

Then in the app: **Upload CSV** and select the file from `data/`.

---

## 8. Reading a candlestick chart

### 8.1 One candle = one period

If interval is `1d`, each candle is one trading day. If `1wk`, each candle is one week.

For each period the market provides four key prices:

| Name | Everyday meaning |
|------|------------------|
| **Open** | Price at the start of the period |
| **High** | Highest price reached during the period |
| **Low** | Lowest price reached during the period |
| **Close** | Price at the end of the period |

### 8.2 The body and the wicks

A candle has:

- A **body** (the thick rectangle): spans from Open to Close.
- **Wicks** (thin lines): extend to High and Low.

Color convention in this app (and many platforms):

- **Green / teal-ish** — Close is greater than or equal to Open (period finished higher than it started; often called a “bullish” candle).
- **Red** — Close is less than Open (finished lower; often called a “bearish” candle).

Analogy: the body is the “net result” of the day; the wicks show how far the tug-of-war went in either direction before settling.

### 8.3 The volume pane

Under the price chart is **volume**: how many shares (or contracts) traded in that period.

- Tall bars mean lots of trading activity.
- Short bars mean quieter trading.

Volume does not say *why* people traded — only *how much*.

### 8.4 Interacting with Plotly charts

- **Hover** — see values for that date.
- **Scroll / zoom** (depending on Plotly controls) — focus on a region.
- **Legend** — click series names to hide/show lines.
- **Reset** — use the camera/home icons in the chart toolbar if you zoom too far.

---

## 9. Glossary of terminology

Use this as a dictionary. Terms are sorted roughly from beginner to more specialized.

### Market and data basics

**Stock**  
A share of ownership in a company. Prices move as buyers and sellers agree on new prices.

**Ticker / symbol**  
Short code identifying what you chart (`AAPL`, `GOOGL`, `SPY`).

**Exchange**  
Marketplace where the stock trades (NYSE, Nasdaq, etc.). You usually do not need to pick the exchange in this app if Yahoo Finance resolves the symbol.

**OHLCV**  
Open, High, Low, Close, Volume — the five fields this app charts.

**Bar / candle**  
One row of OHLCV for one interval (day, week, month).

**Interval**  
How much time one candle represents (`1d`, `1wk`, `1mo` in this app).

**Timeframe / lookback**  
How much history you are viewing (one month, one year, all loaded data, and so on).

**Liquidity**  
How easily something trades. Highly liquid names (big companies, major ETFs) usually have smoother charts; tiny stocks can jump around and have missing days.

**Adjusted prices**  
This app downloads with auto-adjustment for splits/dividends when using yfinance. That makes long histories more comparable across corporate actions. Exact adjustment behavior is handled by the data provider.

**CSV**  
A simple spreadsheet-like text file. Each row is a date; columns are OHLCV.

### Chart language

**Trend**  
A general direction over time: uptrend (higher highs and higher lows), downtrend (lower highs and lower lows), or sideways (range-bound).

**Support**  
A price area where buying interest historically appeared and price stopped falling (informal concept, not a guarantee).

**Resistance**  
A price area where selling interest historically appeared and price stopped rising.

**Breakout**  
Price leaving a range or band, often discussed when close moves beyond a boundary (for example a Bollinger Band).

**Volatility**  
How large and fast prices swing. High volatility means bigger candles and wider bands.

**Bullish / bearish**  
Informal adjectives: bullish roughly means optimism or upward pressure; bearish roughly means pessimism or downward pressure. They are opinions about direction, not facts.

### Indicator language

**Indicator**  
A calculated series derived from price and/or volume (moving average, RSI, MACD, and so on).

**Overlay**  
An indicator drawn on the same pane as price (moving averages, Bollinger Bands).

**Oscillator**  
An indicator in its own pane, often bounded (RSI 0–100) or centered around zero (MACD).

**Lagging indicator**  
Based on past prices; it confirms what already happened more than it predicts. Most popular indicators lag to some degree.

**Leading indicator**  
Attempts to tip earlier (still not magic). Oscillators are sometimes described this way, with many false signals.

**Crossover**  
When one line crosses another (fast MA versus slow MA; MACD versus signal).

**Overbought / oversold**  
Informal labels when an oscillator is very high or very low (classic RSI: above 70 / below 30). They mean “extended versus recent history,” **not** “must reverse tomorrow.”

**Divergence**  
When price makes a new high or low but an oscillator does not (or the reverse). Traders watch this as a *possible* warning that momentum is changing. This app does not auto-detect divergences; you would spot them by eye.

**Signal**  
In this manual and app: a **mechanical event** matching a rule. Not a broker order and not advice.

---

## 10. Technical indicators tutorial

This section teaches the indicators in general, then how they appear in **stock_charting**.

### 10.1 What technical analysis is trying to do

**Technical analysis** studies price and volume history, looking for patterns and statistics that some people find useful for timing decisions.

Contrast with **fundamental analysis**, which studies business value (earnings, products, debt, and so on). This app is almost entirely technical: it does not fetch earnings reports or news.

A healthy beginner mindset:

1. Indicators summarize history; they do not reveal secret future knowledge.
2. Use them as **questions** (“Is momentum stretched?”) not **orders** (“I must buy”).
3. More indicators on one chart often create *more noise*, not more clarity.
4. Always notice the **interval**: a “20” on a daily chart is about 20 trading days; on a weekly chart it is about 20 weeks.

---

### 10.2 Moving averages (SMA and EMA)

#### The idea in plain English

A **moving average** smooths out the zig-zag of daily closes so the overall path is easier to see — like replacing a bumpy road profile with a gently curved summary line.

- **SMA (Simple Moving Average)** — average of the last *N* closing prices, each day weighted equally.
- **EMA (Exponential Moving Average)** — also based on recent closes, but **recent days count more**, so the line reacts faster when price turns.

#### Common lengths and why people use them

| Length | Rough feel on a daily chart | Typical conversation |
|--------|-----------------------------|----------------------|
| 20 | About one trading month | Short-term trend / pullback guide |
| 50 | About two to three months | Medium trend |
| 200 | About a trading year | Long-term “climate” of the trend |
| 12 and 26 | Short EMA pair | Building blocks of classic MACD |

#### Use cases

1. **Trend filter** — Price mostly above a rising 200-SMA is often described as a longer-term uptrend environment (and the reverse for downtrends).
2. **Dynamic support/resistance** — In strong trends, price may pull back toward a moving average and bounce (or break through). This is a tendency some traders watch, not a law.
3. **Crossovers** — When a faster average crosses above a slower one, some call it a “golden cross” style event; the opposite is sometimes called a “death cross.” Names are dramatic; the math is simply one average overtaking another.

#### Limitations

- In sideways markets, averages weave through price and produce many whipsaw crosses.
- They **lag**: a cross often happens after a move is already underway.
- Different lengths tell different stories; none is “the correct” one.

#### In this app

- Toggle **SMA 20 / 50 / 200** and **EMA 12 / 26** under Overlays.
- Enable **MA crosses** markers to highlight cross events with triangles and hover text.

---

### 10.3 Bollinger Bands

#### The idea in plain English

Imagine a moving average as a center of gravity, then draw a soft upper and lower fence based on how jumpy prices have been lately.

Classic settings (what this app uses): **20-period middle SMA**, bands at **plus or minus 2 standard deviations**.

- When the market is calm, bands **narrow** (a “squeeze”).
- When the market is wild, bands **widen**.

#### Use cases

1. **Volatility gauge** — Band width is a visual volatility meter.
2. **Stretch versus mean** — Closes near or outside the bands mean price is statistically extended versus the recent 20-bar average (again: extended does not mean it must reverse).
3. **Squeeze then expansion** — After a quiet squeeze, a burst of movement often follows *some* direction. The app’s squeeze-exit marker flags when bandwidth leaves a historically tight zone; it does **not** tell you up versus down.

#### Limitations

- Strong trends can “walk the band” (repeated closes outside) for a long time.
- Band touches are common; not every touch is meaningful.
- Settings (20, 2 standard deviations) are conventions, not magic numbers.

#### In this app

- Enable **Bollinger Bands (20, 2σ)** to draw the envelope.
- Enable **Bollinger breakout / squeeze exit** markers for:
  - first close outside upper/lower band, and
  - bandwidth leaving a squeeze (with a faint vertical highlight).

---

### 10.4 RSI (Relative Strength Index)

#### The idea in plain English

RSI asks: *Over the last N bars, have closes been winning more often or harder than losing?*

It scales the answer roughly from **0 to 100**.

Classic settings: **14 periods**, with informal zones:

- Above **70** — often labeled **overbought**
- Below **30** — often labeled **oversold**

Those words sound like “too expensive / too cheap.” A safer mental model is: “recent momentum has been one-sided.”

#### Use cases

1. **Momentum stretch** — Very high or low RSI means recent action was strongly directional.
2. **Reclaim / exit from extremes** — Some people care less about RSI hitting 70 and more about RSI **coming back** from above 70 (or back from below 30), treating that as a change in short-term pressure. This app’s RSI exit markers follow that reclaim idea.
3. **Range trading versus trend** — In ranges, fades of extremes sometimes work better; in strong trends, RSI can stay “overbought” or “oversold” for extended periods.

#### Limitations

- In powerful trends, fighting RSI extremes is a common way to lose money.
- RSI does not know news, earnings, or fundamentals.
- Period length (14) changes sensitivity.

#### In this app

- Enable **RSI (14)** to show the oscillator pane with 70/30 guides.
- Enable **RSI exits** for diamond markers on price (and on the RSI pane when visible).

---

### 10.5 MACD (Moving Average Convergence/Divergence)

#### The idea in plain English

MACD compares a fast EMA and a slow EMA of price, then smooths that difference again.

Classic settings (used here):

1. **MACD line** = EMA(12) minus EMA(26)
2. **Signal line** = EMA(9) of the MACD line
3. **Histogram** = MACD line minus signal line (bars showing the gap between them)

When the two EMAs of price pull apart, MACD moves away from zero (“divergence” of the averages in the indicator’s name). When they converge, MACD heads back toward zero.

#### Use cases

1. **Momentum direction** — MACD above zero often aligns with shorter-EMA-above-longer-EMA territory.
2. **Signal-line crosses** — MACD crossing above or below its signal is a popular mechanical event (marked in this app if you enable MACD crosses).
3. **Histogram shrinking or growing** — A visual cue that the MACD–signal gap is narrowing or widening (momentum cooling or heating), still lagging.

#### Limitations

- Like moving averages, MACD is lagging and can whipsaw in ranges.
- Zero-line and signal crosses can disagree with longer-term trend.
- Histogram is easy to over-interpret bar by bar.

#### In this app

- Enable **MACD (12, 26, 9)** for the dedicated pane.
- Enable **MACD crosses** for circle markers on price (and on the MACD pane).

---

### 10.6 Volume and volume spikes

#### The idea in plain English

Price is *what* traded; volume is *how much* participated.

A big price move on tiny volume can mean fewer people were involved. A big move on huge volume often means broader participation (still not automatically “good” or “bad”).

A **volume spike** in this app means: today’s volume is greater than **2 times** the 20-bar simple average of volume (those defaults are fixed in the code).

#### Use cases

1. **Confirming breakouts** — Some traders prefer breakouts that arrive with elevated volume.
2. **Spotting event days** — Earnings, news, and liquidations often print as volume spikes. The marker does not explain the news; it only flags unusual activity.
3. **Quiet markets** — Low volume stretches can precede volatility expansions (related in spirit to Bollinger squeezes, but not identical).

#### Limitations

- Volume definitions differ across exchanges and data vendors.
- ETFs and stocks behave differently.
- A spike alone has no direction.

#### In this app

- Volume is always drawn under price.
- Enable **Volume spikes** for markers on the volume pane and a faint vertical band on the price chart.

---

### 10.7 Combining indicators without fooling yourself

Beginners often stack RSI + MACD + Bollinger + five moving averages and feel overwhelmed.

A simpler approach:

| Goal | Prefer starting with |
|------|----------------------|
| See trend | Price + SMA 50 and/or 200 |
| See short swing context | Add SMA 20 or EMA 12/26 |
| See stretch / volatility | Bollinger **or** RSI (not necessarily both at first) |
| See momentum cross events | MACD **or** MA crosses |
| See participation | Volume (plus spikes occasionally) |

**Confirmation bias warning:** If you only enable markers that fire often, everything looks like a “signal.” Prefer fewer rules and read the hover text carefully.

**Timeframe alignment:** A daily MACD cross that looks constructive against a collapsing weekly chart may simply be a bounce in a larger decline. Use the weekly panel to sanity-check.

---

### 10.8 What this app does *not* include (yet)

Knowing the boundaries helps set expectations:

- No automatic support/resistance drawing
- No candlestick pattern recognition (doji, hammer, and so on)
- No order placement or brokerage connection
- No portfolio tracking
- No fundamental data (P/E, earnings calendar)
- No custom indicator scripting language

You can still learn a great deal of chart literacy with what is included.

---

## 11. Event markers explained

Markers are **optional annotations** for mechanical events.

### 11.1 Design principles used in this project

1. **Default off** — clean candles first.
2. **Hover over permanent labels** — less visual clutter.
3. **Mechanical wording** — “SMA 20 crossed above SMA 50,” not “Buy signal.”
4. **Cap per view** — the slider keeps only the most recent event dates.
5. **Deduping / stacking** — same-day events are offset and may share combined hover text.

### 11.2 Marker cheat sheet

| Marker family | Glyph (typical) | Rule (simplified) |
|---------------|-----------------|-------------------|
| MA cross up | Green triangle below the low | Fast MA crosses **above** slow MA |
| MA cross down | Red triangle above the high | Fast MA crosses **below** slow MA |
| RSI exit from high | Diamond near price / on RSI | RSI was above 70, then returns to 70 or below |
| RSI exit from low | Diamond near price / on RSI | RSI was below 30, then returns to 30 or above |
| BB breakout | Dot on the close | Close crosses outside upper or lower band |
| BB squeeze exit | Open circle + faint band | Bandwidth leaves a historically tight zone |
| MACD cross | Circle on close / on MACD | MACD crosses its signal line |
| Volume spike | Diamond on volume + faint band | Volume greater than 2 times the 20-bar average volume |

### 11.3 A careful way to practice with markers

1. Load a liquid stock or ETF (`SPY`, `AAPL`, and so on) with **2Y** or **5Y** history.
2. View **1Y**.
3. Turn on **only** SMA 20 + SMA 50 overlays and **MA crosses (SMA 20/50)**.
4. Scroll through history and ask: *After a cross, what happened over the next weeks?* Sometimes continuation, sometimes whipsaw.
5. Add RSI exits on a second pass — separately — and compare.
6. Avoid enabling every marker family at once until you recognize each glyph.

---

## 12. Suggested learning path inside the app

Follow this over a few short sessions.

### Session A — Candles only

1. Fetch `SPY` or a stock you recognize, `1Y`, daily.
2. Turn **off** extra overlays if needed (you can uncheck SMAs).
3. Practice reading open/high/low/close from hover.
4. Note a few tall volume days — what did price do that day?

### Session B — Trend with averages

1. Enable SMA 20 and SMA 50.
2. Ask whether price is mostly above or below them.
3. Enable MA cross markers for SMA 20/50.
4. Hover a few triangles and read the rule text.

### Session C — Volatility

1. Enable Bollinger Bands.
2. Find a place where bands were narrow, then wide.
3. Optionally enable Bollinger markers and inspect squeeze exits.

### Session D — Momentum oscillators

1. Enable RSI; watch how it behaves in a smooth uptrend versus a choppy range.
2. Enable RSI exits and see reclaim events.
3. Disable RSI markers; enable MACD pane and MACD crosses; compare timing to MA crosses.

### Session E — Multi-timeframe glance

1. Keep daily chart settings.
2. Enable **Show weekly chart**.
3. Compare whether the weekly picture agrees with the daily markers you care about.

---

## 13. Common problems and fixes

| Symptom | Likely cause | What to try |
|---------|--------------|-------------|
| `streamlit: command not found` | Virtual environment not active or packages not installed | `source .venv/bin/activate` then `pip install -r requirements.txt` |
| Fetch returns no data | Bad ticker, wrong market suffix, or empty date range | Verify the symbol on Yahoo Finance; widen dates; try `AAPL` as a sanity check |
| Chart empty after Custom dates | From is not before To, or range outside loaded data | Fix date order; use **All** once to see available span |
| SMA 200 missing or empty at the start | Not enough bars in the **loaded** history | Download a longer history (for example `5Y`) even if you view `1Y` |
| Too many markers | Many rules plus long history | Disable some families; lower **Max marker dates** |
| Weekly chart warns or skips indicators | Too few weekly bars in the current window | Widen timeframe or download more history |
| Upload CSV error about columns | File is not OHLCV with a `Date` column | Re-download with this project’s fetcher; ensure headers match |
| App looks stale after code changes | Old Streamlit session | Rerun, or press `R` in the app / restart `streamlit run` |

---

## 14. Project files (for the curious)

You do not need this section to use the app. It helps if you want to peek at the code.

| File | Role |
|------|------|
| `chart_app.py` | Streamlit UI: sidebar controls, fetch/upload, wiring indicators and markers |
| `chart_builder.py` | Builds Plotly figures (candles, panes, marker glyphs) |
| `data_utils.py` | Download/normalize data, compute indicators, detect marker events |
| `fetch_stock_data.py` | Optional CLI downloader into `data/` |
| `requirements.txt` | Python package list |
| `README.md` | Short setup reminder |
| `stock_charting_manual.md` | This manual |
| `data/` | Saved CSV files (usually gitignored) |

---

## Closing thoughts

If you remember only four things from this manual, make them these:

1. **Candles show the battle of a period; indicators summarize many periods.**
2. **Overlays live on price; oscillators live in their own panes.**
3. **Markers in this app are labeled math events, not trading advice.**
4. **Learn one tool at a time on liquid symbols before stacking everything.**

When you are ready to explore, start the app:

```bash
source .venv/bin/activate
streamlit run chart_app.py
```

Happy charting — and stay skeptical in a healthy way.
