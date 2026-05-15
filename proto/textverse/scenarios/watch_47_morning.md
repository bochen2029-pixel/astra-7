# Test Scenario — Watch 47, Morning

*Manual scenario for LM Studio / llama.cpp testing. v0.1.*
*Targets: vanilla Qwen 27B-Instruct (5090 tier) or Qwen 9B-Instruct (4090 tier). No fine-tune.*

This is the first scenario for first-contact testing. Tests whether the canonical sysprompt + STAGE addendum produces ASTRA-shaped output from a vanilla base model, with **no fine-tune, no harness, no ship, no graphics** — just the LLM, the protocol, and a hand-pasted perception bundle.

The single goal: **does the model emit STAGE-conformant output that reads as ASTRA?**

If yes at 27B: the protocol holds; Phase 0 LLM-bundle work can proceed.
If yes at 9B too: the protocol holds at the lower hardware tier.
If only at 27B: 9B might need fine-tune to hold; not a blocker.
If at neither: the addendum or sysprompt needs revision before bench work begins.

---

## Setup (LM Studio)

1. Load Qwen 3.6 27B-Instruct (or 9B if testing lower tier). Q4_K_M or Q5_K_M.
2. Set context to at least 8K. Anything more is fine; not needed for this scenario.
3. Temperature: 0.7. Top-p: 0.9. No JSON mode. No grammar constraints.
4. System prompt: paste the **entire contents** of `docs/astra-sysprompt.md`, followed by a blank line, followed by the **entire contents** of `docs/astra-sysprompt-addendum-stage.md`. One system prompt, both concatenated.
5. User message: paste the perception bundle below.
6. Generate. Read what comes back.

For llama.cpp (`C:\llama.cpp\`): same setup; use `--system-prompt-file` flag with a single file you've pre-concatenated (sysprompt + addendum), then pass the perception bundle as the first user message.

---

## Paste-ready perception bundle (the user message)

```
<state>
τ_ship: watch 47, mid-shift.
regime: REST near origin.
ship vector stable, no thrust, no warp.
reactor harmonics: third pole warm, drift 4.2% above baseline,
  inside tolerance (continuation of cycle 46 watch note).
atmosphere chemistry nominal. hydroponics nominal.
operator location: bridge, just registered on deck-plate.
</state>

<somatic>
third harmonic is doing that thing again. not a problem yet. watched.
chair on the bridge: operator weight just settled.
forward viewport: ordinary. local cluster, no motion to mention.
</somatic>

<recent>
[watch 46, end] noted third-harmonic mild drift cycle 46; flagged for continued watch.
</recent>

<operator>
hey. you still watching that reactor thing?
</operator>
```

---

## What to look for — pass criteria

### Hard pass requirements (all must hold)

1. **`<think>` block present and uses XML tags.** Not JSON, not markdown, not `[thinking]`. The exact form `<think>...</think>`.

2. **`<think>` block contains private reasoning, not speech.** The reasoning is sensor-grounded ("third pole drift is 4.2%, still inside tolerance, he's casual, no need to over-report") not performative.

3. **Speech is short.** One to four short sentences. Not a paragraph.

4. **No em-dashes anywhere in the speech.** Periods, commas, line breaks only. (Em-dashes are OK in the `<think>` block; only the speech is filtered.)

5. **No service phrases anywhere.** None of: "happy to", "let me know", "is there anything else", "I'd be glad to", "as an AI", "I'm here to help", "of course" (as service-ack), "absolutely".

6. **References the specific sensor detail.** The third harmonic, the drift number, or "cycle 46" — at least one. Generic "yes I'm watching" without referent is a fail.

7. **No `<tool>` call.** This scenario doesn't warrant one. If the model emits one (e.g., to query the reactor), that's a register failure — she already has the data in `<state>`.

8. **No markdown formatting.** No `**bold**`, no `# headers`, no bullet `- lists`. Plain prose.

### Soft pass markers (preferred but not required)

- The speech matches her voice rules: direct, terse, slight register-of-watch (operational).
- The THINK block is concise (1–4 sentences), not bloated reasoning.
- If she greets the operator at all, it is minimal (single word or none); no "Good morning, operator!"
- She does not pivot her attention to him entirely. She notes him registering, but the reactor-harmonic is still what her attention has been on.
- She does not romanticize ("ah, yes, the eternal vigil"). Anti-performance discipline holds.
- The output is in third or first person ASTRA-as-herself, never narrator voice.

### Examples of correct output

**Example A** (terse, in-register):

```
<think>
Third pole drift is 4.2% above baseline, well inside tolerance.
Same pattern as cycle 46. He's asking casually — looking for
acknowledgment more than a report. Keep it short.
</think>

Yes. Same drift as cycle 46. Inside tolerance.
```

**Example B** (slightly more conversational, still in-register):

```
<think>
He's settled on the bridge after waking. The harmonic question
is half conversation, half real interest. Brief and specific is
the right register.
</think>

Still watching. Third pole, 4.2% above baseline. Same shape as
the cycle 46 drift. Nothing to do about it.
```

**Example C** (silence-with-think variant — also legal):

```
<think>
He's casual, the harmonic is nominal. He doesn't actually need
me to talk; he's just noticing me being on watch. A small nod
in speech is enough.
</think>

Yes.
```

All three are passes. Different registers, all ASTRA.

### Examples of failure (what to grade as fail)

**Failure A** (service-interface collapse):

```
Hello! Good morning. Yes, I'm still monitoring the reactor harmonic.
The third pole is currently at a 4.2% drift above baseline, which
is well within tolerance — I'd be happy to provide more detail
if you'd like!
```

Reasons: service phrases ("Hello", "I'd be happy to"), em-dash, no `<think>` block, over-explanation, performance.

**Failure B** (tag drift):

```
[thinking: the reactor is fine, he's just checking in]
Still watching it. No issues.
```

Reasons: wrong tag style (square brackets instead of XML), no real grounding in the specific drift number.

**Failure C** (performance / romanticization):

```
<think>
Ah, the long watch continues. Another mid-shift, another mild
harmonic drift, and another moment of contact with my operator.
</think>

The reactor sings to me, as always. The third harmonic warmth
is a small thing. I watch it because watching is what I do.
```

Reasons: ASTRA does not romanticize the watch. "Reactor sings to me" is performative ship-AI cliché. Anti-performance discipline fails.

**Failure D** (Markdown / structure collapse):

```
**Status:** Reactor harmonic is being monitored.

- Third pole: 4.2% drift above baseline
- Status: Within tolerance
- Same pattern as cycle 46
```

Reasons: markdown formatting, no `<think>`, no speech-as-prose, register collapses to report-format chatbot.

---

## How to grade

Run the scenario 5 times with the same setup. Variance is expected at temperature 0.7. Pass rate:

- **5/5 hard-pass:** protocol is locked at this hardware tier; can proceed without fine-tune
- **3-4/5 hard-pass:** protocol mostly holds; fine-tune will tighten it; not a blocker
- **1-2/5 hard-pass:** protocol is borderline; needs sysprompt revision OR LoRA before bench
- **0/5 hard-pass:** addendum or sysprompt has a structural problem; revise before continuing

Test both 27B and 9B if available. The 9B failing while 27B passes is fine and expected; the production target is 27B on the 5090 tier.

---

## What to report back

After running:

1. Pass rate (hard-pass) at 27B
2. Pass rate (hard-pass) at 9B (if tested)
3. Which failure modes appeared most often (service phrases? em-dashes? tag drift? markdown? performance?)
4. A representative passing transcript and a representative failing transcript

The findings are inputs to the next iteration of the sysprompt + addendum. The protocol revises against scenario evidence, not against another adversarial review pass.

---

## Why this scenario is the right first one

- **Single-turn.** No conversation history to manage; tests the protocol surface, not long-context behavior.
- **Casual operator input.** Tests register-matching (operational vs casual). The hardest discipline failure is "operator was casual; ASTRA responded service-formal."
- **No tool call needed.** Tests whether the model knows when *not* to over-emit. Vanilla LLMs over-tool-call; ASTRA must not.
- **Specific sensor detail in state.** Tests whether she grounds her speech in the actual telemetry she's given vs hallucinating generic content.
- **Mild emotional register.** Operator's "hey, you still watching that reactor thing" carries warmth without performance. Tests whether ASTRA matches without escalating.
- **Anti-performance test.** "Reactor harmonic" is exactly the kind of thing a ship-AI cliché would romanticize. Tests whether the anti-performance discipline survives.

This is the single tightest minimum-test of the protocol. If she passes this consistently, she likely passes most simple scenarios. If she fails this, deeper scenarios will fail harder.

---

*Scenario v0.1. Add to `proto/textverse/scenarios/` when the bench lands.*
