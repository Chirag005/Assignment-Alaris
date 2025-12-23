import psycopg2

# Supabase configuration
SUPABASE_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "Alaris@4575",
    "host": "db.qcrgyeosydtcptrantke.supabase.co",
    "port": "5432"
}

print("="*70)
print("Setting up Supabase Database Schema")
print("="*70)

try:
    # Connect to Supabase
    print("\n1. Connecting to Supabase...")
    conn = psycopg2.connect(**SUPABASE_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    print("   ✓ Connected successfully!")
    
    # Create nodes table
    print("\n2. Creating 'nodes' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            arxiv_id TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            year INTEGER,
            summary TEXT,
            methods TEXT[],
            datasets TEXT[],
            metrics TEXT[],
            project_page TEXT,
            pdf_link TEXT
        );
    """)
    print("   ✓ Nodes table created")
    
    # Create metadata table
    print("\n3. Creating 'metadata' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            arxiv_id TEXT PRIMARY KEY,
            citation_count INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("   ✓ Metadata table created")
    
    # Create edges table
    print("\n4. Creating 'edges' table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id SERIAL PRIMARY KEY,
            source_id TEXT,
            target_id TEXT,
            relationship_type TEXT,
            reasoning TEXT
        );
    """)
    print("   ✓ Edges table created")
    
    # Verify tables
    print("\n5. Verifying tables...")
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_name IN ('nodes', 'metadata', 'edges');
    """)
    
    tables = [row[0] for row in cur.fetchall()]
    print(f"   ✓ Found tables: {', '.join(tables)}")
    
    # Get counts
    print("\n6. Current data counts:")
    for table in ['nodes', 'metadata', 'edges']:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"   - {table}: {count} records")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*70)
    print("✅ Supabase database setup complete!")
    print("="*70)
    print("\nYou can now run:")
    print("  python process_single_paper.py")
    print("\nTo process papers to Supabase!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
