from groq import Groq
import psycopg2
from pypdf import PdfReader
import json
import time
import os

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

class PostgresResearchAgent:
    def __init__(self):
        self.groq_client = groq_client
        self.conn = psycopg2.connect(**DB_CONFIG)

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

    def process_paper(self, arxiv_id, pdf_path):
        """Process a single paper"""
        print(f"\n{'='*70}")
        print(f"Processing Paper")
        print(f"{'='*70}")
        print(f"ArXiv ID: {arxiv_id}")
        print(f"PDF Path: {pdf_path}\n")
        
        # Check if already processed
        if self.check_if_exists(arxiv_id):
            print(f"⊘ Already in database - skipping")
            return False
        
        try:
            # Extract text
            print(f"→ Extracting text from PDF...")
            raw_text = self.extract_text(pdf_path)
            print(f"✓ Extracted {len(raw_text):,} characters")
            
            # Send to Groq AI
            print(f"→ Sending to Groq AI...")
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
            
            # Retry logic for rate limits
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
            print(f"✓ AI response received and parsed")
            
            # Save to database
            print(f"→ Saving to database...")
            self.save_to_db(data, arxiv_id)  # Force the arxiv_id we want
            print(f"✓ Successfully saved to database\n")
            
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
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
            
            paper_arxiv_id = cur.fetchone()[0]
            print(f"  ✓ Inserted paper: {paper_arxiv_id}")
            
            # Also save to metadata table
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
                print(f"  ✓ Inserted metadata")
            except Exception as meta_error:
                print(f"  ⚠ Metadata insert failed: {meta_error}")
            
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

    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    print("="*70)
    print("PostgreSQL Research Agent with Groq AI")
    print("Individual Paper Processor")
    print("="*70)
    
    try:
        agent = PostgresResearchAgent()
        print(f"✓ Connected to database: {DB_CONFIG['dbname']} on port {DB_CONFIG['port']}\n")
        
        print("Usage:")
        print("  agent.process_paper('arxiv_id', 'path/to/paper.pdf')\n")
        
        print("Example:")
        print("  agent.process_paper('paper_49', r'Alaris/papers/📄 Paper 4.pdf')\n")
        
        print("Features:")
        print("  ✓ Extracts paper metadata (title, authors, year, summary)")
        print("  ✓ Extracts methods, datasets, and metrics")
        print("  ✓ Extracts relationships to other papers (edges)")
        print("  ✓ Saves to nodes, metadata, and edges tables")
        print("  ✓ Automatic duplicate detection")
        print("  ✓ Rate limit handling with retry logic\n")
        
        agent.conn.close()
        print("✓ Ready to use!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()