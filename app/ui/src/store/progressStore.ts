import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

// 对应服务端 WebSocket `type === "progress"` 消息的 data (mdcx/server/signals.py)
export interface ProgressPayload {
  progress: number;
  total: number;
  percentage: number;
  description: string;
}

interface ProgressStore {
  progress: ProgressPayload | null;

  // Actions
  setProgress: (progress: ProgressPayload) => void;
  resetProgress: () => void;
}

export const useProgressStore = create<ProgressStore>()(
  subscribeWithSelector((set) => ({
    progress: null,

    setProgress: (progress) => set({ progress }),

    resetProgress: () => set({ progress: null }),
  })),
);
