# curl Examples

## Registration + referral

```bash
curl -X POST http://localhost:8000/api/v1/identity/register \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "owner@example.com",
    "password": "StrongPass123",
    "full_name": "Owner User"
  }'
```

## Business onboarding

```bash
curl -X POST http://localhost:8000/api/v1/onboarding/businesses \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Idempotency-Key: onboarding-001' \
  -H 'Content-Type: application/json' \
  -d '{
    "tenant_name": "Neura Demo",
    "tenant_slug": "neura-demo",
    "company_name": "Neura Demo",
    "business_description": "AI marketing automation for B2B companies with strategy, content, and analytics.",
    "city": "Moscow",
    "industry": "Marketing",
    "services": ["Strategy", "Content"],
    "social_links": ["https://t.me/neura"],
    "target_audience": "SMB owners and growth teams",
    "competitors": ["Agency A"],
    "business_features": ["Fast onboarding", "Autopublishing"],
    "timezone": "Europe/Moscow"
  }'
```

## Launch AI strategy

```bash
curl -X POST http://localhost:8000/api/v1/onboarding/projects/<PROJECT_ID>/ai-analysis \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-ID: <TENANT_ID>" \
  -H 'Idempotency-Key: ai-analysis-001' \
  -H 'Content-Type: application/json' \
  -d '{"task_type": "strategy_generation"}'
```

## Create content plan

```bash
curl -X POST http://localhost:8000/api/v1/content-plans/projects/<PROJECT_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-ID: <TENANT_ID>" \
  -H 'Idempotency-Key: content-plan-001' \
  -H 'Content-Type: application/json' \
  -d '{
    "period_days": 30,
    "source_mode": "mixed",
    "platforms": ["telegram", "vk"],
    "content_types": ["post", "carousel"]
  }'
```

## Switch publishing mode

```bash
curl -X PATCH http://localhost:8000/api/v1/approval/projects/<PROJECT_ID>/policy \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-ID: <TENANT_ID>" \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "auto",
    "auto_publish_enabled": true,
    "auto_publish_platforms": ["telegram", "vk"]
  }'
```

## Approve publication

```bash
curl -X POST http://localhost:8000/api/v1/approval/publications/<PUBLICATION_ID>/approve \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-ID: <TENANT_ID>"
```

## Get analytics

```bash
curl http://localhost:8000/api/v1/analytics/projects/<PROJECT_ID> \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "X-Tenant-ID: <TENANT_ID>"
```
