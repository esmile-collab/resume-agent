// Input: App 传入的状态、回调函数和后端返回数据。
// Output: 输出 RunTrace 面板 的 React 展示与交互片段。
// Pos: 前端业务面板组件。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import { useMemo, useState } from "react";

import type { TraceItem } from "../types";

function summarizePayload(trace: TraceItem) {
  if (trace.kind === "intent") {
    return `${trace.payload.intent ?? ""} · ${trace.payload.reason ?? ""}`;
  }
  if (trace.kind === "thought") {
    return `${trace.payload.tool_name ?? "no-tool"} · ${trace.payload.thought ?? ""}`;
  }
  if (trace.kind === "tool_call") {
    return `${trace.payload.tool_name ?? ""}`;
  }
  if (trace.kind === "observation") {
    return `${trace.payload.tool_name ?? ""}`;
  }
  return JSON.stringify(trace.payload);
}

export function RunTracePanel({ traces }: { traces: TraceItem[] }) {
  const [kindFilter, setKindFilter] = useState("all");
  const [messageFilter, setMessageFilter] = useState("all");
  const [search, setSearch] = useState("");

  const messageIds = useMemo(
    () => Array.from(new Set(traces.map((trace) => trace.message_id))),
    [traces],
  );

  const filteredTraces = useMemo(() => {
    return traces.filter((trace) => {
      if (kindFilter !== "all" && trace.kind !== kindFilter) {
        return false;
      }
      if (messageFilter !== "all" && trace.message_id !== messageFilter) {
        return false;
      }
      if (!search.trim()) {
        return true;
      }
      const haystack = `${trace.kind} ${trace.message_id} ${JSON.stringify(trace.payload)}`.toLowerCase();
      return haystack.includes(search.trim().toLowerCase());
    });
  }, [kindFilter, messageFilter, search, traces]);

  return (
    <section className="panel trace-panel">
      <div className="panel-head">
        <div>
          <p className="panel-kicker">Run Trace Panel</p>
          <h2>思考与观察轨迹</h2>
        </div>
      </div>
      {traces.length === 0 ? (
        <div className="empty-state compact">
          <p>暂时没有 trace。</p>
          <p>发送一条消息后，这里会出现 intent、thought、tool_call、observation。</p>
        </div>
      ) : (
        <>
          <div className="trace-filters">
            <label className="inline-field">
              Kind
              <select value={kindFilter} onChange={(event) => setKindFilter(event.target.value)}>
                <option value="all">all</option>
                <option value="intent">intent</option>
                <option value="thought">thought</option>
                <option value="tool_call">tool_call</option>
                <option value="observation">observation</option>
              </select>
            </label>
            <label className="inline-field">
              Message
              <select value={messageFilter} onChange={(event) => setMessageFilter(event.target.value)}>
                <option value="all">all</option>
                {messageIds.map((messageId) => (
                  <option key={messageId} value={messageId}>
                    {messageId}
                  </option>
                ))}
              </select>
            </label>
            <label className="inline-field">
              Search
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="tool / payload / reason"
              />
            </label>
          </div>
          <div className="trace-list">
            {filteredTraces.map((trace) => (
              <article key={trace.id} className={`trace-card kind-${trace.kind}`}>
                <div className="trace-meta">
                  <span>{trace.kind}</span>
                  <span>#{trace.step_index}</span>
                </div>
                <strong>{summarizePayload(trace)}</strong>
                <pre>{JSON.stringify(trace.payload, null, 2)}</pre>
              </article>
            ))}
          </div>
          {filteredTraces.length === 0 ? (
            <div className="empty-state compact">
              <p>当前过滤条件下没有 trace。</p>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
