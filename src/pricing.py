import numpy as np
from scipy.stats import norm


def N(d):
    """Standard normal CDF."""
    return norm.cdf(d)


def N_prime(d):
    """Standard normal PDF."""
    return norm.pdf(d)


def _d1_d2(S, K, T, r, sigma):
    d1 = (np.log(S / K) + (r + (sigma ** 2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    return d1, d2


def black_scholes(S, K, T, r, sigma, option_type="call"):
    """Black-Scholes price for a European call or put."""
    if T <= 0:
        # Option has expired: value equals intrinsic value, no time value left
        if option_type == "call":
            return max(S - K, 0.0)
        elif option_type == "put":
            return max(K - S, 0.0)
        else:
            raise ValueError("Invalid option type. Must be 'call' or 'put'.")

    d1, d2 = _d1_d2(S, K, T, r, sigma)

    if option_type == "call":
        return S * N(d1) - K * np.exp(-r * T) * N(d2)
    elif option_type == "put":
        return K * np.exp(-r * T) * N(-d2) - S * N(-d1)
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")


def delta(S, K, T, r, sigma, option_type="call"):
    d1, _ = _d1_d2(S, K, T, r, sigma)
    if option_type == "call":
        return N(d1)
    elif option_type == "put":
        return N(d1) - 1
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")


def gamma(S, K, T, r, sigma):
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return N_prime(d1) / (S * sigma * np.sqrt(T))


def theta(S, K, T, r, sigma, option_type="call"):
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if option_type == "call":
        return (-S * N_prime(d1) * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * N(d2))
    elif option_type == "put":
        return (-S * N_prime(d1) * sigma / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * N(-d2))
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")


def vega(S, K, T, r, sigma):
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return S * N_prime(d1) * np.sqrt(T)


def rho(S, K, T, r, sigma, option_type="call"):
    _, d2 = _d1_d2(S, K, T, r, sigma)
    if option_type == "call":
        return K * T * np.exp(-r * T) * N(d2)
    elif option_type == "put":
        return -K * T * np.exp(-r * T) * N(-d2)
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")


def build_greeks_table(S, K, T, r, sigma, option_type="call"):
    """Build a DataFrame of Greeks across a list/array of strikes K."""
    import pandas as pd
    return pd.DataFrame({
        "Strike Price": K,
        "Delta": [delta(S, k, T, r, sigma, option_type) for k in K],
        "Gamma": [gamma(S, k, T, r, sigma) for k in K],
        "Theta": [theta(S, k, T, r, sigma, option_type) for k in K],
        "Vega": [vega(S, k, T, r, sigma) for k in K],
        "Rho": [rho(S, k, T, r, sigma, option_type) for k in K],
    })


def build_bs_price_table(S, K, T, r, sigma):
    """Build a DataFrame comparing B-S call/put prices across strikes K."""
    import pandas as pd
    return pd.DataFrame({
        "Strike Price": K,
        "B-S Call": [black_scholes(S, k, T, r, sigma, "call") for k in K],
        "B-S Put": [black_scholes(S, k, T, r, sigma, "put") for k in K],
    })