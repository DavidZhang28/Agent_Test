"""
Entry point and test harness for Ghost Manager.

Creates (or reuses) a SQLite-backed session store, creates a Runner
for the top-level coordinator agent, and lets you run a simple query
to test the pipeline end-to-end.

This harness demonstrates:
- Session creation and management
- Running the coordinator agent asynchronously
- Printing the structured summary produced by the coordinator
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService

from utils import (
   ensure_database,
   add_user_query_to_history,
   call_agent_async,
   display_state,
)

from agents import coordinator_agent

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "ghost_manager.db")
INPUT_DATA_PATH = os.path.join(os.path.dirname(__file__), "input_data.txt")

async def main_async():
   # Ensure DB file exists (utils will initialize schema if necessary)
   ensure_database(DB_PATH)

   # Use DatabaseSessionService if available; fallback to InMemorySessionService
   try:
       session_service = DatabaseSessionService(db_path=DB_PATH)
   except Exception:
       # graceful fallback (useful for environments without DB impl)
       session_service = InMemorySessionService()

   APP_NAME = "GhostManager"
   USER_ID = "demo_user"
   initial_state = {
       "user_name": "Demo User",
       "interaction_history": [],
       "alerts": [],
       # any stateful metadata your agents may add
   }

   # create session
   new_session = session_service.create_session(
       app_name=APP_NAME, user_id=USER_ID, state=initial_state
   )
   session_id = new_session.id
   print(f"Created session {session_id} (app={APP_NAME}, user={USER_ID})\n")

   # Build runner using the coordinator agent
   runner = Runner(agent=coordinator_agent, app_name=APP_NAME, session_service=session_service)
  
   # Read test query from input_data.txt
   try:
       with open(INPUT_DATA_PATH, 'r', encoding='utf-8') as f:
           test_query = f.read().strip()
   except FileNotFoundError:
       # Fallback to default query if file doesn't exist
       test_query = "Scan the recent user actions for HIPAA/FDA risks and report high-level results."
       print(f"Warning: {INPUT_DATA_PATH} not found. Using default query.\n")
   
   add_user_query_to_history(session_service, APP_NAME, USER_ID, session_id, test_query)

   # Call agent and print final response
   final = await call_agent_async(runner, USER_ID, session_id, test_query)

   print("\n=== FINAL STRUCTURED RESPONSE ===")
   if final:
       print(final)
   else:
       print("No final response produced by the coordinator agent.")

   # Show final persisted state for inspection
   display_state(session_service, APP_NAME, USER_ID, session_id, label="Final State")

def main():
   asyncio.run(main_async())

if __name__ == "__main__":
   main()