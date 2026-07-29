
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import config

os.makedirs(config.OUTPUT_DIR, exist_ok=True)

C_ACTUAL = "#1F4E79"
C_XGB    = "#2E75B6"
C_RF     = "#E36C0A"
C_TREND  = "#C00000"
C_FILL   = "#BDD7EE"


def _save(fig, name):
    path = os.path.join(config.OUTPUT_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [Chart] Đã lưu: {path}")


def plot_daily_series(df):
    years = sorted(df["Nam"].unique())
    fig, axes = plt.subplots(len(years), 1,
                             figsize=(14, 2.8 * len(years)),
                             sharex=False)
    if len(years) == 1:
        axes = [axes]

    for ax, year in zip(axes, years):
        sub = df[df["Nam"] == year]
        ax.fill_between(sub["DOY"], sub["H"],
                        alpha=0.35, color=C_FILL)
        ax.plot(sub["DOY"], sub["H"],
                color=C_ACTUAL, linewidth=0.9)

        idx = sub["H"].idxmax()
        ax.scatter(sub.loc[idx, "DOY"], sub.loc[idx, "H"],
                   color=C_TREND, zorder=5, s=45)
        ax.annotate(f'{sub.loc[idx,"H"]:.0f} cm',
                    xy=(sub.loc[idx, "DOY"], sub.loc[idx, "H"]),
                    xytext=(5, 3), textcoords="offset points",
                    fontsize=8, color=C_TREND)

        ax.set_xlim(1, 365)
        ax.set_ylabel(f"{year}\n(cm)", fontsize=9)
        ax.set_ylim(df["H"].min() - 20, df["H"].max() + 40)
        ax.grid(linestyle="--", alpha=0.3)

        ticks  = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
        labels = ["T1","T2","T3","T4","T5","T6",
                  "T7","T8","T9","T10","T11","T12"]
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels, fontsize=8)

    fig.suptitle(
        "Diễn biến mực nước ngày tại trạm Ba Thá (2017–2023)",
        fontsize=13, fontweight="bold"
    )
    fig.tight_layout()
    _save(fig, "01_daily_series.png")


def plot_monthly_mean(df):
    monthly = (df.groupby("Thang")["H"]
               .agg(["mean", "std"])
               .reset_index())

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(monthly["Thang"], monthly["mean"],
           color=C_ACTUAL, alpha=0.75, label="Htb tháng")
    ax.errorbar(monthly["Thang"], monthly["mean"],
                yerr=monthly["std"],
                fmt="none", color="black",
                capsize=4, linewidth=1.2, label="±1 Std")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([f"T{m}" for m in range(1, 13)])
    ax.set_xlabel("Tháng", fontsize=11)
    ax.set_ylabel("Mực nước (cm)", fontsize=11)
    ax.set_title(
        "Phân phối mực nước theo tháng – trạm Ba Thá (2017–2023)",
        fontsize=12, fontweight="bold"
    )
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    _save(fig, "02_monthly_mean.png")


def plot_daily_boxplot(df):
    years = sorted(df["Nam"].unique())
    data  = [df[df["Nam"] == y]["H"].values for y in years]

    fig, ax = plt.subplots(figsize=(10, 5))
    bp = ax.boxplot(data, patch_artist=True,
                    labels=[str(y) for y in years],
                    medianprops=dict(color="red", linewidth=2))
    for patch in bp["boxes"]:
        patch.set_facecolor(C_FILL)
        patch.set_alpha(0.8)

    ax.set_xlabel("Năm", fontsize=11)
    ax.set_ylabel("Mực nước (cm)", fontsize=11)
    ax.set_title(
        "Phân phối mực nước ngày theo năm – trạm Ba Thá",
        fontsize=12, fontweight="bold"
    )
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    _save(fig, "03_daily_boxplot.png")


def plot_actual_vs_predicted_daily(y_true, y_pred_xgb, y_pred_rf,
                                   dates=None, n_plot=300):
    n    = min(n_plot, len(y_true))
    yt   = np.array(y_true)[-n:]
    yxgb = np.array(y_pred_xgb)[-n:]
    yrf  = np.array(y_pred_rf)[-n:]
    x    = dates[-n:] if dates is not None else np.arange(n)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.plot(x, yt,   color=C_ACTUAL, linewidth=1.8,
             label="Thực đo", zorder=3)
    ax1.plot(x, yxgb, color=C_XGB, linewidth=1.3,
             linestyle="--", label="XGBoost", zorder=2)
    ax1.plot(x, yrf,  color=C_RF,  linewidth=1.3,
             linestyle=":",  label="Random Forest", zorder=2)
    ax1.set_ylabel("Mực nước (cm)", fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(linestyle="--", alpha=0.35)
    ax1.set_title(
        f"Dự báo mực nước ngày – XGBoost vs. Random Forest "
        f"({n} ngày cuối tập test)",
        fontsize=12, fontweight="bold"
    )

    res = yt - yxgb
    ax2.bar(x, res,
            color=np.where(res >= 0, C_XGB, C_RF),
            alpha=0.75, width=1)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Sai số XGBoost (cm)", fontsize=11)
    ax2.set_xlabel("Ngày", fontsize=11)
    ax2.grid(linestyle="--", alpha=0.35)

    if dates is not None:
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        fig.autofmt_xdate(rotation=30)

    fig.tight_layout()
    _save(fig, "04_daily_comparison.png")


def plot_scatter_daily(y_true, y_pred_xgb, y_pred_rf):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, y_pred, name, color in zip(
        axes,
        [y_pred_xgb, y_pred_rf],
        ["XGBoost", "Random Forest"],
        [C_XGB, C_RF]
    ):
        yt   = np.array(y_true)
        yp   = np.array(y_pred)
        vmin = min(yt.min(), yp.min())
        vmax = max(yt.max(), yp.max())

        ax.scatter(yt, yp, alpha=0.4, color=color, s=12, edgecolors="none")
        ax.plot([vmin, vmax], [vmin, vmax],
                "r--", linewidth=1.5, label="1:1 line")

        r2   = 1 - np.sum((yt-yp)**2) / np.sum((yt-np.mean(yt))**2)
        rmse = np.sqrt(np.mean((yt-yp)**2))
        ax.text(0.05, 0.90,
                f"R² = {r2:.4f}\nRMSE = {rmse:.2f} cm",
                transform=ax.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

        ax.set_xlabel("Thực đo (cm)", fontsize=11)
        ax.set_ylabel("Dự báo (cm)", fontsize=11)
        ax.set_title(f"Scatter – {name} (H ngày)",
                     fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(linestyle="--", alpha=0.35)

    fig.tight_layout()
    _save(fig, "05_daily_scatter.png")


def plot_actual_vs_predicted_monthly(y_true, y_pred_xgb, y_pred_rf,
                                     target="Htb", dates=None):
    x = dates if dates is not None else np.arange(len(y_true))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7), sharex=True)

    ax1.plot(x, y_true,     color=C_ACTUAL, linewidth=2,
             label="Thực đo", zorder=3)
    ax1.plot(x, y_pred_xgb, color=C_XGB,   linewidth=1.5,
             linestyle="--", label="XGBoost", zorder=2)
    ax1.plot(x, y_pred_rf,  color=C_RF,    linewidth=1.5,
             linestyle=":",  label="Random Forest", zorder=2)
    ax1.set_ylabel(f"{target} (cm)", fontsize=11)
    ax1.legend(fontsize=10)
    ax1.grid(linestyle="--", alpha=0.35)
    ax1.set_title(
        f"Dự báo mực nước tháng – {target} "
        f"(XGBoost vs. Random Forest)",
        fontsize=12, fontweight="bold"
    )

    res = np.array(y_true) - np.array(y_pred_xgb)
    ax2.bar(x, res,
            color=np.where(res >= 0, C_XGB, C_RF),
            alpha=0.75, width=20)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Sai số XGBoost (cm)", fontsize=11)
    ax2.grid(linestyle="--", alpha=0.35)

    if dates is not None:
        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        fig.autofmt_xdate(rotation=30)

    fig.tight_layout()
    _save(fig, f"06_monthly_{target}_comparison.png")


def plot_scatter_monthly(y_true, y_pred_xgb, y_pred_rf, target="Htb"):
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    for ax, y_pred, name, color in zip(
        axes,
        [y_pred_xgb, y_pred_rf],
        ["XGBoost", "Random Forest"],
        [C_XGB, C_RF]
    ):
        yt   = np.array(y_true)
        yp   = np.array(y_pred)
        vmin = min(yt.min(), yp.min()) - 10
        vmax = max(yt.max(), yp.max()) + 10

        ax.scatter(yt, yp, alpha=0.7, color=color,
                   s=50, edgecolors="white", linewidths=0.5)
        ax.plot([vmin, vmax], [vmin, vmax],
                "r--", linewidth=1.5, label="1:1 line")

        r2   = 1 - np.sum((yt-yp)**2) / np.sum((yt-np.mean(yt))**2)
        rmse = np.sqrt(np.mean((yt-yp)**2))
        ax.text(0.05, 0.88,
                f"R² = {r2:.4f}\nRMSE = {rmse:.2f} cm",
                transform=ax.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))

        ax.set_xlabel("Thực đo (cm)", fontsize=11)
        ax.set_ylabel("Dự báo (cm)", fontsize=11)
        ax.set_title(f"Scatter – {name} ({target} tháng)",
                     fontsize=11, fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(linestyle="--", alpha=0.35)

    fig.tight_layout()
    _save(fig, f"07_monthly_{target}_scatter.png")


def plot_feature_importance(fi_df, title="Feature Importance",
                             filename="feature_importance.png",
                             top_n=15):
    df_plot = fi_df.head(top_n).copy()
    fig, ax = plt.subplots(figsize=(9, 0.5 * top_n + 2))

    colors = [C_XGB if i < 3 else C_FILL
              for i in range(len(df_plot))]
    bars = ax.barh(
        df_plot["Feature"][::-1],
        df_plot["Importance (%)"][::-1],
        color=colors[::-1], edgecolor="white"
    )
    for bar, val in zip(bars, df_plot["Importance (%)"][::-1]):
        ax.text(bar.get_width() + 0.2,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9)

    ax.set_xlabel("Tầm quan trọng (%)", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlim(0, df_plot["Importance (%)"].max() * 1.2)
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    _save(fig, filename)

        
def plot_metrics_comparison(results_list,
                             filename="metrics_comparison.png"):
    df     = pd.DataFrame(results_list)
    labels = [f"{r['Model']}\n{r['Dataset']}-{r['Target']}"
              for _, r in df.iterrows()]
    colors = [C_XGB if "XGBoost" in r["Model"] else C_RF
              for _, r in df.iterrows()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # RMSE
    bars = ax1.bar(range(len(df)), df["RMSE"],
                   color=colors, alpha=0.8, edgecolor="white")
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(labels, fontsize=8,
                         rotation=20, ha="right")
    ax1.set_ylabel("RMSE (cm)", fontsize=11)
    ax1.set_title("So sánh RMSE (thấp hơn = tốt hơn)",
                  fontsize=11, fontweight="bold")
    for bar, val in zip(bars, df["RMSE"]):
        ax1.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 0.3,
                 f"{val:.2f}", ha="center", fontsize=8)
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    # NSE
    bars = ax2.bar(range(len(df)), df["NSE"],
                   color=colors, alpha=0.8, edgecolor="white")
    ax2.axhline(0.75, color="red", linestyle="--",
                linewidth=1.2, label="Ngưỡng tốt (0.75)")
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(labels, fontsize=8,
                         rotation=20, ha="right")
    ax2.set_ylabel("NSE", fontsize=11)
    ax2.set_ylim(0, 1.05)
    ax2.set_title("So sánh NSE (cao hơn = tốt hơn)",
                  fontsize=11, fontweight="bold")
    for bar, val in zip(bars, df["NSE"]):
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 0.005,
                 f"{val:.4f}", ha="center", fontsize=8)
    ax2.legend(fontsize=9)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    _save(fig, filename)