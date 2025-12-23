import psycopg2

# Check the current database schema
try:
    conn = psycopg2.connect(
        dbname='assignment',
        user='postgres',
        password='asdf',
        host='localhost',
        port=5555
    )
    cur = conn.cursor()
    
    # Get nodes table structure
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nodes' 
        ORDER BY ordinal_position;
    """)
    print("Current 'nodes' table structure:")
    for col_name, data_type in cur.fetchall():
        print(f"  - {col_name}: {data_type}")
    
    # Get edges table structure
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'edges' 
        ORDER BY ordinal_position;
    """)
    print("\nCurrent 'edges' table structure:")
    for col_name, data_type in cur.fetchall():
        print(f"  - {col_name}: {data_type}")
    
    # Check if metadata table exists
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name = 'metadata';
    """)
    if cur.fetchone():
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'metadata' 
            ORDER BY ordinal_position;
        """)
        print("\nCurrent 'metadata' table structure:")
        for col_name, data_type in cur.fetchall():
            print(f"  - {col_name}: {data_type}")
    else:
        print("\n'metadata' table does NOT exist")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
