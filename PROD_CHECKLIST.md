# Production Deployment Checklist

**Last Updated:** 2026-01-08
**Status:** Ready for Production Deployment

---

## Required Environment Variables

Before deploying to production, configure the following environment variables in your hosting dashboard:

### 1. Flask Configuration

```bash
# Flask Environment
FLASK_ENV=production

# Secret Key (CRITICAL - Generate a new random key for production!)
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
FLASK_SECRET_KEY=<64-character-random-hex-string>
```

**Action Required:** Generate a new secret key for production using:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 2. Database Configuration

```bash
# Production Database URL (PostgreSQL recommended)
DATABASE_URL=postgresql://username:password@host:port/database_name
```

**Example for PostgreSQL:**
```bash
DATABASE_URL=postgresql://fylr_user:strong_password@db.yourhost.com:5432/fylr_production
```

**Example for SQLite (NOT recommended for production):**
```bash
DATABASE_URL=sqlite:///instance/fylr.db
```

**Action Required:**
- Set up production PostgreSQL database
- Update DATABASE_URL with production credentials

---

### 3. Stripe API Keys (LIVE KEYS)

```bash
# Stripe Secret Key (Live - starts with sk_live_)
STRIPE_SECRET_KEY=sk_live_...

# Stripe Publishable Key (Live - starts with pk_live_)
STRIPE_PUBLISHABLE_KEY=pk_live_...

# Stripe Webhook Secret (for production webhook endpoint)
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Action Required:**
1. Log into Stripe Dashboard → Developers → API Keys
2. Copy the **LIVE** secret key (sk_live_...)
3. Copy the **LIVE** publishable key (pk_live_...)
4. Set up production webhook endpoint and copy webhook secret

**WARNING:** Never use test keys (sk_test_) in production!

---

### 4. OpenAI API Key (LIVE KEY)

```bash
# OpenAI API Key (Production)
OPENAI_API_KEY=sk-proj-...
```

**Action Required:**
1. Log into OpenAI Platform → API Keys
2. Create a new production API key
3. Set appropriate usage limits and budgets

**Note:** OpenAI keys start with `sk-proj-` or `sk-`

---

## Environment Variables Summary Table

| Variable Name | Required | Example Value | Where to Get It |
|--------------|----------|---------------|-----------------|
| `FLASK_ENV` | Yes | `production` | Set manually |
| `FLASK_SECRET_KEY` | Yes | `a1b2c3...` (64 chars) | Generate with Python |
| `DATABASE_URL` | Yes | `postgresql://...` | Database provider |
| `STRIPE_SECRET_KEY` | Yes | `sk_live_...` | Stripe Dashboard |
| `STRIPE_PUBLISHABLE_KEY` | Yes | `pk_live_...` | Stripe Dashboard |
| `STRIPE_WEBHOOK_SECRET` | Yes | `whsec_...` | Stripe Webhooks |
| `OPENAI_API_KEY` | Yes | `sk-proj-...` | OpenAI Platform |

---

## Pre-Deployment Security Checklist

### Critical Security Items
- [ ] `FLASK_ENV=production` is set (DEBUG mode disabled)
- [ ] New random `FLASK_SECRET_KEY` generated for production
- [ ] Stripe LIVE keys configured (not test keys)
- [ ] OpenAI production API key configured
- [ ] PostgreSQL database set up (not SQLite)
- [ ] `.env` file is in `.gitignore` and not committed
- [ ] Database backups configured
- [ ] SSL/HTTPS enabled on hosting platform

### Application Readiness
- [ ] All migrations applied: `flask db upgrade`
- [ ] Error handlers active (500.html, 404.html)
- [ ] Logging configured (WARNING level in production)
- [ ] Stripe webhook endpoint configured and tested
- [ ] Test user created and tested locally

---

## Database Migration

Before starting the production server for the first time:

```bash
# Apply database migrations
flask db upgrade
```

This will create all necessary tables in the production database.

---

## Testing Production Configuration Locally

To test production configuration locally before deployment:

1. Create a `.env.production` file with production-like settings (use test API keys):
   ```bash
   FLASK_ENV=production
   FLASK_SECRET_KEY=test_secret_key_for_local_testing
   DATABASE_URL=sqlite:///instance/fylr_test.db
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   OPENAI_API_KEY=sk-proj-test...
   ```

2. Run the app:
   ```bash
   python main.py
   ```

3. Verify:
   - DEBUG mode is False (no stack traces on errors)
   - Error pages display correctly (404.html, 500.html)
   - Logging level is WARNING (not DEBUG)
   - All features work as expected

---

## Post-Deployment Verification

After deploying to production, verify:

1. **Health Check:**
   - [ ] Site loads at production URL
   - [ ] HTTPS is working (SSL certificate valid)
   - [ ] No error messages in logs

2. **Authentication:**
   - [ ] User registration works
   - [ ] User login works
   - [ ] Password reset works (if implemented)

3. **Stripe Integration:**
   - [ ] Subscription checkout works
   - [ ] Payment processing works
   - [ ] Webhooks are being received

4. **Database:**
   - [ ] Data is persisting correctly
   - [ ] Database backups are running

5. **Error Handling:**
   - [ ] 404 page displays for invalid URLs
   - [ ] 500 page displays for server errors (without stack trace)
   - [ ] Errors are logged but not exposed to users

---

## Emergency Rollback Plan

If critical issues occur in production:

1. **Immediate Actions:**
   - Set maintenance mode (if available)
   - Revert to previous deployment
   - Check error logs for root cause

2. **Database Rollback:**
   ```bash
   flask db downgrade
   ```

3. **Contact Information:**
   - Stripe Support: https://support.stripe.com
   - OpenAI Support: https://help.openai.com
   - Hosting Provider Support: [Your hosting provider]

---

## Monitoring & Maintenance

### Recommended Tools
- **Error Monitoring:** Sentry (https://sentry.io)
- **Uptime Monitoring:** UptimeRobot or Pingdom
- **Log Management:** Papertrail or Loggly
- **Performance Monitoring:** New Relic or DataDog

### Ongoing Tasks
- [ ] Monitor error logs daily
- [ ] Review Stripe webhooks for failures
- [ ] Check OpenAI API usage and costs
- [ ] Apply security updates monthly
- [ ] Review and rotate API keys quarterly
- [ ] Test database backups monthly

---

## Support Resources

- **Stripe Documentation:** https://stripe.com/docs
- **OpenAI API Documentation:** https://platform.openai.com/docs
- **Flask Documentation:** https://flask.palletsprojects.com
- **SQLAlchemy Documentation:** https://docs.sqlalchemy.org

---

## Security Audit Reference

For detailed security audit results, see: `SECURITY_AUDIT.md`

**Security Grade:** A- (Production Ready)
**Audit Date:** 2026-01-08

---

**Status:** ✅ All security fixes applied
**Ready for Production:** Yes (after environment variables configured)

---

*Generated for .fylr Platform - Tax Intelligence Platform*
*Last Updated: 2026-01-08*
