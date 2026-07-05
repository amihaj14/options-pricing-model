from datetime import datetime as dt, timedelta
from time import sleep as time_sleep

import pandas as pd
import requests

BASE_URL = "https://api.onclickmedia.com/options/"


def safe_get_json(url, params, timeout=15):
    """GET request that returns parsed JSON, or None on any failure
    (bad status, empty body, invalid JSON)."""
    resp = requests.get(url, params=params, timeout=timeout)
    if resp.status_code != 200:
        return None
    text = resp.text.strip()
    if not text:
        return None
    try:
        return resp.json()
    except ValueError:
        return None


def get_valid_date(base_params, date_str, url=BASE_URL, max_tries=10, pause=0.5):
    """Walk backward from date_str to find the most recent date with data."""
    d = dt.strptime(date_str, "%Y-%m-%d")
    for _ in range(max_tries):
        test_params = {**base_params, "date": d.strftime("%Y-%m-%d")}
        records = safe_get_json(url, test_params)
        if records:
            return d.strftime("%Y-%m-%d")
        d -= timedelta(days=1)
        time_sleep(pause)
    raise ValueError("No valid trading date found nearby.")


def fetch_option_chain(symbol, expiration, valuation_date, S, option_type="call", strike_pct_low=0.91, strike_pct_high=1.16, url=BASE_URL):
    """Fetch the option chain for `symbol`/`expiration`, auto-correct the
    valuation date if needed, and filter to a strike band around spot S.

    Returns (opt_chain_df, resolved_valuation_date).
    """
    base_params = {
        "ticker": symbol,
        "date": valuation_date,
        "expiration": expiration,
        "type": option_type,
        "output": "json-v1",
    }

    resolved_date = get_valid_date(base_params, valuation_date, url=url)
    params = {**base_params, "date": resolved_date}

    full_chain = safe_get_json(url, params)
    if not full_chain:
        raise RuntimeError(f"Failed to fetch option chain for params={params}")

    opt_chain = pd.json_normalize(full_chain, sep="_")

    k_min = round(S * strike_pct_low, 0)
    k_max = round(S * strike_pct_high, 0)
    opt_chain = opt_chain[
        (opt_chain["strike"] >= k_min) & (opt_chain["strike"] <= k_max)
    ].copy()

    opt_chain["Pmkt"] = (opt_chain["bid"] + opt_chain["ask"]) / 2

    return opt_chain, resolved_date