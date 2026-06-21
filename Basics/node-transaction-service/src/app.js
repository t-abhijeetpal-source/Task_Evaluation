'use strict';

const { randomUUID } = require('crypto');
const express = require('express');
const transactionRoutes = require('./routes/transactions');
const config = require('./config');
const logger = require('./logger');

/**
 * API layer — builds and configures the Express app.
 * Exported without listening so tests can import it directly (supertest).
 */
function createApp() {
  const app = express();

  // Request context: assign/propagate a request id and log each request as JSON.
  app.use((req, res, next) => {
    const rid = req.headers['x-request-id'] || randomUUID();
    req.id = rid;
    res.setHeader('x-request-id', rid);
    const start = process.hrtime.bigint();
    res.on('finish', () => {
      const elapsedMs = Number(process.hrtime.bigint() - start) / 1e6;
      logger.info('request', {
        request_id: rid,
        method: req.method,
        path: req.path,
        status: res.statusCode,
        elapsed_ms: Math.round(elapsedMs * 100) / 100,
      });
    });
    next();
  });

  // Parse JSON bodies.
  app.use(express.json());

  // Malformed-JSON handler: express.json() throws a SyntaxError with `status`.
  app.use((err, req, res, next) => {
    if (err && err.type === 'entity.parse.failed') {
      return res.status(400).json({ error: 'Malformed JSON in request body' });
    }
    return next(err);
  });

  app.get('/health', (req, res) =>
    res.status(200).json({ status: 'ok', service: config.appName, version: config.appVersion })
  );

  app.use('/', transactionRoutes);

  // 404 fallback.
  app.use((req, res) => res.status(404).json({ error: 'Not found' }));

  // Catch-all error handler: never leak a stack trace; log it, return a clean envelope.
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    logger.error('unhandled_error', { request_id: req.id, error: err && err.message });
    res.status(500).json({ error: 'internal_error' });
  });

  return app;
}

module.exports = createApp;
