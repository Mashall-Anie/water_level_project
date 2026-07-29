import React, { useState } from "react";
import ResultCards from "../components/ResultCards";
import ResultChart from "../components/ResultChart";
import * as PredictService from "../services/PredictService";

function buildHistory(h0, h1, h2, h3, h7, h14, refDate) {
  const anchor = {
    0:  parseFloat(h0),
    1:  parseFloat(h1),
    2:  parseFloat(h2),
    3:  parseFloat(h3),
    7:  parseFloat(h7),
    14: parseFloat(h14),
    34: parseFloat(h14), 
  };

  const anchorDays = Object.keys(anchor).map(Number).sort((a, b) => a - b);
  const rows = [];
  const ref  = new Date(refDate);

  for (let i = 34; i >= 0; i--) {
    const lowerDay = anchorDays.filter((k) => k <= i).at(-1) ?? anchorDays[0];
    const upperDay = anchorDays.filter((k) => k >= i)[0]    ?? anchorDays.at(-1);

    let H;
    if (lowerDay === upperDay) {
      H = anchor[lowerDay];
    } else {
      const t = (i - lowerDay) / (upperDay - lowerDay);
      H = anchor[lowerDay] + (anchor[upperDay] - anchor[lowerDay]) * t;
    }

    const d = new Date(ref);
    d.setDate(d.getDate() - i);
    rows.push({
      date: d.toISOString().split("T")[0],
      H:    parseFloat(H.toFixed(2)),
    });
  }

  return rows; 
}

export default function ManualPage({ model }) {
  const [form, setForm] = useState({
    h0:      "",
    h1:      "",
    h2:      "",
    h3:      "",
    h7:      "",
    h14:     "",
    refDate: new Date().toISOString().split("T")[0],
    nDays:   3,
  });
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const [baseH,   setBaseH]   = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleRun = async () => {
    const fields = [
      ["h0",  "H hôm nay (t)"],
      ["h1",  "H hôm qua (t-1)"],
      ["h2",  "H 2 ngày trước (t-2)"],
      ["h3",  "H 3 ngày trước (t-3)"],
      ["h7",  "H 7 ngày trước (t-7)"],
      ["h14", "H 14 ngày trước (t-14)"],
    ];

    for (const [key, label] of fields) {
      const val = form[key];
      if (val === "" || val === null || val === undefined) {
        setError(`⚠️ Vui lòng nhập đầy đủ: "${label}"`);
        return;
      }
      if (isNaN(Number(val))) {
        setError(`⚠️ "${label}" phải là số hợp lệ`);
        return;
      }
      if (Number(val) < -50 || Number(val) > 700) {
        setError(`⚠️ "${label}" nằm ngoài dải thực tế (-50 đến 700 cm)`);
        return;
      }
    }

    setLoading(true);
    setError("");
    setResult(null);
    setBaseH(parseFloat(form.h0));

    try {
      const history = buildHistory(
        form.h0, form.h1, form.h2, form.h3, form.h7, form.h14, form.refDate
      );
      const data = await PredictService.predictManual(history, form.nDays);
      if (!data.status) throw new Error(data.error);
      setResult(data);
    } catch (e) {
      setError(e.message || "Lỗi kết nối backend");
    } finally {
      setLoading(false);
    }
  };

  const inputFields = [
    ["h0",  "H hôm nay (t)"],
    ["h1",  "H hôm qua (t-1)"],
    ["h2",  "H 2 ngày trước (t-2)"],
    ["h3",  "H 3 ngày trước (t-3)"],
    ["h7",  "H 7 ngày trước (t-7)"],
    ["h14", "H 14 ngày trước (t-14)"],
  ];

  return (
    <div>
      <h1 className="page-title">DỰ BÁO MỰC NƯỚC — NHẬP TAY</h1>

      <div className="card">
        <p className="card-title">📥 Nhập mực nước H (cm) các ngày gần nhất</p>

        <div className="bg-blue-50 border-l-4 border-blue-400 rounded-lg p-3 text-xs text-blue-800 leading-relaxed mb-4">
          Nhập giá trị mực nước H (cm) tại các mốc thời gian. Hệ thống sẽ tự nội suy
          tuyến tính các ngày còn lại để đủ 35 ngày lịch sử cho mô hình.<br />
          <span className="font-semibold">Lưu ý:</span> Giá trị H âm là hợp lệ (mùa kiệt Bà Thá có thể xuống -28 cm).
        </div>

        <div className="grid grid-cols-3 gap-3 mb-3">
          {inputFields.map(([k, label]) => (
            <div key={k} className="flex flex-col">
              <label className="text-xs font-semibold text-gray-500 mb-1">{label}</label>
              <input
                type="number"
                step="0.1"
                placeholder="vd: 42.5"
                value={form[k]}
                onChange={set(k)}
                className="px-3 py-2 rounded-lg border-2 border-gray-200 text-sm focus:outline-none focus:border-blue-400 bg-gray-50"
              />
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="flex flex-col">
            <label className="text-xs font-semibold text-gray-500 mb-1">
              📅 Ngày tham chiếu (hôm nay)
            </label>
            <input
              type="date"
              value={form.refDate}
              onChange={set("refDate")}
              className="px-3 py-2 rounded-lg border-2 border-gray-200 text-sm focus:outline-none focus:border-blue-400 bg-gray-50"
            />
          </div>
          <div className="flex flex-col">
            <label className="text-xs font-semibold text-gray-500 mb-1">🔢 Số ngày dự báo</label>
            <select
              value={form.nDays}
              onChange={set("nDays")}
              className="px-3 py-2 rounded-lg border-2 border-gray-200 text-sm focus:outline-none focus:border-blue-400 bg-gray-50"
            >
              {[1, 3, 7, 14].map((n) => (
                <option key={n} value={n}>{n} ngày</option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleRun}
          disabled={loading}
          className="run-btn w-full py-3 rounded-xl text-white font-bold text-lg disabled:opacity-60"
        >
          {loading ? "🧠 Đang tính toán..." : "🚀 CHẠY DỰ BÁO"}
        </button>

        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      </div>

      {result && (
        <>
          <ResultCards
            rfPreds={result.rf_preds}
            xgbPreds={result.xgb_preds}
            dates={result.dates}
            model={model}
            baseH={baseH}
          />
          <ResultChart
            history={result.history}
            rfPreds={result.rf_preds}
            xgbPreds={result.xgb_preds}
            dates={result.dates}
            model={model}
          />
        </>
      )}
    </div>
  );
}