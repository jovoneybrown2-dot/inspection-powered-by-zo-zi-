import sqlite3

def add_threshold_table():
    """Add threshold_settings table for chart thresholds"""
    conn = sqlite3.connect('inspections.db')
    c = conn.cursor()

    # Create threshold_settings table
    c.execute('''CREATE TABLE IF NOT EXISTS threshold_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  chart_type TEXT NOT NULL,
                  inspection_type TEXT,
                  threshold_value REAL NOT NULL,
                  enabled INTEGER DEFAULT 1,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  UNIQUE(chart_type, inspection_type))''')

    # Create threshold_alerts table for tracking when thresholds are breached
    c.execute('''CREATE TABLE IF NOT EXISTS threshold_alerts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  inspection_id INTEGER,
                  inspector_name TEXT,
                  form_type TEXT,
                  score REAL,
                  threshold_value REAL,
                  acknowledged INTEGER DEFAULT 0,
                  acknowledged_by TEXT,
                  acknowledged_at TEXT,
                  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (inspection_id) REFERENCES inspections(id))''')

    conn.commit()
    conn.close()
    print("✅ Threshold tables added successfully")

if __name__ == '__main__':
    add_threshold_table()
