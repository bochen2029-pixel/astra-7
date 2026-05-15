# BUILD_NOTES — operator-side setup for the textverse bench

## llama-server deployment recipe (empirical, Day 4)

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
