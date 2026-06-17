'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const storage = require('../src/storage/inMemoryStorage');

const app = createApp();

beforeEach(() => storage.clear());

describe('Transaction Tracker API', () => {
  // --- Test 1: creation ---------------------------------------------------
  test('creates a transaction and returns its id', async () => {
    const res = await request(app)
      .post('/transactions')
      .send({ amount: 100, type: 'credit', description: 'salary' });

    expect(res.status).toBe(201);
    expect(res.body).toEqual({ id: 1 });
  });

  // --- Test 2: listing ----------------------------------------------------
  test('lists all transactions', async () => {
    await request(app).post('/transactions').send({ amount: 100, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 40, type: 'debit', description: 'lunch' });

    const res = await request(app).get('/transactions');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(2);
    expect(res.body[0]).toMatchObject({ id: 1, amount: 100, type: 'credit' });
    expect(res.body[1]).toMatchObject({ id: 2, amount: 40, type: 'debit' });
    res.body.forEach((txn) => {
      expect(txn).toHaveProperty('timestamp');
    });
  });

  // --- Test 3: balance ----------------------------------------------------
  test('computes balance = sum(credits) - sum(debits)', async () => {
    await request(app).post('/transactions').send({ amount: 1000, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 300, type: 'debit' });
    await request(app).post('/transactions').send({ amount: 200, type: 'debit' });

    const res = await request(app).get('/balance');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ balance: 500 });
  });

  test('balance is 0 when there are no transactions', async () => {
    const res = await request(app).get('/balance');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ balance: 0 });
  });

  // --- Test 4: validation failures ----------------------------------------
  test('rejects non-positive amount with 422', async () => {
    const res = await request(app).post('/transactions').send({ amount: 0, type: 'credit' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(expect.arrayContaining([expect.stringMatching(/greater than 0/)]));
  });

  test('rejects invalid type with 422', async () => {
    const res = await request(app).post('/transactions').send({ amount: 50, type: 'transfer' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(expect.arrayContaining([expect.stringMatching(/type must be one of/)]));
  });

  test('rejects malformed JSON with 400', async () => {
    const res = await request(app)
      .post('/transactions')
      .set('Content-Type', 'application/json')
      .send('{ "amount": 100, "type": '); // truncated / invalid JSON
    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('error');
  });
});
