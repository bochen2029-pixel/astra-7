# ASTRA_AUDIO — operating contract for coding agents

Read first: this file, then `DESIGN_SPEC.md`, then `README.md`.
Parent canon: `C:\ASTRA-7\CLAUDE.md` (binding — language + platform discipline),
`C:\ASTRA-7\docs\synthesis.md` §4, `C:\ASTRA-7\docs\spec-v0.128.md` §8.2/§8.3.

## Scope lock

Write inside `C:\ASTRA-7\ASTRA_AUDIO\` only. Read anywhere in `C:\ASTRA-7\`.
Never modify the parent spec, the visualizers, or `proto/`.

## Hard rules

- **C++ only.** No Python, no interpreted languages, no Python-adjacent build
  steps. CMake not needed here — UnrealBuildTool owns the build.
- **Windows 11 + UE 5.7 only.** No Apple anything.
- **Zero binary assets.** No .uasset, no .umap. The MetaSound graph is built
  procedurally (Builder API) in `AstraVoyageActor.cpp`. If a change seems to
  need an editor-authored asset, redesign it to stay procedural, or stop and
  surface the tradeoff to the operator.
- **Spec-locked DSP forms** (v0.128 §8.3): modal IIR, DC blocker, grain pool
  semantics. Coefficients are tunable; the FORMS are not. Mark every tunable
  with `PROVISIONAL`.
- The synth node's vertex names (`W`, `dWdt`, `GradW`, `Vorticity`,
  `Interference`, `LifeSupport`, `MasterGain`, `Out Left`, `Out Right`) are a
  contract with `AstraVoyageActor.cpp` graph-input names. Change both or neither.

## Build + verify loop

```
"C:\Program Files\Epic Games\UE_5.7\Engine\Build\BatchFiles\Build.bat" AstraAudioEditor Win64 Development -Project="C:\ASTRA-7\ASTRA_AUDIO\AstraAudio.uproject" -WaitMutex
```

A change is not done until this exits 0. There is no headless audio CI yet
(deferred Rig-B testbed); until then, PIE listening is the operator's gate —
describe expected audible deltas in your handoff notes.

## Logging

Append a dated entry to `BUILD_LOG.md` per session: what changed, why, build
result, what the operator should listen for. Findings that implicate the
parent spec go to `FINDINGS.md` as v0.130 candidates (empirical residue only,
per §15.4 — no speculative spec edits).
