'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const { InMemoryStorage } = require('../src/storage/inMemoryStorage');

describe('createApp dependency injection', () => {
  test('uses an isolated storage instance when provided', async () => {
    const storage = new InMemoryStorage();
    const app = createApp({ storage });

    await request(app).post('/transactions').send({ amount: 50, type: 'credit' });
    expect(storage.listAll()).toHaveLength(1);

    const other = new InMemoryStorage();
    const otherApp = createApp({ storage: other });
    const res = await request(otherApp).get('/balance');
    expect(res.body).toEqual({ balance: 0 });
  });
});
