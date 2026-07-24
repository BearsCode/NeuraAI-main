"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "60px 24px",
          textAlign: "center",
          gap: 16,
        }}>
          <div style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "rgba(239,68,68,0.1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 28,
          }}>
            ⚠
          </div>
          <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary, #e2e8f0)" }}>
            Что-то пошло не так
          </h3>
          <p style={{ margin: 0, fontSize: "0.88rem", color: "var(--text-tertiary, #94a3b8)", maxWidth: 400 }}>
            {this.state.error?.message || "Произошла непредвиденная ошибка. Попробуйте обновить страницу."}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              marginTop: 8,
              padding: "10px 24px",
              borderRadius: 10,
              border: "none",
              background: "var(--accent, #3b82f6)",
              color: "#fff",
              fontSize: "0.88rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Попробовать снова
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
