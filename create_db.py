import sqlite3

def create_db():
    conn = sqlite3.connect("pricing.db")
    cursor = conn.cursor()
    
    # 1. Services Table (Existing)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            name TEXT PRIMARY KEY,
            hourly_rate INTEGER,
            description TEXT
        )
    """)
    
    # 2. Leads Table (NEW)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            service_interested TEXT,
            priority_score INTEGER,
            status TEXT
        )
    """)
    
    # Seed Data
    services = [
        ("Cloud Migration", 200, "Moving on-premise servers to AWS/Azure"),
        ("security_audit", 150, "Full vulnerability scan and report"),
        ("ai_consulting", 300, "implementation of RAG and LLM agents"),
        ("devops_pipeline", 120, "CI/CD setup with GitHub Actions")
    ]
    cursor.executemany("INSERT OR REPLACE INTO services VALUES (?, ?, ?)", services)
    
    conn.commit()
    conn.close()
    print("✅ Database updated with 'leads' table.")

if __name__ == "__main__":
    create_db()