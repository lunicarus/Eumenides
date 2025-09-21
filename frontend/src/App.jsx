import React from "react";
import Dashboard from "./components/Dashboard";

export default function App() {
  return (
    <div style={{ padding: 20, fontFamily: "Inter, system-ui, Arial" }}>
      <h1>Eumenides — Metadata Monitor</h1>
      <Dashboard />
    </div>
  );
}
