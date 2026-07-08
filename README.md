# Options Pricing Model

A Python-based options pricing and analysis toolkit that combines Black-Scholes analytics, Monte Carlo simulation, and implied volatility solving, validated against live market option chain data.

## Overview

This project prices European-style options on AMD using two independent methods — closed-form Black-Scholes and Monte Carlo simulation — and compares both against real market prices fetched from a live option chain API. It also solves for implied volatility using a Newton-Raphson method with a Brent's-method fallback, and builds an implied volatility smile from market data.

The goal is not just to price options, but to validate model assumptions: how closely do Black-Scholes and Monte Carlo agree with each other under matched inputs, and how far does either diverge from what the market is actually pricing.

## Features

- **Black-Scholes pricing** — European call/put pricing plus the full Greeks (Delta, Gamma, Theta, Vega, Rho)
- **Monte Carlo simulation** — GBM-based terminal price simulation and discounted payoff pricing
- **Implied volatility solver** — Newton-Raphson with automatic fallback to Brent's method for strikes where Newton fails (e.g. near-zero Vega, deep ITM/OTM)
- **Live market data** — equity prices via Tiingo, option chains via a live options API, 3-month T-bill rates as the risk-free proxy
- **Model validation** — Black-Scholes vs. Monte Carlo price/IV comparison, with put-call parity and pricing error analysis

## Project Structure

options-pricing-model/
├── data/
│   └── tbill_3mnth.xlsx
├── src/
│   ├── data_loader.py       # Load secrets, Tiingo equity data, T-bill rates
│   ├── pricing.py           # Black-Scholes pricing and Greeks
│   ├── monte_carlo.py       # GBM simulation and Monte Carlo pricing
│   ├── implied_vol.py       # Newton-Raphson / Brent IV solvers
│   └── option_api.py        # Live option chain fetching
├── secrets.json             # API keys (excluded from version control)
├── optionsPricing.ipynb     # Main analysis notebook
└── README.md

## Setup

### Prerequisites

- Python 3.11+
- A Tiingo API key (equity price data)
- Access to a live options data API (option chain / bid-ask data)

### Installation

```bash
git clone <repo-url>
cd options-pricing-model
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Required packages

numpy
pandas
scipy
requests
tiingo
plotly
nbformat
openpyxl
jupyter

### API keys

Create a `secrets.json` file in the project root (not committed to version control):

```json
{
  "tiingo_api_key": "YOUR_TIINGO_API_KEY"
}
```

## Usage

Open `optionsPricing.ipynb` and run cells top to bottom. The notebook:

1. Loads secrets and initializes the Tiingo client
2. Loads T-bill data for the risk-free rate
3. Pulls live equity data for the target symbol (default: AMD) and derives spot price, time to expiration, volatility, and valuation date
4. Fetches the live option chain for a chosen expiration and strike range
5. Prices the chain with Black-Scholes and Monte Carlo
6. Solves for implied volatility across the chain
7. Plots the implied volatility smile and compares Black-Scholes vs. Monte Carlo pricing/IV

To change the underlying symbol or expiration, edit these lines in the notebook:

```python
symbol = "AMD"
optexp = dt(2026, 7, 31)
```

## Key Modules

### `pricing.py`

Core Black-Scholes formulas (`black_scholes`, `delta`, `gamma`, `theta`, `vega`, `rho`) plus `build_greeks_table()` and `build_bs_price_table()` for building strike-indexed DataFrames.

### `monte_carlo.py`

`simulate_terminal()` generates GBM terminal prices under the risk-neutral measure; `mc_price()` discounts the payoff; `build_mc_price_table()` prices an entire strike chain from one simulated path set.

### `implied_vol.py`

`iv_NR()` is a Newton-Raphson solver seeded with the Brenner-Subrahmanyam approximation; `iv_brentq()` is a bracketed fallback for cases where Newton fails to converge (e.g. tiny Vega); `iv_solve()` tries Newton first and falls back automatically; `build_iv_table()` runs this across a full option chain.

### `data_loader.py`

Handles all data ingestion: secrets, Excel-based T-bill data (with configurable `data_dir`), and live Tiingo equity pulls. `get_option_inputs()` derives all Black-Scholes inputs (`S`, `T`, `r`, `sigma`) from equity and T-bill data in one call.

### `option_api.py`

Fetches live option chain data, automatically walking backward to find the nearest valid trading date if the requested date has no data, then filters the chain to a strike band around spot.

## Model Validation

The notebook includes several checks to confirm the pricing models are implemented correctly:

- **Black-Scholes vs. Monte Carlo**: under matched inputs (same `sigma`, `T`, `r`), MC prices and implied vols converge to the Black-Scholes values as `n_sims` grows, confirming the two independent implementations agree.
- **IV round-trip check**: solving for implied volatility from a Black-Scholes price and re-pricing with that IV recovers the original price almost exactly.
- **Market vs. model comparison**: real market bid-ask midpoints are compared against both model prices to reveal where the constant-volatility assumption breaks down (typically at strikes far from at-the-money, where the market prices in a volatility smile that neither model captures without strike-dependent volatility input).

## Known Limitations

- Both Black-Scholes and the current Monte Carlo implementation assume constant volatility (GBM), so neither reproduces the market's implied volatility smile/skew — this is an expected and documented divergence, not a bug.
- Pricing is currently limited to European-style options; no early-exercise (American option) support.
- Implied volatility solving assumes the underlying asset follows a single volatility surface per snapshot; no term structure across multiple expirations is modeled yet.

## License

Personal research project. Not intended for production trading use.
