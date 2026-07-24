import { NextResponse } from "next/server";

import { setAuthCookies } from "@/lib/auth-cookies";
import { backendRequest, readErrorMessage } from "@/lib/backend";
import type { TokenResponse } from "@/lib/types";

export async function POST(request: Request): Promise<NextResponse> {
  const payload = await request.json();
  const response = await backendRequest("/auth/oauth/telegram", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return NextResponse.json(
      { message: await readErrorMessage(response) },
      { status: response.status },
    );
  }

  const tokens = (await response.json()) as TokenResponse;
  const nextResponse = NextResponse.json({ user: tokens.user }, { status: 200 });
  setAuthCookies(nextResponse, tokens);
  return nextResponse;
}
