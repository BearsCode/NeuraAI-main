import { NextResponse } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth-cookie-names";
import type { TokenResponse } from "@/lib/types";

export { ACCESS_COOKIE, REFRESH_COOKIE };

function isSecureCookie(): boolean {
  return process.env.SECURE_COOKIES === "true";
}

export function setAuthCookies(
  response: NextResponse,
  tokens: TokenResponse,
): void {
  response.cookies.set({
    name: ACCESS_COOKIE,
    value: tokens.access_token,
    httpOnly: true,
    sameSite: "strict",
    secure: isSecureCookie(),
    path: "/",
    maxAge: tokens.expires_in,
  });

  response.cookies.set({
    name: REFRESH_COOKIE,
    value: tokens.refresh_token,
    httpOnly: true,
    sameSite: "strict",
    secure: isSecureCookie(),
    path: "/",
    maxAge: tokens.refresh_expires_in,
  });
}

export function clearAuthCookies(response: NextResponse): void {
  response.cookies.set({
    name: ACCESS_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "strict",
    secure: isSecureCookie(),
    path: "/",
    maxAge: 0,
  });

  response.cookies.set({
    name: REFRESH_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "strict",
    secure: isSecureCookie(),
    path: "/",
    maxAge: 0,
  });
}
