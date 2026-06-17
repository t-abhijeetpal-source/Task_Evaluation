'use strict';

const TransactionService = require('../services/transactionService');
const storage = require('../storage/inMemoryStorage');

const service = new TransactionService(storage);

/**
 * Controller layer — translates HTTP <-> service calls.
 * No business logic lives here beyond mapping results to status codes.
 */

function createTransaction(req, res) {
  const errors = service.validate(req.body);
  if (errors.length > 0) {
    return res.status(422).json({ errors });
  }
  const txn = service.create(req.body);
  return res.status(201).json({ id: txn.id });
}

function listTransactions(req, res) {
  return res.status(200).json(service.list());
}

function getBalance(req, res) {
  return res.status(200).json({ balance: service.getBalance() });
}

module.exports = { createTransaction, listTransactions, getBalance };
