# PV Power Forecasting – Hướng dẫn Sử dụng

Tài liệu này giúp bạn thiết lập hệ thống, vận hành ứng dụng PV Power Forecasting và đọc đúng các chỉ số hiển thị trên từng tab.

---

## 1. Chuẩn bị môi trường

### Backend (FastAPI + LightGBM)
```bash
cd backend
python3 -m venv .venv
# Kích hoạt virtualenv
source .venv/bin/activate          # macOS/Linux
.\.venv\Scripts\activate.ps1        # Windows PowerShell

pip install -r requirements.txt

# Huấn luyện mô hình với dữ liệu mẫu
python -m app.train_model --data ../Renewable.csv

# Chạy API
python run.py --reload
```

API chạy tại `http://localhost:8000` và cung cấp Swagger ở `http://localhost:8000/docs`.

### Frontend (Vue 3 + Vite)
```bash
cd frontend
npm install
npm run dev
```

Front-end mặc định truy cập `http://localhost:5173`. Vite proxy những đường dẫn `/forecast`, `/metrics`, `/monitoring`,… về backend. Nếu backend chưa chạy, dev server sẽ báo lỗi `ECONNREFUSED`.

### Tests
Backend cần hoạt động trước khi chạy bộ kiểm thử:
```bash
python tests/test_enhanced_features.py
```

---

## 2. Tổng quan giao diện

Ứng dụng là SPA với thanh điều hướng cố định gồm 6 tab:

1. **Dashboard**
2. **Basic Forecast**
3. **Advanced Forecast**
4. **Data Quality**
5. **Historical Analysis**
6. **Model Management**

Các tab chia sẻ cùng layout và nút `Refresh` để tải lại dữ liệu từ API.

---

## 3. Chi tiết từng tab & diễn giải chỉ số

### 3.1 Dashboard

- **System Health**  
  - *Status indicator*: `healthy`, `warning`, `error` dựa trên `/monitoring/health`.  
  - *Health Score (%)*: 95% khi model sẵn sàng; < 70% nếu model chưa load.
  - *Model Status*: “Loaded” nếu model gateway báo sẵn sàng.
  - *Uptime*: số giờ & phút kể từ khi backend khởi chạy.

- **Data Quality card**  
  - *Data Completeness (%)*: tỉ lệ ô dữ liệu không thiếu trong lô 1.000 bản ghi gần nhất.  
  - *Anomalies*: số lượng điểm bất thường (Isolation Forest).  
  - *Quality Score (%)*: 0–100 (trừ điểm khi nhiều missing hoặc anomaly).

- **Forecast Accuracy card**  
  - *MAE (Wh)*: sai lệch tuyệt đối trung bình.  
  - *RMSE (Wh)*: sai lệch bình phương trung bình (nhạy với outlier).  
  - *Accuracy %*: công thức minh họa `100 - (MAE/1000)*100`, chỉ mang tính tham khảo.

- **Performance card**  
  - *CPU / Memory / Disk Usage (%)*: đọc từ `/monitoring/performance`.

- **Real-time Forecast chart**  
  - Chọn `horizon` (số bước 15 phút) để hiển thị đường dự báo, upper/lower confidence.  
  - Nút **Auto** bật refresh 30s/lần.  
  - Dữ liệu nhận từ `POST /forecast/advanced`.

- **System Monitoring**  
  - Tiến trình CPU, Memory, Disk (phần trăm). Nút **Refresh** gọi lại `/monitoring/performance`.

- **Advanced Features grid**  
  - Nhấp vào từng thẻ để di chuyển sang tab tương ứng (Advanced/Data Quality/Historical/Model).

- **Alerts**  
  - Khi API lỗi, một cảnh báo sẽ xuất hiện (Alert list). Có thể clear từng alert hoặc toàn bộ.

### 3.2 Basic Forecast

Tab hiển thị biểu mẫu `ForecastForm`:

- **Horizon**: số bước (15 phút) cần dự báo. Các giá trị lấy từ `/metrics.available_horizons`.
- **Include Components**: nếu bật, backend trả thêm `leaf_indices` của LightGBM (giải thích nội bộ).

Khi gửi form:
- `mode = "next"` gọi `POST /forecast/next`.
- `mode = "batch"` điều hướng đến block CSV (được parse thành `future_weather`) để gọi `POST /forecast/batch`.

**Diễn giải kết quả**
- `ForecastInsights`: hiển thị tổng quan series (max, min, trung bình, tổng, range thời gian).  
- `ForecastChart`: biểu đồ đường, có thể tải CSV (`ForecastChart @download`).  
- `ForecastTimeline`: danh sách từng bước dự báo.  
- `ForecastHistory`: lưu tối đa 5 lần gần nhất để khôi phục (`restoreHistory`).  
- `Metrics chips`:  
  - `MAE` / `RMSE` hiển thị giá trị lấy từ `/metrics`.  
  - `Last run label`: timestamp cuối trong kết quả dự báo.

**Export**: Nút tải CSV sử dụng timestamp bản địa hóa (`toIsoLocalString`), tên file dạng `pv-forecast-YYYY-MM-DDTHH-mm-ss.csv`.

### 3.3 Advanced Forecast

Mở rộng cho scenario/ensemble:

- **ForecastConfigPanel**  
  - *Horizon*: tương tự Basic.  
  - *Include confidence*: trả thêm `confidence_interval`.  
  - *Ensemble mode*: kết hợp LightGBM + RandomForest (trọng số 0.7/0.3).  
  - *Scenario count*: số kịch bản thời tiết chạy song song (1 → advanced đơn lẻ, >1 → `/forecast/scenarios`).

- **ScenarioList** (với `scenarioCount > 1`)  
  - Chỉnh `ghi`, `temp`, `clouds`, `windSpeed` cho từng kịch bản. Tối đa 5 mẫu template sẵn có.

- **ResultsPanel**  
  - Hiển thị bảng dự báo: `prediction_wh`, `confidence_interval`, `scenario_name`, `step_index`...

- **ExportActions**  
  - CSV, JSON, hoặc copy clipboard:
    - CSV gồm cột `timestamp`, `prediction_wh`, `confidence_lower`, `confidence_upper`, `scenario_name`.
    - JSON lưu toàn bộ `config` và `results`.

**Giải thích các trường trả về**
- `model_used`: `lightgbm` hoặc `ensemble`.  
- `individual_predictions`: khi ensemble bật, hiển thị giá trị riêng từng model.  
- `confidence_interval`:  
  - *lower/upper*: ±1.96*σ, với σ là độ lệch chuẩn error hoặc độ lệch dự báo giữa các model.  
  - *std*: độ lệch chuẩn của sai số (đơn vị Wh).  
- `step_index`: thứ tự bước trong horizon (1-based).  
- `scenario_id/name`: định danh kịch bản (khi chạy nhiều scenario).

### 3.4 Data Quality

Lấy dữ liệu từ `/data/quality` và thao tác import:

- **Quality Overview**  
  - *Quality Score (%)*: thang 0–100. `>= 90` (excellent), `>= 75` (good), `>= 60` (fair), ngược lại `poor`.  
  - *Completeness (%)*: phần trăm ô dữ liệu không bị thiếu.  
  - *Anomalies*: số điểm bất thường phát hiện.  
  - *Total Records*: số bản ghi dùng để tính (mặc định 1.000 gần nhất).  
  - *Last Updated*: timestamp backend tạo báo cáo.

- **Missing Values Analysis**  
  - Bảng liệt kê từng cột và số lượng missing.  
  - *Missing %*: `(count / total_records)*100`.  
  - *Status*: `good` nếu < 1%, `warning` 1–5%, `critical` > 5%.

- **Data Import & Validation**  
  - Hỗ trợ `CSV`, `XLSX`, `JSON`.  
  - Nút **Validate** gọi `POST /data/import` kèm file & tùy chọn `validation_rules`.  
  - Kết quả hiển thị `valid/invalid`, `quality_score`, danh sách `errors` & `warnings`.  
  - Nếu hợp lệ, có thể nhấn **Import Data** (hiện tại vẫn là mock – cần backend xử lý thực).  
  - Nút **Cancel** xóa trạng thái file/validation.

- **Anomaly Detection**  
  - Nút **Run Detection** gọi lại `/data/quality` và cập nhật `anomaly_count`.  
  - Ghi chú: backend dùng Isolation Forest với contamination = 0.1.

### 3.5 Historical Analysis

- **Khoảng thời gian hỗ trợ**: dữ liệu mẫu `Renewable.csv` từ `2017-01-01` đến `2022-08-31`.  
  - Form mặc định chọn 30 ngày cuối cùng (`2022-08-01` → `2022-08-31`).  
  - Nếu chọn ngoài vùng này, sẽ nhận thông báo tiếng Việt để chỉnh lại.

- **Aggregation**: `hour`, `day`, `week`. Backend dùng pandas `resample` tương ứng `H`, `D`, `W`.

- **Metrics summary**  
  - `MAE`, `RMSE`: sai số giữa giá trị thực và forecast naïve (dịch 1 bước).  
  - `MAPE`: phần trăm sai số tuyệt đối trung bình.  
  - `R2_SCORE`: hệ số xác định (1 = khớp hoàn hảo).  
  - Các metric chỉ hiển thị khi có đủ dữ liệu và không phải NaN.

- **Trend cards**  
  - `accuracy`: “improving / declining / stable” dựa vào MAE đầu & cuối (lower better).  
  - `performance`: thay đổi của `energy_sum` (higher better).

- **Line chart** (`Line` từ Chart.js)  
  - Mỗi dataset tương ứng với một chỉ số (`energy_mean`, `energy_sum`, `mae`, `rmse`,...).  
  - Hover hiển thị giá trị từng thời điểm.

- **Aggregated breakdown table**  
  - Tối đa 50 dòng gần nhất.  
  - Cột `timestamp` + các thống kê (`energy_mean`, `energy_sum`, `energy_max`, `energy_min`, `mae`, `rmse`...).

- **Lỗi thường gặp**  
  - “No data points within the requested window”: chọn khoảng ngoài dữ liệu → điều chỉnh.  
  - “Not enough data points to analyse…”: cần tối thiểu 2 điểm để tính sai số.

### 3.6 Model Management

Hiện tại backend trả mẫu tĩnh (placeholder). Tab vẫn hữu ích để chuẩn bị UI:

- **Status overview**  
  - `Current model`: ví dụ `lightgbm_v1.0`.  
  - `Available models`: danh sách model có thể chuyển đổi.  
  - `Last trained`: timestamp UTC.  
  - `Training status`: `ready` / `training` / `failed` (tùy backend).

- **Model metrics**  
  - Bảng `MAE`, `RMSE`, `R2_SCORE`, … đọc từ `model_metrics`.

- **Retraining actions**  
  - Nút **Trigger retrain** gọi `POST /models/retrain`.  
  - Response hiển thị trong khung `Retrain status`: `status`, `message`, `estimated_completion`.  
  - Phần `hint` nhắc cấu hình persistence trước khi ghi log thực tế.

- **Activity log**  
  - Ghi nhớ các hành động gần nhất trên UI (không lưu server).  
  - Mỗi dòng bao gồm timestamp, tiêu đề, mô tả ngắn.

Để hoàn thiện tab này với dữ liệu thật:
1. Cài đặt MySQL/PostgreSQL và tạo bảng `model_metrics`, `retrain_jobs`, `production_history`.  
2. Thay `CSVHistoryRepository` bằng repository đọc/ghi DB.  
3. Sửa `get_model_status` & `retrain_model` trả thông tin từ DB.

---

## 4. API chính & payload

- `GET /health`: kiểm tra nhanh backend sống.  
- `GET /metrics`: lấy horizon, MAE, RMSE, available horizons.  
- `POST /forecast/next`: `{ "horizon": 1, "include_components": false }`.  
- `POST /forecast/batch`: `{ "horizon": 4, "future_weather": [...], "timestamps": [...] }`.  
- `POST /forecast/advanced`: `{ "horizon": 4, "include_confidence": true, "ensemble_mode": false }`.  
- `POST /forecast/scenarios`: `{ "weather_scenarios": [...], "horizon": 4, ... }`.  
- `GET /monitoring/health` / `/performance`: trạng thái hệ thống.  
- `GET /data/quality`, `POST /data/import`.  
- `POST /analysis/historical`: `{ "start_date": "...", "end_date": "...", "aggregation": "day", "metrics": ["mae","rmse"] }`.  
- `GET /models/status`, `POST /models/retrain`.

Chi tiết schema xem thêm tại `backend/app/api/schemas.py`.

---

## 5. Cách đọc các chỉ số chính

| Chỉ số | Ý nghĩa | Ghi chú |
|-------|---------|---------|
| **MAE** (Wh) | Sai số tuyệt đối trung bình | Càng thấp càng tốt |
| **RMSE** (Wh) | Sai số bình phương trung bình | Nhạy với outlier; nên so cùng đơn vị với MAE |
| **MAPE** (%) | Sai số tuyệt đối phần trăm | Không ổn định nếu giá trị thực gần 0 |
| **R²** | Hệ số xác định | 1 = hoàn hảo, < 0 = mô hình tệ hơn baseline |
| **Quality Score** (%) | Đánh giá tổng thể dữ liệu | Dựa trên completeness, anomalies, missing cột quan trọng |
| **Completeness** (%) | % ô dữ liệu có giá trị | < 90% cần kiểm tra nguồn dữ liệu |
| **Anomaly Count** | Số điểm bất thường | Dùng Isolation Forest; cần manual review |
| **CPU/Memory/Disk Usage** (%) | Sức tải hệ thống | > 80% nên scale hoặc tối ưu |
| **Confidence Interval** | Khoảng tin cậy 95% theo sai số lịch sử | Dùng để đánh giá độ chắc chắn của dự báo |

---

## 6. Troubleshooting nhanh

| Triệu chứng | Nguyên nhân thường gặp | Giải pháp |
|-------------|------------------------|-----------|
| Vite báo `ECONNREFUSED` | Backend chưa chạy hoặc port khác | Khởi động lại `python run.py --reload` |
| Historical báo “No data points…” | Chọn khoảng thời gian ngoài dữ liệu mẫu | Chỉnh lại ngày trong 2017–08/2022 |
| Model Management không cập nhật | Backend trả dữ liệu tĩnh | Thực hiện repository DB & cập nhật API |
| `/forecast/next` trả 500 | Model chưa huấn luyện hoặc thiếu dữ liệu lịch sử | Chạy lại train `python -m app.train_model`, kiểm tra `Renewable.csv` |

---

## 7. Ghi chú mở rộng

- Dữ liệu mẫu `Renewable.csv` vẫn làm nguồn chính cho cả train lẫn inference. Khi chuyển sang cơ sở dữ liệu, cập nhật `Container` để trỏ tới repository mới.  
- Các tab Historical Analysis & Model Management đã sẵn UI/logic; chỉ cần backend trả dữ liệu thật để hoàn thiện.  
- Cross-validation cho mô hình chưa được tích hợp; current pipeline dùng split thời gian cố định (train < 2022-01-01, val 01–06/2022, test ≥ 07/2022).

---

Chúc bạn vận hành thuận lợi! Nếu cần mở rộng sang MySQL, logging hay cross-validation nâng cao, hãy cập nhật repository/service tương ứng và chỉnh tài liệu này cho phù hợp.***
