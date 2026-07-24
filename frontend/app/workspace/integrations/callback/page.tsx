"use client";

import { Suspense, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { apiFetch } from "@/lib/client";

function CallbackInner() {
  const router = useRouter();
  const params = useSearchParams();
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;

    const code = params.get("code");
    const state = params.get("state");
    const error = params.get("error");

    if (error || !code) {
      router.replace(`/workspace/integrations?error=oauth_${error ?? "denied"}`);
      return;
    }

    const stored = sessionStorage.getItem("oauth_state_" + state);
    if (!stored) {
      router.replace("/workspace/integrations?error=oauth_state_mismatch");
      return;
    }

    let parsed: { platform: string; code_verifier?: string; redirect_uri: string };
    try {
      parsed = JSON.parse(stored);
    } catch {
      router.replace("/workspace/integrations?error=oauth_invalid_state");
      return;
    }

    sessionStorage.removeItem("oauth_state_" + state);

    apiFetch("/api/backend/social/oauth/" + parsed.platform + "/callback", {
      method: "POST",
      body: JSON.stringify({
        code,
        redirect_uri: parsed.redirect_uri,
        code_verifier: parsed.code_verifier ?? null,
        autoposting_enabled: true,
        publication_settings: {},
      }),
    })
      .then(() => {
        router.replace("/workspace/integrations?ok=" + parsed.platform);
      })
      .catch(() => {
        router.replace("/workspace/integrations?error=oauth_callback_failed");
      });
  }, [params, router]);

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        color: "var(--ink-faint)",
        background: "var(--bg)",
      }}
    >
      Подключаем социальную сеть...
    </div>
  );
}

export default function OAuthCallbackPage() {
  return (
    <Suspense>
      <CallbackInner />
    </Suspense>
  );
}
