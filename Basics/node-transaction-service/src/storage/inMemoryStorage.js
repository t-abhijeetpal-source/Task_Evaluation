'use strict';

/**
 * Storage layer — in-memory persistence with auto-incrementing ids.
 *
 * Swapping this for a real database would not require changes to the
 * service or controller layers, which only depend on its public methods.
 */
class InMemoryStorage {
  constructor() {
    this._transactions = [];
    this._nextId = 1;
  }

  /**
   * Assign an id, persist, and return the stored transaction.
   */
  add(transaction) {
    transaction.id = this._nextId++;
    this._transactions.push(transaction);
    return transaction;
  }

  /** Return all stored transactions (a shallow copy). */
  listAll() {
    return [...this._transactions];
  }

  /** Reset the store — used by tests for isolation. */
  clear() {
    this._transactions = [];
    this._nextId = 1;
  }
}

// Module-level singleton used by the running app.
module.exports = new InMemoryStorage();
module.exports.InMemoryStorage = InMemoryStorage;
