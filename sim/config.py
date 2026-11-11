"""Shared default parameters and random seeds for every experiment.

All times are in milliseconds.
"""

PACKET_BITS = 1000          # fixed data packet length (bits)
LINK_RATE_BPS = 1_000_000   # link bit rate (bits/s)
T_TX = PACKET_BITS / LINK_RATE_BPS * 1000.0   # data packet transmission time = 1 ms
T_PROP = 5.0                # one-way propagation delay (ms); RTT = 10 ms
T_OUT = 15.0                # default retransmission timeout (ms)

# Window needed to keep the link busy with no errors:
#   Ws * T_TX >= T_TX + 2 * T_PROP  ->  Ws >= 11
W_FULL = int(round((T_TX + 2 * T_PROP) / T_TX))

# Random number generator seeds. Use the SAME list for every protocol so that
# comparisons are fair. The first entry must be a group member's student ID.
STUDENT_ID = 400380714      # TODO: replace with a group member's student ID
SEEDS = [STUDENT_ID, 12345, 67890, 24680, 13579]

# Default run length for the always-full (continuously backlogged) source
SIM_TIME = 100_000.0        # ms of simulated time (100 s, ~100k packet slots)
WARMUP = 1_000.0            # ms discarded at the start before collecting statistics
