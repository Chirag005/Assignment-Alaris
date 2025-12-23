from groq import Groq
import psycopg2
from pypdf import PdfReader
import json
import os
import time

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database Configuration - Supabase
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": "db.qcrgyeosydtcptrantke.supabase.co",
    "port": "5432"
}

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

class BatchPaperProcessor:
    def __init__(self):
        self.groq_client = groq_client
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.processed = 0
        self.failed = 0
        self.skipped = 0

    def extract_text(self, pdf_path):
        """Extract text from PDF"""
        reader = PdfReader(pdf_path)
        return "".join([p.extract_text() for p in reader.pages])

    def check_if_exists(self, arxiv_id):
        """Check if paper already exists in database"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM nodes 
            WHERE arxiv_id = %s;
        """, (arxiv_id,))
        exists = cur.fetchone()[0] > 0
        cur.close()
        return exists

    def process_paper(self, arxiv_id, pdf_path, paper_num):
        """Process a single paper"""
        print(f"\n[{paper_num}] Processing: {os.path.basename(pdf_path)}")
        
        # Check if already processed
        if self.check_if_exists(arxiv_id):
            print(f"  ⊘ Already in database - skipping")
            self.skipped += 1
            return True
        
        try:
            # Extract text
            print(f"  → Extracting text...")
            raw_text = self.extract_text(pdf_path)
            print(f"  ✓ Extracted {len(raw_text):,} characters")
            
            # Send to Groq AI
            print(f"  → Sending to Groq AI...")
            prompt = f"""
Extract information from this research paper and return ONLY valid JSON (no markdown):

{{
  "node": {{
    "arxiv_id": "{arxiv_id}",
    "title": "paper title",
    "authors": "author names",
    "year": 2024,
    "summary": "brief summary (1-2 sentences)",
    "methods": ["method1", "method2"],
    "datasets": ["dataset1"],
    "metrics": ["metric1"],
    "project_page": "",
    "pdf_link": ""
  }},
  "edges": [
    {{"target_arxiv_id": "related_paper_id", "relationship_type": "CITES", "reasoning": "why"}},
    {{"target_arxiv_id": "another_paper_id", "relationship_type": "BUILDS_ON", "reasoning": "explanation"}}
  ],
  "metadata": {{"citation_count": 0}}
}}

Paper text (first 15000 chars):
{raw_text[:15000]}
"""
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                        temperature=0.1,
                        max_tokens=2048
                    )
                    break  # Success - exit retry loop
                except Exception as api_error:
                    if "rate_limit" in str(api_error).lower() and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10  # 10, 20, 30 seconds
                        print(f"  ⚠ Rate limit hit - waiting {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise if not rate limit or last attempt
            
            # Parse response
            json_data = response.choices[0].message.content.strip()
            if json_data.startswith('```'):
                json_data = json_data.split('```')[1]
                if json_data.startswith('json'):
                    json_data = json_data[4:]
            json_data = json_data.strip()
            
            data = json.loads(json_data)
            print(f"  ✓ AI response received")
            
            # Save to database
            self.save_to_db(data, arxiv_id)  # Force the arxiv_id we want
            print(f"  ✓ Saved to database")
            
            self.processed += 1
            return True
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.failed += 1
            return False

    def save_to_db(self, data, arxiv_id):
        """Save paper to database"""
        cur = self.conn.cursor()
        try:
            node = data['node']
            
            # Force the arxiv_id to be the one we passed in, not what AI extracted
            node['arxiv_id'] = arxiv_id
            
            # Assignment database uses individual columns, not JSONB
            cur.execute("""
                INSERT INTO nodes (
                    arxiv_id, title, authors, year, summary, 
                    methods, datasets, metrics, project_page, pdf_link
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING arxiv_id;
            """, (
                arxiv_id,  # Use the forced arxiv_id
                node.get('title', ''),
                node.get('authors', ''),
                node.get('year', 0),
                node.get('summary', ''),
                node.get('methods', []),
                node.get('datasets', []),
                node.get('metrics', []),
                node.get('project_page', ''),
                node.get('pdf_link', '')
            ))
            
            # Also save to metadata table if it exists
            try:
                cur.execute("""
                    INSERT INTO metadata (arxiv_id, citation_count)
                    VALUES (%s, %s)
                    ON CONFLICT (arxiv_id) DO UPDATE 
                    SET citation_count = EXCLUDED.citation_count;
                """, (
                    arxiv_id,  # Use the forced arxiv_id
                    data.get('metadata', {}).get('citation_count', 0)
                ))
            except:
                pass  # metadata table might not exist
            
            # Insert edges (relationships)
            edges = data.get('edges', [])
            edges_inserted = 0
            edges_skipped = 0
            if edges:
                print(f"  → Processing {len(edges)} edge(s)...")
                source_arxiv_id = arxiv_id  # Use the forced arxiv_id
                for edge in edges:
                    target_arxiv_id = edge.get('target_arxiv_id')
                    relationship_type = edge.get('relationship_type', 'RELATED')
                    reasoning = edge.get('reasoning', '')
                    
                    if target_arxiv_id:
                        try:
                            cur.execute("""
                                INSERT INTO edges (source_id, target_id, relationship_type, reasoning)
                                VALUES (%s, %s, %s, %s);
                            """, (source_arxiv_id, target_arxiv_id, relationship_type, reasoning))
                            edges_inserted += 1
                        except Exception as edge_error:
                            edges_skipped += 1
                
                if edges_inserted > 0:
                    print(f"  ✓ Inserted {edges_inserted} edge(s)")
                if edges_skipped > 0:
                    print(f"  ⚠ Skipped {edges_skipped} edge(s)")
            else:
                print(f"  ℹ No edges in AI response")
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise e
        finally:
            cur.close()

    def process_all_papers(self, papers_dir):
        """Process all papers in directory"""
        print("="*70)
        print("BATCH PROCESSING ALL PAPERS")
        print("="*70)
        
        # Get all PDF files
        pdf_files = []
        for file in os.listdir(papers_dir):
            if file.endswith('.pdf'):
                pdf_files.append(file)
        
        pdf_files.sort()  # Sort for consistent order
        
        print(f"\nFound {len(pdf_files)} PDF files")
        print(f"Directory: {papers_dir}\n")
        
        # Process each paper
        for i, filename in enumerate(pdf_files, 1):
            # Generate arxiv_id from filename
            arxiv_id = f"paper_{filename.replace('📄 Paper ', '').replace('.pdf', '')}"
            pdf_path = os.path.join(papers_dir, filename)
            
            self.process_paper(arxiv_id, pdf_path, i)
            
            # Delay to avoid rate limits
            if i < len(pdf_files):
                time.sleep(3)  # 3 second delay between papers
        
        # Show summary
        print("\n" + "="*70)
        print("PROCESSING COMPLETE")
        print("="*70)
        print(f"✓ Successfully processed: {self.processed}")
        print(f"⊘ Already in database:    {self.skipped}")
        print(f"✗ Failed:                 {self.failed}")
        print(f"━ Total:                  {len(pdf_files)}")
        
        # Verify in database
        self.verify_database()

    def verify_database(self):
        """Verify all papers are in database"""
        print("\n" + "="*70)
        print("DATABASE VERIFICATION")
        print("="*70)
        
        cur = self.conn.cursor()
        
        # Count papers
        cur.execute("SELECT COUNT(*) FROM nodes;")
        total_papers = cur.fetchone()[0]
        print(f"\n✓ Total papers in database: {total_papers}")
        
        # Show recent papers
        cur.execute("""
            SELECT arxiv_id, title
            FROM nodes 
            ORDER BY arxiv_id DESC
            LIMIT 5;
        """)
        
        print("\n📄 Last 5 papers added:")
        for row in cur.fetchall():
            print(f"  ArXiv {row[0]}: {row[1][:50]}...")
        
        cur.close()
        print("\n" + "="*70)
        print("✅ All data is now in PostgreSQL!")
        print("   View in pgAdmin: Assignment → Schemas → public → Tables → nodes")
        print("="*70)

    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    print("\n🚀 Starting batch paper processing...")
    
    try:
        # Initialize processor
        processor = BatchPaperProcessor()
        
        # Process all papers
        papers_directory = r"Alaris/papers"
        processor.process_all_papers(papers_directory)
        
        # Close connection
        processor.close()
        
        print("\n✅ SUCCESS! All papers processed and saved to PostgreSQL")
        
    except Exception as e:
        print(f"\n❌ Fatal Error: {e}")
        import traceback
        traceback.print_exc()
