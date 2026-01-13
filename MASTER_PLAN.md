# .fylr Master Manifesto (2026 Expansion)

## Phase 1: Compliance & Security
- [ ] Monitor Plaid RFI (Check Dashboard Daily)
- [ ] Draft Mobile-Optimized Privacy Policy (/privacy)
- [ ] Draft Mobile-Optimized Terms of Service (/terms)
- [ ] Move AES-256 Fernet Keys to Secrets Manager
- [ ] Implement 30-Day Database Backup Rotation
- [ ] Set up Managed Postgres (Production DB)
- [ ] Verify DNS: MX Records for email
- [ ] Verify DNS: SPF/DKIM for 'noreply@usefylr.app'

## Phase 2: UI "Shatter-Proofing"
- [ ] Implement CSS Grid for Dashboard Cards (Side-by-Side Desktop)
- [ ] Stack Cards 100% Width on Mobile (No gaps)
- [ ] Force 'overflow-x: hidden' on Body to kill Horizontal Scroll
- [ ] Apply 'inputmode=numeric' to all OTP/MFA fields
- [ ] Fix 'Smart Ledger' Table (Mobile Row Collapse)
- [ ] Fix State/Year Dropdown (Expansion limit fix)
- [ ] Plaid Link Button: Full-width + Fixed-bottom on mobile

## Phase 3: Accuracy & The "Bouncer"
- [ ] Audit Currency Logic: Convert all Floats to 'Decimal' library
- [ ] Build Timestamped Audit Log (Track every ledger change)
- [ ] Plaid Connection Health: Alert user on Token Expiry
- [ ] Evidence Link: ID-match every Transaction to OCR Receipt
- [ ] Account Deletion: Implement 'Cryptographic Wipe' trigger

## Phase 4: The "Transformer" (Gig & Small Biz Logic)
- [ ] 2026 OBBBA Logic: Auto-detect 'Tax-Free Tips'
- [ ] 2026 OBBBA Logic: Auto-detect 'Tax-Free Overtime'
- [ ] Yield Widget: Real-time 'Net Take-Home' tracker
- [ ] Mileage vs Gas Engine: Auto-compare $0.67 rate vs Receipts
- [ ] Manual Cash Entry: Generate Digital Memos for Cash/Tips
- [ ] Trader Module: 1099-DA (Digital Assets) CSV Parser
- [ ] Trader Module: 1099-B (Stocks/Options) CSV Parser

## Phase 5: Native Localization
- [ ] Install Flask-Babel (i18n framework)
- [ ] Create Spanish JSON: Terminology check against IRS Pubs
- [ ] UI Flex-Test: Ensure Spanish strings don't overlap/break
- [ ] Language Toggle: Persistent user-pref (save to DB)
