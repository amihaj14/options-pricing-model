
import pandas as pd
import numpy as np
from scipy.optimize import brentq
from pricing import black_scholes, vega


def iv_NR(S, K, T, r, Pmkt, option_type="call", sigma0=None, tol_sigma=1e-8, tol_price=1e-8, max_iter=100):
    if sigma0 is None:
        sigma = np.sqrt(2 * np.pi / T) * (Pmkt / S)
    else:
        sigma = sigma0

    sigma = max(sigma, 1e-6)

    for _ in range(max_iter):
        price = black_scholes(S, K, T, r, sigma, option_type=option_type)
        v = vega(S, K, T, r, sigma)

        diff = price - Pmkt
        if abs(diff) < tol_price:
            return sigma

        if abs(v) < 1e-12:
            raise ValueError("Vega is too small; Newton method unstable.")

        sigma_next = sigma - diff / v

        if sigma_next <= 0:
            sigma_next = sigma / 2

        if abs(sigma_next - sigma) < tol_sigma:
            return sigma_next

        sigma = sigma_next

    raise RuntimeError("Newton method did not converge.")

def iv_brentq(S, K, T, r, Pmkt, option_type="call", lo=1e-6, hi=5.0):
    def f(sigma):
        return black_scholes(S, K, T, r, sigma, option_type=option_type) - Pmkt
    try:
        return brentq(f, lo, hi, xtol=1e-8)
    except ValueError:
        return np.nan
    

def iv_solve(S, K, T, r, Pmkt, option_type="call", sigma0=None):
    try:
        return iv_NR(S, K, T, r, Pmkt, option_type=option_type, sigma0=sigma0)
    except (ValueError, RuntimeError):
        return iv_brentq(S, K, T, r, Pmkt, option_type=option_type)
    

def build_iv_table(S, opt_chain, T, r, option_type="call"):
    records = []
    for _, row in opt_chain.iterrows():
        strike = row["strike"]
        pmkt = row["Pmkt"]
        iv = iv_solve(S, strike, T, r, pmkt, option_type=option_type)
        price_check = (black_scholes(S, strike, T, r, iv, option_type=option_type)
                       if not np.isnan(iv) else np.nan)
        records.append({
            "Strike Price": strike,
            "IV": iv,
            "Pmkt": pmkt,
            "Price Check": price_check,
        })

    bs_iv = pd.DataFrame(records)
    bs_iv["Price Diff"] = (bs_iv["Price Check"] - bs_iv["Pmkt"]).abs()
    return bs_iv