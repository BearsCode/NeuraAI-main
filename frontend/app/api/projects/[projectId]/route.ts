import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import { readJson } from "@/lib/backend";
import type { ProjectResponse } from "@/lib/types";

type Params = { params: Promise<{ projectId: string }> };

export async function GET(request: NextRequest, { params }: Params) {
  const { projectId } = await params;
  const { response, refreshedTokens } = await fetchWithAuth(
    request,
    `/projects/${projectId}`,
  );

  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }

  const project = await readJson<ProjectResponse>(response);
  return finalizeJsonResponse({ project }, { refreshedTokens });
}
