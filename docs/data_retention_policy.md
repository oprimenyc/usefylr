# .fylr Data Retention and Disposal Policy

**Effective Date:** January 13, 2026

## 1. Purpose
This policy ensures .fylr manages consumer data responsibly, retaining it only for the duration necessary for financial reporting while remaining in compliance with CCPA, GDPR, and Plaid Security requirements.

## 2. Retention Schedule
| Data Category | Retention Period |
| :--- | :--- |
| Sensitive PII (SSN, EIN, Bank Details) | Active account + 60 days |
| Plaid Access Tokens | Duration of active account |
| Transaction History | Duration of active account |
| Terminated Accounts | Purged within 30 days |

## 3. Disposal Procedures
.fylr employs "Cryptographic Wiping":
- **Database Deletion:** Permanent removal of records.
- **Key Destruction:** AES-256 (Fernet) keys associated with the user are destroyed, rendering backup data unrecoverable.

## 4. Review
This policy is reviewed annually.
