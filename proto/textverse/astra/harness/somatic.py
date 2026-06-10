"""Somatic Aggregator — v0.129 TENTATIVE §6.3.1 contract, implemented as
code residue (spec adoption remains an operator decision per §15.4).

The Somatic Aggregator is the stateless bridge between ENDOGENOUS signal
sources (§6.3 endogenous/exogenous principle: hull-local state read at
t_cosmic — power network, warp coils, chaos field, hull stress, cryosleep)
and ASTRA's `<somatic>` perception channel (§4.3: SOMATIC is input only;
her felt-state is something she receives, never something she emits).

Discipline (per the STAGE addendum): the banner is **sensor-grounded, not
phenomenal claim**. Labels name what the sensors read ("third harmonic
warm", "power margin thin"), never inner experience ("I feel", "it hurts").
Deterministic: same signals in, same banner out. At most two short lines.

Source vocabulary (v0.129 draft §6.3.1): "audio", "power", "chaos",
"atmosphere", "hull", "thermal", "hardware", "warp", "cryosleep". Kept as
a documented convention rather than a Literal lock while the contract is
TENTATIVE.

The v0 emitters read the StateBus snapshot directly. The §8.2
AudioPayloadRingBuffer path (GPU hull sensors → audio-rate payload) feeds
the same SomaticSignal shape when the UE5 substrate arrives.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from astra.state_bus import StateBus

# Banner discipline: at most this many salient signals compose the banner,
# across at most two lines.
MAX_BANNER_SIGNALS: int = 3


class SomaticSignal(BaseModel):
    """One endogenous body signal per v0.129 §6.3.1 (TENTATIVE)."""

    model_config = ConfigDict(frozen=True)

    source: str                                   # see module docstring vocab
    label: str                                    # short sensor-grounded prose
    magnitude: float = Field(ge=0.0, le=1.0)      # salience strength
    salient: bool = False                         # banner-eligible this frame


def aggregate(signals: list[SomaticSignal]) -> str:
    """Compose salient signals into a banner of at most two short lines.

    Deterministic: salient signals sort by (magnitude desc, source, label);
    the strongest takes the first line, the next up-to-two share the second.
    No salient signals → empty banner (a quiet body says nothing).
    """
    salient = sorted(
        (s for s in signals if s.salient),
        key=lambda s: (-s.magnitude, s.source, s.label),
    )[:MAX_BANNER_SIGNALS]
    if not salient:
        return ""

    def sentence(label: str) -> str:
        text = label.strip()
        return text if text.endswith((".", "!", "?")) else text + "."

    first = sentence(salient[0].label)
    if len(salient) == 1:
        return first
    rest = " ".join(sentence(s.label) for s in salient[1:])
    return f"{first}\n{rest}"


def emit_somatic_signals(bus: StateBus) -> list[SomaticSignal]:
    """Stateless per-frame emitters: StateBus snapshot → body signals.

    Each block reads one endogenous subsystem. Thresholds are PROVISIONAL
    tuning; the signal SHAPE is the contract.
    """
    signals: list[SomaticSignal] = []

    # Power network (§1.4): total allocation pressure.
    if bus.power_allocation:
        total = sum(bus.power_allocation.values())
        if total > 0.9:
            signals.append(
                SomaticSignal(
                    source="power",
                    label="power margin thin",
                    magnitude=min(total, 1.0),
                    salient=True,
                )
            )
        else:
            signals.append(
                SomaticSignal(
                    source="power",
                    label="power steady",
                    magnitude=max(0.0, min(total, 1.0)) * 0.3,
                    salient=False,
                )
            )

    # Warp coils (§4.2 WarpState).
    if bus.warp is not None:
        if bus.warp.phase == "charging":
            signals.append(
                SomaticSignal(
                    source="warp",
                    label="coils taking charge",
                    magnitude=bus.warp.charge_progress,
                    salient=True,
                )
            )
        elif bus.warp.phase == "cruising":
            signals.append(
                SomaticSignal(
                    source="warp",
                    label="bubble steady, third harmonic warm",
                    magnitude=bus.warp.W,
                    salient=bus.warp.W >= 0.7,
                )
            )
        else:  # dropping / shutdown
            signals.append(
                SomaticSignal(
                    source="warp",
                    label="field ramping down, hull ringing off",
                    magnitude=bus.warp.W,
                    salient=True,
                )
            )

    # Cryosleep (§3.3 composition).
    if bus.cryosleep_active:
        signals.append(
            SomaticSignal(
                source="cryosleep",
                label="pod sealed, metabolic hold",
                magnitude=1.0,
                salient=True,
            )
        )

    # Hull stress map (§1.3 damage map summary).
    if bus.hull_damage:
        section, worst = max(bus.hull_damage.items(), key=lambda kv: kv[1])
        magnitude = max(0.0, min(worst, 1.0))
        signals.append(
            SomaticSignal(
                source="hull",
                label=f"hull stress at {section}",
                magnitude=magnitude,
                salient=magnitude > 0.3,
            )
        )

    # Chaos field summary (§7.1; full PDE lives in astra_nexus).
    chaos = bus.chaos_field_summary
    if chaos.max_amplitude > 0.5:
        signals.append(
            SomaticSignal(
                source="chaos",
                label="field unquiet at the boundary",
                magnitude=min(chaos.max_amplitude, 1.0),
                salient=True,
            )
        )
    elif chaos.max_amplitude > 0.0:
        signals.append(
            SomaticSignal(
                source="chaos",
                label="field murmur, settled",
                magnitude=min(chaos.max_amplitude, 1.0) * 0.4,
                salient=False,
            )
        )

    # Quiet baseline: a body that reads nominal still reads SOMETHING.
    if not signals:
        signals.append(
            SomaticSignal(
                source="hardware",
                label="systems quiet",
                magnitude=0.05,
                salient=False,
            )
        )

    return signals
