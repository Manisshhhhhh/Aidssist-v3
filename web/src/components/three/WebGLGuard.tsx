import { Component, type ErrorInfo, type ReactNode } from "react";

import { useReducedMotion } from "../../hooks/useReducedMotion";
import { useWebGLAvailable } from "../../hooks/useWebGLAvailable";

type WebGLGuardProps = {
  children: ReactNode;
  fallback: ReactNode;
};

export function WebGLGuard({ children, fallback }: WebGLGuardProps) {
  const prefersReducedMotion = useReducedMotion();
  const webGLAvailable = useWebGLAvailable();

  if (prefersReducedMotion || webGLAvailable === false) {
    return <>{fallback}</>;
  }

  if (webGLAvailable === null) {
    return null;
  }

  return <CanvasErrorBoundary fallback={fallback}>{children}</CanvasErrorBoundary>;
}

type CanvasErrorBoundaryProps = {
  children: ReactNode;
  fallback: ReactNode;
};

type CanvasErrorBoundaryState = {
  hasError: boolean;
};

class CanvasErrorBoundary extends Component<CanvasErrorBoundaryProps, CanvasErrorBoundaryState> {
  state: CanvasErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): CanvasErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.warn("Aidssist visual layer disabled after a WebGL error.", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}
