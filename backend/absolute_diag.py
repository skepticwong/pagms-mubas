import sqlite3
import os

LOG_FILE = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\absolute_log.txt'
DB_FILE = r'e:\Post-Award-Grant-Management-System-MUBAS (PAGMS)\pagms-mubas\backend\instance\pagms.db'

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log(f"Starting absolute diagnostic...")
log(f"DB Path: {DB_FILE}")
log(f"DB Exists: {os.path.exists(DB_FILE)}")

try:
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        c.execute("SELECT id, email, role FROM users")
        log("\n--- USERS ---")
        for u in c.fetchall():
            log(f"U: {u}")
            
        c.execute("SELECT id, grant_code, pi_id FROM grants")
        log("\n--- GRANTS ---")
        for g in c.fetchall():
            log(f"G: {g}")
            
        conn.close()
    log("\nDone.")
except Exception as e:
    log(f"\nERROR: {e}")
