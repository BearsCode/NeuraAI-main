import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import { readJson } from "@/lib/backend";
import type {
  BusinessOnboardingPayload,
  ProjectResponse,
  ProjectSummaryResponse,
} from "@/lib/types";

export async function GET(request: NextRequest) {
  const { response, refreshedTokens } = await fetchWithAuth(request, "/projects");

  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }

  const projects = await readJson<ProjectSummaryResponse[]>(response);
  return finalizeJsonResponse({ projects }, { refreshedTokens });
}

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as BusinessOnboardingPayload;
  const { response, refreshedTokens } = await fetchWithAuth(request, "/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }

  const project = await readJson<ProjectResponse>(response);
  return finalizeJsonResponse({ project }, { status: 201, refreshedTokens });
}
