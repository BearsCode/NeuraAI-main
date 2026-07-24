"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            padding: "24px",
            textAlign: "center",
            gap: 16,
            background: "#0f172a",
            color: "#e2e8f0",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <h1 style={{ fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>
            Критическая ошибка
          </h1>
          <p style={{ fontSize: "0.9rem", color: "#94a3b8", maxWidth: 480, margin: 0 }}>
            {error.message || "Произошла критическая ошибка. Обновите страницу."}
          </p>
          <button
            onClick={() => reset()}
            style={{
              padding: "10px 28px",
              borderRadius: 10,
              border: "none",
              background: "#3b82f6",
              color: "#fff",
              fontSize: "0.9rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Обновить страницу
          </button>
        </div>
      </body>
    </html>
  );
}
