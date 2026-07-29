import React, { useState } from "react";
import ManualPage from "./pages/ManualPage";
import CSVPage    from "./pages/CSVPage";
import "./App.css";

const TABS = [
  { id: 1, icon: "📝", label: "Dự báo nhập tay" },
  { id: 2, icon: "📂", label: "Dự báo từ file CSV" },
];

function ModelToggle({ model, onChange }) {
  const btns = [
    { key: "rf",   label: "RF",     active: "bg-blue-500 text-white" },
    { key: "xgb",  label: "XGB",    active: "bg-orange-500 text-white" },
    { key: "both", label: "CẢ HAI", active: "bg-gradient-to-r from-blue-500 to-orange-500 text-white" },
  ];
  return (
    <div className="flex rounded-lg overflow-hidden border border-gray-200">
      {btns.map((b) => (
        <button
          key={b.key}
          onClick={() => onChange(b.key)}
          className={`flex-1 py-2 text-xs font-bold transition-all
            ${model === b.key ? b.active : "bg-gray-50 text-gray-500 hover:bg-gray-100"}`}
          style={{ fontFamily: "Barlow Condensed, sans-serif", letterSpacing: "0.5px" }}
        >
          {b.label}
        </button>
      ))}
    </div>
  );
}

function App() {
  const [tab,   setTab]   = useState(1);
  const [model, setModel] = useState("rf");

  return (
    <div className="flex min-h-screen bg-[#f0f4f8]">
      {/* SIDEBAR */}
      <aside className="w-56 min-w-[224px] bg-white border-r-2 border-gray-100 flex flex-col gap-3 p-4 h-screen sticky top-0 overflow-y-auto">
        {/* Logo */}
        <div
          className="rounded-xl p-4 text-center text-white"
          style={{ background: "linear-gradient(145deg,#002952,#003d7a,#1E88E5)" }}
        >
          <div className="text-3xl">🌊</div>
          <h2
            className="font-black text-xs mt-2 leading-snug tracking-wide"
            style={{ fontFamily: "Barlow Condensed, sans-serif" }}
          >
            HỆ THỐNG DỰ BÁO<br />THỦY VĂN BÀ THÁ
          </h2>
          <p className="text-xs opacity-70 mt-1">Trạm Bà Thá · Ứng Hòa · Hà Nội</p>
        </div>

        {/* Model toggle */}
        <div>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
            🤖 Mô hình
          </p>
          <ModelToggle model={model} onChange={setModel} />
        </div>

        <hr className="border-gray-100" />

        {/* Nav */}
        <div>
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
            Chức năng
          </p>
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`w-full text-left px-3 py-2 rounded-xl flex items-center gap-2 text-sm font-semibold mb-1 transition-all
                ${tab === t.id
                  ? "bg-blue-500 text-white shadow-md"
                  : "text-gray-500 hover:bg-blue-50 hover:text-blue-500"}`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        <div className="mt-auto text-center text-xs text-gray-300 leading-relaxed pt-2">
          📍 Trạm Bà Thá · 1994–2023<br />
          RF + XGBoost · Target: ΔH
        </div>
      </aside>

      {/* MAIN */}
      <main className="flex-1 p-7 overflow-y-auto">
        {tab === 1 && <ManualPage model={model} />}
        {tab === 2 && <CSVPage    model={model} />}
      </main>
    </div>
  );
}

export default App;