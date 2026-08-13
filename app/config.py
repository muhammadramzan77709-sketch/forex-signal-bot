import os
from dataclasses import dataclass

@dataclass
class Settings:
    api_key: str = os.getenv("TWELVE_DATA_API_KEY", "")
    use_live_data: bool = os.getenv("USE_LIVE_DATA", "true").lower() == "true"
    poll_seconds: int = int(os.getenv("POLL_SECONDS", "20"))
    symbols: list[str] = None
    execution_tf: str = os.getenv("EXECUTION_TF", "15min")
    min_score: int = int(os.getenv("SIGNAL_MIN_SCORE", "7"))
    risk_reward: float = float(os.getenv("RISK_REWARD", "2.0"))
    sl_atr_buffer: float = float(os.getenv("SL_ATR_BUFFER", "0.20"))
    allow_equilibrium: bool = os.getenv("ALLOW_EQUILIBRIUM", "false").lower() == "true"

    def __post_init__(self):
        self.symbols = [x.strip() for x in os.getenv(
            "SYMBOLS", "EUR/USD,GBP/USD,USD/JPY,GBP/JPY"
        ).split(",") if x.strip()]

settings = Settings()
