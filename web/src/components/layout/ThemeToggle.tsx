import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

import { Button } from "../ui/Button";

type ThemeMode = "dark" | "light";

const storageKey = "aidssist-theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>("dark");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(storageKey);
    if (savedTheme === "light" || savedTheme === "dark") {
      setTheme(savedTheme);
      applyTheme(savedTheme);
      return;
    }

    applyTheme("dark");
  }, []);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    window.localStorage.setItem(storageKey, nextTheme);
    applyTheme(nextTheme);
  }

  const Icon = theme === "dark" ? Moon : Sun;

  return (
    <Button
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      className="min-h-9 px-3"
      onClick={toggleTheme}
      variant="ghost"
    >
      <Icon size={16} aria-hidden="true" />
    </Button>
  );
}

function applyTheme(theme: ThemeMode) {
  document.documentElement.classList.toggle("theme-light", theme === "light");
}
