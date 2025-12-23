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
print("NODES TABLE VERIFICATION")
print("="*70)

# Check if nodes table exists and its structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'nodes'
    ORDER BY ordinal_position;
""")

columns = cur.fetchall()
print("\n✓ Nodes table structure:")
for col in columns:
    print(f"  - {col[0]} ({col[1]})")

# Count nodes
cur.execute("SELECT COUNT(*) FROM nodes;")
node_count = cur.fetchone()[0]
print(f"\n✓ Total nodes in database: {node_count}")

# Count by type if column exists
try:
    cur.execute("""
        SELECT 'Paper' as type, COUNT(*) as count
        FROM nodes;
    """)
    
    print("\n📊 Node breakdown:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
except:
    pass

# Show sample nodes
if node_count > 0:
    cur.execute("""
        SELECT arxiv_id, title, year, authors
        FROM nodes
        ORDER BY arxiv_id DESC
        LIMIT 10;
    """)
    
    print("\n📄 Sample papers (last 10):")
    print("-" * 70)
    for row in cur.fetchall():
        print(f"\n  ArXiv ID: {row[0]}")
        print(f"  Title:    {row[1][:60]}...")
        print(f"  Year:     {row[2]}")
        print(f"  Authors:  {row[3][:60]}...")
    
    # Check data completeness
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as has_title,
            COUNT(CASE WHEN authors IS NOT NULL AND authors != '' THEN 1 END) as has_authors,
            COUNT(CASE WHEN year > 0 THEN 1 END) as has_year,
            COUNT(CASE WHEN summary IS NOT NULL AND summary != '' THEN 1 END) as has_summary,
            COUNT(CASE WHEN methods IS NOT NULL THEN 1 END) as has_methods,
            COUNT(CASE WHEN datasets IS NOT NULL THEN 1 END) as has_datasets,
            COUNT(CASE WHEN metrics IS NOT NULL THEN 1 END) as has_metrics
        FROM nodes;
    """)
    
    stats = cur.fetchone()
    print("\n" + "="*70)
    print("DATA COMPLETENESS")
    print("="*70)
    print(f"  Total papers:     {stats[0]}")
    print(f"  With title:       {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
    print(f"  With authors:     {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
    print(f"  With year:        {stats[3]} ({stats[3]/stats[0]*100:.1f}%)")
    print(f"  With summary:     {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
    print(f"  With methods:     {stats[5]} ({stats[5]/stats[0]*100:.1f}%)")
    print(f"  With datasets:    {stats[6]} ({stats[6]/stats[0]*100:.1f}%)")
    print(f"  With metrics:     {stats[7]} ({stats[7]/stats[0]*100:.1f}%)")
    
else:
    print("\n⚠ No nodes found in database")
    print("\nRun: python process_all_papers.py")

cur.close()
conn.close()

print("\n" + "="*70)
print("✓ Nodes verification complete")
print("="*70)
