import { NextResponse } from "next/server";
import { backendRequest, readJson } from "@/lib/backend";

type AdminPathResult = {
  today_path: string;
  yesterday_path: string;
  session_ttl_minutes: number;
};

export async function GET() {
  try {
    const response = await backendRequest("/admin/path");
    const data = await readJson<AdminPathResult>(response);
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { today_path: null, yesterday_path: null, session_ttl_minutes: 15 },
      { status: 200 },
    );
  }
}
