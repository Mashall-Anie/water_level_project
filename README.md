# 🌊 Dự báo mực nước trạm Ba Thá – Sông Đáy

**Ứng dụng mô hình học máy (XGBoost & Random Forest) trong dự báo mực nước**  

---

## 📁 Cấu trúc dự án

```
Train_model/
├── data/                          # Dữ liệu đầu vào
│   ├── BaTha_annual_full_1994-2023.csv
│   ├── BaTha_annual_train_1994-2017.csv
│   ├── BaTha_annual_test_2018-2023.csv
│   ├── BaTha_daily_full_2017-2023.csv
│   ├── BaTha_daily_train_2017-2022.csv
│   └── BaTha_daily_test_2022-2023.csv
│
├── models/                        # Model đã lưu (.pkl)
├── outputs/                       # Kết quả: biểu đồ + CSV
│
├── config.py          # Cấu hình đường dẫn & siêu tham số
├── preprocessing.py   # Đọc dữ liệu, làm sạch, feature engineering
├── models.py          # XGBoost, RandomForest, metrics, lưu/tải model
├── visualization.py   # Tất cả đồ thị phân tích & đánh giá
├── main.py            # Pipeline chính (chạy end-to-end)
├── predict.py         # Dự báo cho dữ liệu mới
└── requirements.txt
```

---

## ⚙️ Cài đặt môi trường

```bash
# Tạo môi trường ảo (khuyến nghị)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Cài thư viện
pip install -r requirements.txt
```

---

## 🚀 Cách chạy

### 1. Chạy toàn bộ pipeline (mặc định)
```bash
python main.py
```
Tự động:
- Đọc & phân tích thống kê dữ liệu năm (1994–2023) và ngày (2017–2023)
- Feature engineering (lag, rolling, sin/cos thời gian)
- Huấn luyện XGBoost + Random Forest cho **mô hình năm** (Htb, Hmax, Hmin)
- Huấn luyện XGBoost + Random Forest cho **mô hình ngày**
- Đánh giá: RMSE, MAE, R², NSE
- Lưu model vào `models/`, lưu biểu đồ và kết quả vào `outputs/`

### 2. Chạy với hyperparameter tuning
```bash
python main.py --tune
```
*(Chậm hơn ~5–10 phút vì dùng GridSearch + TimeSeriesSplit)*

### 3. Chỉ chạy mô hình năm hoặc ngày
```bash
python main.py --annual    # chỉ mô hình năm
python main.py --daily     # chỉ mô hình ngày
```

---

## 🔮 Dự báo dữ liệu mới

### Dự báo mực nước ngày kế tiếp từ CLI
```bash
python predict.py \
  --values 150 145 140 135 130 120 110 100 90 85 80 75 70 65 \
  --model xgb
```
*(14 giá trị mực nước ngày gần nhất, từ cũ nhất → mới nhất)*

### Dự báo từ file CSV mới
```bash
python predict.py --file data/new_daily_data.csv --model xgb
```

### Dự báo mực nước năm
```bash
python predict.py --year 2024 --model xgb
```


## 📈 Outputs tạo ra

Sau khi chạy, thư mục `outputs/` chứa:

| File | Mô tả |
|------|-------|
| `01_annual_series.png` | Chuỗi thời gian Htb/Hmax/Hmin + xu thế |
| `02_annual_boxplot.png` | Box plot phân phối mực nước năm |
| `03_daily_series.png` | Chuỗi mực nước ngày theo từng năm |
| `04_monthly_mean.png` | Trung bình mực nước theo tháng |
| `annual_Htb_comparison.png` | Dự báo vs. Thực đo – Htb năm |
| `annual_Hmax_comparison.png` | Dự báo vs. Thực đo – Hmax năm |
| `annual_Hmin_comparison.png` | Dự báo vs. Thực đo – Hmin năm |
| `annual_feature_importance.png` | Feature importance (XGBoost – năm) |
| `daily_comparison.png` | Dự báo vs. Thực đo – H ngày |
| `daily_scatter_xgb.png` | Scatter plot XGBoost – ngày |
| `daily_feature_importance.png` | Feature importance (XGBoost – ngày) |
| `results_annual.csv` | Bảng kết quả mô hình năm |
| `results_daily.csv` | Bảng kết quả mô hình ngày |
| `results_all.csv` | Bảng tổng hợp tất cả mô hình |
