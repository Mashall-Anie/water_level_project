import os
import sys
import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd

import config
import models as mdl
import preprocessing as prep
from features import make_daily_features, FEATURE_COLS, H_MIN_PHYSICAL, H_MAX_PHYSICAL


def predict_daily_from_values(h_values: list, ref_date: date,
                               model_name: str = "xgb") -> float:
    if len(h_values) < 35:
        raise ValueError(
            f"Cần ít nhất 35 giá trị H (có {len(h_values)}). "
            "Rolling window lớn nhất 30 + lag lớn nhất 30."
        )

    model_file = "xgb_daily.pkl" if model_name == "xgb" else "rf_daily.pkl"
    try:
        model = mdl.load_model(model_file)
    except FileNotFoundError:
        print(f"[ERROR] Không tìm thấy '{model_file}'. Hãy chạy main.py trước.")
        sys.exit(1)

    dates = [ref_date - timedelta(days=len(h_values) - 1 - i)
             for i in range(len(h_values))]
    df = pd.DataFrame({
        "Ngay_thang_nam": pd.to_datetime(dates),
        "H":              list(h_values),
    })
    df["Nam"]   = df["Ngay_thang_nam"].dt.year
    df["Thang"] = df["Ngay_thang_nam"].dt.month
    df["Ngay"]  = df["Ngay_thang_nam"].dt.day
    df["DOY"]   = df["Ngay_thang_nam"].dt.dayofyear
    df["Week"]  = df["Ngay_thang_nam"].dt.isocalendar().week.astype(int)
    df = df.sort_values("Ngay_thang_nam").reset_index(drop=True)

    df_feat = make_daily_features(df)
    last    = df_feat[FEATURE_COLS].iloc[[-1]]   # đặc trưng tại ref_date

    dH   = float(model.predict(last)[0])
    H_last = float(h_values[-1])
    pred = float(np.clip(H_last + dH, H_MIN_PHYSICAL, H_MAX_PHYSICAL))
    return round(pred, 2)


def predict_daily_from_file(filepath: str, model_name: str = "xgb") -> pd.DataFrame:
    model_file = "xgb_daily.pkl" if model_name == "xgb" else "rf_daily.pkl"
    try:
        model = mdl.load_model(model_file)
    except FileNotFoundError:
        print(f"[ERROR] Không tìm thấy '{model_file}'. Hãy chạy main.py trước.")
        sys.exit(1)

    df_raw = prep.load_daily_data(filepath)
    df_fe  = prep.make_daily_features(df_raw)

    feat_cols = [c for c in FEATURE_COLS if c in df_fe.columns]
    X         = df_fe[feat_cols].values

    dH_pred = model.predict(X)

    H_base       = df_fe["H"].values                   
    H_next_pred  = np.clip(H_base + dH_pred, H_MIN_PHYSICAL, H_MAX_PHYSICAL)
    H_next_true  = df_fe["H"].shift(-1).values         

    df_out = df_fe[["date", "Nam", "Thang", "Ngay", "H"]].copy()
    df_out.rename(columns={"H": "H_obs_t"}, inplace=True)
    df_out["H_obs_t+1"]   = H_next_true.round(2)
    df_out["H_pred_t+1"]  = H_next_pred.round(2)
    df_out["dH_pred"]     = dH_pred.round(2)
    df_out["Error (cm)"]  = (df_out["H_obs_t+1"] - df_out["H_pred_t+1"]).round(2)

    df_out = df_out.dropna(subset=["H_obs_t+1"]).reset_index(drop=True)
    return df_out


def main():
    parser = argparse.ArgumentParser(description="Dự báo mực nước trạm Bà Thá")
    parser.add_argument("--model",  default="xgb", choices=["xgb", "rf"])
    parser.add_argument("--file",   type=str, default=None,
                        help="Đường dẫn file CSV")
    parser.add_argument("--values", nargs="+", type=float, default=None,
                        help="≥ 35 giá trị H ngày gần nhất, cũ nhất trước")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  DỰ BÁO MỰC NƯỚC TRẠM BÀ THÁ — Mô hình: {args.model.upper()}")
    print("=" * 60)

    if args.file:
        print(f"\n  Dự báo in-sample từ file: {args.file}")
        df_out = predict_daily_from_file(args.file, model_name=args.model)
        print(df_out.tail(10).to_string(index=False))

        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        out_path = os.path.join(config.OUTPUT_DIR, "predictions.csv")
        df_out.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"\n  Đã lưu: {out_path}")

    elif args.values:
        if len(args.values) < 35:
            print(f"  [ERROR] Cần ít nhất 35 giá trị H (đã nhập {len(args.values)}).")
            sys.exit(1)

        today    = date.today()
        tomorrow = today + timedelta(days=1)
        pred     = predict_daily_from_values(
            args.values, ref_date=today, model_name=args.model
        )
        print(f"\n  {len(args.values)} giá trị H — 5 cuối: {args.values[-5:]}")
        print(f"  ▶  Dự báo mực nước ngày {tomorrow}: {pred:.2f} cm")

    else:
        print("\n  Cách dùng:")
        print("    --file data/BaTha_daily_full_2017-2023.csv")
        print("    --values H1 H2 ... H35+")


if __name__ == "__main__":
    main()