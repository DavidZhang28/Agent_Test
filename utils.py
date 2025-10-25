"""
Utilities for Ghost Manager:
- Small database initializer that creates a sqlite file
  (used by DatabaseSessionService if available).
- Session helper functions similar to the example (atomic update, history).
- Display helpers for debugging.
"""

import os
import sqlite3
import time
from datetime import datetime
from typing import Callable, Dict, Any
import asyncio
from google.genai import types

# ANSI color helpers for console output (kept short)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"

def ensure_database(db_path: str):
    """
    Ensure the sqlite database exists and has the minimal schema.
    This schema is intentionally minimal because the ADK's DatabaseSessionService
    may manage sessions itself; this function simply creates a file and a
    sessions table if necessary for testing.
    """
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                app_name TEXT,
                user_id TEXT,
                state TEXT,
                updated_at REAL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

# ---------- Session helpers (compatible with example patterns) ----------
def atomic_update_session(
    session_service,
    app_name: str,
    user_id: str,
    session_id: str,
    patch_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    max_retries: int = 5,
    backoff_factor: float = 0.02,
):
    """
    Merge-safe session state updater that retries on transient exceptions.
    Uses the session_service.get_session and create_session APIs.
    """
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
            latest_state = dict(session.state) if isinstance(session.state, dict) else {}
            new_state = patch_fn(dict(latest_state))
            if not isinstance(new_state, dict):
                raise ValueError("patch_fn must return dict")
            session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id, state=new_state)
            return
        except Exception as exc:
            last_exception = exc
            time.sleep(backoff_factor * attempt)
    raise RuntimeError(f"atomic_update_session failed after {max_retries} attempts: {last_exception}")

def update_interaction_history(session_service, app_name, user_id, session_id, entry: Dict[str, Any]):
    if "timestamp" not in entry:
        entry = dict(entry)
        entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _entry_id(e):
        if not isinstance(e, dict):
            return str(e)
        return f"{e.get('action','')}|{e.get('timestamp','')}|{e.get('query', e.get('course_id', ''))}"

    def patch_fn(latest_state):
        latest_history = list(latest_state.get("interaction_history", []))
        existing_ids = {_entry_id(e) for e in latest_history if isinstance(e, dict)}
        new_id = _entry_id(entry)
        if new_id not in existing_ids:
            latest_history.append(entry)
        latest_state["interaction_history"] = latest_history
        return latest_state

    atomic_update_session(session_service, app_name, user_id, session_id, patch_fn)

def add_user_query_to_history(session_service, app_name, user_id, session_id, query: str):
    update_interaction_history(session_service, app_name, user_id, session_id, {"action":"user_query","query":query})

def add_agent_response_to_history(session_service, app_name, user_id, session_id, agent_name, response: str):
    update_interaction_history(session_service, app_name, user_id, session_id, {"action":"agent_response","agent":agent_name,"response":response})

def display_state(session_service, app_name, user_id, session_id, label="Current State"):
    """
    Print session contents in a friendly format. Uses session_service.get_session.
    """
    print(f"\n{'-'*10} {label} {'-'*10}")
    try:
        session = session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        state = session.state or {}
        print(f"User: {state.get('user_name','Unknown')}")
        #purchases = state.get("purchased_courses", [])
        #print(f"Purchased courses: {len(purchases)}")
        history = state.get("interaction_history", [])
        print(f"Interaction history entries: {len(history)}")
        alerts = state.get("alerts", [])
        print(f"Alerts: {len(alerts)}")
    except Exception as e:
        print(f"{Colors.RED}Error fetching state: {e}{Colors.RESET}")
    print("-"* (22 + len(label)))


async def process_agent_response(event):
    """Process and display streaming agent responses."""
    print(f"Event ID: {event.id}, Author: {event.author}")

    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    final_response = None
    if event.is_final_response() and event.content and event.content.parts:
        final_part = event.content.parts[0]
        if hasattr(final_part, "text"):
            final_response = final_part.text.strip()
            print("\n═══════════════════════════════════════════════════════════════")
            print(f"🧠 FINAL AGENT RESPONSE:\n{final_response}")
            print("═══════════════════════════════════════════════════════════════\n")
    return final_response


async def call_agent_async(runner, user_id, session_id, query):
    """Run the coordinator agent asynchronously with user query input."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(f"\n🟢 Running Query: {query}\n")

    # Display state before query
    display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        label="State BEFORE processing",
    )

    final_response_text = None
    agent_name = None

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.author:
                agent_name = event.author
            response = await process_agent_response(event)
            if response:
                final_response_text = response
    except Exception as e:
        print(f"❌ ERROR during agent run: {e}")

    # Add response to session state
    if final_response_text and agent_name:
        add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text,
        )

    # Display state after query
    display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        label="State AFTER processing",
    )

    print("\n-------------------------------------------------------------\n")
    return final_response_text