'use strict';

/**
 * Application configuration — 12-factor, environment-driven.
 * Nothing tunable is hardcoded in the app body; override via env in prod.
 */
module.exports = Object.freeze({
  appName: process.env.APP_NAME || 'transaction-tracker-api',
  appVersion: process.env.APP_VERSION || '1.1.0',
  port: Number(process.env.PORT) || 3000,
  logLevel: process.env.LOG_LEVEL || 'info',
  // Reject implausibly large amounts (overflow / fat-finger defence).
  maxAmount: Number(process.env.MAX_AMOUNT) || 1_000_000_000, // 1e9
});
