import { NextRequest, NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/auth-cookies";
import { backendRequest, readErrorMessage } from "@/lib/backend";
import type { TokenResponse } from "@/lib/types";

export async function GET(request: NextRequest): Promise<NextResponse> {
  const code = request.nextUrl.searchParams.get("code");
  const error = request.nextUrl.searchParams.get("error");

  if (error || !code) {
    return NextResponse.redirect(
      new URL("/login?error=yandex_auth_failed", request.url),
    );
  }

  const redirectUri = `${request.nextUrl.origin}/api/auth/oauth/yandex/callback`;

  const response = await backendRequest("/auth/oauth/yandex/callback", {
    method: "POST",
    body: JSON.stringify({ code, redirect_uri: redirectUri }),
  });

  if (!response.ok) {
    return NextResponse.redirect(
      new URL("/login?error=yandex_auth_failed", request.url),
    );
  }

  const tokens = (await response.json()) as TokenResponse;
  const nextResponse = NextResponse.redirect(
    new URL("/workspace", request.url),
  );
  setAuthCookies(nextResponse, tokens);
  return nextResponse;
}
