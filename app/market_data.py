from __future__ import annotations
import random, time
from datetime import datetime, timezone, timedelta
import httpx
from .config import settings

class MarketData:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15)
        self.cache = {}

    async def close(self):
        await self.client.aclose()

    async def candles(self, symbol, interval, outputsize=300):
        if settings.use_live_data and settings.api_key:
            r = await self.client.get(
                "https://api.twelvedata.com/time_series",
                params={
                    "symbol": symbol, "interval": interval,
                    "outputsize": outputsize, "apikey": settings.api_key,
                    "format": "JSON"
                }
            )
            r.raise_for_status()
            data = r.json()
            if "values" not in data:
                raise RuntimeError(data.get("message", "No candle data"))
            return [{
                "time": x["datetime"], "open": float(x["open"]),
                "high": float(x["high"]), "low": float(x["low"]),
                "close": float(x["close"])
            } for x in reversed(data["values"])]

        # Clearly labelled synthetic data for testing only.
        key = (symbol, interval)
        rnd = random.Random(sum(map(ord, symbol+interval)) + int(time.time()//60))
        base = self.cache.get(key, 1.10 if "EUR" in symbol else 150.0 if "JPY" in symbol else 1.30)
        step = 0.0006 if base < 10 else 0.06
        minutes = {"1min":1,"5min":5,"15min":15,"30min":30,"1h":60,"4h":240,"1day":1440}
        delta = minutes.get(interval, 15)
        out=[]
        now=datetime.now(timezone.utc)
        for i in range(outputsize):
            t=now-timedelta(minutes=delta*(outputsize-i))
            o=base
            c=max(0.00001,o+rnd.gauss(0,step))
            h=max(o,c)+abs(rnd.gauss(0,step*.7))
            l=min(o,c)-abs(rnd.gauss(0,step*.7))
            out.append({"time":t.isoformat(),"open":o,"high":h,"low":l,"close":c})
            base=c
        self.cache[key]=base
        return out
