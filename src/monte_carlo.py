import pandas as pd
import numpy as np


def simulate_terminal(S, r, sigma, T, N, seed=None):
    rng = np.random.default_rng(seed)
    Z = rng.standard_normal(N)
    return S*np.exp((r - 0.5*sigma**2)*T + sigma*np.sqrt(T)*Z)

def mc_price(St, K, r, T, option_type="call"):
    disc = np.exp(-r * T)
    if option_type == "call":
        return disc * np.maximum(St - K, 0).mean()
    elif option_type == "put":
        return disc * np.maximum(K - St, 0).mean()
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")
    

def build_mc_price_table(S, r, sigma, T, K, n_sims=10_000_000, seed=None):
    St = simulate_terminal(S, r, sigma, T, n_sims, seed=seed)
    return pd.DataFrame({
        "Strike Price": K,
        "MC Call": [mc_price(St, k, r, T, "call") for k in K],
        "MC Put": [mc_price(St, k, r, T, "put") for k in K],
    })

