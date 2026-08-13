from __future__ import annotations
import asyncio,json
from pathlib import Path
from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .market_data import MarketData
from .course_engine import analyse

app=FastAPI(title="Forex Course Signal Bot — Precise v2",version="2.0.0")
BASE=Path(__file__).parent
app.mount("/static",StaticFiles(directory=BASE/"static"),name="static")
md=MarketData(); signals={}; clients=set()

@app.get("/")
async def index(): return FileResponse(BASE/"static"/"index.html")

@app.get("/api/status")
async def status():
    live=bool(settings.use_live_data and settings.api_key)
    return {
        "live_data":live,
        "provider":"Twelve Data" if live else "Mock / Demo",
        "symbols":settings.symbols,
        "execution_tf":settings.execution_tf,
        "min_score":settings.min_score,
        "rr":settings.risk_reward,
        "course_engine":"Fractal + ITH/ITL + STH/STL + PD + IRL/ERL + Sweep + MSS + Displacement + FVG/OB + structural TP/SL"
    }

@app.get("/api/signals")
async def get_signals(): return {"signals":list(signals.values())[-200:]}

async def analyse_symbol(symbol):
    d=await md.candles(symbol,"1day",220)
    h4=await md.candles(symbol,"4h",220)
    h1=await md.candles(symbol,"1h",220)
    m15=await md.candles(symbol,settings.execution_tf,300)
    s=analyse(symbol,d,h4,h1,m15,settings.min_score,settings.risk_reward,settings.sl_atr_buffer,settings.allow_equilibrium)
    if s.direction!="WAIT":
        signals[f"{symbol}:{s.timestamp}:{s.direction}"]=s.__dict__
    return s

@app.get("/api/analyse/{symbol:path}")
async def analyse_one(symbol:str): return (await analyse_symbol(symbol)).__dict__

async def broadcast(x):
    dead=[]
    for ws in clients:
        try: await ws.send_text(json.dumps(x))
        except: dead.append(ws)
    for ws in dead: clients.discard(ws)

async def loop():
    while True:
        for symbol in settings.symbols:
            try:
                s=await analyse_symbol(symbol)
                await broadcast({"type":"signal","data":s.__dict__})
            except Exception as e:
                await broadcast({"type":"error","symbol":symbol,"message":str(e)})
        await asyncio.sleep(settings.poll_seconds)

@app.on_event("startup")
async def startup(): app.state.task=asyncio.create_task(loop())

@app.on_event("shutdown")
async def shutdown():
    app.state.task.cancel()
    await md.close()

@app.websocket("/ws")
async def websocket(ws:WebSocket):
    await ws.accept(); clients.add(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: clients.discard(ws)

if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
