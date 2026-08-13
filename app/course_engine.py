from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Swing:
    index: int
    price: float
    kind: str          # STH, STL, ITH, ITL
    confirmed: bool = True

@dataclass
class Zone:
    low: float
    high: float
    kind: str          # BULL_OB, BEAR_OB, BULL_FVG, BEAR_FVG
    index: int

@dataclass
class Signal:
    symbol: str
    direction: str
    status: str
    score: int
    max_score: int
    entry: Optional[float]
    sl: Optional[float]
    tp: Optional[float]
    rr: float
    bias: str
    pd_zone: str
    liquidity: str
    poi: str
    reasons: list[str]
    warnings: list[str]
    levels: dict
    timestamp: str

def atr(c, n=14):
    if len(c) < n + 1:
        return None
    tr=[]
    for i in range(1,len(c)):
        tr.append(max(
            c[i]["high"]-c[i]["low"],
            abs(c[i]["high"]-c[i-1]["close"]),
            abs(c[i]["low"]-c[i-1]["close"])
        ))
    return sum(tr[-n:])/n

def confirmed_pivots(c, left=2, right=2):
    highs, lows = [], []
    for i in range(left, len(c)-right):
        h,l = c[i]["high"],c[i]["low"]
        left_h = all(h > c[j]["high"] for j in range(i-left,i))
        right_h = all(h >= c[j]["high"] for j in range(i+1,i+right+1))
        left_l = all(l < c[j]["low"] for j in range(i-left,i))
        right_l = all(l <= c[j]["low"] for j in range(i+1,i+right+1))
        if left_h and right_h:
            highs.append(Swing(i,h,"STH"))
        if left_l and right_l:
            lows.append(Swing(i,l,"STL"))
    return highs,lows

def intermediate_pivots(c, left=4, right=4):
    highs, lows = [], []
    for i in range(left, len(c)-right):
        h,l=c[i]["high"],c[i]["low"]
        if all(h > c[j]["high"] for j in range(i-left,i)) and all(h >= c[j]["high"] for j in range(i+1,i+right+1)):
            highs.append(Swing(i,h,"ITH"))
        if all(l < c[j]["low"] for j in range(i-left,i)) and all(l <= c[j]["low"] for j in range(i+1,i+right+1)):
            lows.append(Swing(i,l,"ITL"))
    return highs,lows

def last_before(swings, idx):
    x=[s for s in swings if s.index < idx]
    return x[-1] if x else None

def range_pd(c, lookback=100):
    x=c[-lookback:]
    hi=max(v["high"] for v in x); lo=min(v["low"] for v in x)
    return hi,lo,(hi+lo)/2

def sweep_levels(c, levels):
    x=c[-1]
    bsl = levels["sth"] is not None and x["high"] > levels["sth"] and x["close"] < levels["sth"]
    ssl = levels["stl"] is not None and x["low"] < levels["stl"] and x["close"] > levels["stl"]
    return bsl,ssl

def fvg_zones(c, a, min_atr=.10):
    if len(c)<3: return []
    z=[]
    a0,x=c[-3],c[-1]
    if x["low"] > a0["high"] and x["low"]-a0["high"] >= a*min_atr:
        z.append(Zone(a0["high"],x["low"],"BULL_FVG",len(c)-1))
    if x["high"] < a0["low"] and a0["low"]-x["high"] >= a*min_atr:
        z.append(Zone(x["high"],a0["low"],"BEAR_FVG",len(c)-1))
    return z

def ob_zone(c, a):
    if len(c)<3: return []
    prev,cur=c[-2],c[-1]
    z=[]
    if prev["close"]<prev["open"] and cur["close"]>prev["high"] and abs(cur["close"]-cur["open"])>=a*.8:
        z.append(Zone(prev["low"],prev["high"],"BULL_OB",len(c)-2))
    if prev["close"]>prev["open"] and cur["close"]<prev["low"] and abs(cur["close"]-cur["open"])>=a*.8:
        z.append(Zone(prev["low"],prev["high"],"BEAR_OB",len(c)-2))
    return z

def price_taps(zones, price):
    return [z for z in zones if z.low <= price <= z.high]

def displacement(c,a):
    x=c[-1]; body=abs(x["close"]-x["open"])
    return (
        x["close"]>x["open"] and body>=a*1.2,
        x["close"]<x["open"] and body>=a*1.2
    )

def analyse(symbol,daily,h4,h1,m15,min_score=7,rr=2.0,sl_buffer=.20,allow_eq=False):
    price=m15[-1]["close"]
    a=atr(m15) or max(price*.001,1e-8)

    dsh,dsl=confirmed_pivots(daily,2,2)
    dih,dil=intermediate_pivots(daily,4,4)
    hsh,hsl=confirmed_pivots(h4,2,2)
    hih,hil=intermediate_pivots(h4,4,4)
    osh,osl=confirmed_pivots(h1,2,2)
    oih,oil=intermediate_pivots(h1,4,4)
    lsh,lsl=confirmed_pivots(m15,2,2)
    lih,lil=intermediate_pivots(m15,4,4)

    d_ith=dih[-1] if dih else None
    d_itl=dil[-1] if dil else None
    h_ith=hih[-1] if hih else None
    h_itl=hil[-1] if hil else None
    h_sth=hsh[-1] if hsh else None
    h_stl=hsl[-1] if hsl else None
    l_sth=lsh[-1] if lsh else None
    l_stl=lsl[-1] if lsl else None

    dclose=daily[-1]["close"]; hclose=h4[-1]["close"]

    # Course rule: ITH/ITL breaks are meaningful bias events.
    d_bull = d_ith is not None and dclose > d_ith.price
    d_bear = d_itl is not None and dclose < d_itl.price
    h_bull = h_ith is not None and hclose > h_ith.price
    h_bear = h_itl is not None and hclose < h_itl.price

    # If neither ITH nor ITL is broken, infer direction from the most recent confirmed intermediate swing.
    if not d_bull and not d_bear and dih and dil:
        d_bull = dih[-1].index > dil[-1].index
        d_bear = not d_bull
    if not h_bull and not h_bear and hih and hil:
        h_bull = hih[-1].index > hil[-1].index
        h_bear = not h_bull

    bull_bias=d_bull and not h_bear
    bear_bias=d_bear and not h_bull
    bias="BULLISH" if bull_bias else "BEARISH" if bear_bias else "NEUTRAL"

    hi,lo,eq=range_pd(h4,100)
    zone="DISCOUNT" if price<eq else "PREMIUM" if price>eq else "EQUILIBRIUM"

    # HTF external liquidity and LTF internal liquidity.
    ext_bsl = h_ith.price if h_ith else (h_sth.price if h_sth else None)
    ext_ssl = h_itl.price if h_itl else (h_stl.price if h_stl else None)
    int_bsl = l_sth.price if l_sth else None
    int_ssl = l_stl.price if l_stl else None

    bsl = int_bsl is not None and m15[-1]["high"] > int_bsl and price < int_bsl
    ssl = int_ssl is not None and m15[-1]["low"] < int_ssl and price > int_ssl

    # HTF target liquidity: use nearest valid external level in the trade direction.
    buy_target_candidates=[x for x in [ext_bsl] if x is not None and x>price]
    sell_target_candidates=[x for x in [ext_ssl] if x is not None and x<price]
    ext_buy_target=min(buy_target_candidates) if buy_target_candidates else None
    ext_sell_target=max(sell_target_candidates) if sell_target_candidates else None

    bull_disp,bear_disp=displacement(m15,a)
    zones=fvg_zones(m15,a)+ob_zone(m15,a)
    bull_poi=price_taps([z for z in zones if z.kind.startswith("BULL")],price)
    bear_poi=price_taps([z for z in zones if z.kind.startswith("BEAR")],price)

    # Lower-TF structure confirmation: a reclaimed STH after sell-side sweep
    # or broken STL after buy-side sweep.
    bull_mss=l_sth is not None and price>l_sth.price
    bear_mss=l_stl is not None and price<l_stl.price

    # Inducement proxy: LTF sweep/structure move while HTF bias remains unchanged.
    bullish_inducement=ssl and bull_mss and bull_bias
    bearish_inducement=bsl and bear_mss and bear_bias

    buy_checks=[
        (bull_bias,"Daily/4H ITH-ITL bias bullish"),
        (zone=="DISCOUNT" or (allow_eq and zone=="EQUILIBRIUM"),"Price in discount / allowed equilibrium"),
        (ssl,"Internal sell-side liquidity swept"),
        (bull_mss,"15m STL/short-term structure reclaimed"),
        (bull_disp,"Bullish displacement"),
        (bool(bull_poi) or any(z.kind=="BULL_FVG" for z in zones),"Bullish POI/FVG present"),
        (bullish_inducement,"Sweep + LTF confirmation with HTF bias intact"),
    ]
    sell_checks=[
        (bear_bias,"Daily/4H ITH-ITL bias bearish"),
        (zone=="PREMIUM" or (allow_eq and zone=="EQUILIBRIUM"),"Price in premium / allowed equilibrium"),
        (bsl,"Internal buy-side liquidity swept"),
        (bear_mss,"15m STH/short-term structure broken"),
        (bear_disp,"Bearish displacement"),
        (bool(bear_poi) or any(z.kind=="BEAR_FVG" for z in zones),"Bearish POI/FVG present"),
        (bearish_inducement,"Sweep + LTF confirmation with HTF bias intact"),
    ]

    bs=sum(int(ok) for ok,_ in buy_checks)
    ss=sum(int(ok) for ok,_ in sell_checks)

    direction="WAIT"; entry=sl=tp=None; reasons=[]; warnings=[]
    if bs>=min_score and bs>ss:
        direction="BUY"; entry=price
        structural=l_stl.price if l_stl else min(x["low"] for x in m15[-10:])
        sl=structural-a*sl_buffer
        risk=entry-sl
        target=ext_buy_target if ext_buy_target and ext_buy_target>entry else entry+risk*rr
        tp=target
        if risk<=0 or tp<=entry:
            direction="WAIT"; warnings.append("Invalid BUY risk/target geometry.")
        else:
            reasons=[r for ok,r in buy_checks if ok]
    elif ss>=min_score and ss>bs:
        direction="SELL"; entry=price
        structural=l_sth.price if l_sth else max(x["high"] for x in m15[-10:])
        sl=structural+a*sl_buffer
        risk=sl-entry
        target=ext_sell_target if ext_sell_target and ext_sell_target<entry else entry-risk*rr
        tp=target
        if risk<=0 or tp>=entry:
            direction="WAIT"; warnings.append("Invalid SELL risk/target geometry.")
        else:
            reasons=[r for ok,r in sell_checks if ok]

    poi="BULLISH POI" if bull_poi else "BEARISH POI" if bear_poi else "NO FRESH POI"
    liquidity="SSL SWEPT" if ssl else "BSL SWEPT" if bsl else "NO SWEEP"

    levels={
        "daily_ith": d_ith.price if d_ith else None,
        "daily_itl": d_itl.price if d_itl else None,
        "h4_ith": h_ith.price if h_ith else None,
        "h4_itl": h_itl.price if h_itl else None,
        "h1_sth": h_sth.price if h_sth else None,
        "h1_stl": h_stl.price if h_stl else None,
        "ltf_sth": l_sth.price if l_sth else None,
        "ltf_stl": l_stl.price if l_stl else None,
        "external_bsl": ext_bsl,
        "external_ssl": ext_ssl,
        "equilibrium": eq,
    }

    return Signal(
        symbol,direction,"CONFIRMED" if direction!="WAIT" else "WAIT",
        max(bs,ss),len(buy_checks),entry,sl,tp,rr,bias,zone,liquidity,poi,
        reasons,warnings,levels,m15[-1]["time"]
    )
