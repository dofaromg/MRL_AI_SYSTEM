#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mother_assembly.py — MotherAssembly: Unified System Entry Point
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=1 MotherCore

The MotherAssembly is the crown of the MRL AI System.

    MotherBody = MaxBoundary + MinPacket + ReversibleChain

It combines every industry-standard module (new) with every MRL-specific
core module (existing) into a single, operable assembly that is:

  - fully reversible          (fltnz_parser + memory_chain)
  - self-indexing             (mrl_librarian + vector_store)
  - agent-capable             (tool_registry + agent_planner)
  - prompt-managed            (prompt_template)
  - evaluable                 (eval_engine)
  - extensible                (plugin_manager)
  - world-aware               (world_module)

The combination (組合) is the system's biggest feature.  Every action taken
through the MotherAssembly is:
  1. Signed with origin_signature="MrLiouWord"
  2. Sealed in the MerkleChain (canonical immutable record)
  3. Scored by the EvalPipeline
  4. Stored as a trajectory step in the WorldModule
  5. Searchable via the VectorStore (RAG-ready)

Architecture diagram
--------------------

  ┌─────────────────────────────────────────────────────────┐
  │                    MotherAssembly                        │
  │                                                          │
  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
  │  │ ToolRegistry │  │PromptTemplate│  │  EvalPipeline │  │
  │  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘  │
  │         │                 │                  │            │
  │  ┌──────▼─────────────────▼──────────────────▼────────┐  │
  │  │                  AgentPlanner (ReAct)               │  │
  │  └──────────────────────────┬──────────────────────────┘  │
  │                             │                              │
  │  ┌──────────────────────────▼──────────────────────────┐  │
  │  │          MRL Core Assembly (existing)               │  │
  │  │  MerkleChain · WorldModule · FLTNZParser ·          │  │
  │  │  MRL_Librarian · VectorStore · PluginManager        │  │
  │  └─────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────┘

Usage (library)
---------------
    from mother_assembly import MotherAssembly

    ma = MotherAssembly()
    ma.boot()

    # Run an agent task
    result = ma.run_agent("Summarise the repo structure")
    print(result["answer"])

    # Evaluate an output
    score = ma.evaluate("The MRL system uses Merkle chains.", keywords=["MRL", "Merkle"])
    print(score["composite"])

    # Render a prompt
    prompt = ma.render_prompt("system_intro", {"name": "FlowAgent"})

    # Seal a text into the reversible chain + merkle log
    trace = ma.seal_text("Hello world", label="test")

CLI
---
    python 09_workflow/mother_assembly.py boot
    python 09_workflow/mother_assembly.py status
    python 09_workflow/mother_assembly.py run   --goal "What is 3 + 4?"
    python 09_workflow/mother_assembly.py eval  --output "Hello MRL" --keywords "MRL"
    python 09_workflow/mother_assembly.py seal  --text "Hello world" --label test
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
ASSEMBLY_VERSION = "1.1"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Module path resolution ────────────────────────────────────────────────────
# The numeric-prefixed directories are not packages; add them to sys.path.

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
        _REPO_ROOT / "03_memory" / "vector",
        _REPO_ROOT / "05_persona",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()

# ── Lazy imports (graceful degradation if a module is unavailable) ────────────

def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── MotherAssembly ───────────────────────────────────────────────────────────

class MotherAssembly:
    """
    Unified system entry point that wires all MRL modules together.

    Attributes
    ----------
    tool_registry    : ToolRegistry
    template_registry: TemplateRegistry
    eval_pipeline    : EvalPipeline
    plugin_manager   : PluginManager
    vector_store     : VectorStore
    world            : WorldModule
    chain            : MerkleChain  (canonical immutable record)
    llm_gateway      : LLMGateway   (local-only LLM connector)
    conversation_mgr : ConversationManager
    guardrail        : GuardrailChain wrapper (standard policy)
    input_guard      : InputGuardrail
    output_guard     : OutputGuardrail
    """

    def __init__(self) -> None:
        self._booted = False
        self.tool_registry: Any = None
        self.template_registry: Any = None
        self.eval_pipeline: Any = None
        self.plugin_manager: Any = None
        self.vector_store: Any = None
        self.world: Any = None
        self.chain: Any = None
        # ── New subsystems (v1.1) ──────────────────────────────────────────────
        self.llm_gateway: Any = None
        self.conversation_mgr: Any = None
        self.input_guard: Any = None
        self.output_guard: Any = None
        self._boot_log: List[Dict[str, Any]] = []

    # ── Boot ──────────────────────────────────────────────────────────────────

    def boot(self) -> Dict[str, Any]:
        """
        Initialise all subsystems in dependency order.

        Returns a boot report with status for each subsystem.
        """
        if self._booted:
            return {"already_booted": True}

        report: Dict[str, Any] = {
            "assembly_version": ASSEMBLY_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "booted_at_ms": int(time.time() * 1000),
            "subsystems": {},
        }

        # 1 ── MerkleChain (canonical record)
        report["subsystems"]["merkle_chain"] = self._boot_merkle()

        # 2 ── WorldModule (world state + trajectory)
        report["subsystems"]["world_module"] = self._boot_world()

        # 3 ── VectorStore (RAG)
        report["subsystems"]["vector_store"] = self._boot_vector()

        # 4 ── ToolRegistry
        report["subsystems"]["tool_registry"] = self._boot_tools()

        # 5 ── PromptTemplate registry
        report["subsystems"]["prompt_template"] = self._boot_templates()

        # 6 ── EvalPipeline
        report["subsystems"]["eval_engine"] = self._boot_eval()

        # 7 ── PluginManager
        report["subsystems"]["plugin_manager"] = self._boot_plugins()

        # ── New subsystems (v1.1) ──────────────────────────────────────────────

        # 8 ── LLMGateway (local-only)
        report["subsystems"]["llm_gateway"] = self._boot_llm_gateway()

        # 9 ── ConversationManager
        report["subsystems"]["conversation_mgr"] = self._boot_conversation()

        # 10 ── Guardrail
        report["subsystems"]["guardrail"] = self._boot_guardrail()

        self._booted = True
        self._seal_event("boot", report)
        return report

    # ── Private boot helpers ──────────────────────────────────────────────────

    def _boot_merkle(self) -> str:
        MerkleChain = _try_import("memory_chain", "MerkleChain")
        if MerkleChain is None:
            return "unavailable"
        try:
            data_dir = _REPO_ROOT / "03_memory" / "_data" / "memory_chain"
            self.chain = MerkleChain(data_dir)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_world(self) -> str:
        WorldModule = _try_import("world_module", "WorldModule")
        if WorldModule is None:
            return "unavailable"
        try:
            self.world = WorldModule()
            self.world.set_state("assembly_version", ASSEMBLY_VERSION)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_vector(self) -> str:
        VectorStore = _try_import("vector_store", "VectorStore")
        if VectorStore is None:
            return "unavailable"
        try:
            self.vector_store = VectorStore()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_tools(self) -> str:
        ToolRegistry = _try_import("tool_registry", "ToolRegistry")
        if ToolRegistry is None:
            return "unavailable"
        try:
            self.tool_registry = ToolRegistry()
            self._register_builtin_tools()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_templates(self) -> str:
        TemplateRegistry = _try_import("prompt_template", "TemplateRegistry")
        if TemplateRegistry is None:
            return "unavailable"
        try:
            self.template_registry = TemplateRegistry()
            self._register_builtin_templates()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_eval(self) -> str:
        default_pipeline = _try_import("eval_engine", "default_pipeline")
        if default_pipeline is None:
            return "unavailable"
        try:
            self.eval_pipeline = default_pipeline()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_plugins(self) -> str:
        PluginManager = _try_import("plugin_manager", "PluginManager")
        if PluginManager is None:
            return "unavailable"
        try:
            self.plugin_manager = PluginManager(
                plugin_dir=_REPO_ROOT / "09_workflow" / "plugins",
                registry=self.tool_registry,
            )
            found = self.plugin_manager.discover()
            self.plugin_manager.activate_all()
            return f"ok ({len(found)} plugin(s) discovered)"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_llm_gateway(self) -> str:
        LLMGateway = _try_import("llm_gateway", "LLMGateway")
        if LLMGateway is None:
            return "unavailable"
        try:
            self.llm_gateway = LLMGateway()
            return f"ok (backend={self.llm_gateway.backend}, model={self.llm_gateway.model})"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_conversation(self) -> str:
        ConversationManager = _try_import("conversation", "ConversationManager")
        if ConversationManager is None:
            return "unavailable"
        try:
            self.conversation_mgr = ConversationManager(
                store_dir=_REPO_ROOT / "data" / "sessions",
                gateway=self.llm_gateway,
            )
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_guardrail(self) -> str:
        InputGuardrail  = _try_import("guardrail", "InputGuardrail")
        OutputGuardrail = _try_import("guardrail", "OutputGuardrail")
        if InputGuardrail is None or OutputGuardrail is None:
            return "unavailable"
        try:
            self.input_guard  = InputGuardrail("standard")
            self.output_guard = OutputGuardrail("standard")
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    # ── Built-in tools ────────────────────────────────────────────────────────

    def _register_builtin_tools(self) -> None:
        if self.tool_registry is None:
            return

        @self.tool_registry.register(
            description="Return current UTC timestamp in milliseconds."
        )
        def now_ms() -> int:
            return int(time.time() * 1000)

        @self.tool_registry.register(
            description="Echo a message.",
            parameters={"message": str},
        )
        def echo(message: str) -> str:
            return message

        @self.tool_registry.register(
            description="Add two numbers.",
            parameters={"a": float, "b": float},
        )
        def add(a: float, b: float) -> float:
            return a + b

        @self.tool_registry.register(
            description="Retrieve world state snapshot.",
        )
        def world_snapshot() -> Dict[str, Any]:
            if self.world:
                return self.world.snapshot()
            return {}

        @self.tool_registry.register(
            description="Query the vector store for nearest neighbours.",
            parameters={"query_csv": str, "top_k": int},
        )
        def vector_query(query_csv: str, top_k: int = 3) -> List[Any]:
            if self.vector_store is None:
                return []
            vec = [float(x) for x in query_csv.split(",")]
            hits = self.vector_store.query(vec, top_k=top_k)
            return [{"id": h[0], "score": h[1], "meta": h[2]} for h in hits]

    # ── Built-in templates ────────────────────────────────────────────────────

    def _register_builtin_templates(self) -> None:
        if self.template_registry is None:
            return
        self.template_registry.add(
            "system_intro",
            "You are {name}, a {role} in the MRL AI System. "
            "Your origin signature is MrLiouWord. "
            "Always act in accordance with the Mother Core Assembly laws.",
            "Standard system introduction prompt",
        )
        self.template_registry.add(
            "task_prompt",
            "Goal: {goal}\n\nContext:\n{context}\n\nPlease proceed step by step.",
            "Standard task prompt with goal and context",
        )
        self.template_registry.add(
            "eval_summary",
            "Output evaluation for '{label}':\n"
            "  composite score: {composite}\n"
            "  passed: {passed}\n"
            "  individual scores: {scores}",
            "Evaluation result summary template",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def run_agent(
        self,
        goal: str,
        think_fn: Optional[Any] = None,
        max_steps: int = 20,
    ) -> Dict[str, Any]:
        """
        Run an agent loop for *goal*.

        If *think_fn* is not provided, a simple default think function is used
        that immediately finishes with a fixed answer (useful for testing).
        """
        AgentPlanner = _try_import("agent_planner", "AgentPlanner")
        FINISH_ACTION = _try_import("agent_planner", "FINISH_ACTION") or "__finish__"

        if AgentPlanner is None or self.tool_registry is None:
            return {"error": "AgentPlanner or ToolRegistry unavailable", "goal": goal}

        if think_fn is None:
            def think_fn(_state: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "thought": f"Completing goal: {goal}",
                    "action": FINISH_ACTION,
                    "args": {"answer": f"[MotherAssembly] Goal noted: {goal}"},
                }

        planner = AgentPlanner(self.tool_registry, think_fn=think_fn, max_steps=max_steps)
        result = planner.run(goal)
        self._seal_event("run_agent", {"goal": goal, "finished": result.get("finished")})
        return result

    def evaluate(
        self,
        output: str,
        keywords: Optional[List[str]] = None,
        reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Score *output* with the EvalPipeline."""
        if self.eval_pipeline is None:
            return {"error": "EvalPipeline unavailable"}
        ref = dict(reference or {})
        if keywords:
            ref.setdefault("keywords", keywords)
        result = self.eval_pipeline.run(output, ref)
        self._seal_event("evaluate", {"composite": result["composite"]})
        return result

    def render_prompt(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a named prompt template."""
        if self.template_registry is None:
            return f"[PromptTemplate unavailable] id={template_id}"
        return self.template_registry.render(template_id, variables or {})

    def seal_text(self, text: str, label: str = "unnamed") -> Dict[str, Any]:
        """
        Encode *text* through the full reversible chain and commit to MerkleChain.
        Returns the trace record.
        """
        text_to_trace = _try_import("fltnz_parser", "text_to_trace")
        if text_to_trace is None:
            return {"error": "fltnz_parser unavailable"}
        trace = text_to_trace(text, label=label)
        self._seal_event("seal_text", {"label": label})
        return trace

    # ── New public API (v1.1) ─────────────────────────────────────────────────

    def chat(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
        system_prompt: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
        use_guardrail: bool = True,
    ) -> Dict[str, Any]:
        """
        Send *message* through the guardrail → conversation manager → LLM
        gateway pipeline.

        Creates a new session if *session_id* is None.

        Returns::

            {
              "ok":         bool,
              "session_id": str,
              "reply":      str | None,
              "violations": [...],
              "backend":    str,
              "origin_signature": "MrLiouWord",
            }
        """
        # ── Input guardrail ───────────────────────────────────────────────────
        violations: List[Dict[str, Any]] = []
        if use_guardrail and self.input_guard is not None:
            input_ok, input_viols = self.input_guard.check(message)
            violations.extend(input_viols)
            if not input_ok:
                return {
                    "ok": False,
                    "session_id": session_id,
                    "reply": None,
                    "violations": violations,
                    "backend": None,
                    "origin_signature": ORIGIN_SIGNATURE,
                }

        # ── Session management ────────────────────────────────────────────────
        if self.conversation_mgr is None:
            return {"error": "ConversationManager unavailable", "origin_signature": ORIGIN_SIGNATURE}

        if session_id is None:
            session_id = self.conversation_mgr.new_session(system_prompt=system_prompt)
        else:
            # Ensure the session exists; create if not
            try:
                self.conversation_mgr.get(session_id)
            except FileNotFoundError:
                session_id = self.conversation_mgr.new_session(
                    session_id=session_id, system_prompt=system_prompt
                )

        self.conversation_mgr.add_user(session_id, message)

        # ── LLM call (via conversation manager) ───────────────────────────────
        reply = self.conversation_mgr.generate_reply(
            session_id, max_tokens=max_tokens, temperature=temperature
        )

        # ── Output guardrail ──────────────────────────────────────────────────
        if use_guardrail and self.output_guard is not None:
            output_ok, output_viols = self.output_guard.check(reply)
            violations.extend(output_viols)
            if not output_ok:
                # Remove the blocked reply from session history
                sess = self.conversation_mgr.get(session_id)
                sess.remove_last_assistant_message()
                reply_out = None
                ok = False
            else:
                reply_out = reply
                ok = True
        else:
            reply_out = reply
            ok = True

        backend = self.llm_gateway.backend if self.llm_gateway else "unavailable"
        self._seal_event("chat", {"session_id": session_id, "ok": ok})
        return {
            "ok":               ok,
            "session_id":       session_id,
            "reply":            reply_out,
            "violations":       violations,
            "backend":          backend,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def multi_agent_run(
        self,
        task: str,
        agent_names: Optional[List[str]] = None,
        *,
        max_turns: int = 8,
        include_human_proxy: bool = False,
    ) -> Dict[str, Any]:
        """
        Run a multi-agent group chat for *task*.

        All agents use the attached LLMGateway.  If gateway is unavailable,
        stub replies are used automatically.

        Returns the full transcript dict from GroupChatManager.run().
        """
        Agent            = _try_import("multi_agent", "Agent")
        HumanProxyAgent  = _try_import("multi_agent", "HumanProxyAgent")
        GroupChat        = _try_import("multi_agent", "GroupChat")
        GroupChatManager = _try_import("multi_agent", "GroupChatManager")

        if Agent is None:
            return {"error": "multi_agent module unavailable", "origin_signature": ORIGIN_SIGNATURE}

        names = agent_names or ["Planner", "Executor"]
        agents: List[Any] = [
            Agent(
                name,
                gateway=self.llm_gateway,
                system_prompt=f"You are {name}, a specialist agent in the MRL AI System.",
            )
            for name in names
        ]

        if include_human_proxy:
            agents.append(HumanProxyAgent("Human", interactive=False, auto_reply="TERMINATE"))

        gc  = GroupChat(agents, max_turns=max_turns)
        mgr = GroupChatManager(gc)
        result = mgr.run(task)
        self._seal_event("multi_agent_run", {"task": task, "turns": result.get("total_turns")})
        return result

    def parse_output(self, text: str, parser_type: str = "auto") -> Dict[str, Any]:
        """
        Parse structured data from *text*.

        parser_type : "json" | "list" | "kv" | "code" | "table" | "auto"
            "auto" tries JSON → KV → list in sequence.
        """
        parsers_mod = {
            "json":  ("output_parser", "JSONParser"),
            "list":  ("output_parser", "ListParser"),
            "kv":    ("output_parser", "KeyValueParser"),
            "code":  ("output_parser", "CodeBlockParser"),
            "table": ("output_parser", "TableParser"),
        }

        ParserChain = _try_import("output_parser", "ParserChain")

        if parser_type == "auto":
            if ParserChain is None:
                return {"error": "output_parser unavailable", "origin_signature": ORIGIN_SIGNATURE}
            jp = _try_import("output_parser", "JSONParser")
            kp = _try_import("output_parser", "KeyValueParser")
            lp = _try_import("output_parser", "ListParser")
            chain = ParserChain([jp(), kp(), lp()])
            return chain.parse(text)

        mod, cls_name = parsers_mod.get(parser_type, ("output_parser", "JSONParser"))
        ParserCls = _try_import(mod, cls_name)
        if ParserCls is None:
            return {"error": f"Parser '{parser_type}' unavailable", "origin_signature": ORIGIN_SIGNATURE}
        return ParserCls().parse(text)

    def guard_check(
        self,
        text: str,
        direction: str = "input",
        policy: str = "standard",
    ) -> Dict[str, Any]:
        """
        Run a guardrail check on *text*.

        direction : "input" | "output"
        policy    : "strict" | "standard" | "permissive"
        """
        GuardCls = _try_import(
            "guardrail",
            "InputGuardrail" if direction == "input" else "OutputGuardrail",
        )
        if GuardCls is None:
            return {"error": "guardrail unavailable", "origin_signature": ORIGIN_SIGNATURE}
        guard = GuardCls(policy)
        ok, violations = guard.check(text)
        return {
            "ok":               ok,
            "direction":        direction,
            "policy":           policy,
            "violations":       violations,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def status(self) -> Dict[str, Any]:
        """Return a health-check snapshot of all subsystems."""
        llm_info = {}
        if self.llm_gateway is not None:
            llm_info = {
                "backend": self.llm_gateway.backend,
                "model":   self.llm_gateway.model,
            }
        return {
            "assembly_version": ASSEMBLY_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "booted": self._booted,
            "subsystems": {
                # original seven
                "merkle_chain":      self.chain is not None,
                "world_module":      self.world is not None,
                "vector_store":      self.vector_store is not None,
                "tool_registry":     self.tool_registry is not None,
                "template_registry": self.template_registry is not None,
                "eval_pipeline":     self.eval_pipeline is not None,
                "plugin_manager":    self.plugin_manager is not None,
                # new three (v1.1)
                "llm_gateway":       self.llm_gateway is not None,
                "conversation_mgr":  self.conversation_mgr is not None,
                "guardrail":         self.input_guard is not None,
            },
            "llm": llm_info,
            "checked_at_ms": int(time.time() * 1000),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _seal_event(self, event_type: str, detail: Any = None) -> None:
        """Commit a canonical event to the MerkleChain (if available)."""
        if self.chain is None:
            return
        try:
            self.chain.commit(
                payload={
                    "event_type": event_type,
                    "detail": detail,
                    "origin_signature": ORIGIN_SIGNATURE,
                    "ts_ms": int(time.time() * 1000),
                },
                layer="L7",
                tags=["mother_assembly", event_type],
                meta={"source": "mother_assembly"},
            )
        except Exception:  # noqa: BLE001
            pass  # Chain failure must never crash the assembly


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_boot(_args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    report = ma.boot()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


def _cmd_status(_args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    snap = ma.status()
    ok_count = sum(1 for v in snap["subsystems"].values() if v)
    total = len(snap["subsystems"])
    print(f"MotherAssembly v{snap['assembly_version']}  [{ok_count}/{total} subsystems online]")
    for name, online in snap["subsystems"].items():
        icon = "✅" if online else "❌"
        print(f"  {icon}  {name}")


def _cmd_run(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.run_agent(args.goal)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _cmd_eval(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    result = ma.evaluate(args.output, keywords=keywords)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _cmd_seal(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    trace = ma.seal_text(args.text, label=args.label or "cli")
    print(json.dumps(trace, ensure_ascii=False, indent=2, default=str))


def _cmd_chat(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.chat(
        args.msg,
        session_id=args.session or None,
        system_prompt=args.system or "",
        use_guardrail=not args.no_guardrail,
    )
    if result.get("ok"):
        print(f"[{result.get('backend','?')}] {result['reply']}")
    else:
        print("❌ Blocked or error:")
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _cmd_multi_agent(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    names = [n.strip() for n in args.agents.split(",")] if args.agents else None
    result = ma.multi_agent_run(
        args.task,
        agent_names=names,
        max_turns=args.max_turns,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _cmd_guard(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.guard_check(args.text, direction=args.direction, policy=args.policy)
    status = "✅ PASS" if result["ok"] else "❌ BLOCK"
    print(f"{status}  direction={result['direction']}  policy={result['policy']}")
    for v in result.get("violations", []):
        print(f"  [{v['severity'].upper()}] {v['check']}: {v['reason']}")


def _cmd_parse(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.parse_output(args.text, parser_type=args.type)
    status = "✅ OK" if result["ok"] else "❌ FAIL"
    print(f"{status}  parser={result['parser']}")
    if result["ok"]:
        print(json.dumps(result["data"], ensure_ascii=False, indent=2, default=str))
    else:
        print(f"  error: {result['error']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MotherAssembly v1.1 — unified MRL AGI entry point"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("boot",   help="Boot all subsystems and print report")
    sub.add_parser("status", help="Print subsystem health status")

    r = sub.add_parser("run", help="Run an agent task")
    r.add_argument("--goal", required=True, help="Goal string for the agent")

    e = sub.add_parser("eval", help="Evaluate an output string")
    e.add_argument("--output", required=True)
    e.add_argument("--keywords", default="", help="Comma-separated keywords")

    s = sub.add_parser("seal", help="Seal text through the reversible chain")
    s.add_argument("--text", required=True)
    s.add_argument("--label", default="cli")

    # ── New commands (v1.1) ───────────────────────────────────────────────────

    ch = sub.add_parser("chat", help="Send a guarded chat message (local LLM)")
    ch.add_argument("--msg",          required=True, help="User message")
    ch.add_argument("--session",      default="",    help="Session ID (omit to create new)")
    ch.add_argument("--system",       default="",    help="System prompt for new session")
    ch.add_argument("--no-guardrail", action="store_true",
                    help="Bypass guardrail checks")

    ma = sub.add_parser("multi-agent", help="Run a multi-agent group chat")
    ma.add_argument("--task",      required=True)
    ma.add_argument("--agents",    default="Planner,Executor",
                    help="Comma-separated agent names")
    ma.add_argument("--max-turns", type=int, default=8, dest="max_turns")

    gd = sub.add_parser("guard", help="Run a guardrail check on text")
    gd.add_argument("--text",      required=True)
    gd.add_argument("--direction", default="input", choices=["input", "output"])
    gd.add_argument("--policy",    default="standard",
                    choices=["strict", "standard", "permissive"])

    ps = sub.add_parser("parse", help="Parse structured output from text")
    ps.add_argument("--text", required=True)
    ps.add_argument("--type", default="auto",
                    choices=["auto", "json", "list", "kv", "code", "table"])

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "boot":        _cmd_boot,
        "status":      _cmd_status,
        "run":         _cmd_run,
        "eval":        _cmd_eval,
        "seal":        _cmd_seal,
        "chat":        _cmd_chat,
        "multi-agent": _cmd_multi_agent,
        "guard":       _cmd_guard,
        "parse":       _cmd_parse,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
