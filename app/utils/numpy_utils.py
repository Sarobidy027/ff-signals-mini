"""
Utilitaires NumPy.
"""
import numpy as np
from typing import Tuple, Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


def calculate_sma(prices: np.ndarray, period: int) -> np.ndarray:
    """Calcule la SMA."""
    if not NUMPY_AVAILABLE or len(prices) < period:
        return np.full(len(prices), np.nan) if NUMPY_AVAILABLE else []
    sma = np.full(len(prices), np.nan)
    kernel = np.ones(period) / period
    sma[period-1:] = np.convolve(prices, kernel, mode='valid')
    return sma


def calculate_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """Calcule l'EMA."""
    if not NUMPY_AVAILABLE or len(prices) < period:
        return np.full(len(prices), np.nan) if NUMPY_AVAILABLE else []
    ema = np.full(len(prices), np.nan)
    ema[period-1] = np.mean(prices[:period])
    multiplier = 2 / (period + 1)
    for i in range(period, len(prices)):
        ema[i] = (prices[i] - ema[i-1]) * multiplier + ema[i-1]
    return ema


def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
    """Calcule le RSI."""
    if not NUMPY_AVAILABLE or len(prices) < period + 1:
        return np.full(len(prices), np.nan) if NUMPY_AVAILABLE else []
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.full(len(prices), np.nan)
    avg_loss = np.full(len(prices), np.nan)
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])
    for i in range(period + 1, len(prices)):
        avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
        avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
    rsi = np.full(len(prices), np.nan)
    for i in range(period, len(prices)):
        if avg_loss[i] == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain[i] / avg_loss[i]
            rsi[i] = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Calcule l'ATR."""
    if not NUMPY_AVAILABLE or len(close) < period + 1:
        return np.full(len(close), np.nan) if NUMPY_AVAILABLE else []
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr[0] = tr1[0]
    atr = np.full(len(close), np.nan)
    atr[period] = np.mean(tr[1:period+1])
    for i in range(period + 1, len(close)):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr


def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcule les Bandes de Bollinger."""
    if not NUMPY_AVAILABLE or len(prices) < period:
        nan_arr = np.full(len(prices), np.nan) if NUMPY_AVAILABLE else ([], [], [])
        return nan_arr, nan_arr, nan_arr if not NUMPY_AVAILABLE else (nan_arr, nan_arr, nan_arr)
    middle = calculate_sma(prices, period)
    upper = np.full(len(prices), np.nan)
    lower = np.full(len(prices), np.nan)
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        std = np.std(window)
        upper[i] = middle[i] + std_dev * std
        lower[i] = middle[i] - std_dev * std
    return upper, middle, lower


def calculate_macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcule le MACD."""
    if not NUMPY_AVAILABLE:
        return np.array([]), np.array([]), np.array([])
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    valid_macd = macd_line[~np.isnan(macd_line)]
    if len(valid_macd) < signal:
        nan_arr = np.full(len(prices), np.nan)
        return nan_arr, nan_arr, nan_arr
    signal_valid = calculate_ema(valid_macd, signal)
    full_signal = np.full(len(prices), np.nan)
    start_idx = np.where(~np.isnan(macd_line))[0][0] + signal - 1
    full_signal[start_idx:start_idx+len(signal_valid)] = signal_valid
    histogram = macd_line - full_signal
    return macd_line, full_signal, histogram


def calculate_stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """Calcule le Stochastic Oscillator."""
    if not NUMPY_AVAILABLE or len(close) < k_period:
        return np.array([]), np.array([])
    k_values = np.full(len(close), np.nan)
    for i in range(k_period - 1, len(close)):
        window_high = np.max(high[i - k_period + 1:i + 1])
        window_low = np.min(low[i - k_period + 1:i + 1])
        if window_high != window_low:
            k_values[i] = 100 * (close[i] - window_low) / (window_high - window_low)
        else:
            k_values[i] = 50.0
    valid_k = k_values[~np.isnan(k_values)]
    if len(valid_k) < d_period:
        return k_values, np.full(len(close), np.nan)
    d_valid = calculate_sma(valid_k, d_period)
    full_d = np.full(len(close), np.nan)
    start_idx = k_period - 1 + d_period - 1
    full_d[start_idx:start_idx+len(d_valid)] = d_valid
    return k_values, full_d