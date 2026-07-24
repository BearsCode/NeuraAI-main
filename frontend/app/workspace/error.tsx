"use client";

import { useEffect } from "react";

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function WorkspaceError({ error, reset }: Props) {
  useEffect(() => {
    console.error("Workspace error:", error);
  }, [error]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        padding: "60px 24px",
        textAlign: "center",
        gap: 16,
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: "50%",
          background: "rgba(239,68,68,0.1)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 32,
        }}
      >
        ⚠
      </div>
      <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 600, color: "var(--text-primary, #e2e8f0)" }}>
        Что-то пошло не так
      </h2>
      <p style={{ margin: 0, fontSize: "0.9rem", color: "var(--text-tertiary, #94a3b8)", maxWidth: 440 }}>
        {error.message || "Произошла непредвиденная ошибка. Попробуйте обновить страницу."}
      </p>
      <button
        onClick={reset}
        style={{
          marginTop: 8,
          padding: "10px 28px",
          borderRadius: 10,
          border: "none",
          background: "var(--accent, #3b82f6)",
          color: "#fff",
          fontSize: "0.9rem",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Попробовать снова
      </button>
    </div>
  );
}
