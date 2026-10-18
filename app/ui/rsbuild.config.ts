import { defineConfig } from "@rsbuild/core";
import { pluginReact } from "@rsbuild/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/rspack";

const DEV_API_URL = "http://127.0.0.1:8000";
const DEV_WS_URL = "ws://127.0.0.1:8000";

export default defineConfig(({ command }) => {
  // 生产构建与后端同源：baseURL / wsHost 必须是空串字面量，不能是属性访问
  const isBuild = command === "build";

  return {
    plugins: [pluginReact()],
    tools: {
      rspack: {
        plugins: [tanstackRouter({ target: "react", autoCodeSplitting: true })],
      },
    },
    source: {
      define: {
        "import.meta.env.PROD": JSON.stringify(isBuild),
        "import.meta.env.PUBLIC_DEV_API_URL": JSON.stringify(isBuild ? "" : DEV_API_URL),
        "import.meta.env.PUBLIC_DEV_WS_URL": JSON.stringify(isBuild ? "" : DEV_WS_URL),
        // useWebSocket.ts 拿它跟字符串 "true" 比较，必须是字符串而不是布尔
        "import.meta.env.PUBLIC_DEV_ENABLE_WS": JSON.stringify("true"),
      },
    },
    server: {
      port: 3010,
    },
  };
});
