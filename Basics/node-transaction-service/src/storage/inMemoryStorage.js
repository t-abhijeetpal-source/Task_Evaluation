'use strict';

const { toCents } = require('../money');

/**
 * Storage layer — in-memory persistence with O(1) running balance.
 */
class InMemoryStorage {
  constructor() {
    this._transactions = [];
    this._nextId = 1;
    this._balanceCents = 0;
  }

  add(transaction) {
    transaction.id = this._nextId++;
    this._transactions.push(transaction);
    const cents = toCents(transaction.amount);
    this._balanceCents += transaction.type === 'credit' ? cents : -cents;
    return transaction;
  }

  listAll(limit = null, offset = 0) {
    const start = Math.max(0, offset);
    const slice = limit == null
      ? this._transactions.slice(start)
      : this._transactions.slice(start, start + limit);
    return slice.map((t) => ({ ...t }));
  }

  balanceCents() {
    return this._balanceCents;
  }

  clear() {
    this._transactions = [];
    this._nextId = 1;
    this._balanceCents = 0;
  }
}

const defaultStorage = new InMemoryStorage();

module.exports = defaultStorage;
module.exports.InMemoryStorage = InMemoryStorage;
module.exports.createStorage = () => new InMemoryStorage();
