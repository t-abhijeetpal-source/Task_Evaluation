'use strict';

const express = require('express');
const controller = require('../controllers/transactionController');

const router = express.Router();

router.post('/transactions', controller.createTransaction);
router.get('/transactions', controller.listTransactions);
router.get('/balance', controller.getBalance);

module.exports = router;
