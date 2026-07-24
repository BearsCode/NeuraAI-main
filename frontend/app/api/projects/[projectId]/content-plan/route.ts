import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import { readJson } from "@/lib/backend";
import type { ContentPlanGeneratePayload, ContentPlanResponse } from "@/lib/types";

type Params = { params: Promise<{ projectId: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { projectId } = await params;
  const result = await fetchWithAuth(request, `/content/${projectId}/plan`);

  if (!result.response.ok) {
    return backendErrorResponse(result.response, result.refreshedTokens);
  }

  const contentPlan = await readJson<ContentPlanResponse>(result.response);
  return finalizeJsonResponse({ contentPlan }, { refreshedTokens: result.refreshedTokens });
}

export async function POST(request: NextRequest, { params }: Params) {
  const { projectId } = await params;
  const rawBody = await request.json().catch(() => null);
  const payload = (rawBody ?? {}) as ContentPlanGeneratePayload;
  const result = await fetchWithAuth(request, `/content/${projectId}/plan/generate`, {
    method: "POST",
    body: JSON.stringify({
      period_days: payload.period_days ?? 30,
      source_mode: payload.source_mode ?? "mixed",
      platforms: payload.platforms ?? [],
      content_types: payload.content_types ?? [],
    }),
  });

  if (!result.response.ok) {
    return backendErrorResponse(result.response, result.refreshedTokens);
  }

  const contentPlan = await readJson<ContentPlanResponse>(result.response);
  return finalizeJsonResponse(
    { contentPlan },
    { status: 201, refreshedTokens: result.refreshedTokens },
  );
}
