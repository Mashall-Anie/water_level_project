
import pandas as pd
import numpy as np

import config
import features as feat_module


def load_daily_data(path=None):
    path = path or config.DAILY_FULL

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns=lambda c: c.lstrip("\ufeff"))

    df["date"] = pd.to_datetime(df["Ngay_thang_nam"], errors="coerce")
    df["H"]    = pd.to_numeric(df["H"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    df["Nam"]   = df["date"].dt.year
    df["Thang"] = df["date"].dt.month
    df["Ngay"]  = df["date"].dt.day
    df["DOY"]   = df["date"].dt.dayofyear
    df["Week"]  = df["date"].dt.isocalendar().week.astype(int)

    df["H"] = df["H"].interpolate(method="linear", limit_direction="both")

    return df


def create_monthly_data(df_daily):
    monthly = (
        df_daily
        .groupby(["Nam", "Thang"])["H"]
        .agg([("Htb", "mean"), ("Hmax", "max"), ("Hmin", "min")])
        .reset_index()
    )
    monthly["date"] = pd.to_datetime(
        monthly["Nam"].astype(str) + "-" + monthly["Thang"].astype(str) + "-01"
    )
    return monthly


def make_daily_features(df):
    _df = df.copy()
    if "Thang" not in _df.columns:
        _df["Thang"] = _df["date"].dt.month
    if "Ngay" not in _df.columns:
        _df["Ngay"] = _df["date"].dt.day
    if "DOY" not in _df.columns:
        _df["DOY"] = _df["date"].dt.dayofyear
    if "Week" not in _df.columns:
        _df["Week"] = _df["date"].dt.isocalendar().week.astype(int)

    _df = feat_module.make_daily_features(_df)
    _df = _df.dropna().reset_index(drop=True)
    return _df


def make_monthly_features(df):
    df = df.copy()

    for target in config.MONTHLY_TARGETS:
        for lag in config.LAG_MONTHS:
            df[f"{target}_lag{lag}"] = df[target].shift(lag)

        for w in [3, 6, 12]:
            df[f"{target}_roll{w}_mean"] = df[target].shift(1).rolling(w).mean()
            df[f"{target}_roll{w}_std"]  = df[target].shift(1).rolling(w).std()

        df[f"{target}_diff1"] = df[target].diff(1)
        df[f"{target}_diff3"] = df[target].diff(3)

    df["month_sin"] = np.sin(2 * np.pi * df["Thang"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["Thang"] / 12)
    df["time_idx"]  = np.arange(len(df))
    df["is_flood_season"] = df["Thang"].isin(feat_module.FLOOD_MONTHS).astype(int)

    df = df.dropna().reset_index(drop=True)
    return df


def get_daily_feature_cols(df):
    exclude = ["date", "Ngay_thang_nam", "H", "Nam"]
    return [c for c in df.columns if c not in exclude]


def get_monthly_feature_cols(df, target):
    exclude = ["date", "Htb", "Hmax", "Hmin"]
    return [c for c in df.columns if c not in exclude]

    
def split_daily(df, test_year_start=2022):
    train = df[df["Nam"] < test_year_start]
    test  = df[df["Nam"] >= test_year_start]
    return train, test


def split_monthly(df, test_months=24):
    train = df.iloc[:-test_months]
    test  = df.iloc[-test_months:]
    return train, test


def build_monthly_feature_from_values(values, target, predict_month=6, predict_year=2026):
    values = np.array(values, dtype=float)
    feat   = {}

    for lag in config.LAG_MONTHS:
        feat[f"{target}_lag{lag}"] = values[-lag]

    feat[f"{target}_roll3_mean"]  = np.mean(values[-3:])
    feat[f"{target}_roll6_mean"]  = np.mean(values[-6:])
    feat[f"{target}_roll12_mean"] = np.mean(values[-12:])
    feat[f"{target}_roll3_std"]   = np.std(values[-3:])
    feat[f"{target}_roll6_std"]   = np.std(values[-6:])
    feat[f"{target}_roll12_std"]  = np.std(values[-12:])
    feat[f"{target}_diff1"] = values[-1] - values[-2]
    feat[f"{target}_diff3"] = values[-1] - values[-4]

    feat["Thang"]          = predict_month
    feat["Nam"]            = predict_year
    feat["month_sin"]      = np.sin(2 * np.pi * predict_month / 12)
    feat["month_cos"]      = np.cos(2 * np.pi * predict_month / 12)
    feat["time_idx"]       = len(values)
    feat["is_flood_season"] = 1 if predict_month in feat_module.FLOOD_MONTHS else 0

    return feat