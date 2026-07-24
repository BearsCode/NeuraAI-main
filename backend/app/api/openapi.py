from __future__ import annotations

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Liveness, readiness and dependency checks for backend operations.",
    },
    {
        "name": "identity",
        "description": "Registration, login, token refresh, profile and password management.",
    },
    {
        "name": "auth",
        "description": "Compatibility authentication endpoints for MVP clients.",
    },
    {
        "name": "business_onboarding",
        "description": "Business questionnaire, tenant/project creation and AI analysis launch.",
    },
    {
        "name": "dashboard",
        "description": "Aggregated backend dashboard state for projects, strategy and content calendar.",
    },
    {
        "name": "social_integration",
        "description": "Telegram, VK, Instagram, Threads, TikTok, YouTube, WhatsApp Business and MAX connections.",
    },
    {
        "name": "content_plan",
        "description": "AI content plans, generated posts and versioned content assets.",
    },
    {
        "name": "approval_center",
        "description": "Manual and automatic approval policy, publication queue decisions and moderation.",
    },
    {
        "name": "publishing",
        "description": "Publication orchestration, queueing, retries, saga status and publication history.",
    },
    {
        "name": "analytics",
        "description": "Reach, followers, likes, comments, saves, CTR, ER and audience growth metrics.",
    },
    {
        "name": "ai_optimization",
        "description": "Weekly AI strategy optimization, recommendations and apply/dismiss workflow.",
    },
    {
        "name": "billing",
        "description": "SaaS plans, subscriptions, payments and partner commissions.",
    },
    {
        "name": "files",
        "description": "S3/local file storage, upload validation and signed access helpers.",
    },
    {
        "name": "admin",
        "description": "Backend-only administration for users, projects, subscriptions, tariffs and AI settings.",
    },
    {
        "name": "product_flow",
        "description": "Clean MVP product-flow aliases matching the Neura onboarding and dashboard journey.",
    },
    {
        "name": "users",
        "description": "Small utility endpoints for current-user inspection.",
    },
    {
        "name": "ai_core",
        "description": "AI Planner, Workflow Engine, Scheduler, Publisher Service — полностью автономный цикл генерации и публикации контента.",
    },
    {
        "name": "ai_avatar",
        "description": "Фото-аватар (LoRA на Replicate) и видео-аватар (talking head через HeyGen/D-ID).",
    },
    {
        "name": "ai_retail",
        "description": "Интеграция с товарными системами: 1С, МойСклад, AmoCRM, Битрикс24, Google Sheets.",
    },
    {
        "name": "agents",
        "description": "AI-агенты: Business, Marketing, Brand, Content, Image, Video, Retail, CEO, Checker, Training.",
    },
    {
        "name": "business_memory",
        "description": "Единое хранилище знаний: профиль компании, RLHF-предпочтения, аналитика, топик-модель, каталог.",
    },
    {
        "name": "internship",
        "description": "14-дневная AI-стажировка с RLHF-подходом: оценка контента, обучение предпочтениям, выбор режима.",
    },
]
