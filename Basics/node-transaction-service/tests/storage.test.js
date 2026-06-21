'use strict';

const { InMemoryStorage } = require('../src/storage/inMemoryStorage');
const { toCents } = require('../src/money');

describe('InMemoryStorage', () => {
  let store;

  beforeEach(() => {
    store = new InMemoryStorage();
  });

  test('tracks running balance in cents on add', () => {
    store.add({ amount: 100, type: 'credit', description: '' });
    store.add({ amount: 40, type: 'debit', description: '' });
    expect(store.balanceCents()).toBe(toCents(100) - toCents(40));
  });

  test('balance resets on clear', () => {
    store.add({ amount: 10, type: 'credit', description: '' });
    store.clear();
    expect(store.balanceCents()).toBe(0);
    expect(store.listAll()).toEqual([]);
  });

  test('listAll supports limit and offset', () => {
    store.add({ amount: 1, type: 'credit', description: 'a' });
    store.add({ amount: 2, type: 'credit', description: 'b' });
    store.add({ amount: 3, type: 'credit', description: 'c' });
    expect(store.listAll(2, 0)).toHaveLength(2);
    expect(store.listAll(2, 1)).toHaveLength(2);
    expect(store.listAll(2, 1)[0].amount).toBe(2);
  });
});
