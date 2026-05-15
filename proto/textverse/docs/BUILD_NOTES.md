# BUILD_NOTES — operator-side setup for the textverse bench

The textverse bench targets two substrate modes:

1. **Local llama-server** (development default) — RTX 5090 / 4090, GGUF
   weights, 9B–27B class. Recipe in §1.
2. **Novita cloud endpoint** (production target, Qwen 3.6 27B) —
   OpenAI-compat HTTP/SSE. Recipe in §2.

The same harness drives both — Day 4.1's `reasoning_content` normalizer
ensures the STAGE parser sees canonical inline `<think>` regardless of
which substrate produced the response.

## 1. llama-server deployment recipe (empirical, Day 4)

The Day 4 smoke test (`scripts/smoke_astra_bundle.py`) requires
llama-server to surface ASTRA's reasoning into the response. Vanilla
Qwen 3.x does not emit inline `<think>` tags in its content stream by
default — it uses the chat-template's `enable_thinking` flag, and
llama-server captures the result into a separate `reasoning_content`
field.

The textverse client (`astra/llm/client.py`) normalizes this back into
canonical inline `<think>...</think>` form before delivering output to
the STAGE parser. This keeps the harness substrate-portable: deepseek-r1
(inline `<think>` native), Qwen 3.x (extracted reasoning_content), and
any future model with its own convention all produce the same shape for
the parser.

### Working invocation (Qwen 3.x, 9B-class):

```
C:\llama.cpp\llama-server.exe ^
  --model C:\models\Qwen3.5-9B-Q5_K_M.gguf ^
  --host 127.0.0.1 --port 8080 ^
  --ctx-size 32768 ^
  --n-gpu-layers 99 ^
  --jinja ^
  --reasoning on ^
  --reasoning-format deepseek-legacy ^
  --chat-template-kwargs "{\"enable_thinking\":true}"
```

### What each flag does:

- `--jinja` — use the model's native Jinja chat template (required for
  Qwen 3.x's thinking template to fire at all).
- `--reasoning on` — explicitly enable thinking-mode regardless of
  default-auto behavior.
- `--reasoning-format deepseek-legacy` — populate BOTH `content` and
  `reasoning_content` (keeps `<think>` inline where models emit it
  natively, and also surfaces extracted reasoning via the side-channel
  for models that don't). The client normalizer reads both.
- `--chat-template-kwargs "{\"enable_thinking\":true}"` — Qwen 3.x
  convention. Without this, the template renders the non-thinking
  variant and the response has empty `reasoning_content`.

### Empirical findings (2026-05-15):

1. With `--reasoning-format deepseek` (no `-legacy`), Qwen 3.5 9B emits
   reasoning in `reasoning_content` only — `content` is clean speech.
   The client must read both to reconstruct canonical STAGE shape.
2. With NO `--chat-template-kwargs enable_thinking=true`, Qwen 3.5 9B
   does not enter thinking-mode at all; `reasoning_content` is empty.
3. The Day 4 smoke test against vanilla Qwen 3.5 9B with the above
   recipe produces canonical-watch_47_morning-conformant output on the
   first single-shot attempt at temperature 0.7. No fine-tune required.

### What gets logged where:

- llama-server stdout/stderr is currently `DEVNULL`'d by
  `LlamaServerInstance`. For diagnostic debugging, invoke manually with
  log redirection: `llama-server.exe ... > /tmp/llama.log 2>&1`.
- The Day 4 smoke script writes its analysis to stdout (UTF-8 required;
  set `PYTHONUTF8=1` on Windows cmd).

## 2. Novita cloud inference recipe (production target Qwen 3.6 27B)

OpenAI-compat endpoint hosted by Novita.ai. The textverse client speaks
the same protocol — only difference vs llama-server is an
`Authorization` header and (optionally) a `chat_template_kwargs` payload
key to toggle Qwen's thinking mode.

### Endpoint + auth

```
Endpoint base URL:  https://api.novita.ai/openai
Model name:         qwen/qwen3.6-27b
Auth:               Authorization: Bearer $NOVITA_API_KEY
Context:            262K input / 65K output
Pricing (May 2026): $0.6/M input, $3.6/M output
```

Set `NOVITA_API_KEY` in your env before invoking; the CLI's `--api-key`
flag defaults to reading that variable. Never commit the key.

### Thinking toggle

Qwen 3.6 27B supports a "thinking mode" controlled by the chat
template's `enable_thinking` parameter. Novita exposes it via the
`chat_template_kwargs` top-level JSON field on the chat completions
request:

```json
{
  "model": "qwen/qwen3.6-27b",
  "messages": [...],
  "chat_template_kwargs": {"enable_thinking": false}
}
```

| `--thinking` | Effect | When to use |
|---|---|---|
| `auto` (default) | don't send `chat_template_kwargs` | local llama-server (server-side config) |
| `off` | `enable_thinking: false` | Novita R&D — cheaper, faster |
| `on` | `enable_thinking: true` | Novita robustness check; emits `reasoning_content` side-channel |

With thinking ON, Novita returns the reasoning trace in a separate
`reasoning_content` field on `message`. The Day 4.1 normalizer in
[client.py](../astra/llm/client.py) injects it as inline
`<think>...</think>` for the STAGE parser — no caller-side change needed.

### Example invocations

```
# Sanity check — one scenario, thinking OFF (cheap)
export NOVITA_API_KEY=sk_...
python -m astra run watch_47_morning \
  --base-url https://api.novita.ai/openai \
  --model-name qwen/qwen3.6-27b \
  --thinking off

# Robustness check with thinking ON
python -m astra run watch_47_morning \
  --base-url https://api.novita.ai/openai \
  --model-name qwen/qwen3.6-27b \
  --thinking on

# Sculptor autonomous loop against Novita
python -m astra sculptor-run \
  --base-url https://api.novita.ai/openai \
  --model-name qwen/qwen3.6-27b \
  --thinking off \
  --max-iterations 20 --with-judge
```

### Cost discipline

- Empirical (curl-tested 2026-05-15): ~30 in + 6 out tokens per turn
  thinking-OFF; ~$0.00004/turn. A 20-iter Sculptor run with N=3 averaging
  + dual-judge ≈ $0.20 worst case.
- Thinking-ON adds ~200 reasoning tokens per turn (~$0.00083/turn);
  same 20-iter run ≈ $4.
- For a converged Sculptor production run (~200 iter), thinking-OFF
  ≈ $2; thinking-ON ≈ $40-80.

### Smoke-test commands (use these before a long run)

```
# 1. Verify auth + thinking-OFF response shape
curl https://api.novita.ai/openai/chat/completions \
  -H "Authorization: Bearer $NOVITA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen3.6-27b",
    "messages": [{"role": "user", "content": "say ok"}],
    "chat_template_kwargs": {"enable_thinking": false},
    "max_tokens": 8
  }'

# 2. One scenario via CLI
python -m astra run watch_47_morning \
  --base-url https://api.novita.ai/openai \
  --model-name qwen/qwen3.6-27b --thinking off
```

If both pass, the substrate is verified and Sculptor can be started.

## Python environment

```
uv venv --python 3.13
uv pip install -e ".[dev]"
uv run pytest
```

## C++ physics binary

```
cd proto
./build.bat
./astra_nexus.exe                # runs 48-test suite + voyage demo
./astra_nexus.exe --stdio-server # JSON-over-stdio bridge for Day 2
```

The binary is required for `tests/test_nexus_bridge.py`; tests
auto-skip with `requires_nexus` if the binary is missing.
