# Research Papers Web Viewer

A modern web interface for viewing and exploring research papers from a Supabase database.

## Features

- 📄 View all research papers with metadata
- 🔗 Explore relationships between papers
- 📊 View citation counts and metadata
- 🔍 Search papers by title, author, or arxiv ID
- 🎨 Beautiful, modern UI with gradient effects

## Deployment on Vercel

### 1. Deploy to Vercel

Click the button below or manually import your GitHub repository:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new)

### 2. Configure Environment Variables

In your Vercel project settings, add the following environment variables:

```
DB_HOST=db.qcrgyeosydtcptrantke.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_database_password_here
```

**Important:** Replace `your_database_password_here` with your actual Supabase database password.

### 3. Steps to Add Environment Variables in Vercel:

1. Go to your Vercel project dashboard
2. Click on "Settings"
3. Click on "Environment Variables"
4. Add each variable:
   - **Key**: `DB_HOST`, **Value**: `db.qcrgyeosydtcptrantke.supabase.co`
   - **Key**: `DB_PORT`, **Value**: `5432`
   - **Key**: `DB_NAME`, **Value**: `postgres`
   - **Key**: `DB_USER`, **Value**: `postgres`
   - **Key**: `DB_PASSWORD`, **Value**: `[your actual password]`
5. Click "Save"
6. Redeploy your application

## Local Development

### Using the Local Test Files

For local testing with direct Supabase connection:

1. Open `index-local-test.html` in your browser
2. The page connects directly to Supabase using the JavaScript client
3. No API routes needed - all data fetching happens client-side

### Running with API Routes Locally

```bash
# Install dependencies
npm install

# Run locally with Vercel CLI
vercel dev
```

Then open `index.html` in your browser.

## File Structure

```
web-viewer/
├── api/
│   ├── papers.js      # API route for fetching papers
│   ├── edges.js       # API route for fetching relationships
│   └── metadata.js    # API route for fetching metadata
├── index.html         # Main viewer (uses API routes)
├── index-local-test.html                # Local test version (direct Supabase connection)
├── index-local-test-all-columns.html    # Test version showing all columns
├── package.json       # Dependencies
└── vercel.json        # Vercel configuration
```

## Technologies Used

- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Backend**: Vercel Serverless Functions (Node.js)
- **Database**: Supabase (PostgreSQL)
- **Deployment**: Vercel

## Support

If you encounter any issues:

1. Check that all environment variables are correctly set in Vercel
2. Verify your Supabase database is accessible
3. Check the Vercel deployment logs for errors
