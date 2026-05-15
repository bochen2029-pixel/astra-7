"""astra.llm — three LLM clients, calculator-bound by default.

Implements spec v0.128 §4.1 Substrate Contract, §4.9 Harness Contract, §6.4
Narrator-LLM Contract, §15.6 Calculator-bound LLM agency.

Three LLM instances on three llama-server ports:
- ASTRA-LLM (port 8080):    Qwen 27B target / 9B fallback.
- Narrator-LLM (port 8081): Qwen 9B, calculator-bound.
- Adapter-LLM (port 8082):  Qwen 3B or rules-based v0.

Each bundle wraps a client + sysprompt + calculator-bound validator.
"""

from astra.llm.adapter_bundle import (
    AdapterBundle,
    AdapterResult,
    RulesBasedAdapter,
    load_adapter_sysprompt,
)
from astra.llm.astra_bundle import (
    AstraBundle,
    default_prompts_dir,
    load_astra_sysprompt,
)
from astra.llm.client import (
    DEFAULT_CHAT_PATH,
    ChatMessage,
    LLMClient,
    LLMClientError,
    SamplingParams,
)
from astra.llm.llama_server import (
    DEFAULT_BINARY,
    DEFAULT_HOST,
    LlamaServerConfig,
    LlamaServerError,
    LlamaServerInstance,
    LlamaServerOrchestrator,
)
from astra.llm.narrator_bundle import NarratorBundle, load_narrator_sysprompt
from astra.llm.validator import (
    CalculatorBoundValidator,
    UngroundedNumber,
    ValidationReport,
    find_ungrounded_numerics,
    validate_speech,
)

__all__ = [
    "DEFAULT_BINARY",
    "DEFAULT_CHAT_PATH",
    "DEFAULT_HOST",
    "AdapterBundle",
    "AdapterResult",
    "AstraBundle",
    "CalculatorBoundValidator",
    "ChatMessage",
    "LLMClient",
    "LLMClientError",
    "LlamaServerConfig",
    "LlamaServerError",
    "LlamaServerInstance",
    "LlamaServerOrchestrator",
    "NarratorBundle",
    "RulesBasedAdapter",
    "SamplingParams",
    "UngroundedNumber",
    "ValidationReport",
    "default_prompts_dir",
    "find_ungrounded_numerics",
    "load_adapter_sysprompt",
    "load_astra_sysprompt",
    "load_narrator_sysprompt",
    "validate_speech",
]
