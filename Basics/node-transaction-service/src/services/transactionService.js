'use strict';

const { TRANSACTION_TYPES, createTransaction } = require('../models/transaction');
const { fromCents } = require('../money');
const config = require('../config');

class TransactionService {
  constructor(storage) {
    this._storage = storage;
  }

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

  create(body) {
    const txn = createTransaction(body);
    return this._storage.add(txn);
  }

  list(limit = 100, offset = 0) {
    return this._storage.listAll(limit, offset);
  }

  getBalance() {
    return fromCents(this._storage.balanceCents());
  }
}

module.exports = TransactionService;
