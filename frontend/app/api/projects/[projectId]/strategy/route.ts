import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import { readJson } from "@/lib/backend";
import type { StrategyResponse } from "@/lib/types";

type Params = { params: Promise<{ projectId: string }> };

export async function POST(request: NextRequest, { params }: Params) {
  const { projectId } = await params;
  const generation = await fetchWithAuth(request, `/ai/${projectId}/generate`, {
    method: "POST",
  });

  if (!generation.response.ok) {
    return backendErrorResponse(generation.response, generation.refreshedTokens);
  }

  const strategy = await readJson<StrategyResponse>(generation.response);
  return finalizeJsonResponse(
    { strategy },
    { refreshedTokens: generation.refreshedTokens },
  );
}
