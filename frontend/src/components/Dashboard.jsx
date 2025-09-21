import React, { useEffect, useState } from "react";
import axios from "axios";
import FlagCard from "./FlagCard";

export default function Dashboard() {
  const [flags, setFlags] = useState([]);
  useEffect(() => {
    fetchFlags();
  }, []);
  async function fetchFlags() {
    try {
      const res = await axios.get("/api/flags");
      setFlags(res.data);
    } catch (e) {
      console.error(e);
    }
  }
  return (
    <div>
      {flags.length === 0 && <p>No flagged items yet.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(320px,1fr))", gap: 12 }}>
        {flags.map((f) => (
          <FlagCard key={`${f.platform}-${f.handle}`} flag={f} />
        ))}
      </div>
    </div>
  );
}
