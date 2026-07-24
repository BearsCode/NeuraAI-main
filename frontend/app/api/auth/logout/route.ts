import { NextRequest, NextResponse } from "next/server";

import { REFRESH_COOKIE } from "@/lib/auth-cookie-names";
import { clearAuthCookies } from "@/lib/auth-cookies";
import { backendRequest } from "@/lib/backend";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;

  if (refreshToken) {
    await backendRequest("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => null);
  }

  const response = NextResponse.json({ ok: true }, { status: 200 });
  clearAuthCookies(response);
  return response;
}
