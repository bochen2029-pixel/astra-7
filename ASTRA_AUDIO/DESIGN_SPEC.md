# ASTRA-7 Warp Hull Audio PoC — Design Spec v0

Date: 2026-06-09. Author: Bo Chen + Claude (Fable 5). Scope-locked to `C:\ASTRA-7\ASTRA_AUDIO\`.

## 1. Purpose

Hear the warp field. Prove the canon claim — *"32 hull sensor points feed five
synthesis layers; at high warp the hull rings; the audio is the field"* — as a
playable, recordable artifact in the production audio substrate (UE MetaSound),
before any UE5 game work exists. This is the audio sibling of
`ASTRA_VISUALIZER_02` (which proved the same spec's *visual* claims).

## 2. Canon sources (binding)

- `docs/synthesis.md` §4 "The audio is the field": five layers + drive params.
- Spec v0.128 §8.2: GPU→audio transport is a triple-buffered latest-state
  payload (NOT a queue). Out of scope for this PoC (no GPU field yet) but the
  parameter-push architecture mirrors it: latest value wins, no history.
- Spec v0.128 §8.3 locked DSP forms (implemented verbatim):
  - Modal resonator per mode: `y[n] = 2·cos(ω₀)·r·y[n−1] − r²·y[n−2] + x[n]`,
    `r = exp(−π·BW/SR)`.
  - DC blocker: `y[n] = α·(y[n−1] + x[n] − x[n−1])`, `α = exp(−2π·f_c/SR)`.
  - Granular voice pool: 8–16 voices, round-robin allocation.
- Spec v0.128 §8.3 endogenous rule: audio is hull-local, runs on t_cosmic,
  never retarded-time. (Trivially satisfied here; recorded for the future.)
- `brainstorm/GLM_Warp_Sounds.txt`: 32-sensor extraction design, π modulator
  ratio, 38 Hz drone anchor, sensor placement.

## 3. Architecture

```
AAstraAudioGameMode (spawns) → AAstraVoyageActor
    BeginPlay:  MetaSound Builder API → graph { 7 float graph-inputs →
                [AstraAudio.WarpHullSynth] → stereo out } → Audition()
    Tick:       voyage arc f(t) → SetFloatParameter × 6
    Recording:  StartRecordingOutput / StopRecordingOutput → WAV

WarpHullSynthNode (custom MetaSound node, all DSP in C++)
    inputs:  W, dWdt, GradW, Vorticity, Interference, LifeSupport, MasterGain
    outputs: Out Left, Out Right
```

Zero binary assets, by design: graph built procedurally; map = engine's
`/Engine/Maps/Entry`; everything reviewable as text. The full project IS the
diff.

### Normalized-drive convention

The node takes [0,1] normalized drives. The mapping from physical quantities
(metric W, |∇W| in 1/m, vorticity in 1/s, κ·W_A·W_B) to [0,1] is owned by the
DRIVER (voyage actor now; the §8.2 payload consumer later). This keeps the
node stable while the physics-side scaling calibrates.

## 4. The five layers (structure locked / coefficients PROVISIONAL)

| # | Layer | Structure (locked) | Coefficients (provisional) |
|---|---|---|---|
| L1 | Drone | Additive partial stack, f0 tracks W | f0 = 12+33·W Hz; ratios 1/2/2.98/4.21; gains 1/.5/.3/.18 |
| L2 | Boundary shear | 2-op FM, ratio π, index = \|∇W\|×150 (§synthesis.md), DC-blocked (§8.3) | fc = 240+80·W; index curve GradW^1.5; level .35 |
| L3 | Turbulence | Granular, rate = vorticity×800/s, 16-voice round-robin (§8.3) | 5 ms Hann grains; 1.2–4 kHz; 0.6 tone + 0.4 noise |
| L4 | Interference | Ring modulation of L1+L2 bed | carrier 90+310·Intf Hz; level .45·Intf |
| L5 | Hull modes | 8-mode §8.3 IIR bank; **BW = BW0·max(1−0.92·W, .05)^1.5** (damping ∝ 1/W → rings at high warp); excited by L2+L3+\|dWdt\|·noise | freqs 55–2431.7 Hz stretched ×~1.66 series seeded by 280×78×22 m hull; BW0 6–14 Hz |
| — | Life support | LP white noise floor, fades with W | −26 dB-ish, ×(1−0.85·W) |

Master: per-channel tanh(1.15·x)·0.85·MasterGain.

## 5. Voyage arc (the 90 s showcase)

| t (s) | Phase | Drives |
|---|---|---|
| 0–10 | REST | all 0; life support only |
| 10–25 | CHARGE | W→.35, GradW→.18 (smoothstep) |
| 25–25.5 | JUMP | W .35→.55 fast; dWdt spike strikes the modes |
| 25.5–45 | CRUISE 2c | W .55 + slow wobble; Intf beats |
| 45–65 | PUSH 8000c | W→.95, GradW→.85, Vort→.70 — **hull crosses into sustained ring** |
| 65–72 | BH PROXIMITY | Vort→.92, Intf→.70 (chaos α-coupling flavor) |
| 72–72.3 | EMERGENCY DROP | all drives →0 in 300 ms |
| 72.3–90 | RING-DOWN | modal bank decays alone; the payoff; then life support |

WAV auto-recorded (master submix) to `Saved/BouncedWavFiles/`.

## 6. Acceptance (PoC v0)

Mechanical: builds clean; PIE plays; all 7 params live; voyage runs; WAV lands.
Operator (the real gate, ear-side, analog of the visualizer's S05 sign-off):

1. REST is comfortable to sit in (no fatigue, no hiss prominence).
2. CHARGE→JUMP reads as *energy accumulating then releasing*.
3. 8000c unmistakably **rings** — sustained metallic resonance, not just louder drone.
4. EMERGENCY DROP ring-down is audibly a struck-structure decay ≥ 5 s.
5. No clipping/zipper artifacts across the full arc.

## 7. Deferred (v0.x+)

- 32-sensor spatialization (per-sensor drives → panned layer instances; quad/5.1).
- §8.2 AudioPayloadRingBuffer transport from a real GPU field (visualizer link or UDP/OSC).
- Spectral assertion suite + golden spectrograms (the Rig-B C++ testbed; CI like the visualizer).
- Hull-damage modal detune (synthesis.md: "if the hull damages, the modal frequencies shift").
- Blackbody-correct... (n/a — that's the visual testbed's item; audio analog: loudness-curve calibration).
- Tidal-stress transient channel (spec §7.6) as a distinct exciter.

## 8. Discipline notes

- Language: C++ only (this entire PoC). No Python anywhere, per CLAUDE.md root directive.
- Platform: Windows 11 + UE 5.7. No Apple paths.
- MetaSound = canon audio substrate (root CLAUDE.md "MetaSound + Niagara").
- All spec-revision-worthy findings land in `FINDINGS.md` (create on first finding)
  and route to v0.130 candidates per §15.4 (empirical residue only).
