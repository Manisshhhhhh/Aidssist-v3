import { useEffect, useState } from "react";

export function useWebGLAvailable() {
  const [isAvailable, setIsAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    setIsAvailable(checkWebGLSupport());
  }, []);

  return isAvailable;
}

function checkWebGLSupport(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      window.WebGLRenderingContext &&
        (canvas.getContext("webgl2") || canvas.getContext("webgl")),
    );
  } catch {
    return false;
  }
}
