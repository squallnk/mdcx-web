import "./App.css";
import CssBaseline from "@mui/material/CssBaseline";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { client } from "./client/client.gen";
import { ThemeProvider } from "./contexts/ThemeProvider";
import { ToastProvider } from "./contexts/ToastProvider";
import { webSocketManager } from "./hooks/useWebSocket";
import { routeTree } from "./routeTree.gen";
import { type LogEntry, useLogStore } from "./store/logStore";
import { type ProgressPayload, useProgressStore } from "./store/progressStore";
import { type ScrapeShowData, type ShowListNamePayload, useResultStore } from "./store/resultStore";

const router = createRouter({ routeTree });
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

// 首个请求可能早于 __root 的 useEffect 发出，这里在模块作用域先定好 baseURL/auth，
// 否则会先打到生成代码里的 localhost:8000 默认值。
client.setConfig({
  baseURL: import.meta.env.PROD ? "" : import.meta.env.PUBLIC_DEV_API_URL,
  auth: localStorage.getItem("apiKey") ?? undefined,
});

// Add interceptor to handle invalid API Key
client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("apiKey");
      router.navigate({ to: "/auth" });
    }
    return Promise.reject(error);
  },
);

// 注册全局 WebSocket 消息处理器
webSocketManager.addHandler<LogEntry>("qt_signal", (log, msg) => {
  // 原有行为不变: 所有 qt_signal 都进日志
  useLogStore.getState().addLog(msg);

  const payload = log?.data;
  if (!payload || typeof payload !== "object") return;

  // 按 signal name 分发到结果 store (见 docs/API-CONTRACT.md 第 3 节)
  if (log.name === "show_list_name") {
    useResultStore.getState().addResult(payload as ShowListNamePayload);
  } else if (log.name === "set_main_info") {
    useResultStore.getState().setCurrent((payload as { show_data: ScrapeShowData | null }).show_data ?? null);
  }
});

// 进度消息的 type 是 "progress", 不是 "qt_signal"
webSocketManager.addHandler<ProgressPayload>("progress", (data) => {
  if (!data) return;
  const { setProgress, resetProgress } = useProgressStore.getState();
  // 百分比走满即视为本轮结束, 进度条归零
  if ((data.percentage ?? 0) >= 100) {
    resetProgress();
  } else {
    setProgress(data);
  }
});

const App = () => {
  const queryClient = new QueryClient();
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <CssBaseline />
          <RouterProvider router={router} />
          <ReactQueryDevtools />
        </ToastProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
