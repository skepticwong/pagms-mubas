import sqlite3
import os

LOG_FILE = 'diag_log.txt'

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')
    print(msg)

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log("Starting diagnostic...")

db_path = 'instance/pagms.db'
log(f"DB Path: {os.path.abspath(db_path)}")
log(f"DB Exists: {os.path.exists(db_path)}")

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    log("\n--- USERS ---")
    c.execute("SELECT id, name, email, role FROM users")
    for u in c.fetchall():
        log(f"USER: {u}")
        
    log("\n--- GRANTS ---")
    c.execute("SELECT id, grant_code, title, pi_id FROM grants")
    for g in c.fetchall():
        log(f"GRANT: {g}")
        
    log("\n--- GRANT TEAM ---")
    c.execute("SELECT grant_id, user_id, role FROM grant_team")
    for t in c.fetchall():
        log(f"TEAM: {t}")
        
    conn.close()
    log("\nDiagnostic complete successfully.")
except Exception as e:
    log(f"\nERROR: {e}")
