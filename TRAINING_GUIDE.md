# Hướng Dẫn Huấn Luyện & Đọc Thông Số Mô Hình

Tài liệu này giúp bạn (1) chuẩn bị môi trường, (2) chạy huấn luyện mô hình dự báo công suất điện mặt trời, (3) hiểu rõ pipeline hoạt động ra sao và (4) đọc/giải thích các thông số đầu ra.

## 1. Chuẩn Bị

| Hạng mục | Ghi chú |
| --- | --- |
| Phiên bản Python | 3.10+ (đã kiểm thử với 3.12) |
| Thư mục làm việc | `backend/` |
| Phụ thuộc | `pip install -r backend/requirements.txt` |
| Dữ liệu huấn luyện | `Renewable.csv` ở thư mục gốc, độ phân giải 15 phút, cột chính `Time`, `Energy delta[Wh]` và các biến thời tiết |

> **Tip:** Nếu bạn đặt dữ liệu ở vị trí khác, dùng tham số `--data` khi chạy lệnh huấn luyện để chỉ định đường dẫn mới.

## 2. Huấn Luyện Nhanh

```bash
cd backend
python -m app.train_model \
  --data ../Renewable.csv \
  --horizon 1
```

Mặc định horizon = 1 tương đương dự báo sản lượng của 15 phút kế tiếp. Có thể tăng `--horizon` để dự báo xa hơn (mỗi bước = 15 phút).

### Tham số CLI

| Tham số | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `--data PATH` | `../Renewable.csv` | Đường dẫn tới tệp dữ liệu nguồn |
| `--horizon INT` | `1` | Số bước 15 phút cần dự báo; giá trị lớn yêu cầu đủ lịch sử ở cuối file |

## 3. Pipeline Hoạt Động

1. **Đọc & kiểm tra dữ liệu** *(app/train_model.py:32–40)*  
   - Kiểm tra file tồn tại, nạp vào pandas DataFrame.
2. **Tạo đặc trưng với `make_features`** *(backend/app/infrastructure/services/feature_engineering.py)*  
   - Chuẩn hóa cột `Time` ➝ index 15 phút.  
   - Đổi tên `Energy delta[Wh]` thành `energy_wh`, loại giá trị âm, nội suy khoảng thiếu ngắn.  
   - Sinh đặc trưng lag (`lag_1`, `lag_4`, …), thống kê trượt (`roll_mean_4`, …), lag cho biến thời tiết, mã hóa chu kỳ (giờ, thứ, tháng) và tạo `target = energy_wh` dịch `horizon` bước.
3. **Chia tập** *(app/train_model.py:24–33)*  
   - Train: trước `2022-01-01`.  
   - Validation: `2022-01-01` → `2022-06-30`.  
   - Test: từ `2022-07-01` trở đi.
4. **Huấn luyện LightGBM** *(app/train_model.py:43–63)*  
   - Siêu tham số cố định: `n_estimators=2000`, `learning_rate=0.05`, `num_leaves=64`, `subsample=0.9`, `colsample_bytree=0.8`, `reg_lambda=0.1`, `reg_alpha=0.05`.  
   - Theo dõi `eval_metric='l2'` trên tập validation để đảm bảo không quá khớp.
5. **Đánh giá & lưu artefact** *(app/train_model.py:65–90)*  
   - Tính MAE, RMSE trên tập test.  
   - Ghi `model.joblib` & `metrics.json` vào `backend/app/artifacts/`.

## 4. Đọc Các Artefact

### `backend/app/artifacts/model.joblib`
- Object `dict` gồm:
  - `model`: LightGBM đã huấn luyện.
  - `features`: danh sách cột đầu vào theo đúng thứ tự khi huấn luyện.
  - `horizon`: số bước dự báo tương ứng artefact này.
  - `trained_on`: thông tin mốc thời gian train/val.
- Cách kiểm tra nhanh:

```python
import joblib
state = joblib.load("backend/app/artifacts/model.joblib")
print(state["horizon"], len(state["features"]))
```

### `backend/app/artifacts/metrics.json`

```json
{
  "horizon": 1,
  "mae": 128.42,
  "rmse": 210.77
}
```

- `mae`: Sai số tuyệt đối trung bình (Wh). Giá trị càng thấp càng tốt, dễ diễn giải vì cùng đơn vị với sản lượng.  
- `rmse`: Sai số bình phương trung bình (Wh). Nhạy hơn với outlier; hữu ích để phát hiện sai lệch lớn.  
- `horizon`: Nhắc lại mô hình đang dự báo trước bao nhiêu bước.

> **Mẹo đọc nhanh:** So sánh `mae` với sản lượng trung bình giờ cao điểm để đánh giá ý nghĩa. Ví dụ: nếu trung bình giờ cao điểm 3000 Wh mà MAE 120 Wh thì sai số ~4%.

## 5. Kiểm Tra Sau Huấn Luyện

1. **Đảm bảo file artefact mới sinh**  
   - `ls backend/app/artifacts/` phải thấy `model.joblib` và `metrics.json` (thời gian cập nhật mới nhất).  
2. **Gọi API `/metrics`** (sau khi chạy backend) để chắc chắn dịch vụ đã nạp metric mới.  
3. **Chạy test nhanh** (tùy chọn) để xác thực pipeline không bị phá vỡ:  
   ```bash
   python tests/test_enhanced_features.py
   ```

## 6. Tùy Biến & Thực Tiễn Tốt

- **Huấn luyện nhiều horizon**: chạy lặp với các giá trị `--horizon` khác nhau và lưu artefact riêng (ví dụ đặt tên `model_h{horizon}.joblib`).  
- **Theo dõi version dữ liệu**: ghi chú SHA/timestamp của `Renewable.csv` vào README hoặc commit message để dễ tái lập.  
- **Làm sạch bổ sung**: nếu dữ liệu có nhiều missing liên tiếp > 4 bước, hãy xử lý trước khi gọi script (ví dụ nội suy theo ngày).  
- **Giới hạn tài nguyên**: LightGBM có thể tiêu tốn RAM với `n_estimators` cao; giảm `num_leaves` hoặc `n_estimators` nếu máy yếu.

## 7. Frontend: Đầu Vào, Params & Biểu Đồ

### 7.1 Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Đảm bảo `.env.development` có `VITE_API_URL=http://localhost:8000` để frontend truy cập API.

### 7.2 Tab Dashboard (`frontend/src/components/Dashboard.vue`)
- **Điều khiển chính**
  - `Refresh`: gọi đồng thời `/monitoring/health`, `/data/quality`, `/metrics`, sau đó cập nhật biểu đồ realtime.
  - `Horizon select`: 1/4/8/24 bước (≈15 phút → 6h); giá trị gởi tới `/forecast/advanced`.
  - `Auto/Pause`: bật tắt cron 30s để làm mới số liệu; nên tắt khi cần kiểm tra thủ công.
  - `System Monitoring Refresh`: cập nhật riêng CPU/Memory/Disk từ `/monitoring/performance`.
- **Outputs cần đọc**
  - **System/Data/Accuracy/Performance cards**: hiển thị `healthScore`, `modelStatus`, `dataQuality`, `mae`, `rmse`, `cpuUsage`, `memoryUsage`, `diskUsage`.
  - **Real-time chart**: ba dataset (`Prediction`, `Confidence Upper`, `Confidence Lower`). Các dải xanh lá tạo vùng tin cậy; biến mất nếu backend không trả `confidence_interval`.
  - **Alerts**: push khi fetch lỗi hoặc khi backend trả cảnh báo; luôn kiểm trước khi thao tác để không bỏ lỡ sự cố.

### 7.3 Tab Basic Forecast – Inputs (`frontend/src/components/ForecastForm.vue`)
| Chế độ | Trường | Mô tả | API đích |
| --- | --- | --- | --- |
| Immediate (`mode = 'next'`) | `Horizon (steps)` | Số bước 15 phút; ánh xạ `payload.horizon`. | `/forecast/next` |
|  | `Include tree leaf indices` | Boolean `includeComponents`; bật để nhận thêm `leaf_indices`. | `/forecast/next` |
| Batch (`mode = 'batch'`) | `futureCsv` textarea | Block CSV gồm header + dữ liệu phù hợp `Renewable.csv`; script chuẩn hóa alias (`timestamp` → `Time`, `energy` → `Energy delta[Wh]`, …). | `/forecast/batch` |
|  | `timestamps override` | Danh sách `ISO8601` dùng nếu muốn ép nhãn thời gian. | `/forecast/batch` |
|  | `Insert sample data` | Nút điền mẫu 3 hàng để người dùng chỉnh sửa. | – |

- **Validation flow**: frontend tự loại dòng rỗng, convert số → `Number`, chuỗi trống → `null`. Thiếu cột `Time` hoặc không có hàng ➝ cảnh báo; backend tiếp tục kiểm schema chi tiết.
- **History**: mỗi lần chạy sẽ ghi nhận trong `ForecastHistory` gồm mode, số bước, tổng Wh, range timestamp để người dùng khôi phục.

### 7.4 Tab Basic Forecast – Outputs
- **ForecastChart (`frontend/src/components/ForecastChart.vue`)**: đường màu xanh `prediction_wh`; tooltip hiển thị `Wh`. Có nút `Download CSV` (emit `download`) để lấy dữ liệu đã render.
- **ForecastTimeline (`frontend/src/components/ForecastTimeline.vue`)**: danh sách từng bước với `valueLabel`, phần trăm lấp đầy so với đỉnh (`fillWidth`), và `deltaLabel` (bao gồm % thay đổi). Dùng để phát hiện ramp-up/down.
- **ForecastInsights (`frontend/src/components/ForecastInsights.vue`)**: tự phân tích `max/min/avg`, `trend`, `volatility`, và tạo thông điệp (`Upward momentum`, `High volatility`). Khi truyền `metrics`, sẽ có thêm insight về horizon và confidence band.
- **ForecastHistory (`frontend/src/components/ForecastHistory.vue`)**: cho phép `Restore view` (emit `restore`). Mỗi entry hiển thị mode, tổng Wh, peak/avg/min, range thời gian.

### 7.5 Tab Advanced Forecast (`frontend/src/components/AdvancedForecast.vue`)
- **Inputs**
  - `Forecast Horizon`: select 1/4/8/24/48 bước → gửi `horizon`.
  - `Include Confidence Intervals`: toggle `include_confidence`.
  - `Use Ensemble Models`: bật `ensemble_mode`; nên dùng khi muốn ổn định hơn đổi lấy thời gian phản hồi.
  - `Weather Scenarios`: 1,3,5. Khi >1, `ScenarioList` hiển thị từng scenario có tham số `ghi`, `temp`, `clouds`, `windSpeed`. Người dùng có thể chỉnh để mô phỏng điều kiện thời tiết.
- **Gọi API**
  - ScenarioCount = 1 ➝ POST `/forecast/advanced` với `{horizon, include_confidence, ensemble_mode}` và nhân bản kết quả cho từng bước.
  - ScenarioCount > 1 ➝ POST `/forecast/scenarios` với danh sách `weather_scenarios` (đã đổi tên cột phù hợp backend).
- **Outputs (`ResultsPanel.vue`)**
  - `summary-stats`: Average Prediction, Confidence Range (min–max), Model Used.
  - Chart multi-line tương tự Basic.
  - `result-cards`: mỗi step/senario có `prediction_wh`, delta vs bước trước, progress bar, text Confidence (hoặc “No confidence band”). Các thẻ đổi màu theo xu hướng (`intent`).
  - `ExportActions`: tải CSV/JSON hoặc copy clipboard kèm confidence; dùng để kiểm toán.

### 7.6 Tab Data Quality (`frontend/src/components/DataQuality.vue`)
- **Inputs/Actions**
  - `Refresh`: fetch `/data/quality`.
  - File upload khu “Upload Data File”: nhận `.csv/.xlsx/.json`; lưu vào `selectedFile`.
  - `Validate File`: POST multipart tới `/data/import`, hiển thị `validationResult` (score + errors). Chỉ sau khi hợp lệ mới bấm `Import Data` (hiện tại mô phỏng).
  - `Run Detection`: giả lập phát hiện bất thường, cập nhật danh sách anomalies (mong chờ tích hợp backend `/monitoring/anomalies`).
  - `Add/Edit/Delete Rule`: hiện log ra console; dự kiến mở modal để cấu hình.
- **Outputs**
  - `Overall Quality Score`, `Completeness`, `Anomaly Count`, `Missing Values` bảng: xem % thiếu theo cột và trạng thái (`excellent/good/warning/critical`).
  - `Data Statistics`: tổng bản ghi, thời gian cập nhật, tổng thiếu.
  - `Validation Results`: hiển thị `quality_score`, danh sách lỗi/cảnh báo, trạng thái `Valid/Invalid`.
  - `Anomalies list`: timestamp, mô tả, mức độ (`high/medium/...`).
  - `Rules list`: liệt kê Rule name, column, condition, trạng thái bật/tắt.

### 7.7 Tabs khác & quy tắc duyệt
- **Historical Analysis** & **Model Management**: hiện dạng “Coming Soon”; nếu build tương lai cần kiểm tra branch hoặc bật feature flag.
- **Trình tự khuyến nghị trước khi thao tác**
  1. Mở Dashboard kiểm tra health/alerts.
  2. Sang Basic Forecast nếu cần chạy nhanh; ghi nhớ horizon/metrics đang hiển thị.
  3. Nếu phải mô phỏng đa kịch bản hoặc cần confidence, chuyển Advanced và điều chỉnh config + scenario rồi mới Generate.
  4. Khi chuẩn bị nhập dữ liệu mới, qua tab Data Quality để rà thiếu, chạy validate & import.
  5. Lặp lại chu trình khi metric/alert đổi trạng thái.

### 7.8 Cách đọc đầu vào/đầu ra nói chung
- **Input validation flow**
  1. Người dùng chọn tab phù hợp và nhập tham số.
  2. Frontend chuẩn hóa dữ liệu (đổi tên cột, parse số) trước khi gửi JSON/Multipart.
  3. Backend phản hồi; nếu lỗi 4xx/5xx hiển thị alert/toast (cần bổ sung toast cho trải nghiệm tốt hơn).
- **Outputs quan trọng**
  - `prediction_wh`: giá trị dự báo chính (Wh mỗi 15 phút).
  - `confidence_interval.upper/lower`: dải tin cậy; càng hẹp mô hình càng tự tin.
  - `leaf_indices`: chỉ có khi bật, dùng cho phân tích nội bộ LightGBM.
  - `metrics.mae/rmse/horizon`: baseline chất lượng; hiển thị cả trong hero chip và Dashboard.
  - `system` metrics (CPU/Memory/Disk): giám sát tài nguyên backend; >80% nên tạm dừng auto-refresh.
- **Đọc biểu đồ**
  - Độ dốc đường xanh = tốc độ ramp.  
  - `ForecastTimeline`/`result-cards` giúp nhận diện delta lớn.  
  - Nếu điểm thực tế (khi đối chiếu) nằm ngoài `Confidence Upper/Lower`, kiểm tra lại dữ liệu đầu vào hoặc huấn luyện lại.

## 8. Khắc Phục Sự Cố

| Triệu chứng | Nguyên nhân phổ biến | Cách xử lý |
| --- | --- | --- |
| `FileNotFoundError: Dataset not found` | Sai đường dẫn `--data` | Kiểm tra lại path, ưu tiên dùng đường dẫn tuyệt đối |
| `ValueError: Input frame must contain 'Time'` | Dữ liệu đổi tên cột | Đảm bảo cột `Time` đúng chính tả và định dạng ngày `day-first` |
| `ValueError: Expected 'Energy delta[Wh]'` | Thiếu cột năng lượng | Đổi tên cột hoặc cập nhật script để tương thích |
| MAE/RMSE tăng đột biến | Dữ liệu mới sai lệch, horizon cao | Kiểm tra phân bố dữ liệu, cân nhắc tăng kích thước train set hoặc tinh chỉnh siêu tham số |

---

Bạn đã có đầy đủ thông tin để huấn luyện, hiểu cơ chế hoạt động và đọc các thông số đánh giá của mô hình dự báo PV. Nếu cần thêm ví dụ cụ thể (ví dụ huấn luyện đa horizon, logging …), hãy tạo issue hoặc cập nhật tài liệu này.
