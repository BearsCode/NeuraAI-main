import { NextRequest } from "next/server";
import { fetchWithAuth, finalizeJsonResponse, backendErrorResponse } from "@/lib/backend-auth";
import type { TokenResponse } from "@/lib/types";

async function proxyGet(
  request: NextRequest,
  backendPath: string,
  init: RequestInit = {},
) {
  const refreshed: TokenResponse[] = [];
  const { response, refreshedTokens } = await fetchWithAuth(request, backendPath, init);
  if (refreshedTokens) refreshed.push(refreshedTokens);
  if (!response.ok) {
    return backendErrorResponse(response, refreshedTokens);
  }
  const data = response.status === 204 ? null : await response.json();
  return finalizeJsonResponse(data, refreshed.length > 0 ? { refreshedTokens: refreshed[refreshed.length - 1] } : {});
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const { path } = await params;
  return proxyGet(request, "/" + path.join("/"));
}

export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const backendPath = "/" + path.join("/");
  const body = request.headers.get("content-type")?.includes("application/json")
    ? await request.json()
    : undefined;
  return proxyGet(request, backendPath, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function PATCH(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const backendPath = "/" + path.join("/");
  const body = request.headers.get("content-type")?.includes("application/json")
    ? await request.json()
    : undefined;
  return proxyGet(request, backendPath, {
    method: "PATCH",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const backendPath = "/" + path.join("/");
  const body = request.headers.get("content-type")?.includes("application/json")
    ? await request.json()
    : undefined;
  return proxyGet(request, backendPath, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyGet(request, "/" + path.join("/"), { method: "DELETE" });
}
