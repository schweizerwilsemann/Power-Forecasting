# Ghi chú Kỹ thuật Dự báo Điện Mặt Trời

## Tổng quan Bộ Dữ liệu
- Tệp nguồn: `Renewable.csv` (độ phân giải 15 phút bắt đầu từ năm 2017) được lưu ở thư mục gốc của dự án.
- Các cột bao gồm:
  - `Time`: dấu thời gian dạng ngày đứng trước (`01/01/2017 00:00`).
  - `Energy delta[Wh]`: điện lượng tạo ra trong mỗi khoảng 15 phút; là biến mục tiêu dự báo.
  - `GHI`: Global Horizontal Irradiance, đại lượng biểu thị bức xạ mặt trời khả dụng.
  - `temp`: nhiệt độ không khí, tính bằng độ C.
  - `pressure`: áp suất khí quyển tại mặt đất, đơn vị hPa.
  - `humidity`: độ ẩm tương đối (%).
  - `wind_speed`: tốc độ gió (m/s).
  - `rain_1h`, `snow_1h`: lượng mưa/tuyết trong giờ trước (mm).
  - `clouds_all`: phần trăm mây bao phủ.
  - `isSun`: cờ nhị phân cho biết mặt trời đang trên đường chân trời.
  - `sunlightTime`: số phút đã nhận ánh nắng trong ngày.
  - `dayLength`: tổng số phút ban ngày của ngày đó.
  - `SunlightTime/daylength`: tỷ lệ phần ngày đã có ánh nắng.
  - `weather_type`: mô tả thời tiết dạng phân loại.
  - `hour`, `month`: các cột trợ giúp do bộ dữ liệu cung cấp.
- Những cột bổ sung khác (nếu có) vẫn được giữ lại và có thể tạo thêm đặc trưng nếu được hỗ trợ trong bước xử lý đặc trưng.

## Quy trình Chuẩn bị Dữ liệu (`backend/app/train_model.py`)
1. Đọc tệp CSV bằng pandas, kiểm tra sự tồn tại của tập dữ liệu (dòng 35).
2. Gọi `make_features` để biến đổi dữ liệu thô thành bảng học có giám sát (dòng 36).
3. Chia bảng theo trục thời gian thành các tập train, validation và test với mốc cố định:
   - Train: dấu thời gian trước 2022-01-01.
   - Validation: từ 2022-01-01 tới 2022-06-30.
   - Test: từ 2022-07-01 trở đi.
4. Huấn luyện LightGBM trên tập train và theo dõi loss trên tập validation (dòng 49).
5. Tính MAE, RMSE trên tập test và lưu các artefact vào `backend/app/artifacts/` (dòng 65-82).

## Kỹ thuật Tạo Đặc Trưng (`backend/app/infrastructure/services/feature_engineering.py`)
- Xử lý thời gian:
  - Chuyển `Time` sang kiểu `datetime` của pandas với `dayfirst=True`, sắp xếp, đặt làm chỉ số và ép tần suất 15 phút (`asfreq('15min')`).
  - Các hàng thiếu dấu thời gian sẽ bị loại trong quá trình chuẩn hóa ở chế độ suy luận.
- Làm sạch năng lượng:
  - Đổi tên `Energy delta[Wh]` thành `energy_wh` cho thống nhất.
  - Loại bỏ giá trị điện âm và nội suy các đoạn thiếu ngắn (tối đa bốn mốc liên tiếp) để làm mượt các gián đoạn ngắn.
- Tín hiệu trễ của năng lượng:
  - Tạo các đặc trưng `lag_k` với `k` thuộc `(1, 4, 8, 16, 24)` phản ánh lịch sử sản lượng gần nhất.
- Thống kê trượt:
  - Với các cửa sổ `(4, 8, 16, 32)` (tương đương 1 tới 8 giờ) tính trung bình trượt và độ lệch chuẩn trượt trên chuỗi năng lượng trễ để nắm bắt xu hướng và độ biến động ngắn hạn.
- Trễ của các biến thời tiết:
  - Với mỗi cột thời tiết khả dụng (`temp`, `humidity`, `wind_speed`, `GHI`, `clouds_all`, `rain_1h`, `snow_1h`, `sunlightTime`, `SunlightTime/daylength`) tạo thêm giá trị trễ ở 1, 4 và 8 bước để mô hình nhận biết diễn biến thời tiết gần đây.
- Mã hóa lịch:
  - Mã hóa giờ trong ngày, thứ trong tuần và tháng trong năm bằng cặp sin/cos để thể hiện tính chu kỳ (`hour_sin`, `hour_cos`, ...).
- Tạo mục tiêu:
  - `target` là `energy_wh` tại tương lai được dịch `horizon` bước (mặc định 1 bước = 15 phút).
  - Các dòng thiếu dữ liệu sau khi tạo đặc trưng sẽ bị loại bỏ.
- Hỗ trợ suy luận:
  - Lớp `FeatureEngineer` chuẩn hóa dữ liệu lịch sử và tương lai, giới hạn cửa sổ lịch sử (mặc định 500 dòng) và tái sử dụng `make_features` để dựng đúng bộ đặc trưng mà mô hình mong đợi.

## Thông số Huấn luyện Mô hình
- Thuật toán: LightGBM regressor (`lightgbm.LGBMRegressor`).
- Siêu tham số:
  - `n_estimators = 2000`
  - `learning_rate = 0.05`
  - `num_leaves = 64`
  - `max_depth = -1` (không giới hạn độ sâu)
  - `subsample = 0.9`
  - `colsample_bytree = 0.8`
  - `reg_lambda = 0.1`
  - `reg_alpha = 0.05`
- Đầu vào: toàn bộ cột đặc trưng đã tạo, ngoại trừ `energy_wh` (giá trị hiện tại) và `target`.
- Đầu ra:
  - `model.joblib` lưu mô hình đã huấn luyện, danh sách đặc trưng theo thứ tự và metadata (horizon, mốc thời gian huấn luyện).
  - `metrics.json` lưu MAE và RMSE cho horizon tương ứng.
  - Các metric cũng được in ra stdout dưới dạng JSON khi kết thúc huấn luyện.

## Quy trình Suy luận và API
- `ArtifactModelRepository` nạp artefact một lần và lưu cache. `MetricsService` trả về metric khi cần.
- `CSVHistoryRepository` cung cấp các dòng cuối của `Renewable.csv` cho API khi cần dữ liệu lịch sử thời gian thực.
- `/forecast/next` sử dụng lịch sử lưu sẵn, dựng một hàng đặc trưng duy nhất và trả về dự báo tức thời (có thể thêm chỉ số lá cây LightGBM để giải thích nếu yêu cầu).
- `/forecast/batch` nhận tùy chọn mảng `history` và `future_weather`, dựng đặc trưng cho từng mốc tương lai và trả về danh sách kết quả.

## Giải thích Các Biến Thời Tiết
- `GHI`: thước đo trực tiếp lượng bức xạ mặt trời; càng cao thì sản lượng PV thường càng lớn.
- `temp`: hiệu suất tấm pin phụ thuộc nhiệt độ; nhiệt quá cao có thể làm giảm sản lượng ngay cả khi bức xạ mạnh.
- `humidity`: độ ẩm cao thường đi kèm mù sương hoặc mây, làm giảm bức xạ.
- `wind_speed`: gió giúp làm mát tấm pin, giảm hao hụt do nhiệt và báo hiệu sự dịch chuyển thời tiết.
- `rain_1h`, `snow_1h`: mưa/tuyết gần đây cho thấy trời nhiều mây và thiếu nắng; tuyết còn có thể che phủ bề mặt pin.
- `clouds_all`: tỷ lệ mây bao phủ, là chỉ báo mạnh cho các cú sụt sản lượng đột ngột.
- `sunlightTime` và `SunlightTime/daylength`: theo dõi tiến trình của ngày để suy ra giai đoạn bình minh/hoàng hôn.
- `isSun`: xác định liệu mặt trời đang chiếu sáng tại thời điểm đó.
- `dayLength`: tổng thời gian có nắng trong ngày, phản ánh biến thiên mùa vụ.
- Các trường phân loại khác như `weather_type` có thể được LightGBM xử lý khi được mã hóa dạng số.

## Tái tạo Toàn bộ Quy trình
1. (Tùy chọn) Tạo hoặc kích hoạt môi trường ảo Python và cài đặt phụ thuộc (`pip install -r requirements.txt`).
2. Chạy huấn luyện: `python -m app.train_model --data ..\Renewable.csv --horizon 1`.
3. Kiểm tra `backend/app/artifacts/metrics.json` để xem metric đánh giá.
4. Khởi động API: `uvicorn app.main:app --reload --port 8000`.
5. Frontend (`frontend/`):
   - `npm install`
   - Đảm bảo `.env.development` trỏ về backend (`VITE_API_URL=http://localhost:8000`).
   - `npm run dev` và mở URL hiển thị.

Tài liệu này cung cấp cái nhìn tổng quát về cách dữ liệu được biến đổi, những đặc trưng nào thúc đẩy mô hình và vì sao từng biến thời tiết lại ảnh hưởng đến dự báo công suất điện mặt trời.
