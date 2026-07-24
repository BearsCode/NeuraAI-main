# MVP-Compatible API

The production backend keeps the normalized bounded-context model internally, but exposes the MVP paths from the product brief under `/api/v1`.

## Core Flow

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","password":"StrongPass123","full_name":"Owner User"}'

curl -X POST http://localhost:8000/api/v1/business/profile \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{
    "company_name": "MVP Dental",
    "description": "Dental clinic with implantology and preventive services",
    "city": "Moscow",
    "industry": "dentistry",
    "services": ["implantology", "cleaning"],
    "target_audience": "Adults who need careful dental treatment",
    "competitors": ["Clinic A"],
    "features": ["certified doctors"]
  }'

curl -X POST http://localhost:8000/api/v1/social/connect \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"platform":"telegram","account_identifier":"@mvpdental","access_token":"token"}'

curl -X POST http://localhost:8000/api/v1/content/plan/generate \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"period_days":30,"platforms":["telegram"],"post_types":["post"]}'

curl http://localhost:8000/api/v1/approval/posts \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X POST http://localhost:8000/api/v1/approval/posts/<POST_ID>/approve \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X POST http://localhost:8000/api/v1/publishing/trigger \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H 'Content-Type: application/json' \
  -d '{"post_id":"<POST_ID>"}'

curl http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Mini Plan Flow

```bash
curl 'http://localhost:8000/api/v1/registration/referral?code=<REFERRAL_CODE>'

curl -X POST http://localhost:8000/api/v1/registration/email/request-code \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com"}'

curl -X POST http://localhost:8000/api/v1/registration/email/confirm \
  -H 'Content-Type: application/json' \
  -d '{"email":"owner@example.com","code":"<CODE_FROM_EMAIL_OR_DEBUG_CODE>"}'

curl -X POST http://localhost:8000/api/v1/registration/complete \
  -H 'Content-Type: application/json' \
  -d '{
    "first_name": "Owner",
    "last_name": "User",
    "email": "owner@example.com",
    "password": "StrongPass123",
    "company_name": "MVP Dental",
    "category": "dentistry",
    "inn": "7707083893",
    "offer_accepted": true,
    "data_confirmed": true
  }'

curl http://localhost:8000/api/v1/registration/status \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl http://localhost:8000/api/v1/tariffs

curl http://localhost:8000/api/v1/dashboard/user \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X POST http://localhost:8000/api/v1/dashboard/brand-analysis \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl -X POST http://localhost:8000/api/v1/social/analyze \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

curl http://localhost:8000/api/v1/social/analysis \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Mapping

- `business_profile_id` maps to the internal `projects.id`.
- MVP social accounts map to `social_integrations`.
- MVP planned posts map to `content_items`.
- MVP publication history maps to `publications` and `publication_targets`.
- MVP tariffs map to `subscription_plans`.
