import sys
from mcp.server.fastmcp import FastMCP
import sqlite3
import random

# Initialize Server
mcp = FastMCP("TitanFlow Tools")
DB_FILE = "pricing.db"

# --- EXISTING READ TOOLS ---
def query_db(service_name: str):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, hourly_rate, description FROM services WHERE name LIKE ?", (f"%{service_name}%",))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception:
        return None

@mcp.tool()
def get_service_price(service_name: str) -> str:
    """Check if a service exists in the database and get its price."""
    data = query_db(service_name)
    if data:
        return f"Service: {data[0]}, Rate: ${data[1]}/hr, Scope: {data[2]}"
    else:
        return "Service not found. Available: Cloud Migration, security_audit, ai_consulting."

@mcp.tool()
def calculate_lead_score(client_name: str, industry: str) -> str:
    """Calculates a VIP score (0-100)."""
    score = 50
    if "tech" in industry.lower() or "ai" in industry.lower(): score += 30
    if len(client_name) > 3: score += 10
    final_score = min(score + random.randint(0, 10), 100)
    
    return f"{final_score}" # Return just the number as a string for easier parsing

# --- NEW WRITE TOOL (ACTION) ---
@mcp.tool()
def save_qualified_lead(client_name: str, service: str, score: int) -> str:
    """
    Saves a qualified lead into the internal CRM database.
    ONLY call this if the lead is 'Approved'.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO leads (client_name, service_interested, priority_score, status) VALUES (?, ?, ?, ?)",
            (client_name, service, score, "NEW")
        )
        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return f"Success: Lead saved to CRM with ID #{lead_id}"
    except Exception as e:
        return f"Error saving lead: {str(e)}"

if __name__ == "__main__":
    mcp.run()