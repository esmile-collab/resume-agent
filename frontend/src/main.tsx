// Input: Vite 入口与 App 组件。
// Output: 把 React 应用挂载到浏览器 DOM。
// Pos: 前端启动入口。
// Rule: 一旦我被更新，务必同步更新本文件头注释与所属目录 README。
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
