const { Pool } = require('pg');
const redis = require('redis');

// PostgreSQL Pool
const pool = new Pool({
  user: process.env.DB_USER || 'devuser',
  host: process.env.DB_HOST || 'localhost',
  database: process.env.DB_NAME || 'ticket_booking',
  password: process.env.DB_PASSWORD || 'devpassword',
  port: process.env.DB_PORT || 5432,
});

// Redis Client
const redisClient = redis.createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379'
});

redisClient.on('error', (err) => console.log('Redis Client Error', err));

async function connectDb() {
  await redisClient.connect();
  console.log('Connected to Redis');
  
  const client = await pool.connect();
  console.log('Connected to PostgreSQL');
  client.release();
}

module.exports = {
  pool,
  redisClient,
  connectDb,
};
