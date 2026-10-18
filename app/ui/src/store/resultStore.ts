import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

/**
 * ShowData (mdcx/models/types.py) 经 dataclasses.asdict 序列化后的形状。
 * 只声明界面用到的字段, 其余保持可选, 避免为生成类型之外的字段做无谓映射。
 */
export interface ScrapeShowData {
  show_name?: string;
  file_info?: {
    number?: string;
    file_name?: string;
    file_path?: string;
    mosaic?: string;
    [key: string]: unknown;
  };
  data?: {
    number?: string;
    title?: string;
    originaltitle?: string;
    actors?: string[];
    directors?: string[];
    outline?: string;
    poster?: string;
    thumb?: string;
    release?: string;
    year?: string;
    runtime?: string;
    score?: string;
    series?: string;
    studio?: string;
    publisher?: string;
    mosaic?: string;
    tags?: string[];
    [key: string]: unknown;
  };
  other?: Record<string, unknown>;
}

export interface ScrapeListEntry {
  id: string;
  status: "succ" | "fail";
  real_number: string;
  show_data: ScrapeShowData | null;
}

export interface ShowListNamePayload {
  status: "succ" | "fail";
  show_data: ScrapeShowData | null;
  real_number: string;
}

// 与服务端 signals.show_list_name 的调用节奏一致, 给个上限防止长时间刮削撑爆内存
const MAX_ENTRIES = 500;
let seq = 0;

interface ResultStore {
  success: ScrapeListEntry[];
  failed: ScrapeListEntry[];
  current: ScrapeShowData | null;

  // Actions
  addResult: (payload: ShowListNamePayload) => void;
  setCurrent: (showData: ScrapeShowData | null) => void;
  clearResults: () => void;
}

const append = (list: ScrapeListEntry[], entry: ScrapeListEntry) => [...list, entry].slice(-MAX_ENTRIES);

export const useResultStore = create<ResultStore>()(
  subscribeWithSelector((set) => ({
    success: [],
    failed: [],
    current: null,

    addResult: (payload) =>
      set((state) => {
        const entry: ScrapeListEntry = {
          id: `${Date.now()}-${seq++}`,
          status: payload.status,
          real_number: payload.real_number ?? "",
          show_data: payload.show_data ?? null,
        };
        return payload.status === "succ"
          ? { success: append(state.success, entry) }
          : { failed: append(state.failed, entry) };
      }),

    setCurrent: (showData) => set({ current: showData }),

    clearResults: () => set({ success: [], failed: [], current: null }),
  })),
);
