'use strict';

const express = require('express');
const transactionRoutes = require('./routes/transactions');

/**
 * API layer — builds and configures the Express app.
 * Exported without listening so tests can import it directly (supertest).
 */
function createApp() {
  const app = express();

  // Parse JSON bodies.
  app.use(express.json());

  // Malformed-JSON handler: express.json() throws a SyntaxError with `status`.
  app.use((err, req, res, next) => {
    if (err && err.type === 'entity.parse.failed') {
      return res.status(400).json({ error: 'Malformed JSON in request body' });
    }
    return next(err);
  });

  app.get('/health', (req, res) => res.status(200).json({ status: 'ok' }));

  app.use('/', transactionRoutes);

  // 404 fallback.
  app.use((req, res) => res.status(404).json({ error: 'Not found' }));

  return app;
}

module.exports = createApp;
