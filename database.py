import sqlite3

conn = sqlite3.connect("threadsparkle.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    product_name TEXT,
    price TEXT,
    size TEXT,
    thread_color TEXT,
    instructions TEXT,
    payment TEXT,
    image TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database Created")