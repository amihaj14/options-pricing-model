import os
import json
import numpy as np
import pandas as pd
from datetime import datetime as dt, timedelta
from tiingo import TiingoClient

try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    SCRIPT_DIR = os.getcwd()


def load_secrets(secrets_path=None):
    path = secrets_path or os.path.join(SCRIPT_DIR, "secrets.json")
    with open(path) as f:
        return json.load(f)


def get_tiingo_client(secrets=None):
    secrets = secrets or load_secrets()
    config = {"api_key": secrets["tiingo_api_key"]}
    return TiingoClient(config)


def load_excel(filepath, data_dir=None):
    """Load a single Excel file (e.g. ZFL.TO.xlsx) with date index."""
    data_dir = data_dir or SCRIPT_DIR
    return pd.read_excel(os.path.join(data_dir, filepath), index_col=0, parse_dates=True)


def load_all_assets(data_dir=None):
    """Load bond/equity/gold ETF price histories from Excel files."""
    files = {
        "bond1": "ZFL.TO.xlsx",
        "bond2": "ZFM.TO.xlsx",
        "equity": "VFV.TO.xlsx",
        "gold": "CGL.TO.xlsx",
    }
    return {key: load_excel(path, data_dir) for key, path in files.items()}

def clean_data(df):
    """Drop NaNs and compute log returns on the 'Close' column."""
    df = df.dropna().copy()
    df["Returns"] = np.log(df["Close"] / df["Close"].shift(1))
    return df


def compute_volatility(df, window=30):
    """Rolling annualized volatility from log returns."""
    df = df.copy()
    df["Volatility"] = df["Returns"].rolling(window).std() * np.sqrt(252)
    return df


def load_tbill_data(filepath="tbill_3mnth.xlsx", data_dir=None):
    """Load and clean 3-month T-bill rate data."""
    data_dir = data_dir or SCRIPT_DIR
    df_t = pd.read_excel(os.path.join(data_dir, filepath))
    df_t.columns = ["date", "rf"]
    df_t["date"] = pd.to_datetime(df_t["date"], errors="coerce")
    df_t["rf"] = pd.to_numeric(df_t["rf"], errors="coerce")
    df_t = df_t.dropna(subset=["rf"])
    df_t["rf"] = df_t["rf"] / 100
    df_t["rf_daily"] = (1 + df_t["rf"]) ** (1 / 252) - 1
    df_t["rf_log_daily"] = np.log(1 + df_t["rf_daily"])
    return df_t


def load_equity_market_data(symbol, client, start_date="2020-01-01"):
    """Fetch equity price history from Tiingo, sorted most-recent-first."""
    df = client.get_dataframe(
        symbol,
        startDate=start_date,
        endDate=dt.today() - timedelta(days=1),
    )
    df.columns = [c.lower() for c in df.columns]
    df = df.sort_index(ascending=False)
    return df


def get_option_inputs(df, df_tbill, expiration_date):
    """Derive S, T, r, sigma, valuation_date from equity + T-bill data.

    df must be sorted most-recent-first with lowercase columns
    (e.g. from load_equity_market_data).
    """
    spot_row = df.iloc[0]
    S = spot_row["close"]
    valuation_date = spot_row.name.strftime("%Y-%m-%d")

    log_returns = np.log(df["adjclose"] / df["adjclose"].shift(1))
    sigma = log_returns.std() * np.sqrt(252)

    T = (expiration_date - dt.now()).total_seconds() / (365 * 24 * 60 * 60)
    r = df_tbill["rf_log_daily"].iloc[-1]

    return {
        "S": S,
        "T": T,
        "r": r,
        "sigma": sigma,
        "valuation_date": valuation_date,
        "log_returns": log_returns,
    }