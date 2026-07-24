import { NextRequest } from "next/server";
import { fetchWithAuth, finalizeJsonResponse } from "@/lib/backend-auth";
import type {
  AnalyticsSummary,
  MvpContentPlanResponse,
  MvpStrategyResponse,
  ProfileResponse,
  ProjectSummaryResponse,
  PublishedPost,
  SocialAccount,
  TokenResponse,
} from "@/lib/types";

async function authFetch<T>(
  request: NextRequest,
  path: string,
  results: TokenResponse[],
): Promise<T | null> {
  const { response, refreshedTokens } = await fetchWithAuth(request, path);
  if (refreshedTokens) results.push(refreshedTokens);
  if (!response.ok) return null;
  return (await response.json()) as T;
}

export async function GET(request: NextRequest) {
  const refreshed: TokenResponse[] = [];

  const [userRes, projectsRes, socialsRes, strategyRes, planRes, pubsRes, analyticsRes, recommendationsRes] = await Promise.all([
    authFetch<ProfileResponse>(request, "/users/me", refreshed),
    authFetch<ProjectSummaryResponse[]>(request, "/projects", refreshed),
    authFetch<SocialAccount[]>(request, "/social", refreshed),
    authFetch<MvpStrategyResponse>(request, "/business/strategy", refreshed),
    authFetch<MvpContentPlanResponse>(request, "/content/plan", refreshed),
    authFetch<PublishedPost[]>(request, "/publishing/history", refreshed),
    authFetch<AnalyticsSummary>(request, "/analytics/summary", refreshed),
    authFetch<Record<string, unknown>[]>(request, "/business/recommendations", refreshed),
  ]);

  return finalizeJsonResponse({
    user: userRes ?? null,
    projects: projectsRes ?? [],
    analytics: analyticsRes ?? null,
    strategy: strategyRes ?? null,
    socials: socialsRes ?? [],
    contentPlan: planRes ?? null,
    publications: pubsRes ?? [],
    recommendations: recommendationsRes ?? [],
  }, refreshed.length > 0 ? { refreshedTokens: refreshed[refreshed.length - 1] } : {});
}