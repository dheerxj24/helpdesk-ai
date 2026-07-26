"""
Seeds the DB with sample KB articles so you have demo data for RAG testing.
Run once: python seed_kb.py
"""

from app.database import SessionLocal, init_db
from app.models import KBArticle

SAMPLE_ARTICLES = [
    {
        "title": "VPN Not Connecting",
        "content": "If VPN fails to connect: 1) Check internet connectivity. "
                    "2) Restart the VPN client. 3) Verify credentials haven't "
                    "expired. 4) Clear VPN cache in settings. 5) If on Windows, "
                    "check that the VPN adapter is enabled in Network Adapters.",
        "category": "Network",
        "tags": ["vpn", "network", "connectivity"],
    },
    {
        "title": "Password Reset Request",
        "content": "To reset your password: go to the self-service portal at "
                    "password.company.com, enter your employee ID, and follow "
                    "the OTP verification sent to your registered email. "
                    "Password must be 12+ characters with 1 number and 1 symbol.",
        "category": "Access",
        "tags": ["password", "login", "account"],
    },
    {
        "title": "Printer Offline / Not Responding",
        "content": "For offline printer issues: 1) Check printer is powered on "
                    "and connected to network. 2) Restart the print spooler "
                    "service. 3) Remove and re-add the printer in Devices settings. "
                    "4) Update printer drivers if available.",
        "category": "Hardware",
        "tags": ["printer", "hardware", "office"],
    },
    {
        "title": "Outlook Not Syncing Emails",
        "content": "If Outlook stops syncing: 1) Check internet connection. "
                    "2) Verify mailbox isn't over storage quota. 3) Repair the "
                    "Outlook profile via Control Panel > Mail. 4) Recreate the "
                    "Outlook profile if repair doesn't work.",
        "category": "Email",
        "tags": ["outlook", "email", "sync"],
    },
    {
        "title": "Software Installation Access Denied",
        "content": "Standard user accounts don't have admin rights to install "
                    "software. Submit a software request via the IT portal with "
                    "business justification, or request temporary admin access "
                    "through your manager's approval.",
        "category": "Software",
        "tags": ["installation", "permissions", "admin"],
    },
    {
        "title": "Laptop Running Slow",
        "content": "For slow performance: 1) Check Task Manager for high CPU/RAM "
                    "usage processes. 2) Clear temp files and browser cache. "
                    "3) Run disk cleanup. 4) Check for pending Windows updates. "
                    "5) If issue persists, may need a RAM upgrade or SSD check.",
        "category": "Hardware",
        "tags": ["performance", "laptop", "slow"],
    },
    {
        "title": "Cannot Access Shared Drive",
        "content": "If shared drive access fails: 1) Confirm you're connected "
                    "to VPN if working remotely. 2) Verify you have permissions "
                    "granted by the drive owner. 3) Try mapping the drive again "
                    "using \\\\server\\sharename. 4) Contact drive owner for "
                    "access approval if newly assigned.",
        "category": "Access",
        "tags": ["shared drive", "permissions", "network"],
    },
    {
        "title": "Microsoft Teams Audio/Video Not Working",
        "content": "For Teams call issues: 1) Check mic/camera permissions in "
                    "system settings. 2) Verify correct device is selected in "
                    "Teams settings > Devices. 3) Restart Teams. 4) Update audio "
                    "drivers. 5) Test mic/camera in another app to isolate the issue.",
        "category": "Software",
        "tags": ["teams", "audio", "video", "calls"],
    },
]


def run():
    init_db()
    db = SessionLocal()
    try:
        existing = db.query(KBArticle).count()
        if existing > 0:
            print(f"KB already has {existing} articles. Skipping seed.")
            return
        for item in SAMPLE_ARTICLES:
            db.add(KBArticle(**item))
        db.commit()
        print(f"Seeded {len(SAMPLE_ARTICLES)} KB articles.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
