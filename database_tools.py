# database_tools.py
import sqlite3
import os
from typing import List, Dict, Any

# Database file path (Meta Ads simulation)
DB_PATH = "meta_ads.db"

def init_database():
    """
    Initialize the database with tables relevant to Meta Ads simulation
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Campaigns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        campaign_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        objective TEXT,
        status TEXT,
        start_date TEXT,
        end_date TEXT
    )
    """)

    # Ad sets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ad_sets (
        ad_set_id INTEGER PRIMARY KEY,
        campaign_id INTEGER,
        name TEXT NOT NULL,
        daily_budget REAL,
        bid_amount REAL,
        targeting TEXT, -- JSON or simple text
        start_date TEXT,
        end_date TEXT,
        status TEXT,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
    )
    """)

    # Ads table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ads (
        ad_id INTEGER PRIMARY KEY,
        ad_set_id INTEGER,
        name TEXT NOT NULL,
        status TEXT,
        creative_text TEXT,
        creative_media TEXT,
        tracking_url TEXT,
        created_time TEXT,
        FOREIGN KEY (ad_set_id) REFERENCES ad_sets(ad_set_id)
    )
    """)

    # Ad metrics per day
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ad_metrics (
        metric_id INTEGER PRIMARY KEY,
        ad_id INTEGER,
        date TEXT NOT NULL,
        impressions INTEGER DEFAULT 0,
        clicks INTEGER DEFAULT 0,
        spend REAL DEFAULT 0.0,
        conversions INTEGER DEFAULT 0,
        ctr REAL,
        cpc REAL,
        cpm REAL,
        FOREIGN KEY (ad_id) REFERENCES ads(ad_id)
    )
    """)

    # Audiences (optional)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audiences (
        audience_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT,
        size INTEGER,
        description TEXT
    )
    """)

    # Insert sample data only if tables are empty
    if cursor.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0] == 0:
        # Insert sample campaigns
        cursor.executemany(
            "INSERT INTO campaigns (name, objective, status, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            [
                ("Spring Sale 2024", "CONVERSIONS", "ACTIVE", "2024-03-01", "2024-04-30"),
                ("Brand Awareness Q2", "BRAND_AWARENESS", "PAUSED", "2024-04-01", "2024-06-30"),
                ("Retargeting - Site Visitors", "CONVERSIONS", "ACTIVE", "2024-02-15", "2024-12-31")
            ]
        )

        # Insert sample ad_sets
        cursor.executemany(
            "INSERT INTO ad_sets (campaign_id, name, daily_budget, bid_amount, targeting, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "Spring - Women 25-34", 50.0, 1.2, '{"age":[25,34],"genders":[1],"interests":["fashion","sale"]}', "2024-03-01", "2024-04-30", "ACTIVE"),
                (1, "Spring - Men 25-44", 40.0, 1.0, '{"age":[25,44],"genders":[2],"interests":["technology","gadgets"]}', "2024-03-01", "2024-04-30", "ACTIVE"),
                (2, "Awareness - Broad", 100.0, None, '{"locations":["US","CA"],"broad":true}', "2024-04-01", "2024-06-30", "PAUSED"),
                (3, "Retargeting - 30d Visitors", 30.0, 0.8, '{"retargeting_window":30}', "2024-02-15", "2024-12-31", "ACTIVE")
            ]
        )

        # Insert sample ads
        cursor.executemany(
            "INSERT INTO ads (ad_set_id, name, status, creative_text, creative_media, tracking_url, created_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "Spring - Carousel 1", "ACTIVE", "New Spring collection — up to 50% off!", "https://cdn.example.com/creative1.jpg", "https://shop.example.com/?utm=ad1", "2024-03-01T08:00:00"),
                (1, "Spring - Video Promo", "ACTIVE", "Watch the new lineup", "https://cdn.example.com/video1.mp4", "https://shop.example.com/?utm=ad2", "2024-03-02T10:30:00"),
                (2, "Tech - Single Image", "ACTIVE", "Latest gadgets at great prices", "https://cdn.example.com/creative2.jpg", "https://shop.example.com/?utm=ad3", "2024-03-05T12:00:00"),
                (3, "Brand - Awareness Banner", "PAUSED", "Discover our brand", "https://cdn.example.com/banner1.jpg", "https://shop.example.com/?utm=ad4", "2024-04-01T09:00:00"),
                (4, "Retarget - Dynamic", "ACTIVE", "We miss you — come back for 10% off", "https://cdn.example.com/dyn1.jpg", "https://shop.example.com/?utm=ad5", "2024-02-20T14:20:00")
            ]
        )

        # Insert sample ad metrics (per-day)
        cursor.executemany(
            "INSERT INTO ad_metrics (ad_id, date, impressions, clicks, spend, conversions, ctr, cpc, cpm) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, "2024-03-01", 12000, 300, 150.25, 12, 0.025, 0.5008, 12.52),
                (1, "2024-03-02", 10000, 250, 130.00, 10, 0.025, 0.52, 13.0),
                (2, "2024-03-02", 8000, 200, 80.00, 8, 0.025, 0.40, 10.0),
                (3, "2024-03-05", 6000, 90, 45.00, 2, 0.015, 0.50, 7.5),
                (4, "2024-04-01", 50000, 400, 300.00, 0, 0.008, 0.75, 6.0),
                (5, "2024-03-10", 4000, 120, 60.00, 6, 0.03, 0.50, 15.0)
            ]
        )

        # Insert sample audiences
        cursor.executemany(
            "INSERT INTO audiences (name, type, size, description) VALUES (?, ?, ?, ?)",
            [
                ("Women 25-34 - Interest: Fashion", "CUSTOM", 120000, "Lookalike & interest based"),
                ("Site Visitors 30d", "RETARGETING", 45000, "People who visited site in last 30 days"),
                ("USA - Broad", "SAVED", 5000000, "Saved audience for broad reach")
            ]
        )

    conn.commit()
    conn.close()

    return "Meta Ads database initialized with sample data."

def execute_sql_query(query: str) -> List[Dict[str, Any]]:
    """
    Execute an SQL query and return the results as a list of dictionaries
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(query)

        # Check if this is a SELECT query
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [{k: row[k] for k in row.keys()} for row in rows]
        else:
            result = [{"affected_rows": cursor.rowcount}]
            conn.commit()

        conn.close()
        return result

    except sqlite3.Error as e:
        return [{"error": str(e)}]

def get_table_schema() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get the schema of all tables in the database
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        schema = {}

        for table in tables:
            table_name = table[0]
            # Skip SQLite internal tables if any
            if table_name.startswith("sqlite_"):
                continue
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "notnull": bool(col[3]),
                    "default": col[4],
                    "pk": bool(col[5])
                }
                for col in columns
            ]

        conn.close()
        return schema

    except sqlite3.Error as e:
        return {"error": str(e)}

# Function to be used as a tool in an agent
def text_to_sql(sql_query: str) -> Dict[str, Any]:
    """
    Execute a SQL query against the database
    """
    if not os.path.exists(DB_PATH):
        init_database()

    try:
        results = execute_sql_query(sql_query)
        return {
            "query": sql_query,
            "results": results
        }
    except Exception as e:
        return {
            "query": sql_query,
            "results": [{"error": str(e)}]
        }

def get_database_info() -> Dict[str, Any]:
    """
    Get information about the database schema and sample data
    """
    if not os.path.exists(DB_PATH):
        init_database()

    schema = get_table_schema()

    sample_data = {}
    for table_name in schema.keys():
        if isinstance(table_name, str):
            try:
                sample_data[table_name] = execute_sql_query(f"SELECT * FROM {table_name} LIMIT 3")
            except:
                sample_data[table_name] = []

    return {
        "schema": schema,
        "sample_data": sample_data
    }

if __name__ == "__main__":
    print(init_database())
    print("Meta Ads database created with sample data.")