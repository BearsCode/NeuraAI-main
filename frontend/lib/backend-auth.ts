import { NextRequest, NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE, clearAuthCookies, setAuthCookies } from "@/lib/auth-cookies";
import { backendRequest, readErrorMessage } from "@/lib/backend";
import type { TokenResponse } from "@/lib/types";

async function refreshTokens(refreshToken: string): Promise<TokenResponse | null> {
  const response = await backendRequest("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!response.ok) {
    return null;
  }

  return (await response.json()) as TokenResponse;
}

async function sendAuthorizedRequest(
  path: string,
  init: RequestInit,
  accessToken: string,
): Promise<Response> {
  return backendRequest(path, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function fetchWithAuth(
  request: NextRequest,
  path: string,
  init: RequestInit = {},
): Promise<{ response: Response; refreshedTokens?: TokenResponse }> {
  const accessToken = request.cookies.get(ACCESS_COOKIE)?.value;
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  if (!accessToken && !refreshToken) {
    return {
      response: new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    };
  }

  if (!accessToken && refreshToken) {
    const tokens = await refreshTokens(refreshToken);
    if (!tokens) {
      return {
        response: new Response(JSON.stringify({ detail: "Session expired" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        }),
      };
    }

    return {
      response: await sendAuthorizedRequest(path, init, tokens.access_token),
      refreshedTokens: tokens,
    };
  }

  const initialResponse = await sendAuthorizedRequest(path, init, accessToken!);
  if (initialResponse.status !== 401 || !refreshToken) {
    return { response: initialResponse };
  }

  const tokens = await refreshTokens(refreshToken);
  if (!tokens) {
    return { response: initialResponse };
  }

  return {
    response: await sendAuthorizedRequest(path, init, tokens.access_token),
    refreshedTokens: tokens,
  };
}

export function finalizeJsonResponse(
  payload: unknown,
  init: { status?: number; refreshedTokens?: TokenResponse } = {},
): NextResponse {
  const response = NextResponse.json(payload, { status: init.status ?? 200 });
  if (init.refreshedTokens) {
    setAuthCookies(response, init.refreshedTokens);
  }
  return response;
}

export function finalizeEmptyResponse(
  init: { status?: number; refreshedTokens?: TokenResponse } = {},
): NextResponse {
  const response = new NextResponse(null, { status: init.status ?? 204 });
  if (init.refreshedTokens) {
    setAuthCookies(response, init.refreshedTokens);
  }
  return response;
}

export async function backendErrorResponse(
  response: Response,
  refreshedTokens?: TokenResponse,
): Promise<NextResponse> {
  const message = await readErrorMessage(response);
  const nextResponse = NextResponse.json(
    { message },
    { status: response.status },
  );

  if (response.status === 401) {
    clearAuthCookies(nextResponse);
  } else if (refreshedTokens) {
    setAuthCookies(nextResponse, refreshedTokens);
  }

  return nextResponse;
}
