from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import os
from datetime import timedelta

from features import make_daily_features, FEATURE_COLS, H_MIN_PHYSICAL, H_MAX_PHYSICAL

app = Flask(__name__)
CORS(app)

BASE      = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE, "models")

rf_daily  = None
xgb_daily = None


def load_models():
    global rf_daily, xgb_daily
    rf_path  = os.path.join(MODEL_DIR, "rf_daily.pkl")
    xgb_path = os.path.join(MODEL_DIR, "xgb_daily.pkl")

    if not os.path.exists(rf_path) or not os.path.exists(xgb_path):
        raise FileNotFoundError(
            f"Không tìm thấy model trong {MODEL_DIR}. "
            "Hãy chạy main.py để train trước."
        )

    rf_daily  = joblib.load(rf_path)
    xgb_daily = joblib.load(xgb_path)

    if hasattr(xgb_daily, "feature_names_in_"):
        model_feats = list(xgb_daily.feature_names_in_)
        if model_feats != FEATURE_COLS:
            diff = set(model_feats).symmetric_difference(set(FEATURE_COLS))
            print(f"[WARN] Feature mismatch: {diff}")
        else:
            print("[OK] Feature columns khớp với model.")
    print("[OK] Models loaded thành công.")


load_models()


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Ngay_thang_nam"] = pd.to_datetime(df["Ngay_thang_nam"])
    df = df.sort_values("Ngay_thang_nam").reset_index(drop=True)
    df["Nam"]   = df["Ngay_thang_nam"].dt.year
    df["Thang"] = df["Ngay_thang_nam"].dt.month
    df["Ngay"]  = df["Ngay_thang_nam"].dt.day
    df["DOY"]   = df["Ngay_thang_nam"].dt.dayofyear
    df["Week"]  = df["Ngay_thang_nam"].dt.isocalendar().week.astype(int)
    df["H"]     = pd.to_numeric(df["H"], errors="coerce")
    return df


def _single_model_forecast(df_hist: pd.DataFrame, model, n_days: int) -> list:

    df = df_hist.copy().reset_index(drop=True)
    preds = []

    for _ in range(n_days):
        df_feat = make_daily_features(df)
        last    = df_feat[FEATURE_COLS].iloc[[-1]]   # đặc trưng tại ngày t

        dH     = float(model.predict(last)[0])
        H_last = float(df["H"].iloc[-1])
        H_next = float(np.clip(H_last + dH, H_MIN_PHYSICAL, H_MAX_PHYSICAL))
        preds.append(round(H_next, 2))

        nd = df["Ngay_thang_nam"].iloc[-1] + timedelta(days=1)
        new_row = pd.DataFrame([{
            "Ngay_thang_nam": nd,
            "Nam":   nd.year,
            "Thang": nd.month,
            "Ngay":  nd.day,
            "DOY":   nd.timetuple().tm_yday,
            "Week":  int(nd.isocalendar()[1]),
            "H":     H_next,
        }])
        df = pd.concat([df, new_row], ignore_index=True)

    return preds


def rolling_forecast(df_hist: pd.DataFrame, n_days: int):
    """Chạy rolling forecast độc lập cho RF và XGBoost."""
    rf_preds  = _single_model_forecast(df_hist, rf_daily,  n_days)
    xgb_preds = _single_model_forecast(df_hist, xgb_daily, n_days)

    last_date = df_hist["Ngay_thang_nam"].iloc[-1]
    dates = [
        (last_date + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        for i in range(n_days)
    ]
    return rf_preds, xgb_preds, dates


@app.route("/api/predict/csv", methods=["POST"])
def predict_csv():
    try:
        file   = request.files.get("file")
        n_days = int(request.form.get("n_days", 3))

        if not file:
            return jsonify({"status": False, "error": "Không có file được gửi lên"}), 400

        df = pd.read_csv(file, parse_dates=["Ngay_thang_nam"])
        df = _prepare_df(df)

        if len(df) < 35:
            return jsonify({
                "status": False,
                "error":  "Cần ít nhất 35 dòng dữ liệu liên tục để tính rolling features"
            }), 400

        df_feat   = make_daily_features(df)
        hist_rows = df_feat.tail(30)
        history = {
            "dates": hist_rows["Ngay_thang_nam"].dt.strftime("%Y-%m-%d").tolist(),
            "H":     hist_rows["H"].round(2).tolist(),
        }

        df_fore = df.tail(35).reset_index(drop=True)
        rf_preds, xgb_preds, pred_dates = rolling_forecast(df_fore, n_days)

        return jsonify({
            "status":    True,
            "history":   history,
            "rf_preds":  rf_preds,
            "xgb_preds": xgb_preds,
            "dates":     pred_dates,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": False, "error": str(e)}), 500


@app.route("/api/predict/manual", methods=["POST"])
def predict_manual():
    try:
        body   = request.get_json()
        n_days = int(body.get("n_days", 3))
        rows   = body.get("history")

        if not rows or len(rows) < 35:
            return jsonify({
                "status": False,
                "error":  "Cần ít nhất 35 ngày lịch sử để tính rolling features"
            }), 400

        df = pd.DataFrame(rows)
        df["Ngay_thang_nam"] = pd.to_datetime(df["date"])
        df["Nam"]   = df["Ngay_thang_nam"].dt.year
        df["Thang"] = df["Ngay_thang_nam"].dt.month
        df["Ngay"]  = df["Ngay_thang_nam"].dt.day
        df["DOY"]   = df["Ngay_thang_nam"].dt.dayofyear
        df["Week"]  = df["Ngay_thang_nam"].dt.isocalendar().week.astype(int)
        df["H"]     = df["H"].astype(float)
        df = df.sort_values("Ngay_thang_nam").reset_index(drop=True)

        history = {
            "dates": df["Ngay_thang_nam"].dt.strftime("%Y-%m-%d").tail(14).tolist(),
            "H":     df["H"].tail(14).round(2).tolist(),
        }

        rf_preds, xgb_preds, pred_dates = rolling_forecast(df, n_days)

        return jsonify({
            "status":    True,
            "history":   history,
            "rf_preds":  rf_preds,
            "xgb_preds": xgb_preds,
            "dates":     pred_dates,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)