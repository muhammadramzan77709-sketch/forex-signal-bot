# Forex Course Signal Bot — Precise Course Engine v2

This version restructures the bot around the concepts supplied in the user's Videos 1–11 transcripts.

## Course model implemented

1. **Fractal structure**
   - Every timeframe is analysed independently.
   - Higher-timeframe swings become intermediate structure on lower timeframes.
   - Confirmed pivots require a left swing and a right swing; the bot does not label an unconfirmed pivot as ITH/ITL.

2. **STH / STL**
   - Confirmed short-term highs/lows are pivot highs/lows.
   - A single liquidity grab of an STH/STL is NOT automatically an ITH/ITL.

3. **ITH / ITL**
   - Intermediate pivots are confirmed from a wider fractal.
   - An ITH/ITL is treated as a higher-quality bias reference than an STH/STL.
   - Breaking an ITH/ITL can invalidate the current higher-timeframe bias.
   - Breaking only an STL/STH is treated as a temporary/short-term event, not an automatic overall trend reversal.

4. **HTF bias**
   - Daily and 4H are the main directional filters.
   - 1H is the mid-timeframe context.
   - 15m is the default execution timeframe.
   - A signal is blocked when the higher-timeframe bias is contradictory.

5. **Premium / Discount**
   - Uses a configurable HTF dealing range.
   - Longs prefer discount; shorts prefer premium.
   - Equilibrium is explicitly recognised as neutral unless the configuration allows an equilibrium setup.

6. **Liquidity**
   - Internal liquidity (IRL) is represented by short-term swing liquidity inside the current range.
   - External liquidity (ERL) is represented by major HTF swing liquidity.
   - A sweep requires price to trade beyond a prior level and close back through it.
   - The engine distinguishes:
     - sell-side sweep -> potential bullish setup
     - buy-side sweep -> potential bearish setup

7. **Inducement / trap proxy**
   - A lower-timeframe structure break without HTF confirmation is treated as a possible temporary move.
   - The engine looks for a sweep + displacement + reclaim/break sequence instead of treating every LTF structure break as a trend reversal.

8. **POI**
   - Explicit OHLC proxies are used for:
     - bullish/bearish order blocks
     - bullish/bearish FVGs
   - POIs are stored as price zones rather than single labels.
   - A signal prefers price to return/tap a POI after the liquidity event, rather than buying/selling simply because an FVG or OB exists.

9. **Displacement**
   - Strong candle body relative to ATR is required.
   - Displacement following a liquidity event is stronger than displacement in isolation.

10. **Sequence**
    - The engine prefers the course-style sequence:
      HTF bias -> location (PD) -> liquidity event -> LTF structure confirmation -> displacement -> POI/FVG -> entry.
    - It does not claim to detect "institutional intent"; that part is inherently discretionary.

11. **TP / SL**
    - SL is placed beyond the structural invalidation point plus ATR buffer.
    - TP prefers the next relevant liquidity target when available.
    - If no valid liquidity target exists, configurable fixed R:R is used.
    - A signal is rejected if the target is on the wrong side or the risk is invalid.

12. **No fake certainty**
    - The dashboard shows exactly which conditions passed/failed.
    - "WAIT" is a valid output.
    - This is a rule-based approximation of the supplied course, not a guarantee of profitability.

## Live data

The included adapter uses Twelve Data. You can replace `app/market_data.py` with another broker/data provider without changing the course engine.

Demo mode is used when no API key is configured.

## Run locally

Python 3.10+:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m app.main
```

Open `http://127.0.0.1:8000`.

## Environment variables

- `TWELVE_DATA_API_KEY`
- `USE_LIVE_DATA=true`
- `POLL_SECONDS=20`
- `SYMBOLS=EUR/USD,GBP/USD,USD/JPY,GBP/JPY`
- `EXECUTION_TF=15min`
- `SIGNAL_MIN_SCORE=7`
- `RISK_REWARD=2.0`
- `SL_ATR_BUFFER=0.20`
- `ALLOW_EQUILIBRIUM=false`

## Important before real money

The project is intentionally signal-only. Do not connect it to a live broker yet.

Before real-money use, add:
- persistent database
- authentication
- HTTPS
- provider failover
- spread/commission/slippage checks
- historical backtest
- walk-forward testing
- duplicate-signal protection
- broker execution adapter with a separate kill switch
- monitoring/logging
- timezone/session rules
- data-quality checks
