import { NextResponse } from "next/server";

import { backendRequest, readErrorMessage } from "@/lib/backend";
import type { RegisterPayload } from "@/lib/types";

export async function POST(request: Request): Promise<NextResponse> {
  const payload = (await request.json()) as RegisterPayload;
  const response = await backendRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return NextResponse.json(
      { message: await readErrorMessage(response) },
      { status: response.status },
    );
  }

  const body = await response.json();
  return NextResponse.json(body, { status: 201 });
}
