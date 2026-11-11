# COE 4DK4 Lab 4: Simulation of ARQ Protocols

Discrete-event simulator for Stop-and-Wait, Go-Back-N and Selective-Repeat ARQ.
One general SR simulator (send window `Ws`, receive window `Wr`):
`Wr = 1` gives GBN, `Ws = Wr = 1` gives S&W.

## Layout
| Folder | Contents |
|---|---|
| `sim/` | Simulator core and shared config (parameters, seeds) |
| `experiments/` | One script per experiment (`exp1` ... `exp7`) |
| `results/` | Raw simulation output (CSV) |
| `plots/` | Generated figures |
| `report/` | Report drafts |

## Default parameters
- Packet length 1000 bits, link rate 1 Mbps, so transmission time is 1 ms
- Round-trip propagation delay 10 ms (5 ms each way)
- Timeout 15 ms
- ACK transmission and processing times are neglected

## Task split
| Member | Work |
|---|---|
| A | Simulator core, Exp 1 (verification), Exp 2 (error-free Ws sweep); report: simulation design, verification |
| B | Exp 3 (packet errors), Exp 4 (packet and ACK errors) |
| C | Exp 5 (timeout), Exp 6 (finite transfer, N = 100), Exp 7 (transfer size); finite-source mode |

## Workflow
- Keep `main` working; do your work on your own branch and merge when it runs.
- Use the shared seeds and parameters in `sim/` so results are comparable.
