'use strict';

const { TRANSACTION_TYPES, createTransaction } = require('../models/transaction');
const { toCents, fromCents } = require('../money');
const config = require('../config');

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
    } else if (!Number.isFinite(amount)) {
      errors.push('amount must be a finite number');
    } else if (amount <= 0) {
      errors.push('amount must be greater than 0');
    } else if (amount > config.maxAmount) {
      errors.push(`amount must not exceed ${config.maxAmount}`);
    } else if (Math.abs(amount * 100 - Math.round(amount * 100)) > 1e-9) {
      // Reject sub-cent precision like 9.999 — not representable money.
      errors.push('amount must have at most 2 decimal places');
    }

    if (!TRANSACTION_TYPES.includes(type)) {
      errors.push(`type must be one of: ${TRANSACTION_TYPES.join(', ')}`);
    }

    if (body.description !== undefined && typeof body.description !== 'string') {
      errors.push('description must be a string');
    } else if (typeof body.description === 'string' && body.description.length > 500) {
      errors.push('description must be at most 500 characters');
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

  /**
   * balance = sum(credits) - sum(debits).
   * Summed in integer minor units (cents) so the result is exact — no
   * binary-float drift (e.g. 0.1 + 0.2). Converted back to a 2-dp number only
   * at the end.
   */
  getBalance() {
    const cents = this._storage.listAll().reduce((acc, txn) => {
      return txn.type === 'credit' ? acc + toCents(txn.amount) : acc - toCents(txn.amount);
    }, 0);
    return fromCents(cents);
  }
}

module.exports = TransactionService;
