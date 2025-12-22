const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'db.qcrgyeosydtcptrantke.supabase.co',
  port: process.env.DB_PORT || 6543,
  database: process.env.DB_NAME || 'postgres',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD,
  ssl: { rejectUnauthorized: false }
});

module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET');
  
  try {
    const result = await pool.query('SELECT * FROM edges ORDER BY id DESC');
    res.status(200).json(result.rows);
  } catch (error) {
    console.error('Database error:', error);
    res.status(500).json({ error: 'Failed to fetch edges', details: error.message });
  }
};
