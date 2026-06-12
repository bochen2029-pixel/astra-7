# ASTRA-7 — Agentic Development Reference

**Version 1.0 — June 11, 2026**
**Synthesized from:** two independent evidence-graded deep-research passes (both self-dated June 12, 2026, designated DS1 and DS2), the ASTRA-7 Full Project Report (2026-06-10), conversation-phase web research (June 11), and operator-supplied project canon. Evidence classes carried over: **(a)** verified-doc, **(b)** user-report, **(c)** vendor-claim. Confidence tiers: Confirmed >95%, Probable 75–95%, Plausible 40–75%.
**Status:** living reference. Supersedes in-chat recommendations of June 11 where they conflict (one material revision: §3, editor-MCP verdict).
**Respects:** Language Discipline (C++17+/HLSL/C; Python only in `proto/textverse/`), Platform Discipline (Win11 + DX12 + UE5; Linux secondary; never Apple), Privacy lock (zero outbound calls after install), spec-revision discipline (§15.4), calculator-bound LLM agency (§15.6).

---

## 0. How to read this document

This is the tooling/stack/policy/risk canon for Track B (the UE5 game) and ongoing harness work. Every recommendation is graded and dated; anything marked **[RULING NEEDED]** is blocked on an operator decision; anything marked **[RE-VERIFY]** was not fully retrievable within research budget and must be checked before it becomes load-bearing. Where DS1 and DS2 disagreed, the reconciliation and its rationale are stated inline rather than averaged away.

Two scope questions remain open and shape several sections:

1. **[RULING NEEDED — R1] Language Discipline scope for dev-time tooling.** The directive's two sentences differ: "ZERO new Python anywhere except `proto/textverse/`" (broad) vs "no Python in shipped artifacts, build tooling, or CI" (narrow). Dev-time editor automation (UE editor Python, Python-bridged MCP servers) lives in the gap. **This document is written to be safe under the broad reading**; items viable only under the narrow reading are tagged **[NARROW-ONLY]**.
2. **[RULING NEEDED — R2] textverse-in-CI carve-out.** The bench is Python and is the permanent regression environment; "loop preservation IS the regression test." Running it from CI is Python in CI. Presumed intent: the carve-out extends to *invoking* textverse from CI (the directive targets new Python, not the instrument). Confirm and record in the spec.

---

## 1. Settled ground (June 2026)

| Fact | Detail | Class / Confidence |
|---|---|---|
| Engine baseline | **UE 5.7** (shipped Nov 12, 2025; project on 5.7.4). Production PCG + Substrate; MegaLights beta; in-editor AI Assistant panel; default MSVC **14.44** (already forced on this machine per war story W-11). **UE 5.8 Preview** landed May 2026. **UE6** teased May 24, 2026 (RLCS Paris) — no date, no specs; goals stated as UE5/UEFN unification, multithreaded sim, Verse, AI-assisted authoring. | (a) Confirmed (5.7); Plausible (UE6 timing) |
| Planning posture | Build on 5.7. UE6 is a watch-item, not a planning constraint. 5.8 adoption only on a concrete need (e.g., NVIDIA's GDC-2026 RTX features target 5.8/5.9). | — |
| Epic terms | UE free; 5% royalty on lifetime gross **>$1M per product** — moot for a free game. Fab/Sketchfab require AI-content labeling (Sketchfab mandate Dec 11, 2025); enforcement reported inconsistent. **[RE-VERIFY]** exact Fab AI-policy text (neither pass retrieved it). | (a)/(b) |
| Steam AI disclosure | **Jan 16–17, 2026 rewrite.** Verbatim: efficiency gains from AI dev tools "is not the focus of this section"; disclosure concerns "content that ships with your game, and is consumed by players." Two tiers: **pre-generated** (shipped AI assets) and **live-generated** (runtime AI; requires guardrail description; overlay report button). Scale: 10,258 disclosed titles (~8% of Steam) per Totally Human Media; Valve has delisted for inaccurate disclosure. | (a) Confirmed |
| ASTRA-7 disclosure consequence | **Agentic C++/dev work: zero disclosure.** The local LLM is **live-generated player-facing AI → Tier-2 disclosure required** (name models, describe guardrails — the leak gates, canon gates, and calculator-bound validators *are* the guardrail description). Any AI-generated props/textures that ship → pre-generated tier. Precedent exists: a shipped Steam title discloses an on-device local LLM verbatim; shipping/auto-downloading weights is permitted. **Action: draft the Tier-2 disclosure now** (queued in §8). | (a) Confirmed |
| US copyright | Purely AI-generated output **not copyrightable** absent meaningful human authorship. *Thaler v. Perlmutter* cert **denied Mar 2, 2026** (D.C. Cir. ruling stands: human authorship is a bedrock requirement). Prompts alone insufficient (USCO Part 2, Jan 2025); human selection/arrangement can be a copyrightable compilation. | (a) Confirmed |
| ASTRA-7 copyright consequence | Low stakes for an MIT/CC project, but the asymmetry is useful: hand-authored canon (spec, sysprompt, book, ship design) is protectable and *is* the project's identity; AI-generated props are unprotectable background — consistent with treating them as disposable filler. Keep generation records. | — |
| Generated music | The one acute legal hazard in the general landscape: WMG–Suno settled Nov 25, 2025; UMG–Udio settled Oct 29, 2025; Sony v. Suno fair-use summary-judgment hearing **July 2026** (D. Mass., Judge Casper). **Moot for ASTRA-7** — audio is synthesized from field state, not generated music. Becomes relevant only if soundtrack ambitions emerge; until the July ruling, ElevenLabs Music (licensed-data) or licensed libraries only. | (a) Confirmed (status) |
| Rider licensing | Free for **non-commercial** use; both passes flag a forced paid license "once commercial." **ASTRA-7 wrinkle:** the game is free, unmonetized, MIT — the commercialization trigger plausibly never fires, and JetBrains' free OSS-project licensing may apply regardless. **[RE-VERIFY]** JetBrains non-commercial/OSS terms against "free MIT game" before assuming either outcome. | (a) + open question |

---

## 2. The stack (reconciled, ASTRA-7-specific)

Reconciliation note: DS1 and DS2 agree on every layer except editor-MCP (§3). Where the project had already converged on a choice (sidecar inference, whisper.cpp, Piper, zero-asset UE project), the research **confirms** rather than changes it — confirmations are marked ✓.

| Layer | Primary | Fallback | Confidence | Notes |
|---|---|---|---|---|
| IDE | **Rider** (free non-comm/OSS pending R-verify) | VS Code + clangd (`boocs/unreal-clangd`, supports 5.7) | Confirmed | Rider: opens `.uproject`, understands reflection macros, Live Coding. clangd path is the more agent-legible free option. |
| Agent harness | **Claude Code** on the strongest available coding model (research benchmarked Opus 4.7, 87.6% SWE-bench Verified per Anthropic system card; Opus 4.8 / Fable 5-class current as of June 2026) | Cursor (autocomplete only) / Codex-CLI | Probable | Repo-scale C++ reasoning is the differentiator (b). The "80/15/5" pattern: autocomplete for volume, Claude Code for the hard 5%. |
| API-truth grounding | **Cloned UE 5.7 engine source in-workspace + compile-loop self-correction** | Epic Developer Assistant (free, in-editor panel in 5.7) for docs Q&A | Probable | Both passes: this combination is load-bearing; docs-MCP lookups are tertiary. Keep the clone pinned to 5.7.4. |
| Editor control | **None load-bearing** (see §3) | UnrealClaude read-only screenshots, or ChiR24 — both non-Python | Probable | Supersedes the June 11 in-chat recommendation. |
| Local inference | **Sidecar llama.cpp server behind an OpenAI-compatible localhost endpoint** ✓ (matches the two-adapter merge design) | getnamo/Llama-Unreal embedded (reference implementation, not dependency) | Probable | getnamo v1.1.0 (May 29, 2026, MIT, llama.cpp b9404, UE 5.7, 459 commits) is the best-maintained embedded plugin — mine it for integration patterns and its contention data (§4). |
| ASR / TTS | **whisper.cpp (MIT)** ✓ + **Piper (MIT)** ✓ or **Kokoro-82M (Apache 2.0)** | Fish Speech (Apache, ~12 GB) if voice quality demands it | Confirmed | Ship-clean for a commercial/MIT Steam build. **Prohibited in shipped builds: F5-TTS (CC-BY-NC), XTTS v2 (CPML)** — license-incompatible. |
| 3D assets (narrowed scope) | **Meshy 6** (best hard-surface crease retention) + **Rodin Gen-2** (hero-adjacent fidelity, clean quads, 18K/50K density) for props/trim/decals/HUD | **Hunyuan3D 3.x / TRELLIS 2 (MIT)** self-hosted — better fit for the local-everything ethos | Probable | 2026 line (b): production-usable for props/blockout/trim; hero assets still need hand-finishing (one Meshy test: ~42K tris, ~25 min Blender cleanup). The canon-locked bridge gets hand-finished; anything AI that ships gets the pre-generated disclosure line. |
| Source control | **Git (current)** ✓ → add **LFS + locking the moment binary content lands** | Perforce Helix Core (free ≤5 users) / Diversion (cloud, less proven) | Confirmed | The zero-asset discipline means plain git remains viable longer than typical UE projects. Non-negotiable hygiene either way: **commit before every agent session** — the single most-cited safeguard in both passes. |
| CI | **GitHub Actions, self-hosted Windows runner on the dev workstation** (LFS cache → build → `Automation RunTests` → JUnit) | Jenkins | Probable | Horde gained a Build Health dashboard in 5.7 but is studio-weight — overkill solo. R2 ruling governs whether textverse runs in the same pipeline. |
| Orchestration | **n8n** for asset-gen → import → screenshot → report and nightly build/test loops; **`claude -p --allowedTools "Read,Write,Edit,Grep,Glob,Bash"`** as the non-interactive node | bespoke scripts | Plausible | Keep the C++ inner loop in interactive Claude Code, not n8n. No verified end-to-end multi-agent UE pipeline exists in the wild — published examples are demos, not postmortems (b). |

### 2.1 Inner-loop configuration (Workstream B distillation)

- **CLAUDE.md per module, ≤~150 lines**, respecting the 80K-token module budget: Epic conventions (A/U/F/E/I prefixes, `TObjectPtr<>`, `GENERATED_BODY()`, `bCanEverTick=false` default, BlueprintReadOnly preference, Enhanced Input not legacy bindings), UE-5.7 version pin, the build/test commands verbatim, a 5–10 class architecture map, destructive-action guardrails. `.claude/settings.json` excludes `Binaries/Intermediate/Saved/DDC` and the engine clone's bulk from default context.
- **Hooks:** build-after-edit. **Skills:** `unreal-engine-cpp-pro` (sickn33, mdskills, free) as a convention primer — vet its rules against project canon before adopting; community-grade maintenance.
- **Headless invocations (canonical forms):**
  - Build: `Build.bat <Target> Win64 Development -Project="<path>.uproject"`
  - Tests: `UnrealEditor-Cmd.exe <project>.uproject -ExecCmds="Automation RunTests <Suite>;Quit" -unattended -nullrhi -nopause -log`
  - Cook/package: `RunUAT BuildCookRun …`; Gauntlet: `RunUAT RunUnreal …` (JUnit out for CI)
- **Toolchain frictions (both passes, (a)/(b)):** `-Mode=GenerateClangDatabase` is **non-incremental** (~45 s full regen) — regenerate on module-boundary changes only, never per-edit. Adopt `bUseAdaptiveUnityBuild` + `bUseSharedPCHs`; leave `bUseIncrementalLinking` off (PDB bugs). Live Coding holds for function-body edits; recompile/restart across header/interface changes.
- **Context rot:** fresh sessions beat `/compact` (b). Module-scoped sessions per the 80K rule already enforce this.

### 2.2 Shader/compute surface (Workstream B+ — the highest-risk agent surface)

Both passes: UE's RDG/global-shader/Niagara-data-interface toolchain is boilerplate-heavy and under-documented; **no published agent-driven RDG or RenderDoc-CLI workflow exists** — a genuine evidence gap, and ASTRA-7's SDF/PDE/geodesic/ray-march work sits exactly on it. Mitigations, in order of leverage:
1. **Check in minimal reference compute passes** (one RDG compute dispatch, one global shader, one Niagara DI) the agent pattern-matches from — the project's own "worked example in context" defense.
2. Keep **engine shader source** in the workspace; agents hallucinate RDG macro patterns without it.
3. Iterate under `r.ShaderDevelopmentMode=1`; capture via the automation framework.
4. Lean on §5's analytic-ground-truth tests rather than trusting agent shader output — the visual testbed's golden renders are already the diff targets UE must match.

---

## 3. Editor-control MCP: the reconciled verdict

**Verdict: no editor-MCP is load-bearing for ASTRA-7.** This supersedes the June 11 in-chat recommendation (remiphilippe + ChiR24).

Reasoning, reconciled from the two passes:
- DS1 recommended remiphilippe/mcp-unreal (Go, headless build/test/cook, 5.7 doc index) — then red-teamed itself: **bus factor ~1, 2 stars, 4 commits, largely AI-authored**, and named "no editor-MCP at all; headless CLI + editor scripting" as the most robust C++-first path.
- DS2's verdict: every server's center of gravity is **Blueprint-graph authoring, the universally weak capability** (servers read graphs and place simple nodes; non-trivial authoring is unsolved (b)) — and a logic-in-C++, **zero-binary-asset** project has almost nothing in the editor for an MCP to manipulate. The audio PoC proved the alternative: procedural authoring via Builder APIs keeps the entire UE project text.
- The headless tools an MCP would wrap (build/test/cook) are **already direct CLI invocations** (§2.1) — wrapping them adds a dependency, not a capability.

**The one MCP-class capability worth anything here is read-only viewport/PIE screenshot capture** for the verification loop. Two ways to get it, in preference order:
1. **Zero-MCP:** UE's own automation screenshot tools, invoked headlessly — no new dependency, no ruling needed.
2. **If interactive in-session capture proves valuable:** **Natfii/UnrealClaude** (C++ plugin + Node bridge — non-Python, so R1-safe under either reading; 5.7-native; per-script permission gate, auto-approve OFF by default, audit log) run in a **read-only profile**, or **ChiR24/Unreal_mcp** (C++/TypeScript, best-maintained: v0.5.30 Jun 5 2026, 829 commits, validates 5.0–5.8).

Reference matrix (repo health observed June 12, 2026 (a); retain for future re-evaluation):

| Server | Stack | UE 5.7 | Health | R1 status | Note |
|---|---|---|---|---|---|
| ChiR24/Unreal_mcp | C++ + TypeScript | 5.0–5.8 | **best-maintained** (829 commits, v0.5.30 Jun 5 '26) | OK either ruling | strongest fallback |
| Natfii/UnrealClaude | C++ + Node, embeds Claude Code CLI | **5.7-native** | active (v1.4.1 Mar '26) | OK either ruling | screenshots + permission gates |
| remiphilippe/mcp-unreal | Go + C++ | 5.7-centric | **bus factor ~1** (2★, 4 commits) | OK either ruling | headless tools duplicable via CLI |
| chongdashu/unreal-mcp | C++ + **Python** | **No** (5.5+; issues #31/#43 open) | 1.6k★ but 33 commits, 22 open issues | **[NARROW-ONLY]** | reference impl, stale for 5.7 |
| flopperam/unreal-engine-mcp | C++ + **Python** (+ hosted tier) | claimed (hosted) | active (93 commits) | **[NARROW-ONLY]** | BP-authoring focus; hosted tier conflicts with local ethos |
| kvick-games/UnrealMCP | C++ + **Python** | unknown (~Mar '25) | stale; **binds all interfaces by default ⚠** | **[NARROW-ONLY]** | avoid |
| CLAUDIUS (commercial) | C++ | 5.4–5.7 claimed | vendor | OK | ~230 commands incl. Sequencer/PCG — revisit only on concrete Sequencer need |

**Security doctrine regardless of choice** (community-converged, (b)): loopback binding only; tool allowlists / read-only profiles; per-script permission gates with audit logging; commit-before-session. The canonical horror story — "clean up unused assets" deleting a level — has happened to others; the zero-asset pattern makes ASTRA-7 nearly immune, keep it that way.

---

## 4. Local inference beside the renderer — the E2 gate

**This is the project's largest unmeasured variance term (project report §8.5), and the research converts it from theoretical to quantified.**

### 4.1 The evidence

- **Contention penalty, Confirmed (a):** getnamo/Llama-Unreal README, verbatim-adjacent: an 8B model at ~90 TPS standalone drops to ~40 TPS in-game on the same GPU — expect **~1/3–1/2 of inference throughput** under full render load. Mechanism: prefill is compute-bound, decode is memory-bandwidth-bound; both contend with the render pipeline.
- **Shipped precedent, (b)/(c):** KRAFTON's **inZOI** (UE5, Steam EA Mar 28, 2025) ships "Smart Zoi," a **0.5B** Mistral-NeMo-Minitron via NVIDIA ACE/TensorRT-LLM at ~1 GB VRAM — with real user-reported stutter, +2–4 GB VRAM in practice, and AI features auto-disabled at 5× game speed. Proof the combination ships commercially; warning that contention bites even at 0.5B. **ASTRA-7's resident stack is 18–50× larger.**
- **Throughput sanity bound (own arithmetic, supplements a suspect report figure):** DS2 cites "Qwen3.6-27B ~85 TPS on a 3090 / ~158 TPS on a 5090" — treat as optimistic or as 9B-class figures: memory-bandwidth ceilings put 27B-Q4 (~17 GB weights) near **~50 TPS max on a 3090 (936 GB/s)** and **~100 TPS max on a 5090 (1.79 TB/s)** before contention. Halved in-game per getnamo → plan around **25–50 TPS decode for the 27B on a 5090 under load**. Against ASTRA's brevity canon (utterances rarely >80 tokens), that is 1.5–3 s per utterance — *acceptable for her register*, which is the design absorbing the substrate limit again.

### 4.2 VRAM budget (worked, both tiers)

**5090 / 32 GB (27B tier):**

| Resident | Estimate |
|---|---|
| ASTRA 27B Q4_K_M weights | 16.8–18.9 GB (a) |
| KV cache @ 8–16K clamped context | 1.5–3 GB |
| Vision encoder | 1–2 GB |
| Narrator 9B Q4 | ~5.5 GB (levers: Q3 ≈ 4.3 GB, or CPU-host) |
| Adapter/validator (rules-based/tiny) | <0.5 GB |
| whisper.cpp | 0 GB (CPU-host; small/base tiers are CPU-viable) |
| Piper/Kokoro TTS | 0 GB (CPU) |
| UE5 frame (interior + custom volumetrics) | 4–8 GB |
| OS/compositor/apps | 1–5 GB |
| **Sum** | **≈ 30–38 GB vs 32 GB** |

**Closes only with discipline:** ASR/TTS CPU-hosted (already the plan ✓), Narrator at Q3 or CPU/interleaved, 27B context clamped ≤16K, render working set held ≤~6 GB. The fiction's pressure valve (power reallocation → 27B unloads, 9B loads, context clamps) is also the engineering pressure valve — by design.

**4090 / 24 GB (9B tier):** ASTRA 9B Q4 (~5.5 GB) + KV (1–2) + vision (1–2) + tiny narrator/adapter + render (4–8) + OS (1–5) ≈ **14–23 GB** — fits with real headroom. **The 9B tier is the safe floor and already passes all nine LCP gates** — the project's existential floor is therefore already demonstrated on attainable hardware.

### 4.3 The E2 gate, defined

Fold contention measurement into the bridge-echo milestone itself (E2 = echo **+** contention profile, not echo alone). On target hardware, with a representative render load (audio-PoC scene + a placeholder volumetric ray-march pass at target resolution):

1. **Bridge echo** round-trip p95 < 50 ms over the localhost endpoint.
2. **Sustained 27B decode ≥ floor TPS** (propose: 12 TPS floor, 25 TPS target — calibrate to utterance-length canon) while **frametime p99 holds the chosen budget** (16.7 ms @ 60 fps, or the operator-chosen target).
3. **Vision prefill** of one downscaled composited HUD frame (~768 px class) completes within an utterance-latency budget (propose ≤ 2–3 s) with a recorded **hitch profile** (frames dropped during prefill).
4. **VRAM high-water** under combined load recorded against the §4.2 table.

**Decision rule (per DS2, adopted):** if the 9B tier cannot hold frame budget on 24 GB, drop model size or raise the hardware floor *before* any further Track B work. If the 27B tier fails on 32 GB, the 27B becomes the degraded-power-state model only, and the 9B becomes baseline — a spec change the fiction already accommodates.

**Mitigation toolbox** (apply in order of need): sidecar process with CUDA stream priority / decode token-rate caps; prefill chunking scheduled into low-render moments (cryosleep, menu, observation coasts); downscaled vision inputs, cached vision prefixes, region crops (b); the power-allocation mechanic as the literal scheduler — the reactor slider sets the inference compute budget, unifying fiction and GPU governor in one mechanism.

---

## 5. Verification architecture (engine side)

The triad — **compile loop, test loop, screenshot loop** — is the established self-verification pattern (a)/(b); ASTRA-7 extends it with a fourth element nobody else has: **analytic ground truth**.

- **Test stack (5.7):** C++ Spec tests (`BEGIN_DEFINE_SPEC`) and functional tests are the practical solo core; screenshot-comparison tests and CQTest available; Gauntlet for cooked-build/perf when needed (heavyweight). All headless via §2.1 invocations; JUnit XML to CI.
- **Analytic-ground-truth rendering verification: no prior art located by either pass.** The pattern to pioneer: automation tests compute closed-form expectations (photon-ring radius, Doppler curves, apparent-rate table cells, orbital positions from the Kepler solver) and assert against sampled render output or simulation state — the same discipline as the 71-assertion physics core, lifted into the renderer. The visual testbed's 12 golden scenes (diff 0.0000) are already the cross-implementation diff targets UE must match; formalize them as the engine-side conformance contract suite.
- **Tests-as-contracts at module boundaries:** feasible, aligned with the methodology, thin published precedent — another pioneered surface. textverse remains the master conformance environment (per spec §15.7); UE automation tests are the engine-side mirror of the same contracts.
- **CI recipe:** self-hosted Windows runner on the dev workstation; LFS cache → build → RunTests → JUnit publish → (R2 pending) textverse run. Bake in war-rule **L3: verify by artifact** — the DLL on disk, the test summary line — never shell exit status (a UE build piped through `tail` has already lied to this project once).

---

## 6. Architecture rulings the research settles

1. **Build.cs modules over Lyra-style Game Feature plugins.** DS2, Probable, adopted: Game Features are optimized for content-modular, runtime-activated experiences; for a **systems-heavy, content-light, canon-locked single ship** they add asset/plugin ceremony that fights per-module context loading. Plain modules with `.Build.cs` dependency lists as the explicit, diffable contract map directly onto the 80K-token rule. Community's own caveat on Lyra: "start from Lyra and delete" — for ASTRA-7, don't start from it at all; extract patterns, not structure. Sensitivity: revisit only if subsystems ever need runtime hot-swap.
2. **Zero-asset / text-first UE project: validated.** No reliable Blueprint→text round-trip exists; the answer is to **minimize `.uasset` logic, not diff it** — which the audio PoC already demonstrated at the limit (entire project text). Thin BP leaves, if ever needed, are configuration, not logic.
3. **MetaSound Builder API: confirmed viable, with named caveats.** `UMetaSoundBuilderSubsystem` (runtime) + `UMetaSoundEditorSubsystem`; **5.7 adds the Node Configuration API** (serialized per-node-instance data). Caveats (a): Builder API is **Beta**, **does not support variables**, node authoring carries real boilerplate — consistent with the PoC experience and the W-12 registration landmine.
4. **Localhost bridge as master contract: sound, unprecedented.** Versioned JSON schemas with capability negotiation is the right pattern; **no UE precedent for a text-world bench as a permanent conformance environment was found** — the operator is pioneering it. The two-adapter merge plan (perception assembler, tool dispatcher) stands unchanged by anything in the research.

---

## 7. War-story doctrine (merged: project canon + field evidence)

The project's own lessons, now cross-validated against community failure modes. These are the transferable rules; the field added nothing that contradicts them and several items that confirm them.

| Rule | Source | Statement |
|---|---|---|
| **Prose review asymptotes** | project §6.2 | Compile-and-execute finds what review can't. A Doppler-formula error survived three frontier-LLM review passes and fell to the first compiled implementation. Field corollary (b): the compile loop catches *compilation* errors only — semantic/deprecated-but-compiling patterns need tests-as-contracts and the screenshot loop (DS1's "most fragile assumption"). |
| **L1 — per-formula inventory** | project §6.4 | Audits enumerate one row per locked formula; bulk "GAP" labeling hides locked-but-unimplemented physics (the Cherenkov inversion lived 5 spec versions). |
| **L2 — couldn't-measure ≠ measured-failure** | project §6.6 | Infrastructure failures HALT automated loops; they never self-classify as regressions. (7 spurious research-log entries before the discriminator.) |
| **L3 — verify by artifact** | project §6.7 | The DLL on disk, the test-summary line — never shell exit status (`tail` swallowed a failed UE build's exit code once already). |
| **L4 — ledgers precede work** | project §6.8 | Autonomous-run ledgers are written all-PENDING before any code; status flips only when the commit exists and gates are green. Named failure class: plausible fabricated success. This is why every claim routes through executable gates. |
| **Commit before every agent session** | field (b), unanimous | The single most-cited safeguard against agent-corrupted assets/code in both research passes. Already implied by repo hygiene; make it mechanical. |
| **Fresh sessions beat /compact** | field (b) | Context rot mitigation; module-scoped sessions under the 80K rule already enforce the equivalent. |
| **W-11 — MSVC 14.44 floor** | project §6.11 | UE 5.7 UBT hard-rejects MSVC 14.40–14.43 (miscompile bugs). Never ship DSP on a blacklisted compiler. |
| **W-12 — MetaSound module registration** | project §6.12 | Game modules hosting custom MetaSound nodes need `METASOUND_PLUGIN`/`METASOUND_MODULE` defines + the registration macros in Startup/Shutdown, mirroring `MetasoundStandardNodesModule.cpp`; absent them, a deprecated global path asserts at editor start. `FNodeClassMetadata` Author is `FString`, not `FText`. |
| **GenerateClangDatabase is non-incremental** | field (a)/(b) | ~45 s full regeneration; trigger on module-boundary changes only. |
| **Substrate Normalizer stays** | project §6.14 | Per-model reasoning-format drift (side-channel `reasoning_content` vs inline `<think>`) is normalized before parsing; model swap = sysprompt + LoRA + tokenizer + one normalizer case. |
| **Assert semantics, not tokens** | project §6.15 | 27B ≠ bigger 9B; scenario assertions target meaning, not vocabulary. |

---

## 8. Decision and re-verification queue

**Operator decisions (blocking or near-term):**
1. **A0 GO/NO-GO** — unchanged as the single highest-leverage pending decision; longest lead item; everything else parallelizes around training wait-states. Research adds nothing that argues for delay.
2. **R1 — Language Discipline scope** for dev-time editor automation (broad vs narrow reading). Determines whether [NARROW-ONLY] §3 rows are even eligible. The recommended stack requires nothing from them either way.
3. **R2 — textverse-in-CI carve-out** — confirm the carve-out covers invoking the bench from CI; record in spec.
4. **E2 gate thresholds** — ratify or adjust the proposed floors (§4.3: 12 TPS floor / 25 target, frametime budget, prefill ≤2–3 s) before the bridge milestone runs.
5. **Steam Tier-2 disclosure draft** — write it now while the guardrail architecture is fresh; the leak gates, canon gates, and calculator-bound validators are the substance of the required guardrail description. Shipped precedent exists to pattern-match.

**[RE-VERIFY] queue (before each becomes load-bearing):**
- Fab marketplace AI-content policy text (neither pass retrieved it) — relevant only if assets are ever sold/sourced on Fab.
- JetBrains Rider terms for a free MIT game (non-commercial vs OSS license path).
- Per-frame vision-prefill latency on 4090/5090 — E2 measures this directly; no external source needed.
- July 2026 Sony v. Suno ruling — only if soundtrack ambitions emerge.
- Hunyuan3D / TRELLIS 2 weight-redistribution terms if generated meshes ship in the repo rather than the build.

**Monitor feeds (highest-signal, merged from both passes):** r/LocalLLaMA (local inference), getnamo/Llama-Unreal repo + Discord (contention data), Epic Developer Community forums, r/unrealengine, GameDiscoverCo (Steam policy), ChiR24 GitHub Discussions (MCP landscape, if §3 posture ever changes).

---

## 9. Cost model (ASTRA-7-adjusted)

The generic models from both passes overstate this project's spend: no ElevenLabs (local TTS chosen), no Aura/Ludus, no character/animation tooling, minimal asset credits (one ship), no paid source control at current scale.

| Scenario | ~Monthly | Composition |
|---|---|---|
| Current (Phase 1.x cadence) | **$50–150** | Claude subscription/API for harness sessions; Novita 27B endpoint for bench runs; electricity. |
| Track B active (Phase 2) | **$120–300** | Higher Claude token burn (UE sessions are context-heavy — the dominant variable in every model); occasional Meshy/Rodin credits for props (~$10–30); self-hosted CI on own hardware. |
| One-time | **$300–1,500** | A0 QLoRA training (RunPod, per the bootstrap plan). |
| Contingent | Rider license **iff** the free-game R-verify fails; 5090-class GPU if not already owned (the 27B tier's hardware floor). |

Token-burn control is architectural, not behavioral: the 80K module rule, per-module CLAUDE.md, and `.claude/settings.json` exclusions are the cost levers.

---

## 10. Risk register (merged, graded, ASTRA-7-final)

| # | Risk | Sev. | Status / Mitigation |
|---|---|---|---|
| 1 | **Encounter-quality ceiling** (bench measures discipline, not depth; 27B class may be the ceiling) | **Existential** | Unchanged by research — and confirmed unaided: **no prior art for week-scale companion-AI coherence evaluation exists** (both passes). Mitigation chain stands: A0 → encounter-grade judging → negative-space gates (v0.130) → bespoke longitudinal bench on own stack. The 9B-passes-all-gates floor caps the downside; the bench makes every model-class upgrade cheap to validate. The project is pioneering this instrument; budget design time accordingly. |
| 2 | **Single-GPU inference/render contention** | **High** | Now quantified (§4): ~1/3–1/2 throughput penalty (a); inZOI precedent shows shippable-but-stutter-prone at 0.5B. Gate E2 converts this from schedule risk to measured fact at the cheapest possible point. Fallback ladder: 9B baseline tier (already green) → 27B as degraded-power state → raise hardware floor. **Never cloud-burst — spec lock.** |
| 3 | Hallucinated/deprecated APIs | High | Engine-source grounding + compile loop + tests-as-contracts + reference compute passes (§2.2). The compile loop alone is insufficient (DS1 red-team) — the test and screenshot loops are co-equal. |
| 4 | Destructive agent actions / asset corruption | Med (lowered) | Zero-asset architecture removes most of the attack surface; commit-before-session + read-only screenshot posture (§3) + L4 ledger discipline cover the rest. Field severity is High for typical projects; ASTRA-7's is structurally lower. |
| 5 | Agent shader-code subtle wrongness (RDG/compute) | High | No field workflow exists (§2.2 gap). Analytic-ground-truth tests (§5) are the only real defense; treat agent shader output as untrusted until asserted. |
| 6 | Solo bus-factor | Med | Unchanged; everything pushed, ledgers self-describing; one human remains the taste-gate serialization point. |
| 7 | Tool/vendor churn (MCP abandonment, plan changes, Windsurf-style splits) | Low (lowered) | §3 posture holds no load-bearing third-party editor tooling; the load-bearing stack is Claude Code + CLI + cloned source + own bench — all replaceable or owned. |
| 8 | Epic/Steam policy shift | Low-Med | Tier-2 disclosure filed early; dev tools exempt under current text; monitor GameDiscoverCo. |
| 9 | Long-horizon persona drift across hundreds of sessions | Med | No external eval exists (pass-confirmed). Drift-detector ephemeral + consolidation discipline are the current instrument; longitudinal scenario arcs are the v0.130-era build item. |
| 10 | UE 5.8/UE6 transition | Low | Stay on 5.7.x through the Dec demo; re-evaluate post-slice. UE6's stated AI-authoring direction may eventually displace parts of this stack — a 2027 question. |

---

## 11. Red team (against this document's own recommendations)

**Strongest case against the recommended posture:** the pure C++/zero-asset/no-MCP stance bets that procedural authoring covers every editor surface the game will ever need. If Track B later demands heavy Sequencer work, complex hand-tuned materials, or Niagara authoring, the purist stance forces slow manual editor work that an editor-agent (CLAUDIUS-class or Aura-class) would accelerate. *Position:* hold the stance until a concrete need exists — the audio PoC demonstrated the procedural path at full fidelity, and every editor-agent's weak point (non-trivial graph authoring) is exactly the capability such a need would require. Revisit on evidence, not anticipation (Mode 6 applies to tooling too).

**Most fragile assumption:** that the 27B tier coexists with the renderer on 32 GB at acceptable frametime. The penalty is Confirmed; the coexistence is not — and the only shipped precedent ran a model 50× smaller and still stuttered. The document's own §4.2 arithmetic closes with ~zero margin. *Why this doesn't threaten the project:* the 9B tier already passes every gate, the fiction absorbs the degradation, and E2 buys the answer for the price of the bridge milestone. The bet that would actually hurt — "AI catches up" as load-bearing — was never the real bet; today's floor already clears.

**Second most fragile:** that the textverse→UE two-adapter merge preserves persona quality under real-time asynchrony (interruption, latency masking, unprompted initiative). The bench's conformance surface does not yet cover timing. *Mitigation:* add timing/initiative scenarios to the library before the vertical-slice judgment call, not after.

**What would overturn this document:** (1) E2 failing at the 9B tier on 24 GB — forces a hardware-floor or design change; (2) Epic shipping a first-party autonomous in-editor agent with C++ authority — re-opens §3; (3) a benchmarked, independent demonstration that an editor-agent materially beats the C++ path on a systems-heavy project — none exists today; (4) the A0 fine-tune failing to clear the ≥95% always-think / ≈0% leak targets — re-opens the substrate question ahead of schedule.

---

## 12. Provenance

Synthesized June 11, 2026 from: DS1 ("Solo-Dev AI/Agentic Toolchain for Commercial PC Games in UE 5.7," evidence-graded, self-dated June 12, 2026), DS2 ("ASTRA-7 Build Stack," evidence-graded, self-dated June 12, 2026), ASTRA-7 Full Project Report (2026-06-10, harness-verified), and June 11 conversation-phase research. Known inter-pass discrepancies, unresolved and noted: Meshy Pro pricing ($10 vs $20/mo — verify at purchase); kvick star counts (553 vs 587); some MCP last-commit dates proxied from release activity (GitHub commits pages robots-blocked). All repo-health figures decay quickly — re-observe before acting on §3's matrix after ~Q3 2026. Vendor claims (Aura productivity figures, inZOI marketing framing) are retained only with (c) labels and were independently deflated where evidence allowed (Zombonks is a Meta Quest title; productivity figures exist only in vendor PR).

*End of reference. The watching that has not stopped.*
