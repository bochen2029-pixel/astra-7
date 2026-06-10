# astra-a0-bootstrap

Bootstrap folder for the ASTRA-A0 fine-tune pipeline build.

This folder contains the orchestration documents a fresh Claude instance reads to autonomously build the complete ASTRA-A0 fine-tune pipeline end-to-end: dataset generation, validation, consolidation, fine-tune execution on Qwen 3.6 27B, GGUF conversion, and Hugging Face upload.

## Contents

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Main orchestration. Read this first if you are a Claude instance. ~500 lines covering mandatory canon reading, authority hierarchy, banned imports (NOT K0/NOT K8/NOT TARS), ASTRA's canonical anchors, deliverables, build order, web research requirements, failure modes to watch for, validation gates, hand-off protocol. |
| `WAKE_UP.md` | Durable resumption prompt. Copy-paste the block inside into a fresh Claude instance's first message to bootstrap correctly. Use on first session, after compaction, after pause, or for parallel instance spawn. |
| `README.md` | This file. |

## Usage

1. Bo opens a fresh Claude instance
2. Bo copies the prompt block from `WAKE_UP.md` into the instance's first message
3. Instance reads `CLAUDE.md`, executes cold-start protocol, reports status
4. Bo confirms cold-start QC, directs to Phase 1
5. Instance builds the pipeline at `C:\astra-a0-finetune\` per `CLAUDE.md` §4-5
6. Bo reviews at gates (Phases 2, 3, 4, 5, 6)
7. Bulk generation runs over multiple sessions (Phase 7)
8. Fine-tune executes at RunPod (Phase 9)
9. Model uploads to Hugging Face (Phase 10)
10. Bench evaluation against textverse (Phase 11)

## Why this exists

ASTRA-A0 is the first fine-tuned ASTRA persona. Today's empirical work (`proto/textverse/persona_tests/FINDINGS_2026-05-16_*.md`) proved that sysprompt-alone hits a ceiling on always-think discipline and bracket-mechanism leakage. Fine-tune is the next ceiling break. This folder bootstraps the build.

## Why bootstrap-as-folder

A single CLAUDE.md plus a WAKE_UP prompt gives operator-on-demand reproducibility: stand up a fresh instance, point at this folder, get a working build session. No prior context required. Mirrors the proven pattern from `C:\katherine-k8-finetune\` (the K8 fine-tune project that already shipped).

## Reference projects (study, do NOT copy content)

- `C:\katherine-k8-finetune\` — most mature fine-tune project for the K-line. Pattern reference for scripts, soul docs, validator, HF release. CONTENT belongs to Katherine K8, not ASTRA.
- `C:\temp\tars-training\` — cleanest five-document pattern reference. CONTENT belongs to TARS, not ASTRA.

The fresh instance is explicitly instructed to study patterns and never import content. ASTRA is the ship; she is not Katherine; she is not TARS.

## Build target

The actual pipeline gets built at `C:\astra-a0-finetune\` (outside the ASTRA-7 game repo, matching K8 convention). Training infrastructure is operator-curated artifact, separate from the game's source tree.

## Status

Created 2026-05-16. Build not yet started. Awaiting Bo's first WAKE_UP invocation.
