import { NextRequest } from "next/server";

import { backendErrorResponse, fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import type {
  AIAnalysisResponse,
  AIRecommendationResponse,
  ContentPlanResponse,
  DashboardResponse,
  ProjectOverviewResponse,
  ProjectResponse,
  StrategyResponse,
  TokenResponse,
} from "@/lib/types";

type Params = { params: Promise<{ projectId: string }> };

async function parallelFetch<T>(
  request: NextRequest,
  path: string,
  refreshedTokens: TokenResponse[],
): Promise<{ data: T | null; ok: boolean }> {
  const { response, refreshedTokens: tokens } = await fetchWithAuth(request, path);
  if (tokens) refreshedTokens.push(tokens);
  if (!response.ok) return { data: null, ok: false };
  const data = (await response.json()) as T;
  return { data, ok: true };
}

export async function GET(request: NextRequest, { params }: Params) {
  const { projectId } = await params;
  const projectResult = await fetchWithAuth(request, `/projects/${projectId}`);

  if (!projectResult.response.ok) {
    return backendErrorResponse(projectResult.response, projectResult.refreshedTokens);
  }

  const project = await projectResult.response.json() as ProjectResponse;
  const refreshed: TokenResponse[] = [];
  if (projectResult.refreshedTokens) refreshed.push(projectResult.refreshedTokens);

  try {
    const [dashboardRes, contentPlanRes, strategyRes, analysisRes, recommendationsRes] =
      await Promise.all([
        parallelFetch<DashboardResponse>(request, `/dashboard/${projectId}`, refreshed),
        parallelFetch<ContentPlanResponse>(request, `/content/${projectId}/plan`, refreshed),
        project.strategy_status === "draft"
          ? Promise.resolve<{ data: StrategyResponse | null; ok: boolean }>({ data: null, ok: true })
          : parallelFetch<StrategyResponse>(request, `/ai/${projectId}/strategy`, refreshed),
        project.strategy_status === "draft"
          ? Promise.resolve<{ data: AIAnalysisResponse | null; ok: boolean }>({ data: null, ok: true })
          : parallelFetch<AIAnalysisResponse>(request, `/ai/${projectId}/analysis`, refreshed),
        project.strategy_status === "draft"
          ? Promise.resolve<{ data: AIRecommendationResponse | null; ok: boolean }>({ data: null, ok: true })
          : parallelFetch<AIRecommendationResponse>(request, `/ai/${projectId}/recommendations`, refreshed),
      ]);

    if (!dashboardRes.ok || !contentPlanRes.ok) {
      return finalizeJsonResponse(
        { message: "Failed to load project data" },
        { status: 502, refreshedTokens: refreshed.length > 0 ? refreshed[refreshed.length - 1] : undefined },
      );
    }

    const overview: ProjectOverviewResponse = {
      project,
      dashboard: dashboardRes.data!,
      strategy: strategyRes.data ?? null,
      analysis: analysisRes.data ?? null,
      recommendations: recommendationsRes.data ?? null,
      contentPlan: contentPlanRes.data!,
    };

    return finalizeJsonResponse(
      { overview },
      { refreshedTokens: refreshed.length > 0 ? refreshed[refreshed.length - 1] : undefined },
    );
  } catch (error) {
    return finalizeJsonResponse(
      {
        message: error instanceof Error ? error.message : "Failed to load project overview",
      },
      { status: 500, refreshedTokens: refreshed.length > 0 ? refreshed[refreshed.length - 1] : undefined },
    );
  }
}