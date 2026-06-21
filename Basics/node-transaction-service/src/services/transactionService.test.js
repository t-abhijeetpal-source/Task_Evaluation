'use strict';

const TransactionService = require('./transactionService');
const { InMemoryStorage } = require('../storage/inMemoryStorage');

describe('TransactionService unit', () => {
  test('getBalance uses storage running total', () => {
    const storage = new InMemoryStorage();
    const service = new TransactionService(storage);
    service.create({ amount: 10, type: 'credit' });
    service.create({ amount: 3, type: 'debit' });
    expect(service.getBalance()).toBe(7);
  });
});
