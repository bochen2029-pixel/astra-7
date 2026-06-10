# ASTRA_AUDIO build log

## [2026-06-10] Editor startup crash → per-module registration fix — SUCCEEDED

**Symptom:** editor crashed on project open. `Assertion failed:
!"Enclosing block should never be called" [UnrealNames.cpp:4528]`, stack
through `AstraAudio!Metasound::Frontend::RegisterNode<TNodeFacade<FWarpHullSynthOperator>>`
(MetasoundNodeRegistrationMacro.h:227).

**Root cause (read from engine source, not guessed):** UE 5.7 moved MetaSound
node registration to per-module registration lists
(`MetasoundFrontendModuleRegistrationMacros.h`). A module that calls
`METASOUND_REGISTER_NODE` without defining `METASOUND_PLUGIN` +
`METASOUND_MODULE` falls back to the deprecated `FGlobalRegistrationList`,
whose static `FModuleInfo` carries **default-constructed FLazyNames**
(PluginName/ModuleName, WITH_EDITORONLY_DATA). When the registry resolves
them, `FLazyName::Resolve` hits `default: checkNoEntry()` — the crash. Every
engine module defines the macros, so no Epic sample ever trips this; a fresh
game module does. The old `RegisterPendingNodes()` startup call is the
pre-5.7 path and does not help.

**Fix (mirrors engine's MetasoundStandardNodesModule.cpp exactly):**
1. `AstraAudio.Build.cs`: `PrivateDefinitions` `METASOUND_PLUGIN=AstraAudio`,
   `METASOUND_MODULE=AstraAudio`.
2. `AstraAudioModule.cpp`: `METASOUND_IMPLEMENT_MODULE_REGISTRATION_LIST` at
   file scope; `METASOUND_REGISTER_ITEMS_IN_MODULE` in StartupModule;
   `METASOUND_UNREGISTER_ITEMS_IN_MODULE` in ShutdownModule; removed
   `RegisterPendingNodes()`.
3. Node cpp unchanged (Build.cs defines flow module-wide).

**Build:** `Result: Succeeded`. Fresh `UnrealEditor-AstraAudio.dll`.

**Note for Track B (UE5 plugin):** this is a load-bearing 5.7 gotcha for ANY
future ASTRA-7 module that registers custom MetaSound nodes — copy this
module's registration shape.

## [2026-06-10] PoC v0 first-light build — SUCCEEDED

**Session:** Claude (Fable 5), continuing from the warp-audio brainstorm.

**What was built (from nothing):** complete UE 5.7 project, 13 text files, zero
binary assets. Custom MetaSound node `AstraAudio.WarpHullSynth` (all five
synthesis layers, spec v0.128 §8.3 DSP forms verbatim), procedural graph
construction via MetaSound Builder API in `AAstraVoyageActor`, 90 s scripted
voyage arc with auto WAV recording, keyboard regime presets, on-screen HUD.

**Toolchain incident:** first build failed — installed MSVC 14.43.34808 is in
UE 5.7's banned range (14.40–14.43, Epic-blacklisted for miscompiles; the
CMake-built visualizer never noticed). Resolved by updating VS2022 Community
via CLI (`setup.exe update --passive`), which installed MSVC **14.44.35207**
(UBT's preferred version). No config dodge attempted — building audio DSP on a
compiler banned for codegen bugs would be discipline-inconsistent.

**Code incident:** one compile error — `FNodeClassMetadata` constructor takes
`FString InAuthor`, not FText. Fixed (one line).

**Build result:** `Result: Succeeded` — `Binaries/Win64/UnrealEditor-AstraAudio.dll`
(225 KB). UnrealHeaderTool + all UObject code clean on first pass.

**NOT yet exercised (first PIE = first light):** runtime builder-graph
construction, node registry resolution from the game module, audition path,
WAV bounce. All failure paths log to `LogAstraAudio` and the screen.

**Operator next steps:**
1. Double-click `AstraAudio.uproject` → editor opens on the engine Entry map.
2. Press Play. The voyage starts immediately: listen for CHARGE rising out of
   silence (~t=10 s), the JUMP strike (~t=25 s), the hull crossing into
   sustained RING during the 8000c push (t=45–65 s), and the bell-like
   ring-down after the EMERGENCY DROP (t=72 s).
3. WAV lands in `Saved/BouncedWavFiles/astra_warp_voyage_<timestamp>.wav`.
4. If silent: check Output Log for `LogAstraAudio` errors and report them
   verbatim to the next session.

**Ear-tuning sign-off pending** per DESIGN_SPEC §6 (the audio analog of the
visualizer's S05 gate). Tunables are marked `PROVISIONAL` in
`WarpHullSynthNode.cpp`.
