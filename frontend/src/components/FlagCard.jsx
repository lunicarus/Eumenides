import React from "react";
import axios from "axios";

export default function FlagCard({ flag }) {
  const { platform, handle, display_name, description, risk_score, reasons } = flag;
  async function onReport() {
    try {
      await axios.post(`/api/report/${platform}/${handle}`);
      alert("Marked for manual review (no automatic reporting).");
    } catch (e) {
      console.error(e);
      alert("Failed to mark for review.");
    }
  }
  return (
    <div style={{ border: "1px solid #e5e7eb", padding: 12, borderRadius: 8, background: "#fff" }}>
      <h3 style={{ margin: "0 0 8px 0" }}>{display_name || handle}</h3>
      <div style={{ fontSize: 13, color: "#6b7280" }}>
        <div><strong>Platform:</strong> {platform}</div>
        <div><strong>Handle:</strong> {handle}</div>
        <div><strong>Score:</strong> {risk_score}</div>
      </div>
      <p style={{ marginTop: 8, fontSize: 13 }}>{description}</p>
      <p style={{ fontSize: 12, color: "#374151" }}><strong>Reasons:</strong> {Array.isArray(reasons) ? reasons.join(", ") : reasons}</p>
      <div style={{ marginTop: 8 }}>
        <button onClick={onReport} style={{ padding: "8px 12px", borderRadius: 6, border: "none", background: "#111827", color: "#fff" }}>
          Mark for manual review
        </button>
      </div>
    </div>
  );
}
