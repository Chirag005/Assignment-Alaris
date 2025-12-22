const { Pool } = require('pg');

const pool = new Pool({
  host: 'db.qcrgyeosydtcptrantke.supabase.co',
  port: 5432,
  database: 'postgres',
  user: 'postgres',
  password: 'Alaris@4575',
  ssl: { rejectUnauthorized: false }
});

module.exports = async (req, res) => {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  
  try {
    const result = await pool.query('SELECT * FROM nodes ORDER BY arxiv_id DESC');
    res.status(200).json(result.rows);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to fetch papers', details: error.message });
  }
};
