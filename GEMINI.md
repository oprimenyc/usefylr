# fylr | Strategic Roadmap & Core Principles

## 🎯 The Mission
To build a "TurboTax Killer" for the gig economy that combines "Quiet Luxury" UI with "Hard-Wired" IRS compliance.

## ⚖️ Non-Negotiable Tax Logic
1. TEMPORAL VERSIONING: All math must support 2021-2026. Never flatten logic into a single year.
2. CITATION-LINKED: Every major calculation must eventually map to an IRC Section or IRS Publication.
3. CONSISTENCY ENGINE: All user data must be cross-referenced against industry benchmarks (DIF Scoring).

## 🎨 UI/UX Standards (Antigravity Protocol)
- Theme: "Quiet Luxury" (Deep blacks, pure whites, #FF7043 accents).
- Motion: 0.6s cubic-bezier transitions. No "cheap" snapping.
- Mobile: Sticky headers must collapse; no horizontal overflow on 393px width.

## 🏗️ Technical Architecture
- Database: Single Source of Truth (fylr/instance/database.db).
- Engine: Centralized in `app/services/tax_engine.py`.
- Security: `is_admin` flag required for all `/admin` routes.

## 🚀 The "Killer" Backlog (To Be Implemented)
- [ ] OCR Document Intelligence (1099-NEC/K parsing).
- [ ] MeF JSON Generation (E-file Readiness).
- [ ] Real-time Industry Benchmarking.
