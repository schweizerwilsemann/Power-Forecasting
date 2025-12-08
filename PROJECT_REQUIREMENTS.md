# Báo cáo đáp ứng yêu cầu đồ án

Tài liệu này tổng hợp các minh chứng để chứng tỏ project PV Power Forecasting đã đáp ứng từng mục trong yêu cầu đồ án khai thác dữ liệu.

## 1. Phát biểu bài toán

- **Bối cảnh**: Trang trại điện mặt trời cần biết trước công suất phát trong từng khoảng 15 phút để lập kế hoạch hòa lưới, đặt điểm vận hành inverter, tối ưu lịch bảo trì và cảnh báo thiếu hụt khi mây kéo tới. Dữ liệu lịch sử nằm trong `Renewable.csv` với các biến thời tiết đo tại hiện trường.
- **Bài toán**: Với một chuỗi thời gian gồm năng lượng PV trong quá khứ và các tín hiệu thời tiết (GHI, nhiệt độ, độ ẩm, gió, mây,…), dự báo năng lượng sinh ra trong `h` bước tiếp theo (mỗi bước = 15 phút) sao cho sai số MAE/RMSE nhỏ nhất trên giai đoạn kiểm thử từ 2022-07-01 trở đi.
- **Đầu ra yêu cầu**: (1) bảng dự báo thời gian thực, (2) các kịch bản thời tiết giả lập, (3) confidence interval cho mỗi bước dự báo, (4) dashboard giám sát chất lượng dữ liệu & hệ thống để minh hoạ ứng dụng thực tế.

## 2. Dữ liệu & thống kê

### 2.1 Nguồn và thành phần

- **Tệp nguồn**: `Renewable.csv` do giảng viên cung cấp trên LMS (được trích xuất từ hệ thống SCADA nhà máy PV, độ phân giải 15 phút), lưu tại thư mục gốc repo.
- **Quy mô**: 196 776 dòng, 20+ thuộc tính; khoảng thời gian 2017-01-01 00:00 → 2022-08-31 23:45.
- **Thuộc tính chính**: `Time`, `Energy delta[Wh]`, `GHI`, `temp`, `humidity`, `wind_speed`, `rain_1h`, `snow_1h`, `clouds_all`, `sunlightTime`, `SunlightTime/daylength`, `isSun`, cùng các cột hỗ trợ như `weather_type`, `hour`, `month`.
- **Cách tái tạo thống kê**: `python3 scripts/data_profile.py --csv Renewable.csv`.

### 2.2 Thống kê mô tả

| Thuộc tính           | Min   | Max   | Mean  | Median | Std   | Ghi chú |
|----------------------|-------|-------|-------|--------|-------|---------|
| Energy delta[Wh]     | 0.0   | 5020.0| 573.01| 0.0    | 1044.82| 196 776 mẫu; median 0 phản ánh nhiều bước ban đêm. |
| GHI (W/m²)           | 0.0   | 229.2 | 32.60 | 1.6    | 52.17 | GHI cao trùng khung giờ nắng; tỷ lệ 0 lớn vào buổi tối. |
| temp (°C)            | -16.6 | 35.8  | 9.79  | 9.3    | 7.99  | Mùa đông lạnh sâu, mùa hè ~35 °C. |
| humidity (%)         | 22.0  | 100.0 | 79.81 | 84.0   | 15.60 | Khá ẩm, ảnh hưởng tới suy hao quang học. |
| wind_speed (m/s)     | 0.0   | 14.3  | 3.94  | 3.7    | 1.82  | Đa số <5 m/s; tăng vào buổi chiều. |

*(Nguồn số liệu: `scripts/data_profile.py`, ngày chạy 2024-05-06).*  
Ngoài các cột trên, báo cáo có thể bổ sung mô tả `rain_1h`, `clouds_all`, `sunlightTime` tùy nhu cầu.

### 2.3 Nhận xét

- Phân phối mục tiêu rất lệch phải (median 0), nên cần đặc trưng lag/rolling để phân biệt ban ngày/ban đêm thay vì chỉ dựa vào trung bình.
- Các biến thời tiết đều nằm trong miền hợp lý (không có giá trị âm bất thường), thuận lợi cho việc nội suy ngắn hạn (đã triển khai trong pipeline).

## 3. Tiền xử lý & lý do chọn

Áp dụng trong `backend/app/infrastructure/services/feature_engineering.py`:

1. **Chuẩn hóa thời gian**: ép `Time` sang UTC, sắp xếp và `.asfreq('15min')` để giữ đúng độ phân giải → tránh thiếu/nhân bản thời gian.
2. **Làm sạch năng lượng**: đổi tên `Energy delta[Wh]` → `energy_wh`, loại giá trị âm và nội suy tối đa 4 bước để bịt các lỗ hổng ngắn.
3. **Đặc trưng lịch sử**: tạo lag `(1,4,8,16,24)` và thống kê trượt `(4,8,16,32)` nhằm mô tả xu hướng, độ biến động ngắn hạn.
4. **Đặc trưng thời tiết trễ**: với các cột thời tiết hiện có, bổ sung lag 1/4/8 để mô hình nhận biết diễn biến mây, nhiệt độ gần nhất.
5. **Mã hóa chu kỳ**: sin/cos cho giờ, thứ, tháng để giữ tính tuần hoàn mà không tạo ranh giới giả (ví dụ 23h vs 0h).
6. **Tạo nhãn**: `target = energy_wh.shift(-horizon)` cho từng horizon ⇒ biến bài toán chuỗi thời gian thành bài toán hồi quy thông thường.

## 4. Giải thuật & lý do chọn

| Thuật toán | Vai trò | Lý do lựa chọn |
|------------|---------|----------------|
| **Persistence baseline** (dùng ngay giá trị gần nhất) | Benchmark tối thiểu | Đơn giản, không cần huấn luyện; giúp chứng minh mô hình học máy đem lại lợi ích thực sự. |
| **LightGBM Regressor** (`backend/app/train_model.py`) | Mô hình chính | Xử lý tốt đặc trưng tabular với nhiều cột lag/mã hóa chu kỳ, hỗ trợ training nhanh cho nhiều horizon, có sẵn công cụ explainability (leaf indices). |
| **RandomForest + Ensemble** (`backend/app/application/advanced_forecasting_service.py`) | Mô hình phụ để kết hợp, cung cấp confidence interval | RandomForest ổn định với nhiễu, đóng vai trò “ý kiến thứ hai” giúp ensemble giảm phương sai; dễ huấn luyện lại từ dữ liệu lịch sử mới khi chạy API. |

## 5. Đánh giá & độ đo

### 5.1 Công thức sử dụng

- Mean Absolute Error (MAE): `MAE = (1/n) * Σ |y_i - ŷ_i|`
- Root Mean Squared Error (RMSE): `RMSE = sqrt( (1/n) * Σ (y_i - ŷ_i)^2 )`
- Mean Absolute Percentage Error (MAPE): `MAPE = (100/n) * Σ |(y_i - ŷ_i) / y_i|`
- Coefficient of Determination (R²): `R² = 1 - Σ (y_i - ŷ_i)^2 / Σ (y_i - ȳ)^2`

MAE dễ diễn giải vì cùng đơn vị Wh; RMSE nhạy với outlier; MAPE dùng cho báo cáo tỉ lệ; R² giúp so sánh phù hợp mô hình trên các giai đoạn khác nhau.

### 5.2 Kết quả & so sánh

| Phương pháp / Horizon (15') | MAE (Wh) | RMSE (Wh) | Ghi chú |
|-----------------------------|----------|-----------|---------|
| Persistence baseline / 1    | **168.98** | 375.01 | Đo bằng `scripts/data_profile.py` trên giai đoạn test ≥ 2022-07-01. |
| Moving-average-4 / 1        | 229.24 | 419.96 | Baseline thứ hai để tham chiếu. |
| LightGBM / 1                | **165.90** | 359.79 | `backend/artifacts/metrics_h1.json`. Cải thiện cả MAE & RMSE so với baseline. |
| LightGBM / 4                | 219.92 | 451.83 | `metrics_h4.json`. Sai số tăng khi dự báo xa hơn. |
| LightGBM / 8                | 251.60 | 506.31 | `metrics_h8.json`. |
| LightGBM / 24               | 304.11 | 587.35 | `metrics_h24.json`. |
| LightGBM / 48               | 321.30 | 617.72 | `metrics_h48.json`. |

- **Confidence intervals** do `AdvancedForecastingService` sinh dựa trên (1) độ lệch chuẩn lỗi lịch sử hoặc (2) độ lệch giữa các model trong ensemble, giúp chuyển giao kết quả theo yêu cầu mục IV.
- Khi cần đánh giá RandomForest/Ensemble đầy đủ, bật `ensemble_mode=True` ở `/forecast/advanced`, ghi lại MAE/RMSE từ log API để bổ sung vào bảng trên.

## 6. Kết luận, ưu/nhược và hướng phát triển

- **Ưu điểm**: pipeline huấn luyện rõ ràng, mô hình chính ổn định hơn baseline, dashboard + API chứng minh tính ứng dụng thực tế, có chức năng giám sát chất lượng dữ liệu và hệ thống.
- **Hạn chế**: LightGBM chưa được tinh chỉnh siêu tham số theo từng mùa, chưa log metrics cho RandomForest/ensemble và các horizon > 48 vẫn là placeholder; dữ liệu hiện vẫn nằm ở CSV (chưa có DB).
- **Hướng phát triển**: 
  1. Tự động hoá retraining theo mùa và lưu lịch sử metric để so sánh nhiều lần chạy. 
  2. Ghi nhận kết quả ensemble trong `metrics_h*.json` + bổ sung biểu đồ so sánh trong dashboard. 
  3. Tích hợp kho dữ liệu (PostgreSQL) và viết module import thực thay cho mock trong `/data/import`. 
  4. Viết báo cáo PDF & slide chính thức dựa trên tài liệu này.

## 7. Deliverables theo yêu cầu GV

| Hạng mục | Trạng thái/ghi chú |
|----------|-------------------|
| **Báo cáo PDF** | Dựa trên nội dung file này + hình ảnh giao diện. |
| **Slide trình chiếu** | Tóm tắt bài toán, pipeline, kết quả so sánh (LightGBM vs baseline). |
| **Mã nguồn & dữ liệu** | Toàn bộ repo kèm `Renewable.csv`, `backend/artifacts/`. |
| **Hướng dẫn cài đặt** | Đã có `README.md`, `USAGE_GUIDE.md`, `TRAINING_GUIDE.md`; cần xuất ra PDF hoặc gắn link trong báo cáo. |
| **Ứng dụng demo** | Frontend + backend (đã mô tả trong README). |

> Khi nộp trên LMS: đóng gói thư mục chứa (1) báo cáo PDF, (2) slide, (3) mã nguồn + dữ liệu + hướng dẫn. Link tới tài liệu này nên đặt trong phụ lục để GV dễ kiểm tra.
