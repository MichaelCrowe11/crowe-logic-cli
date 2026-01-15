# Crowe Logic CLI - Monetization Architecture

This document describes the monetization strategy and technical implementation for Crowe Logic CLI.

## Overview

The monetization model is a **tiered subscription** with optional enterprise licensing:

| Tier | Price | Target User |
|------|-------|-------------|
| Free | $0/month | Individual developers, evaluation |
| Pro | $19/month | Power users, small teams |
| Enterprise | Custom | Large organizations |

## Tier Features

### Free Tier
- **Commands**: `ask`, `chat`, `interactive`, `history`, `config`, `doctor`
- **Rate Limits**: 50 requests/day, 10 requests/hour
- **Token Limit**: 4,096 tokens per request
- **History**: 7-day retention, 10 saved conversations
- **Support**: Community (GitHub Issues)

### Pro Tier ($19/month)
Everything in Free, plus:
- **Commands**: `quantum`, `molecular`, `research`, `code`, `agents`, `plugins`, `mcp`
- **Features**: Cost tracking, JSON output, clipboard, retry logic
- **Rate Limits**: 1,000 requests/day, 100 requests/hour
- **Token Limit**: 32,000 tokens per request
- **History**: 90-day retention, 100 saved conversations
- **Support**: Email support with 48-hour response time

### Enterprise Tier (Custom)
Everything in Pro, plus:
- **Team Features**: SSO, role-based access, team sharing
- **Security**: Audit logs, compliance reports
- **Custom**: Custom model deployments, API access
- **Rate Limits**: Unlimited
- **Token Limit**: 128,000 tokens per request
- **History**: 365-day retention, unlimited conversations
- **Support**: Dedicated support, SLA guarantees

## Technical Implementation

### License Key Format

**Offline Keys** (for air-gapped environments):
```
{TIER}-{EMAIL_HASH}-{EXPIRY_YYYYMMDD}-{SIGNATURE}
```

Example: `PRO-a1b2c3-20261231-xyz789`

**Online Keys** (validated against license server):
```
{UUID}-{CHECKSUM}
```

Example: `550e8400-e29b-41d4-a716-446655440000-abc123`

### License Validation Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   CLI Call   │────▶│   Check      │────▶│   Feature    │
│              │     │   License    │     │   Available? │
└──────────────┘     └──────────────┘     └──────────────┘
                            │                    │
                            ▼                    │
                     ┌──────────────┐            │
                     │  Load from   │            │
                     │  ~/.crowelogic/│           │
                     │  license.json │            │
                     └──────────────┘            │
                            │                    │
                            ▼                    │
                     ┌──────────────┐            │
                     │  Validate    │            │
                     │  Expiry &    │            │
                     │  Signature   │            │
                     └──────────────┘            │
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌──────────────┐
                     │   Return     │────▶│   Execute    │
                     │   Tier Info  │     │   or Block   │
                     └──────────────┘     └──────────────┘
```

### License Storage

Licenses are stored in `~/.crowelogic/license.json`:

```json
{
  "tier": "pro",
  "email": "user@example.com",
  "organization": null,
  "expires_at": "2026-12-31T23:59:59Z",
  "issued_at": "2026-01-14T12:00:00Z",
  "features": ["quantum", "molecular", "research", ...],
  "limits": {
    "requests_per_day": 1000,
    "max_tokens_per_request": 32000
  }
}
```

### Feature Gating

Features are gated using the `@require_feature` decorator:

```python
from crowe_logic_cli.licensing import require_feature

@require_feature("quantum")
def quantum_command():
    # Only runs if user has Pro/Enterprise license
    ...
```

Or programmatically:

```python
from crowe_logic_cli.licensing import get_license_manager

manager = get_license_manager()
allowed, message = manager.check_feature("quantum")
if not allowed:
    print(f"Upgrade required: {message}")
```

### Rate Limiting

Rate limits are enforced per-tier using a sliding window counter stored in `~/.crowelogic/usage/rate_limits.json`:

```python
manager = get_license_manager()
allowed, message = manager.check_limit("requests_per_hour", current_count)
```

## Payment Integration

### Recommended: Stripe

1. **Pricing Page**: Static page at `https://crowelogic.com/pricing`
2. **Checkout**: Stripe Checkout session
3. **Webhook**: `/api/webhooks/stripe` handles subscription events
4. **License Delivery**: Email license key after successful payment

### API Endpoints (Backend Required)

```
POST /api/licenses/activate
  Body: { "license_key": "..." }
  Returns: { "success": true, "license": {...} }

POST /api/licenses/validate
  Body: { "license_key": "..." }
  Returns: { "valid": true, "tier": "pro", "expires_at": "..." }

GET /api/licenses/status
  Headers: Authorization: Bearer {license_key}
  Returns: { "tier": "pro", "usage": {...}, "limits": {...} }
```

## Revenue Projections

| Scenario | Monthly Users | Conversion Rate | MRR |
|----------|--------------|-----------------|-----|
| Conservative | 1,000 | 2% | $380 |
| Moderate | 5,000 | 3% | $2,850 |
| Optimistic | 10,000 | 5% | $9,500 |

## Implementation Roadmap

### Phase 1: Foundation (Current)
- [x] License management module (`licensing.py`)
- [x] CLI commands (`license status`, `activate`, `deactivate`)
- [x] Feature definitions and tier limits
- [x] Offline license key validation

### Phase 2: Backend
- [ ] License server API
- [ ] Stripe integration
- [ ] Usage tracking & analytics
- [ ] Admin dashboard

### Phase 3: Growth
- [ ] Annual billing (2 months free)
- [ ] Team/organization licenses
- [ ] Referral program
- [ ] Volume discounts

### Phase 4: Enterprise
- [ ] SSO integration (SAML, OIDC)
- [ ] Audit logging
- [ ] Custom SLAs
- [ ] On-premise deployment option

## CLI Commands

```bash
# View license status
crowelogic license status

# Activate a license
crowelogic license activate PRO-abc123-20261231-xyz789

# View features by tier
crowelogic license features

# Show upgrade options
crowelogic license upgrade

# Deactivate license
crowelogic license deactivate
```

## Security Considerations

1. **Key Storage**: License keys stored with file permissions 0600
2. **Validation**: Cryptographic signature verification (HMAC-SHA256)
3. **Grace Period**: 7-day grace period after expiration
4. **Offline Support**: Offline keys work without internet
5. **No Phone Home**: Free tier works entirely offline

## Metrics to Track

- License activations per day
- Conversion rate (Free → Pro)
- Churn rate
- Feature usage by tier
- Rate limit hit frequency
- Support ticket volume by tier

---

*Last updated: 2026-01-14*
