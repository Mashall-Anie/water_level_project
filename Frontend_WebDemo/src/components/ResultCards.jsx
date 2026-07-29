import React from "react";

const RF_COLOR  = "#1E88E5";
const XGB_COLOR = "#F4511E";


function Delta({ cur, base }) {
  if (base === null || base === undefined) return null;
  const d    = cur - base;
  const absD = Math.abs(d);

  if (absD < 0.5) {
    return <span className="text-gray-400 text-xs">→ Ổn định</span>;
  }

  const isUp = d > 0;
  return (
    <span className={`text-xs font-semibold ${isUp ? "text-red-500" : "text-green-600"}`}>
      {isUp ? "▲" : "▼"} {absD.toFixed(1)} cm
    </span>
  );
}

function AlertBanner({ rfPreds, xgbPreds, model, baseH }) {
  const preds = [
    ...(model !== "xgb" ? rfPreds  : []),
    ...(model !== "rf"  ? xgbPreds : []),
  ];

  if (!preds.length || baseH === null || baseH === undefined) return null;

  const maxP    = Math.max(...preds);
  const minP    = Math.min(...preds);
  const maxRise = maxP - baseH;
  const maxDrop = baseH - minP;

  let bg, icon, msg;

  if (maxRise >= 25) {
    bg   = "#E53935"; icon = "🚨";
    msg  = `CẢNH BÁO: MỰC NƯỚC TĂNG MẠNH (+${maxRise.toFixed(1)} cm)`;
  } else if (maxRise >= 10) {
    bg   = "#FB8C00"; icon = "⚠️";
    msg  = `CHÚ Ý: Mực nước có xu hướng tăng (+${maxRise.toFixed(1)} cm)`;
  } else if (maxDrop >= 25) {
    bg   = "#1E88E5"; icon = "🌊";
    msg  = `GIẢM MẠNH: Mực nước giảm (-${maxDrop.toFixed(1)} cm)`;
  } else if (maxDrop >= 10) {
    bg   = "#29B6F6"; icon = "📉";
    msg  = `Mực nước có xu hướng giảm (-${maxDrop.toFixed(1)} cm)`;
  } else {
    bg   = "#00897B"; icon = "✅";
    msg  = "MỰC NƯỚC DỰ KIẾN ỔN ĐỊNH";
  }

  return (
    <div
      className="rounded-xl text-white text-center py-3 px-4 mb-4 font-bold text-base"
      style={{ background: bg, fontFamily: "Barlow Condensed, sans-serif", letterSpacing: "0.5px" }}
    >
      {icon} {msg}
    </div>
  );
}

export default function ResultCards({ rfPreds, xgbPreds, dates, model, baseH }) {
  if (!rfPreds || !xgbPreds) return null;

  const modelLabel =
    model === "rf"   ? "Random Forest" :
    model === "xgb"  ? "XGBoost" :
                       "RF + XGBoost";

  const tableTitle =
    model === "both"
      ? "📊 BẢNG SO SÁNH RF vs XGBOOST"
      : `📊 KẾT QUẢ DỰ BÁO — ${modelLabel.toUpperCase()}`;

  const colSpan = model === "both" ? 3 : 2;

  return (
    <div className="mt-4">
      <AlertBanner rfPreds={rfPreds} xgbPreds={xgbPreds} model={model} baseH={baseH} />

      <p className="text-xs text-gray-400 italic mb-3">
        ⏱️ Mô hình: {modelLabel} &nbsp;|&nbsp; Dự báo {rfPreds.length} ngày tới
      </p>

      {/* ── Thẻ RF ─────────────────────────────────────── */}
      {model !== "xgb" && (
        <div
          className="grid gap-3 mb-3"
          style={{ gridTemplateColumns: `repeat(${Math.min(rfPreds.length, 4)}, 1fr)` }}
        >
          {rfPreds.map((v, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-xs font-bold text-[#003366] mb-1">
                <span className="bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full text-xs font-bold mr-1">
                  RF
                </span>
                {dates[i]?.slice(5)}
              </div>
              <div
                className="font-black leading-none"
                style={{ fontFamily: "Barlow Condensed, sans-serif", fontSize: 32, color: RF_COLOR }}
              >
                {v.toFixed(1)} <span className="text-sm font-semibold">cm</span>
              </div>
              <div className="mt-1">
                <Delta cur={v} base={baseH} />
              </div>
            </div>
          ))}
        </div>
      )}

      {model !== "rf" && (
        <div
          className="grid gap-3 mb-3"
          style={{ gridTemplateColumns: `repeat(${Math.min(xgbPreds.length, 4)}, 1fr)` }}
        >
          {xgbPreds.map((v, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
              <div className="text-xs font-bold text-[#003366] mb-1">
                <span className="bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full text-xs font-bold mr-1">
                  XGB
                </span>
                {dates[i]?.slice(5)}
              </div>
              <div
                className="font-black leading-none"
                style={{ fontFamily: "Barlow Condensed, sans-serif", fontSize: 32, color: XGB_COLOR }}
              >
                {v.toFixed(1)} <span className="text-sm font-semibold">cm</span>
              </div>
              <div className="mt-1">
                <Delta cur={v} base={baseH} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <p
          className="font-bold text-[#003366] text-sm mb-3"
          style={{ fontFamily: "Barlow Condensed, sans-serif" }}
        >
          {tableTitle}
        </p>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50">
              <th className="text-left px-3 py-2 font-bold text-[#003366] border-b-2 border-gray-200">
                Ngày
              </th>
              {model !== "xgb" && (
                <th
                  className="text-left px-3 py-2 font-bold border-b-2 border-gray-200"
                  style={{ color: RF_COLOR }}
                >
                  RF (cm)
                </th>
              )}
              {model !== "rf" && (
                <th
                  className="text-left px-3 py-2 font-bold border-b-2 border-gray-200"
                  style={{ color: XGB_COLOR }}
                >
                  XGBoost (cm)
                </th>
              )}
              {model === "both" && (
                <th className="text-left px-3 py-2 font-bold text-gray-400 border-b-2 border-gray-200">
                  Chênh lệch (cm)
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {rfPreds.map((_, i) => (
              <tr key={i} className="hover:bg-gray-50 border-b border-gray-100">
                <td className="px-3 py-2 font-medium">{dates[i]}</td>
                {model !== "xgb" && (
                  <td className="px-3 py-2 font-semibold" style={{ color: RF_COLOR }}>
                    {rfPreds[i].toFixed(2)}
                  </td>
                )}
                {model !== "rf" && (
                  <td className="px-3 py-2 font-semibold" style={{ color: XGB_COLOR }}>
                    {xgbPreds[i].toFixed(2)}
                  </td>
                )}
                {model === "both" && (
                  <td className="px-3 py-2 text-gray-500 font-medium">
                    {Math.abs(rfPreds[i] - xgbPreds[i]).toFixed(2)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}