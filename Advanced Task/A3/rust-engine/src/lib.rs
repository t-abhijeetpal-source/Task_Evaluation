//! Deterministic Risk Scoring Engine (A3 shared contract v1.0).
//!
//! Implements the scoring rules defined in CONTRACT.md EXACTLY:
//! start at 0, add points, clamp to [0,100], then classify risk level.

use serde::{Deserialize, Serialize};

/// Default schema version used when the input omits `schema_version`.
fn default_schema_version() -> String {
    "1.0".to_string()
}

/// HIGH-RISK merchant categories per CONTRACT.md.
const HIGH_RISK_MERCHANTS: [&str; 4] = ["gambling", "crypto", "jewelry", "wire_transfer"];

/// Incoming transaction (matches the contract Transaction schema).
#[derive(Debug, Clone, Deserialize)]
pub struct Transaction {
    #[serde(default = "default_schema_version")]
    pub schema_version: String,
    pub transaction_id: String,
    pub user_id: String,
    pub amount: f64,
    pub country: String,
    pub merchant_category: String,
    pub timestamp: String,
}

/// Outgoing score result (matches the contract ScoreResult schema).
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct ScoreResult {
    pub schema_version: String,
    pub transaction_id: String,
    pub score: i64,
    pub risk_level: String,
    pub reasons: Vec<String>,
}

/// Score a transaction deterministically per CONTRACT.md.
///
/// Rules:
/// - `amount > 10000.0` -> +40, reason `high_amount`
/// - `country != "IN"`  -> +20, reason `foreign_country`
/// - `merchant_category` in HIGH-RISK set -> +30, reason `high_risk_merchant`
///
/// Score is clamped to `[0, 100]`. Risk level:
/// `< 30` -> `low`, `30..=69` -> `medium`, `>= 70` -> `high`.
pub fn score(txn: &Transaction) -> ScoreResult {
    let mut score: i64 = 0;
    let mut reasons: Vec<String> = Vec::new();

    if txn.amount > 10000.0 {
        score += 40;
        reasons.push("high_amount".to_string());
    }

    if txn.country != "IN" {
        score += 20;
        reasons.push("foreign_country".to_string());
    }

    if HIGH_RISK_MERCHANTS.contains(&txn.merchant_category.as_str()) {
        score += 30;
        reasons.push("high_risk_merchant".to_string());
    }

    // Clamp to [0, 100].
    let score = score.clamp(0, 100);

    let risk_level = if score < 30 {
        "low"
    } else if score <= 69 {
        "medium"
    } else {
        "high"
    }
    .to_string();

    ScoreResult {
        schema_version: txn.schema_version.clone(),
        transaction_id: txn.transaction_id.clone(),
        score,
        risk_level,
        reasons,
    }
}
