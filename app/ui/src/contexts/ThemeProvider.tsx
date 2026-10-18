import { createTheme, ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { createContext, type ReactNode, useEffect, useMemo, useState } from "react";

type ThemeMode = "light" | "dark" | "system";
type ResolvedMode = "light" | "dark";

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// 中文优先字体栈
const FONT_FAMILY = [
  '"Noto Sans CJK SC"',
  '"Noto Sans SC"',
  '"Source Han Sans SC"',
  '"PingFang SC"',
  '"Microsoft YaHei"',
  '"Hiragino Sans GB"',
  "system-ui",
  "-apple-system",
  '"Segoe UI"',
  "Roboto",
  "sans-serif",
].join(",");

const GLASS_BLUR = "blur(18px) saturate(140%)";

const createAppTheme = (mode: ResolvedMode) => {
  const dark = mode === "dark";
  const borderColor = dark ? "rgba(255,255,255,.08)" : "rgba(15,23,42,.08)";
  const border = `1px solid ${borderColor}`;
  const glass = dark ? "rgba(17,24,45,.62)" : "rgba(255,255,255,.72)";
  const glassStrong = dark ? "rgba(13,19,38,.88)" : "rgba(255,255,255,.9)";
  const radius = 16;

  return createTheme({
    palette: {
      mode,
      primary: { main: dark ? "#8ab4ff" : "#2563eb" },
      secondary: { main: dark ? "#c792ea" : "#7c3aed" },
      divider: borderColor,
      background: {
        default: dark ? "#070b18" : "#eef2fb",
        paper: glass,
      },
      text: {
        primary: dark ? "#e8ecf7" : "#0f172a",
        secondary: dark ? "#9aa6c2" : "#5b6785",
      },
    },
    shape: { borderRadius: 12 },
    typography: {
      fontFamily: FONT_FAMILY,
      h4: { fontWeight: 600, letterSpacing: ".02em" },
      h6: { fontWeight: 600 },
      button: { textTransform: "none", fontWeight: 600 },
    },
    components: {
      // 页面背景: 深色渐变 + 柔和光斑 (亮色模式换一套浅色光斑)
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            minHeight: "100vh",
            backgroundAttachment: "fixed",
            backgroundRepeat: "no-repeat",
            backgroundImage: dark
              ? [
                  "radial-gradient(1100px 620px at 12% -8%, rgba(72,110,255,.30), transparent 60%)",
                  "radial-gradient(900px 520px at 96% 6%, rgba(190,92,255,.22), transparent 62%)",
                  "radial-gradient(760px 520px at 50% 110%, rgba(24,224,196,.16), transparent 60%)",
                  "linear-gradient(160deg, #070b18 0%, #0b1124 45%, #05070f 100%)",
                ].join(",")
              : [
                  "radial-gradient(1000px 600px at 8% -10%, rgba(37,99,235,.18), transparent 60%)",
                  "radial-gradient(900px 520px at 98% 4%, rgba(168,85,247,.14), transparent 62%)",
                  "linear-gradient(160deg, #f6f8ff 0%, #eef2fb 55%, #e7ecf9 100%)",
                ].join(","),
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundColor: glass,
            backgroundImage: "none",
            border,
            borderRadius: radius,
            backdropFilter: GLASS_BLUR,
            WebkitBackdropFilter: GLASS_BLUR,
            boxShadow: dark ? "0 18px 48px rgba(2,6,23,.45)" : "0 18px 40px rgba(15,23,42,.10)",
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundColor: glass,
            backgroundImage: "none",
            border,
            borderRadius: radius,
            backdropFilter: GLASS_BLUR,
            WebkitBackdropFilter: GLASS_BLUR,
            boxShadow: dark ? "0 18px 48px rgba(2,6,23,.42)" : "0 18px 40px rgba(15,23,42,.10)",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: glassStrong,
            backgroundImage: "none",
            borderBottom: border,
            boxShadow: "none",
            backdropFilter: GLASS_BLUR,
            WebkitBackdropFilter: GLASS_BLUR,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: glass,
            backgroundImage: "none",
            borderRight: border,
            boxShadow: "none",
            backdropFilter: GLASS_BLUR,
            WebkitBackdropFilter: GLASS_BLUR,
          },
        },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
          root: { borderRadius: 10, paddingInline: 18 },
          containedPrimary: dark
            ? {
                backgroundImage: "linear-gradient(135deg, #4f7bff, #8ab4ff)",
                color: "#05070f",
                "&:hover": { backgroundImage: "linear-gradient(135deg, #6b90ff, #a3c6ff)" },
              }
            : {},
        },
      },
      MuiTableContainer: {
        styleOverrides: { root: { border, borderRadius: radius, backgroundImage: "none" } },
      },
      MuiTableCell: {
        styleOverrides: {
          root: { borderBottom: `1px solid ${borderColor}` },
          head: {
            fontWeight: 600,
            color: dark ? "#c3cde8" : "#33415c",
            backgroundColor: dark ? "rgba(255,255,255,.03)" : "rgba(15,23,42,.03)",
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: { "&:hover": { backgroundColor: dark ? "rgba(138,180,255,.06)" : "rgba(37,99,235,.05)" } },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            height: 8,
            borderRadius: 999,
            backgroundColor: dark ? "rgba(255,255,255,.08)" : "rgba(15,23,42,.08)",
          },
          bar: { borderRadius: 999, backgroundImage: "linear-gradient(90deg, #4f7bff, #22d3ee)" },
        },
      },
      MuiTabs: { styleOverrides: { indicator: { height: 3, borderRadius: 999 } } },
      MuiTab: { styleOverrides: { root: { textTransform: "none", fontWeight: 600 } } },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            backgroundColor: dark ? "rgba(255,255,255,.04)" : "rgba(255,255,255,.72)",
            "& fieldset": { borderColor },
          },
        },
      },
      MuiChip: { styleOverrides: { root: { borderRadius: 8 } } },
      MuiDialog: {
        styleOverrides: {
          paper: {
            backgroundColor: glassStrong,
            backgroundImage: "none",
            border,
            borderRadius: radius,
            backdropFilter: GLASS_BLUR,
            WebkitBackdropFilter: GLASS_BLUR,
          },
        },
      },
    },
  });
};

const resolveMode = (mode: ThemeMode): ResolvedMode => {
  if (mode !== "system") return mode;
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    if (typeof window === "undefined") return "dark";
    const storedMode = localStorage.getItem("themeMode");
    if (storedMode === "system" || storedMode === "light" || storedMode === "dark") return storedMode;
    // 深色为默认
    return "dark";
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const currentTheme = resolveMode(mode);
    document.documentElement.classList.toggle("dark", currentTheme === "dark");
    localStorage.setItem("themeMode", mode);

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = () => {
      if (mode === "system") {
        document.documentElement.classList.toggle("dark", mediaQuery.matches);
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [mode]);

  const theme = useMemo(() => createAppTheme(resolveMode(mode)), [mode]);

  return (
    <ThemeContext.Provider value={{ mode, setMode }}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
