import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import { readJson } from "@/lib/backend";
import type { ProfileResponse, UpdateProfilePayload } from "@/lib/types";

export async function GET(request: NextRequest) {
  const { response, refreshedTokens } = await fetchWithAuth(request, "/users/me");

  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }

  const user = await readJson<ProfileResponse>(response);
  return finalizeJsonResponse({ user }, { refreshedTokens });
}

export async function PATCH(request: NextRequest) {
  const payload = (await request.json()) as UpdateProfilePayload;
  const { response, refreshedTokens } = await fetchWithAuth(request, "/users/me", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }

  const user = await readJson<ProfileResponse>(response);
  return finalizeJsonResponse({ user }, { refreshedTokens });
}
