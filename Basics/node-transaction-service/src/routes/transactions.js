'use strict';

const express = require('express');
const TransactionService = require('../services/transactionService');

function createTransactionRouter(service) {
  const router = express.Router();

  router.post('/transactions', (req, res) => {
    const errors = service.validate(req.body);
    if (errors.length > 0) {
      return res.status(422).json({ errors });
    }
    const txn = service.create(req.body);
    return res.status(201).json({ id: txn.id });
  });

  router.get('/transactions', (req, res) => {
    const rawLimit = parseInt(req.query.limit, 10);
    const rawOffset = parseInt(req.query.offset, 10);
    const limit = Number.isFinite(rawLimit) ? Math.min(Math.max(rawLimit, 1), 1000) : 100;
    const offset = Number.isFinite(rawOffset) ? Math.max(rawOffset, 0) : 0;
    return res.status(200).json(service.list(limit, offset));
  });

  router.get('/balance', (req, res) => {
    return res.status(200).json({ balance: service.getBalance() });
  });

  return router;
}

module.exports = createTransactionRouter;
