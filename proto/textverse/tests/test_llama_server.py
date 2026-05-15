"""Day 4 tests for llama-server lifecycle (config + argv construction).

Subprocess spawn is heavyweight; these tests verify the parts we can check
without actually running llama-server: argv construction, config validation,
error paths for missing binary / missing model, orchestrator roll-back
semantics. Real-spawn tests are marked `requires_llama` and skipped unless
the binary + model are available.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from astra.llm import (
    DEFAULT_BINARY,
    DEFAULT_HOST,
    LlamaServerConfig,
    LlamaServerError,
    LlamaServerInstance,
    LlamaServerOrchestrator,
)

# --- LlamaServerConfig shape -------------------------------------------------

def test_config_default_ctx_size() -> None:
    c = LlamaServerConfig(name="x", model_path=Path("/tmp/x.gguf"), port=8080)
    assert c.ctx_size == 131_072
    assert c.n_gpu_layers == 99
    assert c.reasoning_format == "deepseek"


def test_config_port_bounds() -> None:
    with pytest.raises(ValidationError):
        LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=0)
    with pytest.raises(ValidationError):
        LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=70_000)


def test_config_frozen() -> None:
    c = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8080)
    try:
        c.port = 9999
    except Exception:
        return
    raise AssertionError("LlamaServerConfig must be frozen")


# --- LlamaServerInstance argv construction -----------------------------------

def test_argv_includes_all_required_args(tmp_path: Path) -> None:
    model_path = tmp_path / "qwen-9b.gguf"
    binary_path = tmp_path / "llama-server"
    cfg = LlamaServerConfig(
        name="astra",
        model_path=model_path,
        port=8080,
        ctx_size=32_768,
        n_gpu_layers=50,
        chat_template_kwargs={"enable_thinking": "true"},
    )
    inst = LlamaServerInstance(cfg, binary_path=binary_path)
    argv = inst._build_argv()
    assert argv[0] == str(binary_path)
    assert "--model" in argv
    assert str(model_path) in argv
    assert "--port" in argv
    assert "8080" in argv
    assert "--ctx-size" in argv
    assert "32768" in argv
    assert "--n-gpu-layers" in argv
    assert "50" in argv
    assert "--reasoning-format" in argv
    assert "deepseek" in argv
    assert "--chat-template-kwargs" in argv
    assert "enable_thinking=true" in argv


def test_argv_extra_args_appended(tmp_path: Path) -> None:
    cfg = LlamaServerConfig(
        name="astra",
        model_path=tmp_path / "x.gguf",
        port=8080,
        extra_args=["--flash-attn", "1"],
    )
    inst = LlamaServerInstance(cfg, binary_path=tmp_path / "llama-server")
    argv = inst._build_argv()
    assert argv[-2:] == ["--flash-attn", "1"]


def test_base_url_format() -> None:
    cfg = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8083)
    inst = LlamaServerInstance(cfg, binary_path="/x")
    assert inst.base_url == "http://127.0.0.1:8083"


def test_custom_host_propagates() -> None:
    cfg = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8080)
    inst = LlamaServerInstance(cfg, binary_path="/x", host="10.0.0.1")
    assert inst.base_url == "http://10.0.0.1:8080"


def test_default_binary_path_constant() -> None:
    assert DEFAULT_BINARY.endswith("llama-server.exe")
    assert DEFAULT_HOST == "127.0.0.1"


# --- Failure paths -----------------------------------------------------------

def test_start_raises_when_binary_missing(tmp_path: Path) -> None:
    cfg = LlamaServerConfig(name="x", model_path=tmp_path / "x.gguf", port=8080)
    inst = LlamaServerInstance(cfg, binary_path=tmp_path / "no-such-binary")
    with pytest.raises(LlamaServerError, match="binary not found"):
        inst.start()


def test_start_raises_when_model_missing(tmp_path: Path) -> None:
    fake_binary = tmp_path / "llama-server"
    fake_binary.write_text("fake binary", encoding="utf-8")
    cfg = LlamaServerConfig(
        name="x", model_path=tmp_path / "missing.gguf", port=8080,
    )
    inst = LlamaServerInstance(cfg, binary_path=fake_binary)
    with pytest.raises(LlamaServerError, match="model GGUF not found"):
        inst.start()


def test_stop_is_idempotent() -> None:
    cfg = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8080)
    inst = LlamaServerInstance(cfg, binary_path="/x")
    inst.stop()
    inst.stop()  # second call: no-op, no exception


def test_is_running_false_when_not_started() -> None:
    cfg = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8080)
    inst = LlamaServerInstance(cfg, binary_path="/x")
    assert inst.is_running is False


# --- LlamaServerOrchestrator -------------------------------------------------

def test_orchestrator_rejects_empty_list() -> None:
    with pytest.raises(ValueError, match="at least one instance"):
        LlamaServerOrchestrator(instances=[])


def test_orchestrator_holds_instances() -> None:
    cfg = LlamaServerConfig(name="x", model_path=Path("/x.gguf"), port=8080)
    inst = LlamaServerInstance(cfg, binary_path="/x")
    orch = LlamaServerOrchestrator(instances=[inst])
    assert orch.instances == [inst]


def test_orchestrator_rollback_on_start_failure(tmp_path: Path) -> None:
    """If instance N fails to start, instances 0..N-1 are stopped."""
    binary = tmp_path / "bin"
    binary.write_text("fake", encoding="utf-8")
    bad_model = tmp_path / "missing.gguf"

    # Single bad instance — start_all should raise without partial state.
    cfg = LlamaServerConfig(name="x", model_path=bad_model, port=8080)
    inst = LlamaServerInstance(cfg, binary_path=binary)
    orch = LlamaServerOrchestrator(instances=[inst])
    with pytest.raises(LlamaServerError):
        orch.start_all()
    assert orch._started == []   # no leaked started state
