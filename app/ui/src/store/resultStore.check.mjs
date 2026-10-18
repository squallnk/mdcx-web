// 自检: node src/store/resultStore.check.mjs
// 校验 WS 信号 -> 结果列表的分支、500 条上限、当前番号替换与进度归零。
import assert from "node:assert/strict";
import { useProgressStore } from "./progressStore.ts";
import { useResultStore } from "./resultStore.ts";

const results = useResultStore.getState();

results.addResult({ status: "succ", show_data: { data: { number: "ABP-001" } }, real_number: "ABP-001" });
results.addResult({ status: "fail", show_data: null, real_number: "ABP-002" });

assert.equal(useResultStore.getState().success.length, 1);
assert.equal(useResultStore.getState().failed.length, 1);
assert.equal(useResultStore.getState().success[0].real_number, "ABP-001");
assert.equal(useResultStore.getState().failed[0].show_data, null);

for (let i = 0; i < 600; i++) {
  results.addResult({ status: "succ", show_data: null, real_number: `X-${i}` });
}
const successAfter = useResultStore.getState().success;
assert.equal(successAfter.length, 500);
assert.equal(successAfter[499].real_number, "X-599");

results.setCurrent({ data: { title: "当前番号" } });
assert.equal(useResultStore.getState().current?.data?.title, "当前番号");
results.setCurrent(null);
assert.equal(useResultStore.getState().current, null);
results.clearResults();
assert.equal(useResultStore.getState().success.length + useResultStore.getState().failed.length, 0);

useProgressStore.getState().setProgress({ progress: 3, total: 10, percentage: 30, description: "Processing..." });
assert.equal(useProgressStore.getState().progress?.percentage, 30);
useProgressStore.getState().resetProgress();
assert.equal(useProgressStore.getState().progress, null);

console.log("resultStore/progressStore self-check passed");
