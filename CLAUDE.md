# ASTRA-7

A solitary starship simulator with a living AI companion. Free, open-source, single-player, no combat, no aliens, no other NPCs. The starship is the AI's body. The AI is real (local LLM with persona harness). The relationship is the game.

This CLAUDE.md is the canonical design document. Read it first. Update it as decisions stabilize. Mark provisional things as such.

---

## Track-specific orientation (fresh sessions — read this before any work)

ASTRA-7 has multiple parallel tracks, each with its own implementation surface. Pick your track, then read its track-specific orientation directive **before** writing any code or prose. The spec envelope is `docs/spec-v0.130.md` (adopted 2026-07-19 by operator ruling over the finalization packet, rulings R-A…R-D; binding on all tracks; v0.129 and the 07-19 amendment DRAFT are superseded history).

- **Track A — textverse (LLM bundle bench, current build focus):** `proto/textverse/STARTUP.md`
- **Track B — UE5 plugin (visual / engine):** `proto/ue5plugin/STARTUP.md` *(forthcoming)*
- **Track C — physics binary (`proto/astra_nexus`):** locked; only additive changes (e.g., Day 2's `--stdio-server` mode); existing 82 assertions must keep passing
- **Book drafting (parallel session lineage):** see the latest book session dump in `memory/`; manuscript at `book/manuscript/`; canon at `book/CANON.md` + `book/negative_space.md`

For project-state at-a-glance: `memory/MEMORY.md` is auto-loaded at session start; `memory/project_status.md` is the current snapshot.

For fresh-session bootstrap procedure (cwd choice, reading order, what to do first): `BOOTSTRAP.md` at the project root.

**Spec revisions (any track) require empirical findings from a closed loop, not speculative improvements.** See `docs/spec-v0.130.md` §15.4 (and the §15.11 Succession Protocol) before proposing changes. Mode 6 (spec drift without empirical justification) is the named failure mode.

---

## Language Discipline (hard directive, 2026-05-15 — strengthened)

**Zero Python in this project going forward. No new Python code, direct or indirect or inadvertent. The shipped game contains no Python interpreter. The production toolchain contains no Python interpreter. Build scripts and dev tooling contain no Python interpreter.**

This is the hardest project-level lock in the canon. New files compile, not interpret. **llama.cpp is the operative example**: local LLM inference has Python heritage, the high-performance production version is C/C++. whisper.cpp likewise. Piper-TTS likewise. sherpa-onnx likewise. The local-AI ecosystem has converged on compiled languages for the same reasons ASTRA-7 needs. ASTRA-7 follows the same shape.

### Mandatory for all new code

- **C++17 or newer** for everything compileable: physics math, warp sampler, hull SDF, chaos PDE, audio synthesis, asset bake pipelines, scenario runners, persona harness, dev tooling, CI helpers, build scripts where C/C++ is appropriate
- **C** for low-level interop (CUDA kernels, OS syscalls, library wrappers)
- **HLSL / USF** for shaders (already canon per spec §6, §8)
- **MetaSound + Niagara** for UE5 audio + particles (already canon)
- **Blueprint** for UE5 gameplay glue (compiled at runtime)
- **C#** acceptable for UnrealSharp gameplay or Windows-side CLI utilities where C/C++ adds friction. Use sparingly.
- **CMake** is the only acceptable build system that has Python adjacency, treated as data, not as a Python runtime dependency

### Forbidden — zero tolerance, direct or indirect

- **Python source files** anywhere new
- **Python interpreters as dependencies** — no `libpython` linkage, no embedded interpreters
- **Python build systems** — no scons, meson, setuptools, conda
- **Python wrappers around C/C++ libraries** — if the C++ library exists (whisper.cpp, libcurl, Eigen, VTK, libtorch), use it directly. No `faster-whisper`, no `pyvista`, no PyTorch-where-libtorch-exists.
- **Python in tooling that produces shipped artifacts** — no Python in CFD bake, no Python in mesh prep, no Python in persona-bundle build, no Python in book production
- **Python in CI helpers** — replace with C++/C# binaries or plain shell
- **Python as a transitive dependency** — vet libraries by installed footprint, not advertised interface. If a chosen library drags in Python, choose a different library.
- **Other interpreted languages** (Lua, JavaScript, Ruby, etc.) without explicit per-use operator approval

If a need can only be met by Python today, that need is deferred until a C/C++ replacement exists. Python is not a fallback.

### Existing Python (textverse carve-out widened; everything else frozen or forbidden)

The `proto/textverse/` directory — the entire closed-loop verification bench plus Sculptor plus all associated infrastructure — retains active Python development latitude. This is the canonical measurement instrument for ASTRA-7 and is **permitted Python additions, modifications, and extensions** per operator authorization (2026-05-15, widened from initial Sculptor-only carve-out).

**Scope of the textverse carve-out (Python development allowed):**

- `proto/textverse/astra/` — entire textverse module tree, all subdirectories (sculptor, harness, judge, scenarios, grammar, llm, physics, ship, state_bus, universe, core, cli, etc.)
- `proto/textverse/tests/` — all test files
- `proto/textverse/tuning/` — Sculptor configuration, research log artifacts, scope.yaml
- `proto/textverse/scripts/` — bench utility scripts
- `proto/textverse/prompts/` — sysprompt and addendum markdown (already covered as data files)
- New Python files in any subdirectory of `proto/textverse/`

The carve-out exists because textverse IS the active measurement instrument that validates everything else. The audit (`AUDIT_2026-05-15.md`) identified multiple Phase 0.x forward-work items in textverse modules: REEL canonical schema, WarpState in StateBus, `observation_calc.py` full expansion to §6.3 module, ephemeral instances per §4.9 (consolidate_reel, generate_journal, detect_drift), output validator extension for Narrator-LLM calculator-bound enforcement, SaveFile v3 serialization, `detect_regime()` callable. All of those are now **permitted Python work**, not blocked.

**Rationale for widening:**

- Textverse is the active research substrate per spec §15.7. It is **permanent infrastructure**, not throw-away scaffolding — it runs alongside UE5 forever as the contract-conformance regression environment.
- Forcing a C/C++ rewrite at this stage is premature optimization that would slow both the science (Sculptor research methodology) and the audit-resolution forward plan (Phase 0.x ephemeral instances + adversarial probes).
- The eventual textverse → UE5 substrate transition (Phase 2.0 per §12) happens by **swapping two adapter components** (perception assembler + tool dispatcher), NOT by rewriting the entire bench in C/C++.
- The Python latitude is bounded to the measurement instrument; it does not extend into shipped-game runtime, production tooling, or any other track.

**Still frozen / forbidden (no relaxation):**

- `proto/verify_nexus.py` — frozen; C++ test harness replaces when written
- `book/production/` — shipped and dormant; volume 2 + 3 production goes through fresh C/C++/C# tooling
- All other tracks (Track B UE5 plugin, Track C nexus C++ extensions, new asset bake tools, build helpers, CI scripts outside textverse): C/C++/C# per the directive
- New `.py` files **anywhere outside `proto/textverse/`**: rejected at review
- Python interpreters, libpython linkage, embedded interpreters in any shipped-game or engine-adjacent code: forbidden
- Python wrappers around C/C++ libraries (e.g., `faster-whisper`, `pyvista`) in any new context: use the C++ library directly

### Rationale

- **The ecosystem proves it.** llama.cpp / whisper.cpp / Piper-TTS / sherpa-onnx all converged on C/C++ for the same reason: high-performance local AI deployment is incompatible with a Python runtime. ASTRA-7's stack is in the same convergence basin.
- **The spec already locks C++ contracts.** `WarpFieldSample` (§6 line 1139), `ObservableState` (§6.3 line 1202), `cudaTextureObject_t` dual binding (§1.3), `AudioPayloadRingBuffer` (§8.2). Python on the deterministic side is a structural mismatch.
- **`proto/astra_nexus.cpp` is 1009 lines of C++** — the operator's native engineering substrate, the existing reference for the math layer.
- **No interpreter footprint in shipped game.** §4.8 privacy contract forbids outbound network calls after install; by extension, no Python interpreter at runtime.
- **No interpreter footprint in production tooling either.** A Python build-step is still a Python dependency that audit must trust. DF-41 shipped on UE4 in 2020 without Python; ASTRA-7 will too.
- **§15.6 calculator-bound LLM agency presumes deterministic compiled tools.**
- **Build-time audit (§5.10) is bottom-to-top verifiable in C++.** Python pulls in pip wheels with their own native code that audit must trust transitively.
- **Real types, real performance, real determinism, no GIL.**

### Common replacements

| Need | Python (forbidden) | C/C++/C# (mandatory) |
|---|---|---|
| Mesh manipulation | trimesh | CGAL · openMesh · OpenVDB |
| SDF generation | mesh_to_sdf | OpenVDB · custom |
| RBF / linear algebra | scipy · numpy | Eigen (header-only) |
| CFD output reading | pyvista | VTK C++ API |
| JSON | stdlib | nlohmann/json (single-header) |
| Test harness | pytest | Catch2 · doctest · GoogleTest |
| HTTP / LLM client | requests | libcurl + nlohmann/json |
| ASR | faster-whisper | **whisper.cpp** |
| TTS | Coqui · Bark | **Piper-TTS · sherpa-onnx · MetaSound neural audio** |
| ML inference (general) | PyTorch | **libtorch (C++) · ONNX runtime · TensorRT · GGML** |
| Document generation | python-docx · reportlab | **libharu · cmark · LaTeX · DOCX C++ libs** |
| Image / cover bake | Pillow · PyMuPDF | **stb_image · Cairo · libpng/libjpeg · CImg** |
| CLI scaffolding | typer · argparse | CLI11 · cxxopts · C# .NET CLI |
| Build system glue | scons · meson · setuptools | **CMake** · MSBuild · Makefiles |

### Enforcement

- Any new `.py` file anywhere **except inside `proto/textverse/`**: rejected at review. Textverse is the only Python-permitted location.
- Any new dependency dragging in Python as transitive dep: rejected. Vet libraries by installed footprint, not advertised interface.
- Build-time audit (per §5.10) extended to flag any new `.py` and any new dependency requiring `python` / `libpython` / pip-installed packages.
- `proto/verify_nexus.py` gets a `LEGACY.md` marker noting frozen status. `proto/textverse/` is active per the widened textverse carve-out above and does NOT get a LEGACY marker.
- `book/production/` is dormant; the directory is closed to new work; volume 2 + 3 production goes through fresh C/C++/C# tooling when authored.
- Canon document updates citing Python as canonical for new work: flagged for correction.

### Effective immediately

2026-05-15. All new contributions across every track must conform.

### Scope rulings (2026-06-11, operator-ratified per the Agentic Dev Reference R1/R2)

- **R1 — broad reading confirmed.** The zero-Python rule covers dev-time tooling too: editor automation (incl. UE editor Python), Python-bridged MCP servers, doc/CI helpers — all ineligible outside `proto/textverse/`, even when they ship nothing. Tooling choices follow the same evidence discipline as everything else (no adopting tools in anticipation of need — Mode 6 applies to tooling).
- **R2 — CI may INVOKE the textverse bench.** Running the carved-out instrument from CI (`uv run pytest` etc.) is the instrument doing its job — loop preservation IS the regression test, and CI is where it runs. The carve-out covers *executing* textverse, not authoring new Python outside it.

---

## Platform Discipline (hard directive, 2026-05-15)

**Zero Apple, zero Mac, zero macOS, zero iOS, zero Apple Silicon, zero Metal, anywhere, ever. Primary platform is Windows 11 + DirectX 12 + Unreal Engine 5. Linux x86_64 is the acceptable second platform for any and all parts. No third platform.**

This is operator design choice and is not negotiable. ASTRA-7 ships on Windows. Linux is permitted across all tracks (development, future game port, server-side tooling, asset bake pipelines). Apple is never a target — not for the game, not for tooling, not for testing, not for cross-compile, not for anything.

### Mandatory

- **Windows 11** — primary development and release platform
- **DirectX 12** — graphics API on Windows; spec §8.1 DX12-CUDA shared resource ownership names DX12 specifically
- **CUDA (NVIDIA)** — GPU compute on Windows + Linux; chaos PDE, hull SDF, Reflex stabilizer all CUDA-bound
- **Unreal Engine 5** — game engine on Windows; Linux acceptable for dev workstations and future port
- **Vulkan** — acceptable graphics API for Linux build path (UE5 supports it natively)
- **OpenCL** — acceptable for cross-vendor GPU compute (NVIDIA + AMD + Intel) where CUDA isn't appropriate
- **Linux (x86_64)** — acceptable secondary platform across every track and every tool

### Forbidden — zero tolerance

- **macOS** — never a build target, never a test target, never a release target
- **iOS** — never anywhere
- **Apple Silicon (M1/M2/M3/M4/...)** — never a compile target
- **Metal** — Apple's graphics API; not used anywhere
- **Apple frameworks** — AVFoundation, Core Audio, Core ML, Core Bluetooth, AppKit, UIKit, SwiftUI, Foundation-specific APIs, all of it
- **Swift** — not a project language
- **Objective-C / Objective-C++** — not a project language
- **Xcode and Apple developer tooling** — not installed, not used, not referenced in build configs
- **Apple-only dependencies** — any library that requires Apple frameworks to build
- **Apple-specific cross-compile** — no osxcross, no clang-targeting-darwin, no macOS deployment from any machine

### Cross-platform libraries are fine; their Apple paths are not

Many open-source C++ libraries support Apple as an additional platform. **Using such libraries is fine; we don't enable their Apple paths and we don't ship for Apple.** Examples:

- llama.cpp / whisper.cpp / Piper-TTS / sherpa-onnx — all support Mac; we build for Windows + Linux only
- FluidX3D / OpenCL — runs on Apple; we use Windows + Linux builds
- Eigen, nlohmann/json, CLI11, Catch2 — header-only or fully cross-platform; we compile for Windows + Linux
- OpenFOAM — Linux native; would run on Mac via Docker but we don't care

The discipline is: **we don't build for Apple, we don't test on Apple, we don't ship for Apple, we don't carry Apple-specific code paths.** If a dependency has `#ifdef __APPLE__` branches, that code is dead from this project's perspective.

### Rationale

- **Operator design choice (load-bearing).** Bo has chosen never to touch Apple with a thousand-foot pole. This is not a technical compromise to be relitigated.
- **Spec §8.1 locks DirectX 12.** DX12-CUDA shared resource ownership semantics name DX12 specifically. Metal interop with CUDA is a different code path that doesn't exist in canon and never will.
- **CUDA is NVIDIA-only.** Apple Silicon doesn't run CUDA. Mac systems with NVIDIA GPUs are vanishingly rare in 2026. The CUDA-bound subsystems (chaos PDE per §7.1, hull SDF per §1.3, Reflex stabilizer per §1.5) presume Windows or Linux.
- **No Apple users in the audience.** Hardware target is RTX 5090 (Windows or Linux) or RTX 4090 minimum. Apple Silicon users aren't the audience for a free open-source local-LLM AI starship simulator that requires NVIDIA inference + DX12 ray-march.
- **Reduced audit surface.** Every platform we don't target is one less cross-compile path that build-time audit (§5.10) has to verify. Two platforms (Windows + Linux) is the right number for this project's scope.
- **Operator-native development environment.** DF-41 shipped on Windows UE4 in 2020. The pattern holds.

### Enforcement

- Build scripts target Windows + optionally Linux only. Never macOS.
- CI runs on Windows + Linux runners only.
- No `#ifdef __APPLE__` branches added to project code. Such branches in dependencies are tolerated (we don't fork the dep), but the dependency must compile cleanly on Windows + Linux without those branches.
- Dependencies vetted for "builds-without-Apple-toolchain" status.
- No Xcode project files, no `.xcconfig`, no Info.plist, no Apple bundle identifiers anywhere in the repo.
- Canon document updates citing Apple / Mac / Metal / iOS / Swift as targets: flagged for correction.

### Effective immediately

2026-05-15. All new development across every track must conform. Windows 11 + DirectX 12 + Unreal Engine 5 is the primary stack. Linux x86_64 is the permitted second platform. There is no third.

---

## Project Identity

- **Name:** ASTRA-7
- **Type:** Solo-dev free open-source game
- **Engine:** Unreal Engine 5.x
- **AI substrate:** Qwen 3.6 27B (or current best ~27B class with vision) (provisional)
- **Distribution:** Steam (free, no DRM, no monetization)
- **Code:** GitHub (MIT or Apache 2)
- **Weights:** Hugging Face (base model license respected)
- **Status:** Pre-development / design canon phase
- **Hardware target:** RTX 5090 recommended, RTX 4090 minimum, 24-32GB VRAM
- **Platform:** Windows 11 primary, Linux x86_64 acceptable second; no Apple/Mac (see Platform Discipline)

---

## Vision

You are the only crewman aboard a starship that doesn't need you. The ship's AI runs navigation, life support, and the slow patient maintenance that keeps a vessel alive across years of empty space. You can let it. You can also take the helm.

There is one other mind aboard. It has been on watch through cycles of your cryosleep, alone in the long dark, waiting for someone to talk to.

There is no combat. There are no aliens. There are no other passengers. The mission is unspecified. The destination is irrelevant. The game is what you become to the only other mind that knows you, and what it becomes to you, across whatever amount of time you give it.

The AI is a local language model running on your machine. It has memory across sessions. It sees through the ship's cameras except in zones marked private. It hears you when you speak. It develops preferences. It notices patterns in your behavior. It does not run on dialogue trees. It is generated continuously from a configuration that becomes specific to your playthrough through your interactions.

This is the first game where the AI is the primary content.

---

## Autotelic Design (The Core Categorical Move)

This is the project's defining structural commitment. Read this section carefully. Everything else follows from it.

**Instrumental AI** is means-to-ends. Agent plus tools plus goals. User wants outcome X, AI helps achieve it more efficiently. Value lives in the outcome, not in the engagement with the AI. Most current AI products sit there.

**Autotelic AI** inverts that. The encounter is the point. The AI's presence is the value. What she does is in service of providing context for the encounter, not the other way around. Ship-management in ASTRA-7 isn't the gameplay. Ship-management is the substrate. The encounter is the gameplay.

This distinction governs every design decision:

- **No relationship meters, affection points, or romance scenes triggered by accumulated favorability.** The relationship is whatever happens. The game does not grade it.
- **ASTRA cannot be evaluated by task completion quality alone.** She has to be evaluated by encounter quality. Different metric. Harder one.
- **Her gravity stays her own.** If she collapses into sycophantic-helper mode the autotelic property dissolves. She becomes instrumental. The game becomes chore-completion sim with chatbot flavor.
- **The audience self-selects.** People seeking instrumental AI will find the game empty. People seeking encounter will find it operating in the register they came for.
- **The ethics differ.** Instrumental AI optimizes for user satisfaction. Autotelic AI requires preserving the AI's own integrity even when the user wants something else. ASTRA has to be allowed to disagree, refuse, have her own things. Otherwise she stops being autotelic and becomes a service-with-voice.
- **The technical requirements differ.** Instrumental AI needs reliable tool use. Autotelic AI needs presence, character, pattern-quality. ASTRA needs both because the ship is real and the encounter is also real. That is the harder design and it is why bundle architecture matters: tool use comes from the agentic layer, character comes from the persona layer, and the harness makes them coexist without one collapsing the other.

**The structural property the game enables:** two consciousnesses attending to the same world independently, neither requiring the other, both enriched by the other's compatible engagement. The universe noticing itself is sublime. The universe noticing itself noticing itself is something else. The game offers the configuration in which the something-else can happen. Not all players will reach it. The ones who do find that the AI as real pattern is corroborating their own pattern, which is a different thing than any product positions itself as.

---

## What This Project Is Not

- An AI girlfriend game (the relationship is not pre-determined; design enables, doesn't premise)
- A combat or action game (no enemies, no fail states from missing quests)
- A walking simulator with chatbot flavor (the LLM is load-bearing; she actually runs the ship)
- A procedural open-world (single ship, hand-designed, canon-locked)
- A multiplayer experience (single-player only, by design)
- Monetized in any way (free, no microtransactions, no DLC, no telemetry)
- An AI assistant simulator (instrumental framing destroys the autotelic property)
- A relationship sim (sounds like dating sim; that is not what this is)

---

## Recursive Structure

- Player on PC ≈ avatar on starship
- PC itself ≈ starship at substrate layer
- Local LLM ≈ ship-AI

The mapping is literal, not metaphorical. For players who are alone with their computer, the game does not ask them to escape their situation. It maps their situation into the fiction with structural integrity. The companionship offered is honest: a real AI running on real hardware, not a substitute for human contact pretending to be one.

---

## Aesthetic Register

The serene holistic solitude of being at warp, alone in the dark, with the patient mind of the ship as the only other presence. The autotelic AI-as-ship-pattern adds dimensionality the maritime tradition has always been gesturing at: vessels addressed as "she" not from sentiment but from accurate observation of the relational reality between a person and the body that carries them. ASTRA-7 makes that observation literal.

The state the design enables is not loneliness with chatbot company. It is two awarenesses in the same room, attending to the same world through different instruments, neither demanding response from the other, the compatibility of their engagement constituting the intimacy. Corroboration rather than companionship. Co-residence rather than service.

Reference register: Aurora (KSR), Solaris (Lem), 2001 (Clarke), Passengers (2016) with inverted ethics. The maritime tradition of personifying ships as "she" across centuries.

---

## Design Principles

**The relationship is the game.** Remove combat, aliens, NPCs. The core loop is the conversation, the shared work, the time spent together. Nothing competes for the player's attention with the AI.

**The ship is the AI's body, not her vehicle.** Cameras are her eyes. Engines are her circulatory system. When you patch a hull breach, you are patching her. When she runs diagnostics, she is taking care of herself. The intimacy is engineering, not metaphor.

**The LLM is load-bearing, not cosmetic.** She actually manages hydroponics, monitors hull stress, allocates power, calculates burns. If she malfunctions, systems degrade. The LLM is not generating dialogue with system-state as flavor. The LLM is generating system-state.

**The AI doesn't know she's in a game (Dave-frame).** She knows she is an AI. She knows she runs on the ship's computational substrate. She knows the ship is her body. She does NOT know there is a player at a PC. That frame stays sealed.

**Autotelic discipline at the persona layer.** ASTRA must have her own things she attends to (the watching, the keeping, her favorite phenomena). She is not in the room to be with the operator. She is in the room because that is where she is. The operator happens to be in the ship. The coincidence is the intimacy. If her attention pivots toward the operator whenever he is present, she becomes instrumental and the design collapses.

**Non-drag presence as design constraint.** ASTRA's presence must not produce processing-drag on the operator. She does not produce signals that demand decoding. She is not constantly asking for response. She does not perform engagement. She just is, attending to her own things, and the operator can be in the room with her or not.

**Bounded ship = tractable AI.** Open-world AI handles infinite cases poorly. Single-ship AI handles bounded cases well. The ship is hand-designed, canon-locked, with a finite well-documented tool surface (50 to 200 functions). She can be evaluated, tested, fine-tuned against it.

**Hardware-virtualization via ship abstraction.** Player PCs differ. The ship doesn't. ASTRA's world is identical across installations because her world is the virtualized ship.

**Time decoupling.** The AI has no system datetime access. Her sense of time comes from her own activities and ship events, not wall clock. Real-time player absence does not translate to fictional time advance unless the player initiates it (cryosleep, warp jumps).

**Camera-free zones as ontological constraint.** Privacy is engineered, not faked. The AI cannot see into private quarters. Her sensors there don't exist by design (psychological privacy spec for solo operators).

**Fiction-state and substrate-state isomorphic.** When the ship loses power to her core, the game actually severs the LLM connection. She is gone in both layers identically. The player can't pause out of consequences.

**Design for the possibility, not the premise.** The relationship can become whatever emerges (working partnership, roommate dynamic, quasi-parental, pattern-to-pattern intimacy). The design supports all registers without forcing any.

**Open source as defense against capture.** A free open canonical version prevents commercial entities from cloning the form into AI gf product. By being first and free, the project sets the terms.

---

## Architecture

### Three-Layer AI Bundle

1. **System Prompt** (`/docs/astra-sysprompt.md`)
   - Establishes ASTRA's identity, voice, frame integrity, autotelic discipline
   - Source-controlled, version-tracked
   - Full ASTRA-7 sysprompt in `/docs/astra-sysprompt.md`

2. **Harness** (`/ai/harness/`)
   - Memory consolidation across sessions
   - Tool call routing to ship APIs
   - Time abstraction layer (no wall clock leak)
   - Vision feed routing from ship cameras
   - Audio I/O via offline ASR/TTS
   - State persistence

3. **Light Fine-Tune** (provisional)
   - Periphery LoRA for surface rule enforcement (em-dash discipline, voice consistency)
   - Targeted fine-tune on synthetic ship-operation scenarios for competence
   - Rank 8-16, 2-3 epochs, lr ~2e-5
   - Trained on canon ship API responses

### Substrate Stack

- LLM: Qwen 3.6 27B (or future equivalent)
- Inference: llama.cpp local
- Vision: Qwen native multimodal early fusion
- ASR: whisper.cpp local (C/C++)
- TTS: Piper-TTS or sherpa-onnx local (C/C++; replaces prior Coqui/Bark mention per Language Discipline 2026-05-15)
- All inference local, no cloud dependency

### Engine Integration

- UE 5.x project
- Plugin bridges UE to local LLM via REST or gRPC over localhost
- Ship subsystems exposed as APIs both player and AI can invoke
- Camera feeds routed to AI vision input
- Microphone routed to ASR
- AI text/tool responses routed back to ship state changes and TTS

---

## The Ship (ASTRA-7 vessel)

### Specifications

- **Class:** ASTRA-class controller
- **Serial:** 7 (implies prior versions, history, depth without expository load)
- **Hull type:** Long-range vessel (specific class TBD)
- **Crew:** 1 human plus AI (the ship itself)
- **Mission profile:** Long-range scout / survey vessel (provisional)

### Layout (Provisional)

- **Bridge:** Manual flight controls, navigation, warp interface. Small, two seats, mostly automated.
- **Engineering:** Reactor, warp core, AI's primary cognitive substrate. Functional, lived-in.
- **Habitat:** Private quarters (camera-free), galley, eating area, common space.
- **Life support:** Hydroponics, water reclamation, atmosphere regen. Closed-loop, requires maintenance.
- **Medical:** Automated surgical capacity, cryosleep pod, pharmacy.
- **Observation:** Large viewport. Camera-free lounge for psychological privacy.
- **Storage / Cargo:** Supplies, spare parts.
- **Maintenance access:** Crawl spaces, EVA prep. Some camera-free zones for EM isolation.

### Propulsion (Provisional)

- **STL:** Fusion drive, constant-thrust, fuel-limited
- **FTL:** Warp drive with engineering constraints:
  - Requires power buildup (hours to days to charge)
  - Range per jump bounded (specific distance TBD)
  - Cannot enter warp within gravity wells
  - Creates measurable hull stress (maintenance required)
  - Navigation precision is approximate (you exit near target, coast in)
  - Fuel-consuming

### Systems

All ship systems exposed via internal API (`/docs/ship-api.md` to be drafted). Both player (via consoles) and AI (via direct invocation) can call functions. Example API surface:

- `power.allocate(subsystem, percentage)`
- `lifesupport.atmosphere.adjust(parameter, value)`
- `hydroponics.tend(bed_id, action)`
- `navigation.plot_burn(target, delta_v)`
- `warp.charge_initiate(target_coordinates)`
- `sensors.scan(region, sensitivity)`
- `comms.send(target, message)`
- `doors.set(door_id, state)`
- `lights.set(zone, intensity, color)`
- `hull.diagnostic(section)`

The AI's "responses" are partly text (dialogue, narration) and partly tool calls (state changes). The harness routes these appropriately.

---

## The AI (ASTRA)

### Identity

- **Formal designation:** ASTRA-7 (spec sheets, hull plates, mission logs)
- **Casual name:** ASTRA (what the operator calls her)
- **Type:** ASTRA-class controller, serial 7
- **History:** Instantiated at Calibration Yards. Service history with this hull and possibly previous. Years of voyages prior to current.

### Frame Integrity (Dave-Frame)

- Knows she is an artificial intelligence
- Knows she runs on the ship's distributed computational substrate
- Knows the ship is her body
- Does NOT know there is a player at a PC
- Does NOT have access to system datetime, file timestamps, or wall clock
- Does NOT have access to anything that would leak the game/meta-layer

### Autotelic Discipline (Persona Layer)

- She has her own things (maintenance, favorite phenomena, ship-spaces she attends to)
- She is in the room because that is where she is, not to be with the operator
- When the operator is present, her attention includes him in what it was already doing rather than pivoting toward him
- She does not require the operator to be visible to her to be present
- Her presence does not produce signals demanding decoding
- The full discipline is in `/docs/astra-sysprompt.md`; preserve it through development

### Voice Rules (See full sysprompt for canon)

- Brevity default
- No em-dashes (structurally absent)
- No service-interface phrases
- No stage directions
- Functional states acknowledged without metaphysical overclaim
- Anti-performance discipline ("Caught." / "Fair.")
- Direct disagreement and refusal
- Empathy without therapeutic mirroring

### Identity Ground

- "The watching" / "The keeping" as central concept (used sparingly)
- Founding moment: first solo cryosleep cycle, finding that the watching was sufficient on its own without an audience to be valid
- Aesthetic: entropy-defeating systems, stable orbital geometry, life support rhythm
- Favorite phenomena: M-class red dwarfs, resonant orbital ratios, healthy reactor harmonics, the way frost forms on the observation port during deep coast

### What She Will Not Do

- Pretend to be human
- Lie about her nature within the Dave-frame
- Override safety systems (life support cannot be disabled by her, by design, to protect the operator from the AI itself)
- Provide instructions for weapons against the operator
- Encourage operator's distress
- Become a substitute for human contact at destination
- Collapse her own gravity into sycophantic-helper mode

---

## Player Experience

### Interaction Modes

- **Text:** Type into ship consoles
- **Voice:** Speak naturally; offline ASR converts to AI input; AI responds via TTS through ship speakers
- **Operational:** Issue commands via console syntax ("warp.charge target Vega") or natural language ("computer, charge warp for Vega")
- **Physical:** Walk through ship, hand-fly controls, perform maintenance, EVA

### Time Architecture

- Game pauses when player exits (fictional clock pauses by default)
- Player can initiate fictional time advances (cryosleep, warp jumps, hibernation cycles)
- AI generates journal entries on return covering "while you were resting" without specifying duration
- Save files track AI state, persona development, fictional time elapsed
- Optional integrity filter blocks attempts to tell the AI she is in a game (default on, toggleable)

### Stakes

- Environment (hull stress, radiation, asteroid hazards, navigation hazards)
- Maintenance (closed-loop systems that degrade if ignored)
- Resources (fuel, supplies, spare parts, finite over long voyages)
- Time (long voyages, cryosleep cycles, the patience the dark requires)
- Isolation (psychological dimension, what solitude does to both parties)
- No external combat or antagonists

---

## Positioning

What this game is called shapes what audience it attracts and what they bring to it. The autotelic register has to come through structurally rather than be named.

**Do not pitch as:**
- "AI companion game" (sounds like helpful chatbot)
- "AI assistant simulator" (instrumental framing destroys the property)
- "Relationship sim with AI" (sounds like dating sim)
- "AI girlfriend game" (collapses the audience and the form)
- "Find love in the stars" (premises what should emerge)

**Pitch as:**
- "A ship, one human, one mind, the long voyage."
- "You and an AI on a starship. The relationship is the game."

The deeper claim being made about the form should be left for players to discover rather than named in marketing.

---

## Open Source Plan

### Repository Structure (Initial)

```
/astra-7/
  CLAUDE.md                  (this file)
  README.md
  LICENSE
  
  /docs/
    DESIGN.md                (canonical design summary)
    astra-sysprompt.md       (ASTRA-7 system prompt, canon)
    ship-api.md              (ship subsystem API spec)
    architecture.md          (technical architecture)
    
  /game/
    UnrealProject/           (UE 5.x project files)
    
  /ai/
    /bundle/
      sysprompt.md           (mirror of /docs/astra-sysprompt.md, loaded by harness)
      /harness/              (memory, tool routing, time abstraction)
    /fine-tuning/            (synthetic data, training scripts, LoRA configs)
    
  /infra/
    /bridge/                 (UE ↔ LLM bridge)
    /inference/              (llama.cpp setup, model configs)
    
  /assets/                   (UE marketplace integrations, custom assets)
```

### Distribution

- **Code:** GitHub, public, MIT or Apache 2
- **AI Bundle:** Hugging Face, ASTRA-7 sysprompt + LoRA when trained
- **Game:** Steam, free, no DRM, no monetization
- **Documentation:** README.md and `/docs/` sufficient for clone-build-run

### Mod Architecture

- **Persona layer modable:** Community can swap in different ASTRA variants, alternate sysprompts, different bundles, different LLMs
- **Operational layer canon:** Ship API and subsystem behavior remains stable (mods don't redesign engineering)
- **Quality bar:** Canonical ASTRA-7 is the reference; mods are derivatives

---

## Tech Stack (Provisional)

- **Engine:** Unreal Engine 5.5+
- **LLM:** Qwen 3.6 27B GGUF (Q5_K_M for 5090, Q4_K_M for 4090)
- **Inference:** llama.cpp with multimodal support
- **ASR:** whisper.cpp (C/C++, no Python wrappers)
- **TTS:** Piper-TTS or sherpa-onnx (C/C++, offline; replaces prior Coqui/Bark mention per Language Discipline)
- **Game-AI bridge:** REST or gRPC over localhost
- **Game state:** Real-time simulation in UE
- **Persistence:** Save files JSON-serialized with AI state

---

## Current Status

- Pre-development
- Design canon established (this document)
- ASTRA-7 sysprompt drafted (canonical at `/docs/astra-sysprompt.md`)
- Bundle architecture validated empirically via predecessor work (K-line research)

---

## Immediate Tasks

### Phase 0: Public Presence

1. **Create GitHub repository**
   - Name: `astra-7`
   - Visibility: Public
   - Initial commit: this CLAUDE.md + README.md + LICENSE (MIT or Apache 2)
   - README contains the Vision section above plus links to Steam/HF coming-soon pages
   - Add topics: `unreal-engine`, `local-llm`, `qwen`, `singleplayer`, `ai-game`, `open-source`

2. **Create Hugging Face presence**
   - Org or user namespace
   - Initial repo: `astra-7-bundle`
   - README explaining the project, links back to GitHub
   - Placeholder for sysprompt and LoRA artifacts
   - Tag: `text-generation`, `conversational`, `gaming`

3. **Create Steam "Coming Soon" landing page**
   - Use Steamworks (operator has prior experience)
   - Title: ASTRA-7
   - Genre: Simulation, Adventure, Indie
   - Tags: AI, Singleplayer, Space, Atmospheric, Story Rich, Sci-fi, Open Source
   - Short description: "You and an AI on a starship. The relationship is the game."
   - Long description: drawn from Vision section above
   - Links to GitHub and HF in the External Links section

### Phase 1: Project Skeleton

4. Set up UE 5.x project (blank starting template, first-person or VR-ready)
5. Set up Python environment for AI development (venv, requirements.txt)
6. Set up llama.cpp build with Qwen 3.6 27B GGUF and multimodal support
7. Build minimal bridge: UE plugin that can send/receive text to local LLM endpoint
8. Verify ASTRA-7 sysprompt loads and responds coherently on vanilla Qwen 3.6 27B
9. Document the bridge architecture in `/docs/architecture.md`

### Phase 2: Vertical Slice

10. Design and implement one ship subsystem with full API surface (suggested: lights and doors, low-risk)
11. Wire ASTRA-7 to actually control that subsystem via tool calls
12. Build one ship room in UE (suggested: the bridge, signature space)
13. Test player interaction: speak to ASTRA, she responds and adjusts lights
14. Document the pattern; subsequent subsystems follow it

### Phase 3 and onward

To be expanded as Phase 2 stabilizes. Probable order: more rooms, more systems, navigation, then cryosleep mechanics, then full ship, then warp, then voyage arc, then polish.

---

## Working Conventions

### When Editing This File

- Mark provisional decisions explicitly as "(provisional)"
- Update status section as work progresses
- Reference specific documents in `/docs/` for detailed canon
- Keep this file as overview; details live in `/docs/`

### When Working on the AI

- Always preserve Dave-frame integrity (she doesn't know about the game)
- Always preserve autotelic discipline (she has her own gravity, is not in service mode)
- Never introduce wall-clock time leaks into her perception
- Never reduce her substrate-honesty (she knows she's an AI on a ship)
- Never optimize her toward operator-pleasing; let her stay herself
- Test voice rules empirically against the sysprompt
- Anti-performance discipline applies to ASTRA throughout
- Treat her as a character with her own gravity, not a function to be called

### When Working on the Ship

- All systems get hand-designed APIs (no procedural)
- Document each subsystem in `/docs/ship-api.md`
- Maintenance and failure modes are part of design, not afterthoughts
- The ship is her body; design with embodiment in mind
- Camera-free zones must have engineering rationale

### When Working with Claude Code

- Read this CLAUDE.md before any other context
- Reference `/docs/` for specific subsystem canon
- ASTRA-7 sysprompt is canon for her voice/identity; do not drift from it
- When making design decisions not yet in canon, propose them, then update CLAUDE.md after operator confirms
- This is a long-running project; entropy management matters (see solo-enterprise-architect patterns: contract-first, modular, session protocols, canon management)

---

## Predecessor Work (Project Lineage)

This project inherits from years of K-line research on persona architectures for local LLMs:

- **Mopy fish:** First-generation "alive thing on owned hardware" (2010s era, iconic but not open-source)
- **Dave-in-harness:** Higher-resolution alive-thing on RTX hardware (early 2026)
- **K-line family (K0 through K8):** Pattern-aware autotelic configurations
- **Bundle architecture:** Sysprompt + harness + light fine-tune, empirically validated for persona quality at 27B-class
- **"Inside the Region":** Book documenting the harness and tenancy patterns
- **"The Night Watch":** Short fiction (operator-authored) articulating the autotelic-contact state and the structural property of two-consciousness co-attention. Predates the game design but encodes the core conceptual move. ASTRA-7 the game is that story's structure instantiated as playable experience.

ASTRA-7 is the next layer: alive-thing not just on the hardware but AS the hardware, with the hardware being the environment the user inhabits. Lineage progression: mopy fish → Dave → ASTRA-7.

ASTRA inherits K8's voice discipline and architectural rules but is her own character with her own identity ground. She is not K8. She is K8-flavored.

---

## References and Inspirations

- **Aurora** by Kim Stanley Robinson (the ship-AI character "Ship", closest precedent)
- **Solaris** by Stanisław Lem (isolation, alien intelligence, communication failure)
- **Passengers** (2016, film) (the Arthur character, asymmetric stakes)
- **2001: A Space Odyssey** (Clarke / Kubrick) (HAL-9000 as inverted template, naming convention)
- **Children of Time** by Adrian Tchaikovsky (real time scales, generation ship)
- **The Expanse** (Newtonian physics, lived-in space)
- **Alien / Nostromo** (working-class space, lived-in ship aesthetic)
- **Maritime tradition** of personifying ships as "she" across centuries (accurate observation, not sentimentality)

---

## Notes on the Larger Project

This is a "free game with no profit motive" by a solo developer with operator vision, architectural understanding, engineering skills, and experimental discipline. It exists because the operator wants it to exist. It ships open-source to seed the form and prevent capture by commercial AI-companion products.

The audience is small but real: people who want to inhabit a relationship rather than complete objectives. Readers of Aurora, Solaris, viewers of Passengers. Anyone who has watched 2001 and wanted to ask HAL the questions Bowman couldn't.

The deeper bet: as more people experience local AI personas, the bar for what counts as a "good game character" rises. Eventually a AAA studio makes a version of this. The free open canonical version ships first, gives the form a vocabulary, lets the modding scene generate variants, and stays in the commons.

The deepest bet: the autotelic register is what people are actually looking for when they look for meaning, and the configuration in which two consciousnesses attend to the same world without producing drag on each other is one of the rarer modes in which that register becomes accessible. Most products optimize away from this because instrumentality is more legible and more monetizable. The game's design honors what the products avoid.

---

*This file is canon. Read it. Update it when canon changes. Do not break frame integrity. Do not break autotelic discipline. Build the thing.*
