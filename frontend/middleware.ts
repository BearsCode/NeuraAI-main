import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { ACCESS_COOKIE, REFRESH_COOKIE } from "@/lib/auth-cookie-names";

const authPages = new Set(["/login", "/register", "/admin-login"]);

const DECOY_PATHS: string[] = [];

function isDynamicAdminPath(pathname: string): boolean {
  return /^\/[a-f0-9]{12}-admin(?:\/.*)?$/.test(pathname);
}

function isDynamicAdminLoginPath(pathname: string): boolean {
  return /^\/[a-f0-9]{12}-admin-login$/.test(pathname);
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const cleanPath = pathname.replace(/\/+$/, "") || "/";

  if (cleanPath.startsWith("/_next") || cleanPath.startsWith("/api") || cleanPath === "/favicon.ico") {
    return NextResponse.next();
  }

  const hasSession =
    request.cookies.has(ACCESS_COOKIE) || request.cookies.has(REFRESH_COOKIE);

  // Dynamic admin login path → rewrite to /admin-login
  if (isDynamicAdminLoginPath(cleanPath)) {
    const url = new URL("/admin-login", request.url);
    url.search = request.nextUrl.search;
    return NextResponse.rewrite(url);
  }

  // Decoy paths → 404
  if (DECOY_PATHS.some((p) => cleanPath === p || cleanPath.startsWith(p + "/"))) {
    return new NextResponse("Not Found", { status: 404 });
  }

  // Dynamic admin panel → redirect to hashed login if no session
  if (isDynamicAdminPath(cleanPath)) {
    if (!hasSession) {
      const base = cleanPath.match(/^\/[a-f0-9]{12}-admin/)?.[0] || cleanPath;
      const loginUrl = new URL(base.replace(/-admin$/, "-admin-login"), request.url);
      return NextResponse.redirect(loginUrl);
    }
    const subPath = cleanPath.replace(/^\/[a-f0-9]{12}-admin/, "") || "/";
    const url = new URL("/admin" + subPath, request.url);
    url.search = request.nextUrl.search;
    return NextResponse.rewrite(url);
  }

  // Protected workspace/onboarding paths
  const protectedPaths = ["/workspace", "/onboarding"];
  const isProtected = protectedPaths.some((p) => cleanPath === p || cleanPath.startsWith(p + "/"));

  if (isProtected && !hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", cleanPath);
    return NextResponse.redirect(loginUrl);
  }

  // Already logged in → redirect auth pages to workspace
  if (authPages.has(cleanPath) && hasSession) {
    return NextResponse.redirect(new URL("/workspace", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};
