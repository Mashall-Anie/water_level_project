"""
Cấu hình toàn cục cho dự án dự báo mực nước
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR  = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "models")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

DAILY_FULL = os.path.join(
    DATA_DIR, "BaTha_daily_full_2017-2023.csv"
)

DAILY_TARGET = "H"
LAG_DAYS = [1, 2, 3, 5, 7, 14, 21, 30]

MONTHLY_TARGETS = ["Htb", "Hmax", "Hmin"]
LAG_MONTHS = [1, 2, 3, 6, 12]

XGB_PARAMS = {
    "n_estimators":     500,
    "max_depth":        3,
    "learning_rate":    0.01,
    "subsample":        0.8,
    "colsample_bytree": 0.85,
    "reg_alpha":        0.1,
    "reg_lambda":       2.0,
    "random_state":     42,
    "n_jobs":           -1,
}

RF_PARAMS = {
    "n_estimators":      500,
    "max_depth":         15,
    "min_samples_split": 3,
    "min_samples_leaf":  3,
    "max_features":      "sqrt",
    "random_state":      42,
    "n_jobs":            -1,
}