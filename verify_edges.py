import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname='Assignment',
    user='postgres',
    password='asdf',
    host='localhost',
    port=5555
)

cur = conn.cursor()

print("="*70)
print("EDGES TABLE VERIFICATION")
print("="*70)

# Check if edges table exists and its structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'edges'
    ORDER BY ordinal_position;
""")

columns = cur.fetchall()
print("\n✓ Edges table structure:")
for col in columns:
    print(f"  - {col[0]} ({col[1]})")

# Count edges
cur.execute("SELECT COUNT(*) FROM edges;")
edge_count = cur.fetchone()[0]
print(f"\n✓ Total edges in database: {edge_count}")

# Show sample edges if any
if edge_count > 0:
    cur.execute("""
        SELECT source_id, target_id, type, evidence
        FROM edges
        LIMIT 5;
    """)
    
    print("\n📊 Sample edges:")
    for row in cur.fetchall():
        print(f"  {row[0]} --[{row[2]}]--> {row[1]}")
        if row[3]:
            print(f"    Evidence: {row[3][:60]}...")
else:
    print("\n⚠ No edges found in database")
    print("\nPossible reasons:")
    print("  1. Papers haven't been processed with the new edge extraction code yet")
    print("  2. AI didn't extract any relationships from the papers")
    print("  3. Target papers don't exist in the database")

# Check for recent nodes to see what could be connected
cur.execute("""
    SELECT arxiv_id, title
    FROM nodes
    ORDER BY arxiv_id DESC
    LIMIT 5;
""")

print("\n📄 Recent papers that could have edges:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1][:50]}...")

cur.close()
conn.close()

print("\n" + "="*70)
print("To populate edges, run: python process_all_papers.py")
print("="*70)
