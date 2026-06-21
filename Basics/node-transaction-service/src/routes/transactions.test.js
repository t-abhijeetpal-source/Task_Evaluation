'use strict';

const request = require('supertest');
const express = require('express');
const createTransactionRouter = require('./transactions');
const TransactionService = require('../services/transactionService');
const { InMemoryStorage } = require('../storage/inMemoryStorage');

describe('transaction routes', () => {
  test('pagination query params', async () => {
    const storage = new InMemoryStorage();
    const service = new TransactionService(storage);
    const app = express().use(express.json()).use(createTransactionRouter(service));
    await request(app).post('/transactions').send({ amount: 1, type: 'credit' });
    await request(app).post('/transactions').send({ amount: 2, type: 'credit' });
    const res = await request(app).get('/transactions?limit=1&offset=1');
    expect(res.body).toHaveLength(1);
    expect(res.body[0].amount).toBe(2);
  });
});
