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
print("METADATA TABLE VERIFICATION")
print("="*70)

# Check if metadata table exists and its structure
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'metadata'
    ORDER BY ordinal_position;
""")

columns = cur.fetchall()
print("\n✓ Metadata table structure:")
for col in columns:
    print(f"  - {col[0]} ({col[1]})")

# Count metadata records
cur.execute("SELECT COUNT(*) FROM metadata;")
metadata_count = cur.fetchone()[0]
print(f"\n✓ Total metadata records: {metadata_count}")

# Show sample metadata
if metadata_count > 0:
    cur.execute("""
        SELECT m.arxiv_id, m.citation_count, n.title
        FROM metadata m
        LEFT JOIN nodes n ON m.arxiv_id = n.arxiv_id
        ORDER BY m.citation_count DESC
        LIMIT 10;
    """)
    
    print("\n📊 Top 10 papers by citation count:")
    print("-" * 70)
    for row in cur.fetchall():
        print(f"\n  ArXiv ID:     {row[0]}")
        print(f"  Citations:    {row[1]}")
        print(f"  Title:        {row[2][:60] if row[2] else 'N/A'}...")
    
    # Citation statistics
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(citation_count) as avg_citations,
            MAX(citation_count) as max_citations,
            MIN(citation_count) as min_citations,
            COUNT(CASE WHEN citation_count > 0 THEN 1 END) as has_citations
        FROM metadata;
    """)
    
    stats = cur.fetchone()
    print("\n" + "="*70)
    print("CITATION STATISTICS")
    print("="*70)
    print(f"  Total records:        {stats[0]}")
    print(f"  Average citations:    {stats[1]:.1f}")
    print(f"  Max citations:        {stats[2]}")
    print(f"  Min citations:        {stats[3]}")
    print(f"  Papers with citations: {stats[4]} ({stats[4]/stats[0]*100:.1f}%)")
    
    # Check for orphaned metadata (metadata without corresponding nodes)
    cur.execute("""
        SELECT COUNT(*)
        FROM metadata m
        LEFT JOIN nodes n ON m.arxiv_id = n.arxiv_id
        WHERE n.arxiv_id IS NULL;
    """)
    
    orphaned = cur.fetchone()[0]
    if orphaned > 0:
        print(f"\n⚠ Warning: {orphaned} metadata records without corresponding nodes")
    else:
        print(f"\n✓ All metadata records have corresponding nodes")
    
    # Check for nodes without metadata
    cur.execute("""
        SELECT COUNT(*)
        FROM nodes n
        LEFT JOIN metadata m ON n.arxiv_id = m.arxiv_id
        WHERE m.arxiv_id IS NULL;
    """)
    
    no_metadata = cur.fetchone()[0]
    if no_metadata > 0:
        print(f"⚠ Warning: {no_metadata} nodes without metadata records")
        
        # Show some examples
        cur.execute("""
            SELECT n.arxiv_id, n.title
            FROM nodes n
            LEFT JOIN metadata m ON n.arxiv_id = m.arxiv_id
            WHERE m.arxiv_id IS NULL
            LIMIT 5;
        """)
        
        print("\n  Examples of nodes without metadata:")
        for row in cur.fetchall():
            print(f"    - {row[0]}: {row[1][:50]}...")
    else:
        print(f"✓ All nodes have metadata records")
    
else:
    print("\n⚠ No metadata found in database")
    print("\nPossible reasons:")
    print("  1. Papers haven't been processed yet")
    print("  2. Metadata extraction failed")
    print("\nRun: python process_all_papers.py")

cur.close()
conn.close()

print("\n" + "="*70)
print("✓ Metadata verification complete")
print("="*70)
