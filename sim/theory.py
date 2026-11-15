"""Analytical results used to check the simulator (all times in ms)."""

import math

from sim import config


def cycle_time(t_tx=config.T_TX, t_prop=config.T_PROP):
    """Time from the start of a packet's transmission until its ACK returns."""
    return t_tx + 2 * t_prop


def efficiency_error_free(Ws, t_tx=config.T_TX, t_prop=config.T_PROP):
    """Error-free efficiency of a sliding window (GBN, SR, or S&W when Ws = 1)."""
    return min(1.0, Ws * t_tx / cycle_time(t_tx, t_prop))


def efficiency_sw(pd, pa, t_out=config.T_OUT, t_tx=config.T_TX, t_prop=config.T_PROP):
    """S&W efficiency with timeout-only retransmission.

    Each attempt succeeds (the ACK gets back) with probability q = (1-pd)(1-pa).
    A successful attempt takes t_tx + 2 t_prop; a failed one takes t_tx + t_out
    (the timer starts at the end of transmission). So
        E[T] = (t_tx + 2 t_prop) + (1/q - 1)(t_tx + t_out)
    """
    q = (1 - pd) * (1 - pa)
    expected = cycle_time(t_tx, t_prop) + (1 / q - 1) * (t_tx + t_out)
    return t_tx / expected


def completion_time_error_free(N, Ws, t_tx=config.T_TX, t_prop=config.T_PROP):
    """Error-free time to deliver and ACK N packets with send window Ws."""
    T = cycle_time(t_tx, t_prop)
    k = math.ceil(N / Ws) - 1            # number of full windows before the last one
    return k * max(T, Ws * t_tx) + (N - k * Ws) * t_tx + 2 * t_prop


def timeout_slots(t_out=config.T_OUT, t_tx=config.T_TX):
    """Slots lost per data error with timeout-only recovery.

    A lost packet is only resent t_out after its transmission ends, so each
    error costs K = (t_tx + t_out) / t_tx packet slots (K = 16 by default).
    This plays the role of the window size in the textbook GBN formula.
    """
    return (t_tx + t_out) / t_tx


def efficiency_gbn(pd, t_out=config.T_OUT, t_tx=config.T_TX):
    """GBN efficiency with large Ws and timeout-only recovery.

    Each failed transmission of the oldest packet wastes K slots, a success
    uses 1 slot:  eta = (1 - p) / (1 + (K - 1) p).
    """
    K = timeout_slots(t_out, t_tx)
    return (1 - pd) / (1 + (K - 1) * pd)


def efficiency_sr(pd):
    """Ideal SR efficiency (Ws, Wr large enough that the window never stalls)."""
    return 1 - pd


def attempts_ideal_sr(pd, pa=0.0):
    """Mean transmissions per delivered packet for ideal SR (no wasted resends)."""
    return 1 / (1 - pd)


def attempts_sw(pd, pa):
    """Mean transmissions per delivered packet for S&W: geometric with q=(1-pd)(1-pa)."""
    return 1 / ((1 - pd) * (1 - pa))
