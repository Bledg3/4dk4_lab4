"""Discrete-event simulator for a general Selective-Repeat ARQ link.

One simulator covers all three protocols:
    SR  : send window Ws, receive window Wr > 1
    GBN : Wr = 1  (receiver only accepts the next in-order packet)
    S&W : Ws = Wr = 1

Model (see the report for the full list of assumptions):
  * One sender, one receiver, one full-duplex point-to-point link.
  * Data packets take T_TX to transmit and T_PROP to propagate.
    ACKs have zero transmission time and only incur T_PROP.
  * Each data transmission is lost independently with probability pd.
    A lost packet produces no ACK. Each ACK of a received packet is lost
    independently with probability pa.
  * Sequence numbers are unbounded integers (no wrap-around), so the
    Ws + Wr <= 2^m constraint is not an issue.
  * Every data packet that arrives (even a duplicate or an out-of-window one)
    triggers an ACK. The ACK carries:
        cum : the receiver's next expected sequence number (cumulative ACK);
              every seq < cum has been received.
        sel : the sequence number of the packet that triggered the ACK, if
              that packet was accepted into the receive window (selective
              ACK), otherwise None.
    With Wr = 1, sel never adds information beyond cum, so the ACK is
    purely cumulative, which is GBN behaviour.
  * Each outstanding packet has its own retransmission timer, started when
    its transmission finishes. On a timeout only that packet is queued for
    retransmission. With Wr = 1 every packet sent after a lost one is
    discarded by the receiver, so all of them time out in turn and are
    resent back-to-back: the go-back-N behaviour comes out on its own.
  * There are no NAKs; retransmissions are triggered by timeouts only.
  * Retransmissions have priority over new packets, lowest seq first.
  * Events that happen at the same instant are processed in this order:
    ACK arrival, data arrival, end of transmission, timeout. So an ACK
    that arrives exactly at the timeout instant cancels the timeout.
"""

import heapq
import random

from sim import config

# Event types; the number is the tie-break priority at equal times
ACK_ARRIVE = 0
DATA_ARRIVE = 1
TX_END = 2
TIMEOUT = 3

EVENT_NAMES = {ACK_ARRIVE: "ACK_ARRIVE", DATA_ARRIVE: "DATA_ARRIVE",
               TX_END: "TX_END", TIMEOUT: "TIMEOUT"}


def simulate(Ws, Wr, pd=0.0, pa=0.0, t_out=config.T_OUT,
             sim_time=config.SIM_TIME, warmup=config.WARMUP,
             num_packets=None, seed=0, trace=False,
             t_tx=config.T_TX, t_prop=config.T_PROP, max_trace_lines=None):
    """Run one simulation and return a dict of statistics.

    num_packets=None -> continuously backlogged source; stops at sim_time and
                        statistics cover [warmup, sim_time].
    num_packets=N    -> finite transfer of N packets present at t = 0; stops
                        when the sender has received ACKs for all N packets
                        (sim_time and warmup are ignored).
    trace=True       -> also return a list of human-readable trace lines.
    """
    if Ws < 1 or Wr < 1:
        raise ValueError("window sizes must be >= 1")
    rng = random.Random(seed)
    finite = num_packets is not None
    if finite:
        warmup = 0.0
        sim_time = float("inf")

    # ---------------- state variables ----------------
    # Sender
    base = 0                # oldest unacknowledged sequence number
    next_seq = 0            # next new sequence number to send
    acked = set()           # seqs >= base that are acknowledged (selectively)
    retx_queue = []         # heap of seqs waiting for retransmission
    in_retx = set()         # same contents as retx_queue, for O(1) lookup
    attempt = {}            # seq -> transmission count (for timer validity)
    link_busy = False
    # Receiver
    rcv_base = 0            # next in-order seq expected
    rcv_buffer = set()      # out-of-order seqs held in the receive window
    delivered_seqs = []     # only kept for verification when tracing/finite

    # Event list: (time, priority, counter, type, data)
    events = []
    counter = 0

    # Statistics (counted only inside the measurement window)
    n_tx = 0                # all data transmission attempts started
    n_new_tx = 0
    n_delivered = 0         # packets delivered in order to the receiver's upper layer
    n_data_lost = n_data_ok = 0
    n_ack_lost = n_ack_ok = 0
    completion_time = None
    lines = [] if trace else None

    def schedule(t, etype, data):
        nonlocal counter
        heapq.heappush(events, (t, etype, counter, etype, data))
        counter += 1

    def state_str():
        rq = sorted(in_retx)
        buf = sorted(rcv_buffer)
        return (f"S[base={base} next={next_seq} win={base}..{base + Ws - 1}"
                f" sacked={sorted(acked)} retxQ={rq}] R[rcv_base={rcv_base} win={rcv_base}..{rcv_base + Wr - 1}"
                f" buf={buf}]")

    def log(t, what):
        if trace and (max_trace_lines is None or len(lines) < max_trace_lines):
            lines.append(f"{t:9.3f}  {what:<46} {state_str()}")

    def try_send(t):
        """Start a transmission if the link is idle and something can be sent."""
        nonlocal link_busy, next_seq, n_tx, n_new_tx
        if link_busy:
            return
        seq = None
        kind = ""
        # Retransmissions first (lowest seq first)
        while retx_queue:
            s = heapq.heappop(retx_queue)
            in_retx.discard(s)
            if s >= base and s not in acked:
                seq, kind = s, "retx"
                break
        if seq is None:
            can_new = next_seq < base + Ws and (not finite or next_seq < num_packets)
            if not can_new:
                return
            seq, kind = next_seq, "new"
            next_seq += 1
        attempt[seq] = attempt.get(seq, 0) + 1
        link_busy = True
        if t >= warmup:
            n_tx += 1
            if kind == "new":
                n_new_tx += 1
        log(t, f"TX_START  seq={seq} ({kind}, attempt {attempt[seq]})")
        schedule(t + t_tx, TX_END, (seq, attempt[seq]))

    def advance_base():
        nonlocal base
        while base in acked:
            acked.discard(base)
            base += 1

    # ---------------- main loop ----------------
    try_send(0.0)
    while events:
        t, _, _, etype, data = heapq.heappop(events)
        if t >= sim_time:   # measurement window is [warmup, sim_time)
            break

        if etype == TX_END:
            seq, att = data
            link_busy = False
            lost = rng.random() < pd
            if t >= warmup:
                if lost:
                    n_data_lost += 1
                else:
                    n_data_ok += 1
            if lost:
                log(t, f"TX_END    seq={seq}  -> DATA LOST")
            else:
                log(t, f"TX_END    seq={seq}  -> will arrive at {t + t_prop:.3f}")
                schedule(t + t_prop, DATA_ARRIVE, seq)
            schedule(t + t_out, TIMEOUT, (seq, att))
            try_send(t)

        elif etype == DATA_ARRIVE:
            seq = data
            sel = None
            if seq < rcv_base:
                note = "duplicate (already delivered), discard"
            elif seq >= rcv_base + Wr:
                note = "outside receive window, discard"
            elif seq in rcv_buffer:
                note = "duplicate (already buffered), discard"
                sel = seq
            else:
                sel = seq
                rcv_buffer.add(seq)
                n_before = rcv_base
                while rcv_base in rcv_buffer:
                    rcv_buffer.discard(rcv_base)
                    if trace or finite:
                        delivered_seqs.append(rcv_base)
                    rcv_base += 1
                    if t >= warmup:
                        n_delivered += 1
                if rcv_base > n_before:
                    note = f"accepted, delivered {n_before}..{rcv_base - 1}"
                else:
                    note = "accepted, buffered (out of order)"
            ack_lost = rng.random() < pa
            if t >= warmup:
                if ack_lost:
                    n_ack_lost += 1
                else:
                    n_ack_ok += 1
            ack_txt = f"ACK(cum={rcv_base}, sel={sel})"
            if ack_lost:
                log(t, f"DATA_ARR  seq={seq}: {note}; {ack_txt} LOST")
            else:
                log(t, f"DATA_ARR  seq={seq}: {note}; send {ack_txt}")
                schedule(t + t_prop, ACK_ARRIVE, (rcv_base, sel))

        elif etype == ACK_ARRIVE:
            cum, sel = data
            old_base = base
            for s in range(base, min(cum, next_seq)):
                acked.add(s)
            if sel is not None and sel >= base:
                acked.add(sel)
            advance_base()
            log(t, f"ACK_ARR   cum={cum} sel={sel}"
                   + (f"  base {old_base}->{base}" if base != old_base else ""))
            if finite and base >= num_packets and completion_time is None:
                completion_time = t
                log(t, "ALL PACKETS ACKNOWLEDGED - transfer complete")
                break
            try_send(t)

        elif etype == TIMEOUT:
            seq, att = data
            if seq >= base and seq not in acked and attempt.get(seq) == att \
                    and seq not in in_retx:
                heapq.heappush(retx_queue, seq)
                in_retx.add(seq)
                log(t, f"TIMEOUT   seq={seq} -> queued for retransmission")
                try_send(t)

    # ---------------- results ----------------
    if finite:
        duration = completion_time if completion_time is not None else t
    else:
        duration = sim_time - warmup
    res = {
        "Ws": Ws, "Wr": Wr, "pd": pd, "pa": pa, "t_out": t_out, "seed": seed,
        "duration": duration,
        "transmissions": n_tx,
        "new_transmissions": n_new_tx,
        "delivered": n_delivered,
        "efficiency": n_delivered * t_tx / duration if duration > 0 else 0.0,
        "attempts_per_packet": n_tx / n_delivered if n_delivered else float("inf"),
        "data_loss_rate": n_data_lost / max(1, n_data_lost + n_data_ok),
        "ack_loss_rate": n_ack_lost / max(1, n_ack_lost + n_ack_ok),
        "completion_time": completion_time,
    }
    if trace or finite:
        res["delivered_seqs"] = delivered_seqs
    if trace:
        res["trace"] = lines
    return res


def protocol_name(Ws, Wr):
    if Ws == 1 and Wr == 1:
        return "S&W"
    if Wr == 1:
        return f"GBN (Ws={Ws})"
    return f"SR (Ws={Ws}, Wr={Wr})"
