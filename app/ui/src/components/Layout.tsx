import {
  Article,
  Brightness4,
  Brightness7,
  BrightnessAuto,
  Build,
  ChevronLeft,
  ChevronRight,
  Home,
  Info,
  Lan,
  ListAlt,
  Menu,
  Settings,
} from "@mui/icons-material";
import {
  Box,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  AppBar as MuiAppBar,
  type AppBarProps as MuiAppBarProps,
  styled,
  Toolbar,
  Typography,
} from "@mui/material";
import { Link } from "@tanstack/react-router";
import { type ReactNode, useState } from "react";
import { useTheme } from "@/hooks/useTheme";
import type { FileRouteTypes } from "@/routeTree.gen";
import { useProgressStore } from "@/store/progressStore";

const drawerWidth = 240;
const collapsedDrawerWidth = 60;

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })(({ theme }) => ({
  flexGrow: 1,
  padding: theme.spacing(3),
  minHeight: "100vh",
  transition: theme.transitions.create("margin", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: 0,
}));

interface AppBarProps extends MuiAppBarProps {
  open?: boolean;
}

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== "open",
})<AppBarProps>(({ theme, open }) => ({
  transition: theme.transitions.create(["margin", "width"], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  // necessary for content to be below app bar
  ...theme.mixins.toolbar,
  justifyContent: "flex-end",
}));

const createMenuItems = <
  T extends readonly {
    text: string;
    to: FileRouteTypes["to"];
    icon: ReactNode;
  }[],
>(
  items: T,
) => items;

// 订阅 WebSocket `progress` 消息 (见 App.tsx 的处理器)
function ScrapeProgress() {
  const progress = useProgressStore((state) => state.progress);
  if (!progress) return null;

  const percentage = Math.min(100, Math.max(0, progress.percentage ?? 0));

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", mb: 0.75, gap: 2 }}>
        <Typography variant="body2" color="text.secondary" noWrap>
          {progress.description || "正在刮削..."}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: "nowrap" }}>
          {progress.progress}/{progress.total} · {percentage}%
        </Typography>
      </Box>
      <LinearProgress variant="determinate" value={percentage} />
    </Box>
  );
}

export default function Layout({ children }: { children: ReactNode }) {
  const { mode, setMode } = useTheme();
  const [open, setOpen] = useState(true);

  const handleThemeChange = () => {
    const newMode = mode === "light" ? "dark" : mode === "dark" ? "system" : "light";
    setMode(newMode);
  };

  const menuItems = createMenuItems([
    { text: "概览", to: "/", icon: <Home /> },
    { text: "工具", to: "/tool", icon: <Build /> },
    { text: "结果", to: "/results", icon: <ListAlt /> },
    { text: "网络", to: "/network", icon: <Lan /> },
    { text: "日志", to: "/logs", icon: <Article /> },
    { text: "设置", to: "/settings", icon: <Settings /> },
    { text: "关于", to: "/about", icon: <Info /> },
  ]);

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="切换侧边栏"
            onClick={() => setOpen(!open)}
            edge="start"
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1, letterSpacing: ".04em" }}>
            MDCx
          </Typography>
          <IconButton color="inherit" onClick={handleThemeChange} aria-label="切换主题">
            {mode === "light" ? <Brightness7 /> : mode === "dark" ? <Brightness4 /> : <BrightnessAuto />}
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        sx={{
          width: open ? drawerWidth : collapsedDrawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: open ? drawerWidth : collapsedDrawerWidth,
            boxSizing: "border-box",
            transition: "width 0.2s",
          },
        }}
        variant="persistent"
        anchor="left"
        open={true}
      >
        <DrawerHeader>
          <IconButton onClick={() => setOpen(!open)}>{open ? <ChevronLeft /> : <ChevronRight />}</IconButton>
        </DrawerHeader>
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.to} disablePadding>
              <ListItemButton
                component={Link}
                to={item.to}
                activeProps={{ style: { fontWeight: "bold" } }}
                sx={{ borderRadius: 2, mx: 1, my: 0.25 }}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} sx={{ opacity: open ? 1 : 0 }} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <Main>
        <DrawerHeader />
        <ScrapeProgress />
        {children}
      </Main>
    </Box>
  );
}
