'use strict';

const { InMemoryStorage } = require('./inMemoryStorage');
const { toCents } = require('../money');

describe('InMemoryStorage unit', () => {
  test('running balance and pagination', () => {
    const store = new InMemoryStorage();
    store.add({ amount: 100, type: 'credit', description: '' });
    store.add({ amount: 40, type: 'debit', description: '' });
    expect(store.balanceCents()).toBe(toCents(60));
    expect(store.listAll(1, 1)).toHaveLength(1);
    store.clear();
    expect(store.balanceCents()).toBe(0);
  });
});
