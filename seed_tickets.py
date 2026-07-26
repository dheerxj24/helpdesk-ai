"""
Seeds realistic demo tickets by calling the running API (not direct DB
insert) -- this way every ticket goes through the FULL pipeline (classify,
RAG retrieval, resolution synthesis, confidence scoring, routing) exactly
like a real ticket would, so /analytics/summary and /analytics/confidence-dist
show a realistic, demo-ready spread across auto_resolved / suggested / escalated.

Usage:
  1. Make sure the server is already running: uvicorn app.main:app --reload
  2. In a SEPARATE terminal, run: python seed_tickets.py

Takes a minute or two since each ticket makes real Groq API calls.
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000"

# Mix of tickets designed to hit all three routing outcomes:
# - close matches to KB articles -> likely auto_resolve or suggest
# - vague/unrelated issues -> likely escalate
DEMO_TICKETS = [
    # Should closely match KB articles -> auto_resolve / suggest
    {"subject": "Can't connect to VPN", "description": "VPN client shows connection timeout error every time I try to connect from home."},
    {"subject": "Forgot password", "description": "I'm locked out of my account, need to reset my password urgently."},
    {"subject": "Printer says offline", "description": "The office printer on the 3rd floor shows offline and won't print anything."},
    {"subject": "Outlook stopped syncing", "description": "My Outlook hasn't received new emails since this morning, sync seems stuck."},
    {"subject": "Can't install new software", "description": "Trying to install a design tool but getting access denied, I don't have admin rights."},
    {"subject": "Laptop very slow today", "description": "My laptop has been extremely slow since this morning, apps take forever to open."},
    {"subject": "Shared drive not accessible", "description": "I can't open the shared team drive, says access denied even though I had access yesterday."},
    {"subject": "Teams camera not working", "description": "My camera isn't showing up in Teams calls, tried multiple meetings today."},
    {"subject": "VPN drops randomly", "description": "VPN connection keeps dropping every 10 minutes while working remotely."},
    {"subject": "Need password reset for email", "description": "Forgot my email password and the reset link isn't arriving."},

    # Vague / unrelated to KB -> likely escalate
    {"subject": "Laptop screen flickering", "description": "My laptop screen has started flickering randomly, sometimes goes black for a second."},
    {"subject": "Reimbursement not credited", "description": "I submitted a travel reimbursement claim two weeks ago and haven't received the amount yet."},
    {"subject": "New employee onboarding access", "description": "New joinee hasn't received their system access and email account yet, joining tomorrow."},
    {"subject": "Conference room booking system down", "description": "The room booking tool is showing an error page since yesterday, can't book any meeting rooms."},
    {"subject": "Suspicious email received", "description": "Got an email asking to verify my bank details, looks like phishing, not sure what to do."},
]


def main():
    print(f"Seeding {len(DEMO_TICKETS)} demo tickets via {BASE_URL}/tickets ...\n")
    for i, ticket in enumerate(DEMO_TICKETS, 1):
        try:
            resp = requests.post(f"{BASE_URL}/tickets", json=ticket, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                print(
                    f"[{i}/{len(DEMO_TICKETS)}] '{ticket['subject']}' "
                    f"-> status={data['status']} confidence={data['confidence_score']}"
                )
            else:
                print(f"[{i}/{len(DEMO_TICKETS)}] FAILED ({resp.status_code}): {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"[{i}/{len(DEMO_TICKETS)}] ERROR: {e}")
        time.sleep(1)  # small delay to be gentle on the free-tier rate limit

    print("\nDone. Check /analytics/summary and /analytics/confidence-dist now.")


if __name__ == "__main__":
    main()
