import React, { useEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";
Chart.register(...registerables);

const RF_COLOR  = "#1E88E5";
const XGB_COLOR = "#F4511E";

function ResultChart({ history, rfPreds, xgbPreds, dates, model }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    if (!history || !rfPreds) return;
    if (chartRef.current) chartRef.current.destroy();

    const histLabels = history.dates.map((d) => d.slice(5));
    const predLabels = dates.map((d) => d.slice(5));
    const allLabels  = [...histLabels, ...predLabels];

    const histData = [
      ...history.H,
      ...Array(rfPreds.length).fill(null),
    ];
    const pivot = history.H.length - 1;
    const rfData = [
      ...Array(pivot).fill(null),
      history.H[pivot],
      ...rfPreds,
    ];
    const xgbData = [
      ...Array(pivot).fill(null),
      history.H[pivot],
      ...xgbPreds,
    ];

    const datasets = [
      {
        label: "Lịch sử H",
        data: histData,
        borderColor: "#90A4AE",
        backgroundColor: "rgba(144,164,174,0.08)",
        pointRadius: 3,
        tension: 0.35,
        fill: true,
        borderWidth: 2,
      },
    ];

    if (model !== "xgb") {
      datasets.push({
        label: "Dự báo RF",
        data: rfData,
        borderColor: RF_COLOR,
        backgroundColor: "rgba(30,136,229,0.08)",
        pointRadius: [...Array(pivot).fill(0), 5, ...Array(rfPreds.length).fill(6)],
        tension: 0.35,
        fill: true,
        borderDash: [5, 3],
        borderWidth: 2.5,
      });
    }

    if (model !== "rf") {
      datasets.push({
        label: "Dự báo XGBoost",
        data: xgbData,
        borderColor: XGB_COLOR,
        backgroundColor: "rgba(244,81,30,0.07)",
        pointRadius: [...Array(pivot).fill(0), 5, ...Array(xgbPreds.length).fill(6)],
        tension: 0.35,
        fill: true,
        borderDash: [7, 3],
        borderWidth: 2.5,
      });
    }

    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: { labels: allLabels, datasets },
      options: {
        responsive: true,
        plugins: {
          legend: {
            position: "top",
            labels: { font: { family: "Barlow", size: 12 }, boxWidth: 16 },
          },
        },
        scales: {
          x: { grid: { color: "#f0f0f0" }, ticks: { maxTicksLimit: 12 } },
          y: {
            grid: { color: "#f0f0f0" },
            ticks: { callback: (v) => v.toFixed(0) + " cm" },
            title: { display: true, text: "Mực nước H (cm)", font: { size: 12 } },
          },
        },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [history, rfPreds, xgbPreds, dates, model]);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 mt-4">
      <p className="font-bold text-[#003366] text-sm mb-3" style={{ fontFamily: "Barlow Condensed, sans-serif", letterSpacing: "0.3px" }}>
        📈 BIỂU ĐỒ MỰC NƯỚC H (cm) — LỊCH SỬ + DỰ BÁO
      </p>
      <canvas ref={canvasRef} />
    </div>
  );
}

export default ResultChart;
