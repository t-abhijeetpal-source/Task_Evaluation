//! Integration tests for the deterministic scoring engine.
//!
//! Asserts the 4 canonical test vectors from CONTRACT.md, plus a clamp test
//! and a malformed-JSON test.

use fraud_engine::{score, ScoreResult, Transaction};

/// Helper to build a Transaction from the contract-relevant fields.
fn txn(amount: f64, country: &str, merchant: &str) -> Transaction {
    serde_json::from_value(serde_json::json!({
        "schema_version": "1.0",
        "transaction_id": "txn_001",
        "user_id": "user_123",
        "amount": amount,
        "country": country,
        "merchant_category": merchant,
        "timestamp": "2026-06-17T10:00:00Z"
    }))
    .expect("valid fixture transaction")
}

#[test]
fn canonical_baseline() {
    // 5000 / IN / electronics -> 0 / low / []
    let r = score(&txn(5000.0, "IN", "electronics"));
    assert_eq!(
        r,
        ScoreResult {
            schema_version: "1.0".to_string(),
            transaction_id: "txn_001".to_string(),
            score: 0,
            risk_level: "low".to_string(),
            reasons: vec![],
        }
    );
}

#[test]
fn canonical_high_amount() {
    // 15000 / IN / electronics -> 40 / medium / [high_amount]
    let r = score(&txn(15000.0, "IN", "electronics"));
    assert_eq!(r.score, 40);
    assert_eq!(r.risk_level, "medium");
    assert_eq!(r.reasons, vec!["high_amount".to_string()]);
}

#[test]
fn canonical_foreign() {
    // 5000 / US / electronics -> 20 / low / [foreign_country]
    let r = score(&txn(5000.0, "US", "electronics"));
    assert_eq!(r.score, 20);
    assert_eq!(r.risk_level, "low");
    assert_eq!(r.reasons, vec!["foreign_country".to_string()]);
}

#[test]
fn canonical_all_three() {
    // 15000 / US / gambling -> 90 / high / [all three]
    let r = score(&txn(15000.0, "US", "gambling"));
    assert_eq!(r.score, 90);
    assert_eq!(r.risk_level, "high");
    assert_eq!(
        r.reasons,
        vec![
            "high_amount".to_string(),
            "foreign_country".to_string(),
            "high_risk_merchant".to_string(),
        ]
    );
}

#[test]
fn score_is_clamped_to_100() {
    // All three rules fire (40 + 20 + 30 = 90); max possible is already <= 100,
    // so verify the clamp ceiling holds and never exceeds 100.
    let r = score(&txn(1_000_000.0, "ZZ", "wire_transfer"));
    assert!(r.score <= 100, "score must be clamped to <= 100");
    assert_eq!(r.score, 90);
    assert_eq!(r.risk_level, "high");
}

#[test]
fn high_amount_threshold_boundary() {
    // A5-4 (deferred): `amount` is an f64 and the threshold is strict `> 10000`.
    // This test pins the boundary contract so any future move to integer minor
    // units / Decimal must preserve it:
    //   - exactly 10000      -> NOT high_amount (rule is strictly greater-than)
    //   - just above 10000   -> high_amount fires
    let at = score(&txn(10000.0, "IN", "electronics"));
    assert_eq!(at.score, 0, "amount == 10000 must NOT trigger high_amount");
    assert!(!at.reasons.contains(&"high_amount".to_string()));

    let above = score(&txn(10000.01, "IN", "electronics"));
    assert_eq!(above.score, 40, "amount > 10000 must trigger high_amount");
    assert!(above.reasons.contains(&"high_amount".to_string()));
}

#[test]
fn malformed_json_is_err_no_panic() {
    // Parsing bad input must return Err (never panic).
    let parsed: Result<Transaction, _> = serde_json::from_str("{ not valid json ");
    assert!(parsed.is_err());

    // Missing required fields must also fail to deserialize.
    let missing: Result<Transaction, _> =
        serde_json::from_str(r#"{"transaction_id":"x"}"#);
    assert!(missing.is_err());
}
