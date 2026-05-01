"""
MRL AI System — Streamlit Dashboard
origin_signature: MrLiouWord

Panels
------
  💬 Chat        — multi-turn conversation via api_gateway
  🏥 Health      — MotherAssembly status + MRL_health_monitor
  📊 Metrics     — MRL_metrics telemetry snapshot
  📜 Sessions    — browse and export conversation sessions
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
    ["💬 Chat", "🏥 Health", "📊 Metrics", "📜 Sessions"],
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
