import os
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit

import config


def nash_sutcliffe(y_true, y_pred):
    numerator   = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
    denominator = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
    return 1 - numerator / denominator if denominator != 0 else -np.inf


def evaluate(y_true, y_pred, label=""):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    nse  = nash_sutcliffe(y_true, y_pred)

    if label:
        print(f"  [{label}]  RMSE={rmse:.2f} cm  |  MAE={mae:.2f} cm  |  R²={r2:.4f}  |  NSE={nse:.4f}")

    return {"RMSE": rmse, "MAE": mae, "R2": r2, "NSE": nse}


def get_xgb(params=None):
    params = params or config.XGB_PARAMS
    return XGBRegressor(**params, verbosity=0)


def get_rf(params=None):
    params = params or config.RF_PARAMS
    return RandomForestRegressor(**params)


def tune_model(model, param_grid, X_train, y_train, n_splits=5, scoring="neg_root_mean_squared_error"):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    gs = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=tscv,
        scoring=scoring,
        n_jobs=-1,
        verbose=0,
        refit=True,
    )
    gs.fit(X_train, y_train)
    print(f"    Best params: {gs.best_params_}")
    print(f"    Best CV score (neg-RMSE): {gs.best_score_:.4f}")
    return gs.best_estimator_, gs.best_params_


def train_and_predict(model, X_train, y_train, X_test):
    model.fit(X_train, y_train)
    return model.predict(X_test)


def save_model(model, filename):
    os.makedirs(config.MODEL_DIR, exist_ok=True)
    path = os.path.join(config.MODEL_DIR, filename)
    with open(path, "wb") as f:
        pickle.dump(model, f)
    print(f"  Đã lưu model: {path}")


def load_model(filename):
    path = os.path.join(config.MODEL_DIR, filename)
    with open(path, "rb") as f:
        model = pickle.load(f)
    return model


def feature_importance_df(model, feature_names):
    importances = model.feature_importances_
    df = pd.DataFrame({
        "Feature":    feature_names,
        "Importance": importances,
    }).sort_values("Importance", ascending=False).reset_index(drop=True)
    df["Importance (%)"] = (df["Importance"] / df["Importance"].sum() * 100).round(2)
    return df


def results_table(results_list):
    df = pd.DataFrame(results_list)
    for col in ["RMSE", "MAE"]:
        df[col] = df[col].round(2)
    for col in ["R2", "NSE"]:
        df[col] = df[col].round(4)
    return df


if __name__ == "__main__":
    print(">>> Kiểm tra module models.py ...\n")

    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.rand(100) * 500

    X_tr, y_tr = X[:80], y[:80]
    X_te, y_te = X[80:], y[80:]

    xgb = get_xgb()
    y_pred = train_and_predict(xgb, X_tr, y_tr, X_te)
    evaluate(y_te, y_pred, label="XGBoost demo")

    rf = get_rf()
    y_pred_rf = train_and_predict(rf, X_tr, y_tr, X_te)
    evaluate(y_te, y_pred_rf, label="Random Forest demo")

    print("\n[OK] models.py hoạt động bình thường.")
