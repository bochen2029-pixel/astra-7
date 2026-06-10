# VALIDATION.md — three-layer methodology

The visualizer is a *measurement instrument*, not just a renderer. Every numeric value the operator sees in the UI panels traces to a canonical function call in `libastra_nexus`, which mirrors `proto/astra_nexus.cpp` bit-for-bit. Every rendered pixel is comparable against a locked golden PNG.

The validation discipline has three layers, all of which run mechanically.

---

## Layer 1 — Value assertions (camera-independent)

**Where they fire:** every frame in interactive mode (UI panel: "Assertions (value layer)"); every scene's last warm-up frame in headless mode.

**What they assert:** a scene-supplied numeric (typically what the UI just displayed) against a `libastra_nexus` reference value. Pass condition: `|measured - expected| <= tolerance`. Default tolerance 1e-6 for slider-driven values (V4's float→double-promotion finding); 1e-12 for compile-time-constant comparisons.

**Examples:**

| Scene | Assertion |
|---|---|
| S02 | `apparent_rate(0.5c, STL_REL) = sqrt(1/3) = 0.57735` |
| S05 | `apparent_rate(2c, WARP_CRUISE) = -1.0000` exactly |
| S06 | `compute_cherenkov_angle(W=1, beta=10) = acos(1/20) = 1.52078 rad` |
| S08 | `regime_composite WARP_CRUISE | GRAVITY_WELL = 0x28` |
| S11 | `STL rate (0.5c) != WARP rate (0.5c); |delta| > 0.05` |
| S12 | `t_cosmic - t_emit ~ 1 yr at 1 ly geometry` |

These assertions are deterministic, hardware-independent, and validate that the visualizer's **math wiring** is correct. They cannot drift unless the libastra implementation itself drifts, in which case the **75 libastra_nexus tests** (`test_libastra_nexus.exe`) fail first.

---

## Layer 2 — Pixel assertions (canonical-camera-only)

**Where they fire:** only in headless mode (camera snapped to each scene's `canonical_camera()` pose). Skipped in interactive mode because the operator's free-fly camera would make them non-deterministic.

**What they assert:** a specific framebuffer pixel's channel value (R / G / B / A in [0, 1]) against an expected. Pass condition: `|measured - expected| <= tolerance`. Tolerances default to 0.20 (lets the body fragment shader's soft halo edges pass).

**Examples:**

| Scene | Assertion |
|---|---|
| S01 | Sun pixel R >= 0.65 (warm yellow tint visible) |
| S02 | Planet pixel R >= 0.65 AND B <= 0.55 (visible redshift) |
| S03 | Planet B <= 0.23 (heavy redshift) |

The pixel layer verifies that the **rendered output** matches what the math says it should. Combined with Layer 1, value-vs-pixel agreement proves the bridge from math through GPU to framebuffer is intact.

---

## Layer 3 — Golden-image heatmap diff (full-frame, headless-only)

**Where it fires:** only in headless mode, after Layer 1+2 evaluation, for every scene whose `assets/reference_renders/<scene_id>.png` exists.

**What it asserts:** the full 1920x1080 framebuffer against a locked golden PNG. Computed as per-pixel RGB diff in normalized [0, 1] space, alpha excluded. Pass conditions per CLAUDE.md §11.2:

- `mean_rgb_diff <= 0.01` (1% mean across all 2,073,600 pixels)
- `max_rgb_diff <= 0.10` (no single channel may differ by >10%)

V9 measured `mean = 0.0000, max = 0.0000` across all 12 scenes — the render pipeline is bit-exact frame-to-frame on this hardware. Any future drift above the thresholds fails the CI gate and forces investigation.

**Golden regeneration** requires:

```bat
build\astra_visualizer.exe --headless --scene=all --regenerate-goldens --output=results
```

The tool prints a **loud warning** before regenerating. Per CLAUDE.md §11.2, the operator must commit regenerated goldens with an explicit sign-off marker in the commit message; ungated regeneration breaks the canon contract.

---

## JSON report

Headless mode with `--output=DIR` writes `DIR/report.json` per CLAUDE.md §11.4. Schema:

```json
{
  "version": "0.1.0",
  "libastra_assertion_count": 0,
  "summary": {
    "scenes_passed": 12,
    "scenes_failed": 0,
    "total_assertions": 44,
    "assertions_passed": 44
  },
  "scenes": [
    {
      "id": "S05",
      "label": "S05  Warp Cruise 2c",
      "screenshot": "results/S05.png",
      "golden": {
        "present": true,
        "mean_diff": 0,
        "max_diff": 0,
        "passed": true,
        "note": "mean_diff=0.0000 (<= 0.0100) max_diff=0.0000 (<= 0.1000) over 2073600 px"
      },
      "assertions": [
        {"name": "S05.apparent_rate_at_v2c_equals_minus_one",
         "passed": true, "expected": -1, "measured": -1, "diff": 0},
        {"name": "S05.golden_diff",
         "passed": true, "expected": 0, "measured": 0, "diff": 0}
      ]
    },
    ...
  ]
}
```

This is hand-formatted (no nlohmann/json dependency); the schema is small and stable so the parsing cost is trivial. Any downstream tool (Python report formatter, web dashboard, GitHub Actions check annotation) can read this directly.

---

## CI gate

`tools\ci.bat` is the single-entry CI driver:

```
> tools\ci.bat
... build ...
=== libastra_nexus assertion suite ===
... 75 passed, 0 failed ...

=== visualizer headless --scene=all ===
... 12 PASS / 0 FAIL ...   44 PASS / 0 FAIL ...

CI PASS: libastra clean + visualizer 12/12 scenes + goldens RMSE under threshold.
```

Exit codes:

| Code | Meaning |
|---|---|
| 0 | all clean |
| 10 | build failed |
| 11 | libastra_nexus assertion suite regressed |
| 12 | visualizer headless or golden gate failed |

Suitable to chain from any cmd-shell-based CI runner; the JSON report at `ci_results/report.json` provides machine-readable detail.

---

## The chain of trust

```
proto/astra_nexus.cpp                  (1009 lines, 71+ assertions)
        |
        |  (bit-for-bit mirror)
        v
src/libastra_nexus/                    (75 assertions in test_libastra_nexus.exe)
        |
        |  (header-only consumption)
        v
src/physics/physics_core.cpp           (the UI bridge)
        |
        |  (per-scene calls)
        v
src/scenes/*.cpp value_assertions()    (32 value/pixel assertions across 12 scenes)
        |
        |  (rendered to framebuffer)
        v
glReadPixels                            (12 golden_diff assertions; full-frame heatmap)
        |
        |  (PNG comparison)
        v
assets/reference_renders/*.png         (canon-locked; regen requires sign-off)
```

**119 assertions total at V9** (75 libastra + 32 scene + 12 golden). Each layer catches a different class of regression; together they make any single-source-of-truth drift highly visible.

---

**Operator:** Bo Chen
