#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_agent.py — Multi-Agent Orchestrator (AutoGen-style Group Chat)
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Goal: product-level local multi-agent orchestration — zero external
      dependencies, pure Python stdlib only.

Concepts
--------
Agent
    A named participant with a system prompt, an optional tool registry,
    and an attached LLMGateway.  Agents produce responses given a message
    list (their "view" of the conversation so far).

HumanProxyAgent
    Special agent that blocks on stdin (or raises HumanInputRequired) when
    the conversation requires a human decision — enforcing the MRL
    REQUIRE_HUMAN policy.

GroupChat
    A shared message bus.  Manages speaker selection (round-robin or
    auto/LLM-driven) and the turn loop.

GroupChatManager
    Runs the GroupChat loop up to max_turns; emits a structured transcript.

Message format
--------------
    {
      "turn":             int,
      "from_agent":       str,
      "to_agent":         str | "all",
      "role":             "user" | "assistant" | "system",
      "content":          str,
      "ts_ms":            int,
      "origin_signature": "MrLiouWord",
    }

Usage (library)
---------------
    from llm_gateway import LLMGateway
    from multi_agent import Agent, HumanProxyAgent, GroupChat, GroupChatManager

    gw = LLMGateway()   # auto-detects local backend

    planner = Agent("Planner", gw,
                    system_prompt="You decompose tasks into steps.")
    executor = Agent("Executor", gw,
                     system_prompt="You execute one step at a time.")
    human   = HumanProxyAgent("Human")

    gc = GroupChat([planner, executor, human], max_turns=6)
    mgr = GroupChatManager(gc)

    transcript = mgr.run("Build a local file index of the repo.")
    for msg in transcript["messages"]:
        print(f"[{msg['from_agent']}] {msg['content'][:80]}")

CLI
---
    python 09_workflow/multi_agent.py demo
    python 09_workflow/multi_agent.py run --goal "Summarise this repo" --agents Planner,Executor
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
MULTI_AGENT_VERSION = "1.0"

# ─── Exceptions ───────────────────────────────────────────────────────────────

class HumanInputRequired(Exception):
    """Raised when a HumanProxyAgent needs interactive input but none is available."""


# ─── Message helpers ──────────────────────────────────────────────────────────

def _make_msg(
    turn: int,
    from_agent: str,
    to_agent: str,
    role: str,
    content: str,
) -> Dict[str, Any]:
    return {
        "turn":             turn,
        "from_agent":       from_agent,
        "to_agent":         to_agent,
        "role":             role,
        "content":          content,
        "ts_ms":            int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── Agent ────────────────────────────────────────────────────────────────────

class Agent:
    """
    A named participant in a group chat backed by a local LLMGateway.

    Parameters
    ----------
    name : str
        Unique agent identifier within the group.
    gateway : any
        LLMGateway instance (or None → stub replies).
    system_prompt : str
        System-level instruction for this agent.
    max_tokens : int
        Per-reply token budget.
    temperature : float
    """

    def __init__(
        self,
        name: str,
        gateway: Any = None,
        *,
        system_prompt: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> None:
        self.name = name
        self._gateway = gateway
        self._system_prompt = system_prompt or f"You are {name}, a helpful AI agent."
        self._max_tokens = max_tokens
        self._temperature = temperature
        self.is_human = False

    def reply(
        self,
        history: List[Dict[str, Any]],
        *,
        sender: str = "user",
    ) -> str:
        """
        Produce a reply given the shared message history.

        The history is converted to an LLM-compatible message list:
        system prompt first, then the conversation chronologically.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._system_prompt}
        ]
        for msg in history:
            # Map to standard roles understood by LLMs
            role = msg.get("role", "user")
            if role not in ("system", "user", "assistant"):
                role = "user"
            messages.append({"role": role, "content": msg["content"]})

        if self._gateway is not None:
            resp = self._gateway.chat(
                messages,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
            return resp.get("text", "")

        # No gateway — minimal stub
        last = history[-1]["content"][:80] if history else ""
        return f"[{self.name} stub] Received: {last!r}"

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r})"


# ─── HumanProxyAgent ──────────────────────────────────────────────────────────

class HumanProxyAgent:
    """
    A human participant.  When interactive=True (default), blocks on stdin.
    When interactive=False, raises HumanInputRequired (useful in CI / tests).

    MRL policy: REQUIRE_HUMAN decisions must flow through this agent so they
    are visible in the transcript and can be traced to the Merkle chain.
    """

    def __init__(
        self,
        name: str = "Human",
        *,
        interactive: bool = True,
        auto_reply: Optional[str] = None,
    ) -> None:
        self.name = name
        self._interactive = interactive
        self._auto_reply = auto_reply
        self.is_human = True

    def reply(
        self,
        history: List[Dict[str, Any]],
        *,
        sender: str = "user",
    ) -> str:
        if self._auto_reply is not None:
            return self._auto_reply

        if not self._interactive:
            last = history[-1]["content"][:120] if history else ""
            raise HumanInputRequired(
                f"Human input required — last message: {last!r}"
            )

        # Interactive: prompt on stdin
        last_content = history[-1]["content"] if history else ""
        print(f"\n[{sender} → {self.name}] {last_content}")
        try:
            response = input(f"[{self.name}] Your reply: ").strip()
        except EOFError:
            response = "[Human: no input available]"
        return response

    def __repr__(self) -> str:
        return f"HumanProxyAgent(name={self.name!r})"


# ─── GroupChat ────────────────────────────────────────────────────────────────

SpeakerFn = Callable[[List[Dict[str, Any]], List[Any]], Any]


def _round_robin(
    history: List[Dict[str, Any]],
    agents: List[Any],
) -> Any:
    """Default speaker selector: cycle through non-human agents."""
    non_human = [a for a in agents if not getattr(a, "is_human", False)]
    if not non_human:
        return agents[0]
    last_speaker = history[-1].get("from_agent", "") if history else ""
    idx = next(
        (i for i, a in enumerate(non_human) if a.name == last_speaker),
        -1,
    )
    return non_human[(idx + 1) % len(non_human)]


class GroupChat:
    """
    Shared message bus for a multi-agent conversation.

    Parameters
    ----------
    agents : list
        Mix of Agent and HumanProxyAgent instances.
    max_turns : int
        Hard upper bound on the total number of turns.
    speaker_fn : callable | None
        ``(history, agents) -> agent`` — custom speaker selection.
        Default = round-robin over non-human agents.
    """

    def __init__(
        self,
        agents: List[Any],
        max_turns: int = 10,
        speaker_fn: Optional[SpeakerFn] = None,
    ) -> None:
        if not agents:
            raise ValueError("GroupChat: agents list must not be empty")
        self.agents = agents
        self.max_turns = max_turns
        self._speaker_fn = speaker_fn or _round_robin
        self._messages: List[Dict[str, Any]] = []
        self._turn = 0
        self._agent_map: Dict[str, Any] = {a.name: a for a in agents}

    def agent(self, name: str) -> Any:
        return self._agent_map.get(name)

    def messages(self) -> List[Dict[str, Any]]:
        return list(self._messages)

    def inject(self, from_agent: str, content: str, role: str = "user") -> None:
        """Inject an initial message into the chat (e.g., the task description)."""
        msg = _make_msg(self._turn, from_agent, "all", role, content)
        self._messages.append(msg)

    def next_speaker(self) -> Any:
        return self._speaker_fn(self._messages, self.agents)

    def step(self) -> Optional[Dict[str, Any]]:
        """Execute one turn.  Returns the new message or None if max_turns reached."""
        if self._turn >= self.max_turns:
            return None

        speaker = self.next_speaker()
        prev_speaker = (
            self._messages[-1].get("from_agent", "") if self._messages else ""
        )

        try:
            content = speaker.reply(self._messages, sender=prev_speaker)
        except HumanInputRequired:
            raise
        except Exception as exc:
            content = f"[{speaker.name} error: {exc}]"

        role = "user" if getattr(speaker, "is_human", False) else "assistant"
        msg = _make_msg(self._turn, speaker.name, "all", role, content)
        self._messages.append(msg)
        self._turn += 1
        return msg


# ─── GroupChatManager ─────────────────────────────────────────────────────────

class GroupChatManager:
    """
    Runs a GroupChat for up to max_turns, collecting the transcript.

    Parameters
    ----------
    group_chat : GroupChat
    terminate_fn : callable | None
        ``(messages) -> bool`` — return True to stop early.
        Default = stop when the last message contains "TERMINATE".
    """

    def __init__(
        self,
        group_chat: GroupChat,
        terminate_fn: Optional[Callable[[List[Dict[str, Any]]], bool]] = None,
    ) -> None:
        self._gc = group_chat
        self._terminate_fn = terminate_fn or self._default_terminate

    @staticmethod
    def _default_terminate(messages: List[Dict[str, Any]]) -> bool:
        if not messages:
            return False
        last = messages[-1].get("content", "")
        return "TERMINATE" in last.upper()

    def run(
        self,
        task: str,
        *,
        initiator: str = "Human",
    ) -> Dict[str, Any]:
        """
        Run the group chat for *task*.

        Returns
        -------
        {
          "task":             str,
          "total_turns":      int,
          "terminated_early": bool,
          "messages":         [msg, ...],
          "started_at_ms":    int,
          "ended_at_ms":      int,
          "origin_signature": "MrLiouWord",
        }
        """
        started = int(time.time() * 1000)

        # Seed the conversation with the task
        self._gc.inject(initiator, task, role="user")

        terminated_early = False

        for _ in range(self._gc.max_turns):
            msg = self._gc.step()
            if msg is None:
                break
            if self._terminate_fn(self._gc.messages()):
                terminated_early = True
                break

        return {
            "task":             task,
            "total_turns":      self._gc._turn,
            "terminated_early": terminated_early,
            "messages":         self._gc.messages(),
            "started_at_ms":    started,
            "ended_at_ms":      int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── CLI demo ─────────────────────────────────────────────────────────────────

def _demo() -> None:
    """Two-agent stub demo (no LLM required)."""

    planner = Agent(
        "Planner",
        gateway=None,
        system_prompt="You break tasks into numbered steps.",
    )
    executor = Agent(
        "Executor",
        gateway=None,
        system_prompt="You confirm steps are done and report results.",
    )
    human = HumanProxyAgent("Human", interactive=False, auto_reply="Looks good. TERMINATE")

    gc = GroupChat([planner, executor, human], max_turns=6)
    mgr = GroupChatManager(gc)

    transcript = mgr.run("Index all Python files in the repository.")

    print(json.dumps(transcript, ensure_ascii=False, indent=2, default=str))


def _cmd_demo(_args: argparse.Namespace) -> None:
    _demo()


def _cmd_run(args: argparse.Namespace) -> None:
    """Run a minimal stub group chat from the CLI."""
    names = [n.strip() for n in (args.agents or "Planner,Executor").split(",")]
    agents = [Agent(n, gateway=None) for n in names]
    agents.append(HumanProxyAgent("Human", interactive=False, auto_reply="TERMINATE"))

    gc = GroupChat(agents, max_turns=args.max_turns)
    mgr = GroupChatManager(gc)
    result = mgr.run(args.goal)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MultiAgent — group-chat orchestrator")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Run the built-in two-agent stub demo")

    r = sub.add_parser("run", help="Run a group chat with named stub agents")
    r.add_argument("--goal",       required=True, help="Task description")
    r.add_argument("--agents",     default="Planner,Executor",
                   help="Comma-separated agent names (all stub)")
    r.add_argument("--max-turns",  type=int, default=6, dest="max_turns")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"demo": _cmd_demo, "run": _cmd_run}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
