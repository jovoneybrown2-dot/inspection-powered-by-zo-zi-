import psycopg2
import psycopg2.extras
def update_database():
    conn = get_connection()
    c = conn.cursor()
    c.execute("ALTER TABLE residential_inspections ADD COLUMN received_by TEXT")
    c.execute("UPDATE residential_inspections SET received_by = 'N/A' WHERE received_by IS NULL")
    conn.commit()
    conn.close()

update_database()