# ASTRA-7 Warp Hull Audio PoC

**"The audio is the field. Not samples played back over flight."**

Five-layer field-driven synthesis of the warp drive heard through the starship's
hull, per `docs/synthesis.md` §4 and spec v0.128 §8.2/§8.3. The entire project is
text — C++, configs, docs. **Zero binary assets**: the MetaSound graph is built
procedurally at runtime by the Builder API; no .umap, no .uasset.

## Status

PoC v0 — first-light build. DSP structures are spec-locked; numeric
coefficients are PROVISIONAL pending operator ear-tuning.

## Quickstart (operator)

1. Double-click `AstraAudio.uproject` (UE 5.7). Let it compile/load.
   If prompted to rebuild the AstraAudio module, say Yes.
2. Press **Play** (PIE).
3. You hear the 90-second voyage immediately: REST → CHARGE → JUMP →
   CRUISE 2c → **PUSH TO 8000c (the hull rings)** → BH PROXIMITY →
   EMERGENCY DROP → **ring-down**. A WAV of the master output is recorded
   automatically to `Saved/BouncedWavFiles/astra_warp_voyage_<timestamp>.wav`.

### Keys (during PIE)

| Key | Action |
|---|---|
| Space | Toggle auto-voyage / manual (freezes current params) |
| R | Restart voyage + start a fresh WAV recording |
| 1–7 | Presets: rest, charge, cruise 2c, **8000c**, BH proximity, drop (ring-down), cryosleep |
| Up / Down | Manual W ± 0.05 (manual mode) |

On-screen HUD shows phase, parameter values, and recording state.

## What you are hearing (the five layers)

| # | Layer | Drive | Character |
|---|---|---|---|
| 1 | Sub-bass drone | W → f0 = 12–45 Hz | The bubble carrier. Felt more than heard. |
| 2 | FM boundary shear | \|∇W\|×150 index, ratio **π** | Metallic tearing that never resolves. |
| 3 | Granular turbulence | vorticity ×800 grains/sec | Tectonic grinding of the wake. |
| 4 | Ring-mod interference | field coupling | Beating sidebands (nacelle pair). |
| 5 | **Modal hull resonance** | damping ∝ 1/W | 8 modes, 55 Hz–2.4 kHz. At high warp the hull **rings**; on field cut it **rings down** like a struck bell. |

Plus a life-support noise floor that fades as warp rises.

## Tuning

Everything tunable lives in two files:

- `Source/AstraAudio/WarpHullSynthNode.cpp` — layer math, mode table, mix levels
  (search `PROVISIONAL`).
- `Source/AstraAudio/AstraVoyageActor.cpp` — voyage arc keyframes and presets.

Spec-locked structures (do NOT change the forms, only coefficients):
modal IIR + DC blocker + grain pool per v0.128 §8.3; layer drives per
synthesis.md §4.

## Rebuild from CLI

```
"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat" AstraAudioEditor Win64 Development -Project="C:\ASTRA-7\ASTRA_AUDIO\AstraAudio.uproject" -WaitMutex
```
