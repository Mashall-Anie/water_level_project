
import os
import argparse
import numpy as np
import pandas as pd
from datetime import timedelta

import config
import models as mdl
import preprocessing as prep
import features as feat_module
from features import FEATURE_COLS, H_MIN_PHYSICAL, H_MAX_PHYSICAL


def dH_to_H(H_base: np.ndarray, dH_pred: np.ndarray) -> np.ndarray:
    return np.clip(H_base + dH_pred, H_MIN_PHYSICAL, H_MAX_PHYSICAL)

def _backtest(df_fe: pd.DataFrame, model, n_days: int,
              start_year: int, label: str) -> None:
    from features import make_daily_features, FEATURE_COLS as FC

    test = df_fe[df_fe["Nam"] >= start_year].reset_index(drop=True)
    err  = {h: [] for h in range(1, n_days + 1)}
    MIN_HIST = 35

    for i in range(MIN_HIST, len(test) - n_days):
        hist = test.iloc[:i].copy()
        df_h = pd.DataFrame({
            "Ngay_thang_nam": pd.to_datetime(hist["date"]),
            "H":              hist["H"].astype(float),
        })
        df_h["Nam"]   = df_h["Ngay_thang_nam"].dt.year
        df_h["Thang"] = df_h["Ngay_thang_nam"].dt.month
        df_h["Ngay"]  = df_h["Ngay_thang_nam"].dt.day
        df_h["DOY"]   = df_h["Ngay_thang_nam"].dt.dayofyear
        df_h["Week"]  = df_h["Ngay_thang_nam"].dt.isocalendar().week.astype(int)

        preds_h = []
        for _ in range(n_days):
            df_feat = make_daily_features(df_h)
            last    = df_feat[FC].iloc[[-1]]
            dH      = float(model.predict(last)[0])
            H_cur   = float(df_h["H"].iloc[-1])
            H_next  = float(np.clip(H_cur + dH, H_MIN_PHYSICAL, H_MAX_PHYSICAL))
            preds_h.append(H_next)
            nd = df_h["Ngay_thang_nam"].iloc[-1] + timedelta(days=1)
            df_h = pd.concat([df_h, pd.DataFrame([{
                "Ngay_thang_nam": nd,
                "Nam":  nd.year, "Thang": nd.month, "Ngay": nd.day,
                "DOY":  nd.timetuple().tm_yday,
                "Week": int(nd.isocalendar()[1]),
                "H":    H_next,
            }])], ignore_index=True)

        actual = test["H"].iloc[i:i + n_days].values
        for h in range(min(n_days, len(actual))):
            err[h + 1].append(preds_h[h] - actual[h])

    print(f"  {label}:")
    for h in range(1, n_days + 1):
        e = np.array(err[h])
        if len(e) == 0:
            continue
        print(f"    +{h} ngày: RMSE={np.sqrt((e**2).mean()):.2f} cm"
              f" | MAE={np.abs(e).mean():.2f} cm"
              f" | bias={e.mean():+.2f} cm")

def run_daily(tune: bool = False) -> None:
    print("\n" + "=" * 64)
    print("  DAILY FORECAST — Target: ΔH (H[t+1] − H[t])")
    print("=" * 64)

    df_raw = prep.load_daily_data()
    df_fe  = prep.make_daily_features(df_raw)   

    df_fe = df_fe.sort_values("date").reset_index(drop=True)
    df_fe["target_dH"] = df_fe["H"].shift(-1) - df_fe["H"]
    df_fe = df_fe.dropna(subset=["target_dH"] + FEATURE_COLS).reset_index(drop=True)

    print(f"  Tổng mẫu sau dropna: {len(df_fe)}")
    print(f"  ΔH stats — mean: {df_fe['target_dH'].mean():.3f} "
          f"| std: {df_fe['target_dH'].std():.3f} "
          f"| range: [{df_fe['target_dH'].min():.1f}, {df_fe['target_dH'].max():.1f}]")

    train, test = prep.split_daily(df_fe, test_year_start=2022)
    X_train, y_train = train[FEATURE_COLS], train["target_dH"].values
    X_test,  y_test  = test[FEATURE_COLS],  test["target_dH"].values

    print(f"  Train: {len(train)} mẫu ({train['Nam'].min()}–{train['Nam'].max()})")
    print(f"  Test : {len(test)}  mẫu ({test['Nam'].min()}–{test['Nam'].max()})")

    H_base_test = test["H"].values
    H_next_true = H_base_test + y_test     

    results = []

    print("\n  [XGBoost]")
    if tune:
        xgb_model, best_p = mdl.tune_model(
            mdl.get_xgb(),
            {
                "n_estimators":     [500, 700, 1000],
                "max_depth":        [3, 4, 5],
                "learning_rate":    [0.01, 0.02, 0.05],
                "subsample":        [0.8, 0.85],
                "colsample_bytree": [0.8, 0.85],
            },
            X_train, y_train
        )
        print(f"    Best params: {best_p}")
    else:
        xgb_model = mdl.get_xgb()
        xgb_model.set_params(**config.XGB_PARAMS)
        xgb_model.fit(X_train, y_train)

    dH_xgb   = xgb_model.predict(X_test)
    H_xgb    = dH_to_H(H_base_test, dH_xgb)
    r_xgb    = mdl.evaluate(H_next_true, H_xgb, label="XGBoost Daily (H next-day)")
    results.append({"Model": "XGBoost", "Dataset": "Test", "Target": "H next-day", **r_xgb})
    mdl.save_model(xgb_model, "xgb_daily.pkl")

    print("\n  [Random Forest]")
    if tune:
        rf_model, best_p = mdl.tune_model(
            mdl.get_rf(),
            {
                "n_estimators":      [300, 500],
                "max_depth":         [8, 10, 12, 15],
                "min_samples_split": [2, 3, 5],
                "min_samples_leaf":  [1, 2, 3],
            },
            X_train, y_train
        )
        print(f"    Best params: {best_p}")
    else:
        rf_model = mdl.get_rf()
        rf_model.set_params(**config.RF_PARAMS)
        rf_model.fit(X_train, y_train)

    dH_rf  = rf_model.predict(X_test)
    H_rf   = dH_to_H(H_base_test, dH_rf)
    r_rf   = mdl.evaluate(H_next_true, H_rf, label="RF Daily (H next-day)")
    results.append({"Model": "RF", "Dataset": "Test", "Target": "H next-day", **r_rf})
    mdl.save_model(rf_model, "rf_daily.pkl")

    print("\n  [Feature Importance — XGBoost Top 15]")
    fi = mdl.feature_importance_df(xgb_model, FEATURE_COLS)
    print(fi.head(15).to_string(index=False))

    df_res = mdl.results_table(results)
    print("\n  [Bảng kết quả]")
    print(df_res.to_string(index=False))

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    df_res.to_csv(os.path.join(config.OUTPUT_DIR, "results_daily.csv"),
                  index=False, encoding="utf-8-sig")
    print(f"\n  Đã lưu: {config.OUTPUT_DIR}/results_daily.csv")

    print("\n  [Backtest walk-forward — XGBoost]")
    _backtest(df_fe, xgb_model, n_days=7, start_year=2022, label="XGBoost")

    print("\n  [Backtest walk-forward — RF]")
    _backtest(df_fe, rf_model,  n_days=7, start_year=2022, label="RF")


def main():
    parser = argparse.ArgumentParser(
        description="Train/Tune mô hình dự báo mực nước trạm Bà Thá"
    )
    parser.add_argument(
        "--tune", action="store_true",
        help="Chạy GridSearchCV để tìm siêu tham số tốt nhất"
    )
    args = parser.parse_args()

    if args.tune:
        print("⚙️  Chế độ TUNING — GridSearchCV TimeSeriesSplit")
        print("   Kết quả in ra để bạn cập nhật vào config.py\n")
    else:
        print("🚀 Chế độ TRAIN — dùng params từ config.py\n")

    run_daily(tune=args.tune)

    print("\n✅ Hoàn tất! Model đã lưu trong thư mục:", config.MODEL_DIR)
    if not args.tune:
        print("   → Copy rf_daily.pkl + xgb_daily.pkl sang thư mục backend/models/")


if __name__ == "__main__":
    main()