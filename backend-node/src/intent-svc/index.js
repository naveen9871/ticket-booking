const express = require('express');
const { Kafka } = require('kafkajs');

const app = express();
app.use(express.json());

const kafka = new Kafka({
  clientId: 'intent-svc',
  brokers: [process.env.KAFKA_BROKER || 'localhost:9092']
});
const producer = kafka.producer();

app.post('/api/v1/intent/parse', async (req, res) => {
  const { user_id, utterance } = req.body;
  
  // TODO: Call LLM API (e.g., OpenAI or local model)
  // Mock LLM Response
  const parsedIntent = {
    intent: "plan_event",
    constraints: { budget_max: 2000, currency: "INR", location: "Indiranagar" },
    confidence: 0.95
  };

  await producer.send({
    topic: 'intent.parsed',
    messages: [
      { value: JSON.stringify({ user_id, ...parsedIntent }) },
    ],
  });

  res.json({ status: 'success', parsedIntent });
});

async function start() {
  await producer.connect();
  console.log('Intent Service connected to Kafka');
  
  const port = process.env.PORT || 3001;
  app.listen(port, () => {
    console.log(`Intent Service listening on port ${port}`);
  });
}

start().catch(console.error);
