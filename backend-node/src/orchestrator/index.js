const { Kafka } = require('kafkajs');
const { connectDb } = require('../db');

const kafka = new Kafka({
  clientId: 'orchestrator',
  brokers: [process.env.KAFKA_BROKER || 'localhost:9092']
});

const consumer = kafka.consumer({ groupId: 'orchestrator-group' });

async function run() {
  await connectDb();
  
  await consumer.connect();
  console.log('Orchestrator connected to Kafka');
  
  await consumer.subscribe({ topic: 'intent.parsed', fromBeginning: true });
  
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      console.log({
        topic,
        value: message.value.toString(),
      });
      // 1. Receive intent payload
      // 2. Trigger Discovery Agent
      // 3. Trigger Planning Agent
      // 4. Return Itineraries to User
    },
  });
}

run().catch(console.error);
