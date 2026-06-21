'use strict';

const request = require('supertest');
const createApp = require('../src/app');
const { InMemoryStorage } = require('../src/storage/inMemoryStorage');

function buildApp() {
  return createApp({ storage: new InMemoryStorage() });
}

describe('Transaction Tracker API', () => {
  test('creates a transaction and returns its id', async () => {
    const res = await request(buildApp())
      .post('/transactions')
      .send({ amount: 100, type: 'credit', description: 'salary' });

    expect(res.status).toBe(201);
    expect(res.body).toEqual({ id: 1 });
  });

  test('lists all transactions', async () => {
    const app = buildApp();
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

  test('paginates transaction list', async () => {
    const app = buildApp();
    await request(app).post('/transactions').send({ amount: 1, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 2, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 3, type: 'credit' });

    const res = await request(app).get('/transactions?limit=1&offset=1');
    expect(res.status).toBe(200);
    expect(res.body).toHaveLength(1);
    expect(res.body[0].amount).toBe(2);
  });

  test('computes balance = sum(credits) - sum(debits)', async () => {
    const app = buildApp();
    await request(app).post('/transactions').send({ amount: 1000, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 300, type: 'debit' });
    await request(app).post('/transactions').send({ amount: 200, type: 'debit' });

    const res = await request(app).get('/balance');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ balance: 500 });
  });

  test('balance is 0 when there are no transactions', async () => {
    const res = await request(buildApp()).get('/balance');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ balance: 0 });
  });

  test('rejects non-positive amount with 422', async () => {
    const res = await request(buildApp()).post('/transactions').send({ amount: 0, type: 'credit' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(expect.arrayContaining([expect.stringMatching(/greater than 0/)]));
  });

  test('rejects invalid type with 422', async () => {
    const res = await request(buildApp()).post('/transactions').send({ amount: 50, type: 'transfer' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(expect.arrayContaining([expect.stringMatching(/type must be one of/)]));
  });

  test('rejects malformed JSON with 400', async () => {
    const res = await request(buildApp())
      .post('/transactions')
      .set('Content-Type', 'application/json')
      .send('{ "amount": 100, "type": ');
    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('error');
  });

  test('rejects sub-cent precision (9.999) with 422', async () => {
    const res = await request(buildApp()).post('/transactions').send({ amount: 9.999, type: 'credit' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(
      expect.arrayContaining([expect.stringMatching(/at most 2 decimal places/)])
    );
  });

  test('rejects amount over the configured max with 422', async () => {
    const res = await request(buildApp())
      .post('/transactions')
      .send({ amount: 1_000_000_001, type: 'credit' });
    expect(res.status).toBe(422);
    expect(res.body.errors).toEqual(
      expect.arrayContaining([expect.stringMatching(/must not exceed/)])
    );
  });

  test('balance is exact — 0.1 + 0.2 === 0.3 (no float drift)', async () => {
    const app = buildApp();
    await request(app).post('/transactions').send({ amount: 0.1, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 0.2, type: 'credit' });
    const res = await request(app).get('/balance');
    expect(res.body).toEqual({ balance: 0.3 });
  });

  test('balance with mixed decimals is exact', async () => {
    const app = buildApp();
    await request(app).post('/transactions').send({ amount: 100.1, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 0.05, type: 'debit' });
    await request(app).post('/transactions').send({ amount: 0.05, type: 'debit' });
    const res = await request(app).get('/balance');
    expect(res.body).toEqual({ balance: 100 });
  });

  test('rejects an over-long description with 422', async () => {
    const res = await request(buildApp())
      .post('/transactions')
      .send({ amount: 5, type: 'credit', description: 'x'.repeat(501) });
    expect(res.status).toBe(422);
  });

  test('rejects a non-object body with 422', async () => {
    const res = await request(buildApp())
      .post('/transactions')
      .set('Content-Type', 'application/json')
      .send('[1,2,3]');
    expect(res.status).toBe(422);
  });

  test('health reports service + version', async () => {
    const res = await request(buildApp()).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ status: 'ok' });
    expect(res.body).toHaveProperty('version');
  });

  test('assigns a request id when none supplied', async () => {
    const res = await request(buildApp()).get('/health');
    expect(res.headers['x-request-id']).toBeTruthy();
  });

  test('preserves a supplied request id', async () => {
    const res = await request(buildApp()).get('/health').set('x-request-id', 'trace-123');
    expect(res.headers['x-request-id']).toBe('trace-123');
  });

  test('unknown route returns 404 envelope', async () => {
    const res = await request(buildApp()).get('/does-not-exist');
    expect(res.status).toBe(404);
    expect(res.body).toHaveProperty('error');
  });
});
