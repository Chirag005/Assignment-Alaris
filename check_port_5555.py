import psycopg2
from psycopg2 import extras
from datetime import datetime

print("="*70)
print("PORT 5555 - POSTGRESQL DATABASE DIAGNOSTIC")
print("="*70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Configuration
PORT = 5555
DB_USER = "postgres"
DB_PASSWORD = "asdf"
DB_HOST = "localhost"
DB_NAME = "assignment"

print("STEP 1: Testing Connection to Port 5555")
print("-"*70)

try:
    print(f"[1.1] Connecting to postgres database on port {PORT}...")
    conn_test = psycopg2.connect(
        dbname='postgres',
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=PORT,
        connect_timeout=3
    )
    print(f"  SUCCESS - PostgreSQL is running on port {PORT}")
    
    cur = conn_test.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"  Version: {version.split(',')[0]}")
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
    if cur.fetchone():
        print(f"  Database '{DB_NAME}' EXISTS on this port")
    else:
        print(f"  Database '{DB_NAME}' NOT FOUND")
    
    cur.close()
    conn_test.close()
    print("[1.2] Test connection closed\n")
    
except Exception as e:
    print(f"  ERROR: {e}\n")
    exit(1)

print("STEP 2: Connecting to 'assignment' Database")
print("-"*70)

try:
    print(f"[2.1] Opening connection...")
    print(f"  Host: {DB_HOST}")
    print(f"  Port: {PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")
    
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=PORT
    )
    print("  SUCCESS - Connected to database\n")
    
    cur = conn.cursor(cursor_factory=extras.RealDictCursor)
    
    print("STEP 3: Database Schema")
    print("-"*70)
    
    print("[3.1] Listing tables...")
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name;
    """)
    tables = [row['table_name'] for row in cur.fetchall()]
    print(f"  Tables found: {', '.join(tables)}\n")
    
    print("[3.2] Nodes table structure:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nodes' 
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"  - {row['column_name']}: {row['data_type']}")
    
    print("\n[3.3] Edges table structure:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'edges' 
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"  - {row['column_name']}: {row['data_type']}")
    
    print("\nSTEP 4: Data Statistics")
    print("-"*70)
    
    print("[4.1] Node counts:")
    cur.execute("SELECT COUNT(*) as count FROM nodes;")
    total_nodes = cur.fetchone()['count']
    print(f"  Total nodes: {total_nodes}")
    
    cur.execute("SELECT type, COUNT(*) as count FROM nodes GROUP BY type ORDER BY count DESC;")
    for row in cur.fetchall():
        pct = (row['count'] / total_nodes * 100)
        print(f"    {row['type']}: {row['count']} ({pct:.1f}%)")
    
    print("\n[4.2] Edge counts:")
    cur.execute("SELECT COUNT(*) as count FROM edges;")
    total_edges = cur.fetchone()['count']
    print(f"  Total edges: {total_edges}")
    
    cur.execute("SELECT type, COUNT(*) as count FROM edges GROUP BY type ORDER BY count DESC;")
    for row in cur.fetchall():
        pct = (row['count'] / total_edges * 100)
        print(f"    {row['type']}: {row['count']} ({pct:.1f}%)")
    
    print("\nSTEP 5: Sample Data")
    print("-"*70)
    
    print("[5.1] Sample Papers (3 examples):")
    cur.execute("""
        SELECT id, properties FROM nodes 
        WHERE type = 'Paper' LIMIT 3;
    """)
    for i, row in enumerate(cur.fetchall(), 1):
        p = row['properties']
        print(f"\n  Paper {i} (ID: {row['id']}):")
        print(f"    Title: {p.get('title', 'N/A')}")
        print(f"    Year: {p.get('year', 'N/A')}")
        print(f"    Citations: {p.get('citation_count', 0)}")
    
    print("\n[5.2] Sample Methods (5 examples):")
    cur.execute("SELECT id, properties FROM nodes WHERE type = 'Method' LIMIT 5;")
    for i, row in enumerate(cur.fetchall(), 1):
        name = row['properties'].get('name', 'Unknown')
        print(f"  {i}. {name} (ID: {row['id']})")
    
    print("\n[5.3] Sample Relationships (3 examples):")
    cur.execute("""
        SELECT e.id, e.type, e.source_id, e.target_id,
               n1.type as src_type, n2.type as tgt_type
        FROM edges e
        JOIN nodes n1 ON e.source_id = n1.id
        JOIN nodes n2 ON e.target_id = n2.id
        LIMIT 3;
    """)
    for i, row in enumerate(cur.fetchall(), 1):
        print(f"  {i}. Node {row['source_id']} ({row['src_type']}) --[{row['type']}]--> Node {row['target_id']} ({row['tgt_type']})")
    
    print("\nSTEP 6: Connection Statistics")
    print("-"*70)
    
    cur.execute("SELECT COUNT(DISTINCT source_id) as c FROM edges;")
    nodes_out = cur.fetchone()['c']
    
    cur.execute("SELECT COUNT(DISTINCT target_id) as c FROM edges;")
    nodes_in = cur.fetchone()['c']
    
    cur.execute("""
        SELECT AVG(cnt::numeric) as avg 
        FROM (SELECT COUNT(*) as cnt FROM edges GROUP BY source_id) s;
    """)
    avg_edges = cur.fetchone()['avg']
    
    print(f"  Nodes with outgoing edges: {nodes_out}")
    print(f"  Nodes with incoming edges: {nodes_in}")
    print(f"  Average edges per source: {float(avg_edges):.2f}")
    
    print("\nSTEP 7: Cleanup")
    print("-"*70)
    cur.close()
    print("  Cursor closed")
    conn.close()
    print("  Connection closed")
    
    print("\n" + "="*70)
    print("DIAGNOSTIC COMPLETE")
    print("="*70)
    print(f"\nSUMMARY:")
    print(f"  Port: {PORT}")
    print(f"  Database: {DB_NAME}")
    print(f"  Status: CONNECTED and OPERATIONAL")
    print(f"  Nodes: {total_nodes}")
    print(f"  Edges: {total_edges}")
    print(f"  All checks: PASSED")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
