import sqlite3
import os

DB_FILE = "sf_permits.db"

def setup_mock_db():
    if os.path.exists(DB_FILE):
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE sf_city_permits (
            location TEXT,
            closure_reason TEXT,
            permit_type TEXT,
            start_date TEXT,
            end_date TEXT
        )
    """)

    # 8 Realistic SF rows as requested
    rows = [
        ("995 Market St", "Emergency Water Main Break", "Emergency Repair", "2026-03-21", "2026-03-22"),
        ("6th & Market", "Permitted Construction Zone - ABC Corp", "Construction", "2026-01-01", "2026-06-01"),
        ("Van Ness & Geary", "Film Permit - City of SF", "Special Event", "2026-03-20", "2026-03-25"),
        ("Embarcadero & Mission", "Farmer's Market Foot Traffic Redo", "City Project", "2026-03-01", "2026-04-01"),
        ("Columbus & Broadway", "North Beach Festival Prep", "Special Event", "2026-03-22", "2026-03-24"),
        ("19th Ave & Winston", "PG&E Gas Line Upgrade", "Utility Work", "2026-03-15", "2026-04-10"),
        ("Valencia & 16th", "Weekend Slow Streets Program", "Street Closure", "2026-03-21", "2026-03-22"),
        ("Lombard & Hyde", "Pothole Deep Repair", "Public Works", "2026-03-21", "2026-03-21")
    ]

    cursor.executemany("""
        INSERT INTO sf_city_permits (location, closure_reason, permit_type, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()
    print(f"[*] Mock BigQuery (SQLite) database initialized with {len(rows)} SF permits.")

def query_permit(location: str) -> dict:
    """
    Queries the mock SF Permits DB for a specific location.
    Returns permit metadata if found, otherwise 'No active permits'.
    """
    # Auto-initialize if it hasn't been created yet
    setup_mock_db()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT closure_reason, permit_type, start_date, end_date 
        FROM sf_city_permits 
        WHERE location = ?
    """, (location,))

    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "closure_reason": row[0],
            "permit_type": row[1],
            "start_date": row[2],
            "end_date": row[3]
        }
    else:
        return {
            "closure_reason": "No active permits"
        }

if __name__ == "__main__":
    setup_mock_db()
    
    print("\n--- Testing EdgeOps Database Simulation ---")
    
    # Positive case
    loc1 = "995 Market St"
    print(f"[{loc1}]:", query_permit(loc1))
    
    # Negative case
    loc2 = "California & Battery"
    print(f"[{loc2}]:", query_permit(loc2))
