# What Fails

- Extremely short windows can create noisy, high-turnover candidates.
- Expressions with minimal variation from stored history tend to fail diversity checks.


- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 10) - 1) | status=tested | sharpe=2.53 | fitness=2.00 | notes=Self-correlation above maximum.
- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.98 | fitness=0.61 | notes=Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.
- rank(close / ts_mean(close, 5) - 1) | status=tested | sharpe=2.08 | fitness=0.89 | notes=Fitness below threshold.; Self-correlation above maximum.
- rank(ts_mean(returns, 10)) | status=tested | sharpe=0.94 | fitness=2.15 | notes=Sharpe below threshold.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 20) - 1) | status=tested | sharpe=2.43 | fitness=2.20 | notes=Turnover above maximum.; Self-correlation above maximum.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=1.41 | fitness=0.90 | notes=Sharpe below threshold.; Fitness below threshold.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=2.68 | fitness=1.00 | notes=Self-correlation above maximum.
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=2.42 | fitness=1.37 | notes=Drawdown above maximum.; Self-correlation above maximum.
- rank(ts_mean(returns, 65)) | status=tested | sharpe=1.79 | fitness=0.65 | notes=Fitness below threshold.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 10) - 1) | status=tested | sharpe=2.53 | fitness=2.00 | notes=Self-correlation above maximum.
- rank(ts_delta(close, 20) / ts_std_dev(close, 20)) | status=tested | sharpe=1.93 | fitness=2.00 | notes=Self-correlation above maximum.
- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.98 | fitness=0.61 | notes=Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.
- rank(close / ts_mean(close, 5) - 1) | status=tested | sharpe=2.08 | fitness=0.89 | notes=Fitness below threshold.; Self-correlation above maximum.
- rank(ts_mean(returns, 10)) | status=tested | sharpe=0.94 | fitness=2.15 | notes=Sharpe below threshold.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 20) - 1) | status=tested | sharpe=2.43 | fitness=2.20 | notes=Turnover above maximum.; Self-correlation above maximum.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=1.41 | fitness=0.90 | notes=Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=2.68 | fitness=1.00 | notes=Self-correlation above maximum.
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=2.42 | fitness=1.37 | notes=Drawdown above maximum.; Self-correlation above maximum.
- rank(ts_mean(returns, 65)) | status=tested | sharpe=1.79 | fitness=0.65 | notes=Fitness below threshold.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 10) - 1) | status=tested | sharpe=2.53 | fitness=2.00 | notes=Self-correlation above maximum.
- rank(ts_delta(close, 20) / ts_std_dev(close, 20)) | status=tested | sharpe=1.93 | fitness=2.00 | notes=Self-correlation above maximum.
- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.98 | fitness=0.61 | notes=Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.
- rank(close / ts_mean(close, 5) - 1) | status=tested | sharpe=2.08 | fitness=0.89 | notes=Fitness below threshold.; Self-correlation above maximum.
- rank(ts_mean(returns, 10)) | status=tested | sharpe=0.94 | fitness=2.15 | notes=Sharpe below threshold.; Drawdown above maximum.; Self-correlation above maximum.
- rank(close / ts_mean(close, 20) - 1) | status=tested | sharpe=2.43 | fitness=2.20 | notes=Turnover above maximum.; Self-correlation above maximum.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=1.41 | fitness=0.90 | notes=Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=2.68 | fitness=1.00 | notes=Self-correlation above maximum.
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=2.42 | fitness=1.37 | notes=Drawdown above maximum.; Self-correlation above maximum.
- rank(ts_mean(returns, 65)) | status=tested | sharpe=1.79 | fitness=0.65 | notes=Fitness below threshold.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=-1.12 | fitness=-0.67 | notes=Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=2.45 | fitness=1.93 | notes=Turnover above maximum.; Drawdown above maximum.; Self-correlation above maximum.

- rank(ts_mean(returns, 5)) | status=tested | sharpe=-1.12 | fitness=-0.67 | notes=hermes pre-review: FAIL; deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL
- rank(close / ts_mean(close, 10) - 1) | status=tested | sharpe=-0.98 | fitness=-0.62 | notes=WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL
- rank(ts_delta(close, 20) / ts_std_dev(close, 20)) | status=tested | sharpe=-0.57 | fitness=-0.30 | notes=hermes pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL

- rank(-ts_delta(close, 5)) | status=tested | sharpe=1.36 | fitness=0.77 | notes=WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.; hermes post-review: FAIL
- rank(-(close / ts_mean(close, 10) - 1)) | status=tested | sharpe=0.98 | fitness=0.62 | notes=WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.; hermes post-review: FAIL
- rank(-zscore(ts_delta(vwap, 20))) | status=tested | sharpe=0.72 | fitness=0.45 | notes=hermes pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; hermes post-review: FAIL
- rank(-ts_delta(close, 60)) | status=tested | sharpe=0.80 | fitness=0.62 | notes=WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.; hermes post-review: FAIL
- rank(-(close / ts_mean(close, 5) - 1)) | status=tested | sharpe=1.40 | fitness=0.87 | notes=WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.; hermes post-review: FAIL

- rank(ts_delta(close, 5) / ts_std_dev(close, 5)) | status=tested | sharpe=-1.12 | fitness=-0.57 | notes=deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL
- rank(ts_delta(close, 10) / ts_std_dev(close, 10)) | status=tested | sharpe=-0.66 | fitness=-0.32 | notes=deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL
- rank(ts_delta(close, 60) / ts_std_dev(close, 60)) | status=tested | sharpe=-0.66 | fitness=-0.51 | notes=WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL
- zscore(ts_mean(ts_delta(close, 10), 10) / ts_std_dev(returns, 10)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 400 Client Error: Bad Request for url: https://api.worldquantbrain.com/simulations
- rank(zscore(ts_delta(close, 60) / ts_std_dev(close, 60)) + 0.5 * ts_corr(close, volume, 60) - 0.3 * ts_delta(returns, 1) | status=invalid | sharpe=0.00 | fitness=0.00 | notes=Parentheses are unbalanced.

- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 6XRG7J7J: Sub-universe Sharpe of -0.83 is below cutoff of -0.3. SELF_CORRELATION is still pending.

- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 6XRG7J7J: Sub-universe Sharpe of -0.83 is below cutoff of -0.3. SELF_CORRELATION is still pending.

- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 1YoWqo1m: Sub-universe Sharpe of -0.78 is below cutoff of -0.4. SELF_CORRELATION is still pending.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 2rvGMGoZ: Sub-universe Sharpe of -0.39 is below cutoff of -0.3. SELF_CORRELATION is still pending.
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations

- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 1YoWqo1m: Sub-universe Sharpe of -0.78 is below cutoff of -0.4. SELF_CORRELATION is still pending.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for blNxkX2M: Sub-universe Sharpe of 0.27 is below cutoff of 0.4. SELF_CORRELATION is still pending.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for VkXM90MV: Sub-universe Sharpe of -0.47 is below cutoff of -0.3. SELF_CORRELATION is still pending.
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 6XRG7J7J: Sub-universe Sharpe of -0.83 is below cutoff of -0.3. SELF_CORRELATION is still pending.

- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 1YoWqo1m: Sub-universe Sharpe of -0.78 is below cutoff of -0.4. SELF_CORRELATION is still pending.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for blNxkX2M: Sub-universe Sharpe of 0.27 is below cutoff of 0.4. SELF_CORRELATION is still pending.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: 429 Client Error: Too Many Requests for url: https://api.worldquantbrain.com/simulations
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 6XRG7J7J: Sub-universe Sharpe of -0.83 is below cutoff of -0.3. SELF_CORRELATION is still pending.

- rank(ts_mean(returns, 60)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 1YoWqo1m: Sub-universe Sharpe of -0.78 is below cutoff of -0.4. SELF_CORRELATION is still pending.
- rank(ts_delta(volume, 5) * -ts_delta(close, 5)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for blNxkX2M: Sub-universe Sharpe of 0.27 is below cutoff of 0.4. SELF_CORRELATION is still pending.
- rank(close / ts_mean(close, 15) - 1) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
- rank(ts_delta(close, 25) / ts_std_dev(close, 20)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: Timed out waiting for alpha checks to settle for 2rvGMGoZ: Sub-universe Sharpe of -0.39 is below cutoff of -0.3. SELF_CORRELATION is still pending.
- rank(ts_mean(returns, 65)) | status=tested | sharpe=0.00 | fitness=0.00 | notes=Simulation failed: HTTPSConnectionPool(host='api.worldquantbrain.com', port=443): Read timed out. (read timeout=30)

- rank(ts_delta(close, 20) / ts_std_dev(close, 60)) * rank(ts_corr(volume, returns, 20) - ts_corr(volume, returns, 5)) | status=tested | sharpe=2.10 | fitness=0.94 | notes=deerflow pre-review: FAIL; Fitness 0.94 < threshold 1.00.; Self-correlation 1.00 > maximum 0.70.
- rank(ts_mean(returns, 20) / ts_std_dev(returns, 60)) * rank(volume / ts_mean(volume, 20) - ts_mean(volume, 5) / ts_mean(volume, 60)) | status=tested | sharpe=2.04 | fitness=2.00 | notes=deerflow pre-review: FAIL; Self-correlation 1.00 > maximum 0.70.
- rank(ts_delta(close, 10) / ts_std_dev(close, 20)) * rank(ts_corr(volume, returns, 60)) | status=tested | sharpe=1.77 | fitness=1.83 | notes=Self-correlation 1.00 > maximum 0.70.
- `rank(ts_delta(close, 5) / ts_std_dev(close, 20)) * rank(ts_delta(ts_corr(volume, returns, 20) - ts_corr(volume, returns, 5), 3) / ts_mean(volume, 20))` | status=invalid | sharpe=0.00 | fitness=0.00 | notes=Expression contains unsupported characters.
- `zscore(rank(ts_delta(close, 5) / ts_std_dev(returns, 20)) * rank(ts_corr(volume, returns, 10)) - rank(ts_mean(volume, 5) / ts_mean(volume, 60)) * rank(ts_delta(returns, 20)))` | status=invalid | sharpe=0.00 | fitness=0.00 | notes=Expression contains unsupported characters.

- rank(ts_mean(returns, 10) / ts_std_dev(returns, 60)) * rank(1 - ts_corr(volume, returns, 5)) | status=tested | sharpe=0.91 | fitness=0.57 | notes=Sharpe ratio 0.91 < threshold 1.50.; Fitness 0.57 < threshold 1.00.; Drawdown 34.00% > maximum 30.00%.; Self-correlation 0.86 > maximum 0.70.
- `zscore(rank(ts_mean(returns, 10) / ts_std_dev(returns, 20))) * rank(1 - ts_corr(volume, ts_delta(returns, 3), 10)) + 0.3 * rank(ts_delta(volume, 1) / ts_mean(volume, 20))` | status=invalid | sharpe=0.00 | fitness=0.00 | notes=Expression contains unsupported characters.
- `rank(ts_mean(returns, 10) / ts_std_dev(returns, 20)) + rank(-ts_corr(volume, returns, 20)) + 0.3 * rank(ts_delta(volume, 5) / ts_mean(volume, 20))` | status=invalid | sharpe=0.00 | fitness=0.00 | notes=Expression contains unsupported characters.
