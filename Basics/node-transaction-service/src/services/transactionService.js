'use strict';

const { TRANSACTION_TYPES, createTransaction } = require('../models/transaction');

/**
 * Business layer — transaction logic, validation rules, balance calculation.
 *
 * Controllers call into this layer and never compute anything themselves.
 */
class TransactionService {
  constructor(storage) {
    this._storage = storage;
  }

  /**
   * Validate a raw request body against the business rules.
   * @returns {string[]} array of error messages (empty == valid)
   */
  validate(body) {
    const errors = [];
    if (body === null || typeof body !== 'object' || Array.isArray(body)) {
      return ['request body must be a JSON object'];
    }
    const { amount, type } = body;

    if (typeof amount !== 'number' || Number.isNaN(amount)) {
      errors.push('amount is required and must be a number');
    } else if (amount <= 0) {
      errors.push('amount must be greater than 0');
    }

    if (!TRANSACTION_TYPES.includes(type)) {
      errors.push(`type must be one of: ${TRANSACTION_TYPES.join(', ')}`);
    }

    if (body.description !== undefined && typeof body.description !== 'string') {
      errors.push('description must be a string');
    }

    return errors;
  }

  /** Create and persist a transaction from a validated body. */
  create(body) {
    const txn = createTransaction(body);
    return this._storage.add(txn);
  }

  /** Return every recorded transaction. */
  list() {
    return this._storage.listAll();
  }

  /** balance = sum(credits) - sum(debits) */
  getBalance() {
    return this._storage.listAll().reduce((acc, txn) => {
      return txn.type === 'credit' ? acc + txn.amount : acc - txn.amount;
    }, 0);
  }
}

module.exports = TransactionService;
