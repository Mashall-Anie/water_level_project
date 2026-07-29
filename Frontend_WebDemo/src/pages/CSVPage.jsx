import React, { useState, useRef } from "react";
import ResultCards from "../components/ResultCards";
import ResultChart from "../components/ResultChart";
import * as PredictService from "../services/PredictService";

function CSVPage({ model }) {
  const [file, setFile]     = useState(null);
  const [nDays, setNDays]   = useState(3);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");
  const inputRef = useRef();

  const handleFile = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError("");
  };

  const handleRun = async () => {
    if (!file) { setError("Vui lòng chọn file CSV"); return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await PredictService.predictCSV(file, nDays);
      if (!data.status) throw new Error(data.error);
      setResult(data);
    } catch (e) {
      setError(e.message || "Lỗi kết nối backend");
    } finally {
      setLoading(false);
    }
  };

  const baseH = result?.history?.H?.at(-1) ?? 0;

  return (
    <div>
      <h1 className="page-title">DỰ BÁO TỪ FILE CSV</h1>

      <div className="card">
        <p className="card-title">📋 Định dạng file yêu cầu</p>
        <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-3 text-xs text-yellow-800 leading-relaxed mb-4">
          File CSV cần có <strong>≥ 30 dòng</strong> liên tục và các cột:<br />
          <code className="bg-white px-2 py-0.5 rounded mt-1 inline-block text-xs">
            Ngay_thang_nam · Nam · Thang · Ngay · H
          </code><br />
          Ví dụ dòng: <code className="text-xs">2023-12-01,2023,12,1,42.0</code>
        </div>

        <div
          onClick={() => inputRef.current.click()}
          className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center text-gray-400 cursor-pointer hover:border-blue-400 hover:text-blue-500 transition-colors mb-4"
        >
          <div className="text-5xl mb-2">📂</div>
          <p className="font-bold text-base mb-1">Nhấn để chọn file CSV</p>
          <p className="text-xs">Hỗ trợ .csv</p>
          {file && (
            <span className="inline-block mt-2 bg-blue-100 text-blue-600 px-3 py-1 rounded-full text-xs font-semibold">
              ✅ {file.name}
            </span>
          )}
        </div>
        <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={handleFile} />

        <div className="flex flex-col max-w-xs mb-4">
          <label className="text-xs font-semibold text-gray-500 mb-1">🔢 Số ngày dự báo tới</label>
          <select value={nDays} onChange={(e) => setNDays(+e.target.value)}
            className="px-3 py-2 rounded-lg border-2 border-gray-200 text-sm focus:outline-none focus:border-blue-400 bg-gray-50">
            {[1,3,7,14,30].map(n=><option key={n}>{n}</option>)}
          </select>
        </div>

        <button onClick={handleRun} disabled={loading}
          className="run-btn w-full py-3 rounded-xl text-white font-bold text-lg disabled:opacity-60">
          {loading ? "🧠 Đang xử lý file..." : "🚀 CHẠY DỰ BÁO TỪ FILE"}
        </button>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </div>

      {result && (
        <>
          <ResultCards
            rfPreds={result.rf_preds} xgbPreds={result.xgb_preds}
            dates={result.dates} model={model} baseH={baseH}
          />
          <ResultChart
            history={result.history} rfPreds={result.rf_preds}
            xgbPreds={result.xgb_preds} dates={result.dates} model={model}
          />
        </>
      )}
    </div>
  );
}

export default CSVPage;
