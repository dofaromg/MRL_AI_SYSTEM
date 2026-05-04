"""
MRL AI System — Streamlit Dashboard
origin_signature: MrLiouWord

Panels
------
  💬 Chat        — multi-turn conversation via api_gateway
  🏥 Health      — MotherAssembly status + MRL_health_monitor
  📊 Metrics     — MRL_metrics telemetry snapshot
  📜 Sessions    — browse and export conversation sessions
  🔧 Tools       — list and call registered tools interactively
  📝 Templates   — manage and render prompt templates
  ⚙️ Config      — view and edit system configuration
  🤖 Agent       — run agent tasks with step-by-step trajectory
  🛡️ Guardrail   — test input/output text against safety policies
"""

from __future__ import annotations

import json
import pathlib
import sys
import time
from typing import Any, Dict, List

import streamlit as st

# ── Ensure workflow modules are importable ────────────────────────────────────
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
for _sub in [
    _REPO_ROOT / "09_workflow",
    _REPO_ROOT / "03_memory" / "merkle",
    _REPO_ROOT / "03_memory" / "vector",
    _REPO_ROOT / "05_persona",
]:
    _p = str(_sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

ORIGIN_SIGNATURE = "MrLiouWord"

# ── Lazy imports (graceful degradation) ──────────────────────────────────────

def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr, None)
    except Exception:  # noqa: BLE001
        return None


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MRL AI System",
    page_icon="🧠",
    layout="wide",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🧠 MRL AI System")
st.sidebar.caption(f"origin_signature: **{ORIGIN_SIGNATURE}**")

panel = st.sidebar.radio(
    "Panel",
    [
        "💬 Chat",
        "🏥 Health",
        "📊 Metrics",
        "📜 Sessions",
        "🔧 Tools",
        "📝 Templates",
        "⚙️ Config",
        "🤖 Agent",
        "🛡️ Guardrail",
    ],
)

# Keyword search (used in Sessions panel)
search_term = st.sidebar.text_input("🔍 Search sessions by label")

# ── Helpers ───────────────────────────────────────────────────────────────────


@st.cache_resource
def _get_conv_mgr() -> Any:
    ConvMgr = _try_import("conversation_manager", "ConversationManager")
    return ConvMgr() if ConvMgr else None


@st.cache_resource
def _get_llm_gateway() -> Any:
    LLMGateway = _try_import("llm_gateway", "LLMGateway")
    return LLMGateway() if LLMGateway else None


@st.cache_resource
def _get_health_monitor() -> Any:
    HealthMonitor = _try_import("MRL_health_monitor", "HealthMonitor")
    return HealthMonitor() if HealthMonitor else None


@st.cache_resource
def _get_tool_registry() -> Any:
    ToolRegistry = _try_import("tool_registry", "ToolRegistry")
    return ToolRegistry() if ToolRegistry else None


@st.cache_resource
def _get_template_registry() -> Any:
    TemplateRegistry = _try_import("prompt_template", "TemplateRegistry")
    return TemplateRegistry() if TemplateRegistry else None


@st.cache_resource
def _get_config_manager() -> Any:
    ConfigManager = _try_import("config_manager", "ConfigManager")
    return ConfigManager() if ConfigManager else None


@st.cache_resource
def _get_assembly() -> Any:
    MotherAssembly = _try_import("MRL_mother_assembly", "MotherAssembly")
    if MotherAssembly is None:
        return None
    ma = MotherAssembly()
    ma.boot()
    return ma


# ── Module-level constants ────────────────────────────────────────────────────

_STEP_TYPE_ICONS: Dict[str, str] = {
    "think":   "🤔",
    "act":     "⚙️",
    "observe": "👁️",
    "finish":  "✅",
}

_JSON_TYPE_DEFAULTS: Dict[str, Any] = {
    "integer": 0,
    "number":  0.0,
    "boolean": False,
    "string":  "",
    "array":   [],
    "object":  {},
}


def _default_value_for_type(param_type: str) -> Any:
    """Return a sensible default value for a JSON-schema type string."""
    return _JSON_TYPE_DEFAULTS.get(param_type, "")


# ── Panel: Chat ───────────────────────────────────────────────────────────────

if panel == "💬 Chat":
    st.header("💬 Chat")

    # Session management
    conv_mgr = _get_conv_mgr()
    if conv_mgr is None:
        st.error("ConversationManager not available.")
        st.stop()

    # Session selector
    sessions = conv_mgr.list_sessions()
    session_labels = {s["session_id"]: (s.get("label") or s["session_id"][:8]) for s in sessions}

    col_new, col_sel = st.columns([1, 3])
    with col_new:
        if st.button("＋ New session"):
            system = "You are MRL_AGI, a helpful AI assistant. Origin: MrLiouWord."
            new_sid = conv_mgr.new_session(system_prompt=system, label="Chat")
            st.session_state["active_sid"] = new_sid
            st.rerun()

    with col_sel:
        if sessions:
            chosen = st.selectbox(
                "Active session",
                options=[s["session_id"] for s in sessions],
                format_func=lambda sid: session_labels.get(sid, sid),
                index=0,
                key="session_selector",
            )
            st.session_state["active_sid"] = chosen

    active_sid: str = st.session_state.get("active_sid", "")

    if not active_sid:
        st.info("Create a new session or select an existing one.")
        st.stop()

    # Display history
    try:
        history: List[Dict[str, Any]] = conv_mgr.get_history(active_sid)
    except KeyError:
        st.warning("Session not found — please create a new one.")
        st.stop()

    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            continue
        with st.chat_message(role):
            st.markdown(content)

    # Chat input
    user_input = st.chat_input("Type your message…")
    if user_input:
        conv_mgr.add_message(active_sid, "user", user_input)
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                gw = _get_llm_gateway()
                if gw:
                    msgs = conv_mgr.get_history(active_sid)
                    resp = gw.chat(
                        [{"role": m["role"], "content": m["content"]} for m in msgs],
                        max_tokens=1024,
                    )
                    reply = resp.get("text", "[no reply]")
                else:
                    reply = f"[MockAdapter] Echo: {user_input}"
                conv_mgr.add_message(active_sid, "assistant", reply)
                st.markdown(reply)
        st.rerun()

# ── Panel: Health ─────────────────────────────────────────────────────────────

elif panel == "🏥 Health":
    st.header("🏥 System Health")

    monitor = _get_health_monitor()
    if monitor:
        status = monitor.probe_once()
        overall = status.get("overall", "unknown")
        colour = {"ok": "🟢", "warn": "🟡", "error": "🔴"}.get(overall, "⚪")
        st.metric("Overall Status", f"{colour} {overall.upper()}")

        probes = status.get("probes", {})
        if probes:
            cols = st.columns(len(probes))
            for col, (name, result) in zip(cols, probes.items()):
                icon = {"ok": "✅", "warn": "⚠️", "error": "❌"}.get(result["status"], "❓")
                col.metric(name, f"{icon} {result['status']}", result.get("message", ""))
        else:
            st.info("No probe results yet.")

        with st.expander("Raw status JSON"):
            st.json(status)
    else:
        st.warning("MRL_health_monitor not available.")

    st.divider()
    st.subheader("LLM Backend")
    gw = _get_llm_gateway()
    if gw:
        gw_status = gw.status()
        c1, c2, c3 = st.columns(3)
        c1.metric("Backend", gw_status.get("backend", "unknown"))
        c2.metric("Model", gw_status.get("model", "unknown"))
        c3.metric("Stub mode", "Yes" if gw_status.get("is_stub") else "No")
    else:
        st.warning("LLMGateway not available.")

# ── Panel: Metrics ────────────────────────────────────────────────────────────

elif panel == "📊 Metrics":
    st.header("📊 MRL Metrics")

    snapshot_fn = _try_import("MRL_metrics", "snapshot")
    if snapshot_fn is None:
        st.error("MRL_metrics not available.")
        st.stop()

    snap = snapshot_fn()
    subsystems = snap.get("subsystems", {})

    if not subsystems:
        st.info("No metrics recorded yet. Run some chat completions first.")
    else:
        rows = []
        for name, s in subsystems.items():
            rows.append({
                "Subsystem": name,
                "Calls": s.get("call_count", 0),
                "OK": s.get("ok_count", 0),
                "Errors": s.get("error_count", 0),
                "Avg ms": s.get("avg_latency_ms", 0),
                "Max ms": s.get("max_latency_ms", 0),
            })
        st.dataframe(rows, use_container_width=True)

    with st.expander("Raw snapshot JSON"):
        st.json(snap)

    if st.button("↺ Reset metrics"):
        reset_fn = _try_import("MRL_metrics", "reset")
        if reset_fn:
            reset_fn()
            st.success("Metrics reset.")
            st.rerun()

# ── Panel: Sessions ───────────────────────────────────────────────────────────

elif panel == "📜 Sessions":
    st.header("📜 Conversation Sessions")

    conv_mgr = _get_conv_mgr()
    if conv_mgr is None:
        st.error("ConversationManager not available.")
        st.stop()

    sessions = conv_mgr.list_sessions()

    # Filter by search term
    if search_term:
        sessions = [
            s for s in sessions
            if search_term.lower() in (s.get("label") or "").lower()
            or search_term in s["session_id"]
        ]

    st.caption(f"{len(sessions)} session(s) found")

    for sess in sessions:
        sid = sess["session_id"]
        label = sess.get("label") or sid[:8]
        turns = sess.get("turn_count", 0)

        with st.expander(f"**{label}** — {turns} turns"):
            c1, c2 = st.columns([3, 1])
            c1.caption(f"ID: `{sid}`")

            # Export as Markdown
            if c2.button("📥 Export MD", key=f"export_{sid}"):
                md = conv_mgr.export_markdown(sid)
                st.download_button(
                    "Download .md",
                    data=md,
                    file_name=f"session_{sid[:8]}.md",
                    mime="text/markdown",
                    key=f"dl_{sid}",
                )

            # Show messages
            try:
                history = conv_mgr.get_history(sid)
                for msg in history:
                    role = msg.get("role", "?")
                    content = msg.get("content", "")
                    if role == "system":
                        continue
                    # Show ✅ only when the message carries the real origin_signature
                    sig_badge = " ✅" if msg.get("origin_signature") == ORIGIN_SIGNATURE else ""
                    st.markdown(f"**{role.capitalize()}**{sig_badge}: {content[:200]}")
            except KeyError:
                st.warning("Session data unavailable.")

    # Sidebar info
    st.sidebar.divider()
    st.sidebar.caption(f"Showing {len(sessions)} sessions")

# ── Panel: Tools ──────────────────────────────────────────────────────────────

elif panel == "🔧 Tools":
    st.header("🔧 Tool Registry")

    registry = _get_tool_registry()
    if registry is None:
        st.error("ToolRegistry not available.")
        st.stop()

    tool_names = registry.list_tools()

    if not tool_names:
        st.info("No tools registered yet.")
    else:
        st.caption(f"{len(tool_names)} tool(s) registered")

        # Tool selector
        selected_tool = st.selectbox("Select tool", options=tool_names)

        if selected_tool:
            schema = registry.get_schema(selected_tool)
            if schema:
                st.subheader(f"🔍 `{selected_tool}`")
                st.caption(schema.get("description", ""))

                params = schema.get("parameters", {}).get("properties", {})
                required = schema.get("parameters", {}).get("required", [])

                # Build JSON args editor using helper for default values
                default_args: Dict[str, Any] = {
                    param: _default_value_for_type(spec.get("type", "string"))
                    for param, spec in params.items()
                }

                args_text = st.text_area(
                    "Arguments (JSON)",
                    value=json.dumps(default_args, indent=2),
                    height=120,
                    key=f"tool_args_{selected_tool}",
                )

                col_call, col_schema = st.columns([1, 1])
                with col_call:
                    if st.button("▶ Call tool", key=f"call_{selected_tool}"):
                        try:
                            kwargs = json.loads(args_text)
                        except json.JSONDecodeError as exc:
                            st.error(f"Invalid JSON: {exc}")
                            kwargs = None
                        if kwargs is not None:
                            with st.spinner("Running…"):
                                result = registry.call(selected_tool, kwargs)
                            if result.get("ok"):
                                st.success("✅ Tool succeeded")
                                st.json(result)
                            else:
                                st.error(f"❌ {result.get('error', 'unknown error')}")
                                st.json(result)

                with col_schema:
                    with st.expander("Full schema"):
                        st.json(schema)

        st.divider()
        st.subheader("All tools")
        for name in tool_names:
            s = registry.get_schema(name)
            if s:
                with st.expander(f"`{name}` — {s.get('description', '')}"):
                    st.json(s)

# ── Panel: Templates ──────────────────────────────────────────────────────────

elif panel == "📝 Templates":
    st.header("📝 Prompt Templates")

    reg = _get_template_registry()
    if reg is None:
        st.error("TemplateRegistry not available.")
        st.stop()

    # ── Add / update template ──────────────────────────────────────────────
    with st.expander("➕ Add / update template"):
        t_id = st.text_input("Template ID", key="tmpl_add_id")
        t_desc = st.text_input("Description", key="tmpl_add_desc")
        t_text = st.text_area(
            "Template text (use {variable} placeholders)",
            height=100,
            key="tmpl_add_text",
        )
        if st.button("💾 Save template", key="tmpl_save"):
            if not t_id.strip():
                st.error("Template ID is required.")
            elif not t_text.strip():
                st.error("Template text is required.")
            else:
                reg.add(t_id.strip(), t_text.strip(), description=t_desc.strip())
                st.success(f"Template `{t_id.strip()}` saved.")
                st.rerun()

    st.divider()

    templates_raw = reg.list_ids()
    templates = [t.to_dict() for tid in templates_raw if (t := reg.get(tid)) is not None]
    if not templates:
        st.info("No templates found. Add one above.")
        st.stop()

    st.caption(f"{len(templates)} template(s)")

    # ── Render panel ──────────────────────────────────────────────────────
    tmpl_ids = [t["id"] for t in templates]
    render_id = st.selectbox("Select template to render", options=tmpl_ids, key="tmpl_render_sel")

    if render_id:
        tmpl_dict = next((t for t in templates if t["id"] == render_id), None)
        if tmpl_dict:
            st.caption(f"Description: {tmpl_dict.get('description', '—')}")
            vars_needed: List[str] = tmpl_dict.get("variables", [])
            var_values: Dict[str, str] = {}
            if vars_needed:
                st.markdown("**Fill in variables:**")
                for v in vars_needed:
                    var_values[v] = st.text_input(f"`{{{v}}}`", key=f"tmpl_var_{render_id}_{v}")
            if st.button("🖨️ Render", key=f"render_{render_id}"):
                try:
                    rendered = reg.render(render_id, var_values)
                    st.subheader("Rendered output")
                    st.text_area("Result", value=rendered, height=120, disabled=True, key="tmpl_rendered_out")
                except KeyError as exc:
                    st.error(f"Missing variable: {exc}")

    st.divider()
    st.subheader("All templates")
    for tmpl in templates:
        with st.expander(f"`{tmpl['id']}` v{tmpl.get('version', 1)} — {tmpl.get('description', '')}"):
            st.code(tmpl.get("text", ""), language="text")
            col_del, _ = st.columns([1, 3])
            if col_del.button("🗑️ Delete", key=f"del_tmpl_{tmpl['id']}"):
                reg.remove(tmpl["id"])
                st.success(f"Template `{tmpl['id']}` deleted.")
                st.rerun()

# ── Panel: Config ─────────────────────────────────────────────────────────────

elif panel == "⚙️ Config":
    st.header("⚙️ System Configuration")

    cfg = _get_config_manager()
    if cfg is None:
        st.error("ConfigManager not available.")
        st.stop()

    # Full config dump (masked)
    dump = cfg.dump(mask_secrets=True)
    st.caption("Sensitive values are masked. Changes are saved to `data/config.json`.")

    with st.expander("📄 Full config (masked)", expanded=False):
        st.json(dump)

    st.divider()
    st.subheader("Edit a config key")

    key_input = st.text_input(
        "Dotted key (e.g. `llm.default_model`)",
        key="cfg_key",
    )
    if key_input:
        current = cfg.get(key_input)
        current_str = json.dumps(current) if current is not None else ""
        new_val_str = st.text_input(
            "New value (JSON or plain string)",
            value=current_str,
            key="cfg_val",
        )
        col_set, col_reset = st.columns([1, 1])
        with col_set:
            if st.button("💾 Set & save", key="cfg_set"):
                try:
                    new_val = json.loads(new_val_str)
                except (json.JSONDecodeError, ValueError):
                    new_val = new_val_str
                    st.info("Value interpreted as a plain string (not valid JSON).")
                cfg.set(key_input, new_val)
                cfg.save()
                st.success(f"Key `{key_input}` set to `{new_val}` and saved.")
                st.rerun()
        with col_reset:
            if st.button("↺ Reset to defaults", key="cfg_reset"):
                cfg.reset()
                cfg.save()
                st.success("Config reset to defaults and saved.")
                st.rerun()

# ── Panel: Agent ──────────────────────────────────────────────────────────────

elif panel == "🤖 Agent":
    st.header("🤖 Agent Runner")

    ma = _get_assembly()
    if ma is None:
        st.error("MRL_mother_assembly not available.")
        st.stop()

    goal = st.text_area("Agent goal", height=80, placeholder="e.g. Summarise the MRL system architecture.", key="agent_goal")

    col_run, col_multi = st.columns([1, 1])
    with col_run:
        run_single = st.button("▶ Run single agent", key="agent_run_single")
    with col_multi:
        run_multi = st.button("👥 Run multi-agent (sequential)", key="agent_run_multi")

    if (run_single or run_multi) and goal.strip():
        with st.spinner("Agent thinking…"):
            if run_single:
                result = ma.run_agent(goal.strip())
            else:
                result = ma.run_multi_agent(goal.strip())

        st.subheader("Answer")
        if "answer" in result:
            st.markdown(result["answer"])
        elif "results" in result:
            for i, step in enumerate(result["results"], 1):
                role = step.get("role", f"agent-{i}")
                output = step.get("output", "")
                with st.expander(f"Agent {i}: {role}"):
                    st.markdown(output)
            summary = result.get("summary")
            if summary:
                st.subheader("Summary")
                st.markdown(summary)

        # Trajectory / steps
        steps = result.get("trajectory") or result.get("steps") or []
        if steps:
            st.divider()
            st.subheader("Step trajectory")
            for step in steps:
                step_type = step.get("type", "?")
                content = step.get("content", "")
                icon = _STEP_TYPE_ICONS.get(step_type, "•")
                with st.expander(f"{icon} Step {step.get('step', '?')} — {step_type}"):
                    st.markdown(str(content))
                    if step.get("tool"):
                        st.caption(f"Tool: `{step['tool']}`")
                    if step.get("tool_result"):
                        st.json(step["tool_result"])

        with st.expander("Raw result JSON"):
            st.json(result)

    elif (run_single or run_multi) and not goal.strip():
        st.warning("Please enter an agent goal.")

# ── Panel: Guardrail ──────────────────────────────────────────────────────────

elif panel == "🛡️ Guardrail":
    st.header("🛡️ Guardrail Checker")

    InputGuardrail = _try_import("guardrail", "InputGuardrail")
    OutputGuardrail = _try_import("guardrail", "OutputGuardrail")
    POLICY_STRICT = _try_import("guardrail", "POLICY_STRICT")
    POLICY_STANDARD = _try_import("guardrail", "POLICY_STANDARD")
    POLICY_PERMISSIVE = _try_import("guardrail", "POLICY_PERMISSIVE")

    if InputGuardrail is None or OutputGuardrail is None:
        st.error("guardrail module not available.")
        st.stop()

    policy_map = {
        "standard": POLICY_STANDARD,
        "strict": POLICY_STRICT,
        "permissive": POLICY_PERMISSIVE,
    }

    policy_name = st.selectbox("Policy", options=list(policy_map.keys()), index=0, key="guard_policy")
    policy = policy_map[policy_name]

    tab_in, tab_out = st.tabs(["🔍 Input check", "🔍 Output check"])

    with tab_in:
        in_text = st.text_area("Input text to check", height=120, key="guard_in_text")
        if st.button("✅ Check input", key="guard_check_in"):
            if not in_text.strip():
                st.warning("Enter some text first.")
            else:
                guard = InputGuardrail(policy=policy)
                ok, violations = guard.check(in_text)
                if ok:
                    st.success("✅ Input passed all guardrail checks.")
                else:
                    st.error(f"❌ Input blocked — {len(violations)} violation(s)")
                    for v in violations:
                        st.warning(
                            f"**{v['check']}** [{v['severity']}]: {v['reason']}"
                        )
                with st.expander("Policy details"):
                    st.json(policy)

    with tab_out:
        out_text = st.text_area("Output text to check", height=120, key="guard_out_text")
        if st.button("✅ Check output", key="guard_check_out"):
            if not out_text.strip():
                st.warning("Enter some text first.")
            else:
                guard = OutputGuardrail(policy=policy)
                ok, violations = guard.check(out_text)
                if ok:
                    st.success("✅ Output passed all guardrail checks.")
                else:
                    st.error(f"❌ Output blocked — {len(violations)} violation(s)")
                    for v in violations:
                        st.warning(
                            f"**{v['check']}** [{v['severity']}]: {v['reason']}"
                        )
                with st.expander("Policy details"):
                    st.json(policy)

