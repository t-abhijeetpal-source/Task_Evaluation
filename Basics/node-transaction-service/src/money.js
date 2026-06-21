'use strict';

/**
 * Money utilities — exact arithmetic for a 2-decimal currency.
 *
 * Floating-point is unsafe for money (0.1 + 0.2 !== 0.3). Balances are summed
 * in integer minor units (cents) so the result is exact. Inputs are validated
 * to <= 2 decimal places upstream, so `round(amount * 100)` is lossless here.
 */
function toCents(amount) {
  return Math.round(amount * 100);
}

function fromCents(cents) {
  // Divide then round to 2 dp to defend against any residual float artefact.
  return Math.round((cents / 100) * 100) / 100;
}

module.exports = { toCents, fromCents };
