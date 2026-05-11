const express = require('express');
const { connectDb, redisClient, pool } = require('../db');

const app = express();
app.use(express.json());

app.post('/api/v1/bookings/lock-seats', async (req, res) => {
  const { event_id, seat_ids, user_id } = req.body;
  
  // Try to acquire distributed lock for seats in Redis
  const lockKey = `event:${event_id}:seats:${seat_ids.join(',')}`;
  
  try {
    const lockAcquired = await redisClient.setNX(lockKey, user_id);
    if (!lockAcquired) {
      return res.status(409).json({ error: 'Seats currently locked by another agent/user' });
    }
    
    // Set lock TTL to 30 seconds
    await redisClient.expire(lockKey, 30);
    
    res.json({ status: 'locked', lock_id: lockKey, expires_in: 30 });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/v1/bookings/confirm', async (req, res) => {
  // Confirm lock, verify payment, and save to Postgres
  // TODO: Transaction handling
  res.json({ status: 'confirmed' });
});

async function start() {
  await connectDb();
  
  const port = process.env.PORT || 3002;
  app.listen(port, () => {
    console.log(`Booking Service listening on port ${port}`);
  });
}

start().catch(console.error);
