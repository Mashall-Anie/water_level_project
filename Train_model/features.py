
import numpy as np
import pandas as pd

LAG_DAYS = [1, 2, 3, 5, 7, 14, 21, 30]

ROLL_WINDOWS = [3, 7, 14, 30]

FLOOD_MONTHS = [6, 7, 8, 9, 10]

H_MIN_PHYSICAL = -30.0   
H_MAX_PHYSICAL = 650.0   

FEATURE_COLS = [
    "Thang", "Ngay", "DOY", "Week",
    "H_lag1", "H_lag2", "H_lag3", "H_lag5", "H_lag7",
    "H_lag14", "H_lag21", "H_lag30",
    "H_roll3_mean",  "H_roll3_std",  "H_roll3_max",  "H_roll3_min",
    "H_roll7_mean",  "H_roll7_std",  "H_roll7_max",  "H_roll7_min",
    "H_roll14_mean", "H_roll14_std", "H_roll14_max", "H_roll14_min",
    "H_roll30_mean", "H_roll30_std", "H_roll30_max", "H_roll30_min",
    "diff_1", "diff_3", "diff_7",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_flood_season",
]


def make_daily_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for lag in LAG_DAYS:
        df[f"H_lag{lag}"] = df["H"].shift(lag)

    for w in ROLL_WINDOWS:
        rolled = df["H"].shift(1).rolling(w)
        df[f"H_roll{w}_mean"] = rolled.mean()
        df[f"H_roll{w}_std"]  = rolled.std()
        df[f"H_roll{w}_max"]  = rolled.max()
        df[f"H_roll{w}_min"]  = rolled.min()

    df["diff_1"] = df["H"].diff(1)
    df["diff_3"] = df["H"].diff(3)
    df["diff_7"] = df["H"].diff(7)

    df["month_sin"] = np.sin(2 * np.pi * df["Thang"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["Thang"] / 12)
    df["doy_sin"]   = np.sin(2 * np.pi * df["DOY"] / 365)
    df["doy_cos"]   = np.cos(2 * np.pi * df["DOY"] / 365)

    df["is_flood_season"] = df["Thang"].isin(FLOOD_MONTHS).astype(int)

    return df