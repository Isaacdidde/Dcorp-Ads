"""
Database Backup Script

Creates a timestamped MongoDB backup using `mongodump`.

Requirements:
    - MongoDB tools installed (mongodump)
    - MONGO_URI in .env

Run:
    python scripts/backup_db.py
"""

import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
BACKUP_DIR = os.path.join(os.getcwd(), "backups")


def ensure_backup_folder():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"[OK] Created backup folder → {BACKUP_DIR}")


def run_backup():
    if not MONGO_URI:
        print("[ERROR] MONGO_URI not found in environment variables.")
        return

    ensure_backup_folder()

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")

    print(f"[INFO] Starting backup: {out_path}")

    try:
        # Build mongodump command
        cmd = [
            "mongodump",
            f"--uri={MONGO_URI}",
            f"--out={out_path}"
        ]

        # Execute backup
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"[SUCCESS] Backup completed → {out_path}")
        else:
            print("[ERROR] Backup failed")
            print(result.stderr)

    except FileNotFoundError:
        print("[ERROR] `mongodump` not found.")
        print("Install MongoDB Database Tools and ensure it's in your PATH:")
        print("https://www.mongodb.com/try/download/database-tools")


if __name__ == "__main__":
    run_backup()
