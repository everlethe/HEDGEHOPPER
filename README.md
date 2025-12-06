# HEDGEHOPPER PoC

Proof-of-concept paper trading arbitrage engine for spot crypto pairs. The system
simulates cross-exchange arbitrage without placing live orders while recording
rich logs for later slippage and threshold optimization.

## Setup

```bash
pip install -r requirements.txt
```

## Configuration

Edit YAML files in `config/` to control enabled exchanges, pairs, and engine
parameters. The defaults cover six mock exchanges and three base assets
(TRX/XRP/LTC) versus USDT.

## Run paper trading

```bash
python -m hedgehopper_poc.main \
  --config-dir ./config \
  --duration-sec 60
```

The command loads configuration, spins a loop at the configured interval, pulls
mock order books, evaluates arbitrage opportunities, and appends simulated fills
and monitoring flags to CSV logs under `./logs` by default.

## Quick PnL summary

After a simulation run, compute aggregate PnL and trade counts from the CSV log:

```bash
python -m hedgehopper_poc.logger --log-file ./logs/fills.csv
```

The summary prints total PnL and trade counts per symbol to stdout.

## Next steps

This PoC focuses on paper trading only. Integration with real exchange APIs,
robust persistence, and production-grade monitoring can be added by replacing
the mock exchange client and extending the risk/monitor components.
