'use strict';

/**
 * Domain model layer.
 *
 * Defines the valid transaction types and a factory for building a domain
 * transaction object. Storage-agnostic and HTTP-agnostic.
 */

const TRANSACTION_TYPES = Object.freeze(['credit', 'debit']);

/**
 * Build a domain transaction. `id` is assigned later by storage.
 * @param {{amount:number, type:string, description?:string}} input
 * @returns {{id:number|null, amount:number, type:string, description:string, timestamp:string}}
 */
function createTransaction({ amount, type, description }) {
  return {
    id: null,
    amount,
    type,
    description: description || '',
    timestamp: new Date().toISOString(),
  };
}

module.exports = { TRANSACTION_TYPES, createTransaction };
