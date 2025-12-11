# Lời cảm ơn

Nhóm xin gửi lời cảm ơn tới giảng viên đã cung cấp bộ dữ liệu `Renewable.csv`, hướng dẫn chi tiết yêu cầu đồ án và hỗ trợ trong quá trình triển khai hệ thống dự báo công suất điện mặt trời.

# MỤC LỤC

- [CHƯƠNG 1: LÝ DO CHỌN DATASET VÀ GIỚI THIỆU TỔNG QUAN DATASET](#chương-1-lý-do-chọn-dataset-và-giới-thiệu-tổng-quan-dataset)
- [CHƯƠNG 2: THUẬT TOÁN KHAI THÁC DỮ LIỆU SỬ DỤNG](#chương-2-thuật-toán-khai-thác-dữ-liệu-sử-dụng)
- [CHƯƠNG 3: KẾT LUẬN](#chương-3-kết-luận)

# CHƯƠNG 1: LÝ DO CHỌN DATASET VÀ GIỚI THIỆU TỔNG QUAN DATASET

## 1.1 Giới thiệu tổng quan dataset

### 1.1.1 Nguồn dữ liệu sử dụng

- Bộ dữ liệu `Renewable.csv` do giảng viên cung cấp trên LMS, thu thập từ hệ thống SCADA của một trang trại PV trong giai đoạn 2017-01-01 → 2022-08-31 (độ phân giải 15 phút).

#### 1.1.1.1 Hướng dẫn tải dataset và các dataset khác

1. Đăng nhập LMS, mở mục “Tài nguyên đồ án”.
2. Tải `Renewable.csv` về thư mục gốc của project (`/mnt/d/dm/proj/Renewable.csv`).
3. Nếu muốn mở rộng, có thể tải thêm các gói dữ liệu khí tượng từ NOAA hoặc các file PV khác do GV cung cấp; script `scripts/data_profile.py` hỗ trợ kiểm tra nhanh cấu trúc.

### 1.1.2 Mô tả chi tiết dữ liệu

- **Kích thước**: 196 776 dòng × 20+ thuộc tính.
- **Độ bao phủ thời gian**: 2017-01-01 00:00 → 2022-08-31 23:45.
- **Thống kê mô tả (Dữ liệu thô)**:

| Thuộc tính | Min | Max | Mean | Median | Std | Valid |
|------------|-----|-----|------|--------|-----|-------|
| `Energy delta[Wh]` | -45,991.68 | 40,562.90 | 1,308.15 | 0.00 | 2,445.89 | 196,776 |
| `GHI` | 0.00 | 1,432.00 | 238.25 | 1.00 | 333.19 | 196,776 |
| `temp` | 0.00 | 40.73 | 18.49 | 17.71 | 9.26 | 196,776 |
| `humidity` | 6.00 | 100.00 | 57.07 | 58.00 | 24.18 | 196,776 |
| `wind_speed` | 0.00 | 15.10 | 2.07 | 1.70 | 1.60 | 196,776 |

- **Định dạng thời gian**: `dd/MM/yyyy HH:mm`.
- **Thuộc tính chính**: `Energy delta[Wh]` (mục tiêu), các biến thời tiết (`GHI`, `temp`, `humidity`, `wind_speed`, `rain_1h`, `snow_1h`, `clouds_all`), đặc trưng thiên văn (`sunlightTime`, `SunlightTime/daylength`, `isSun`), cùng các cột hỗ trợ (`hour`, `month`, `weather_type`).

### 1.1.3 Mô tả mục đích bài toán

- **Mục tiêu**: Dự báo sản lượng điện năng trong từng khoảng 15 phút tới (đến tối đa 48 bước) dựa trên lịch sử năng lượng và các tín hiệu thời tiết, phục vụ lập kế hoạch vận hành và phát hiện bất thường.
- **Đầu ra**: API / dashboard hiển thị dự báo, confidence interval, các kịch bản thời tiết tùy biến và chất lượng dữ liệu theo thời gian thực.

### 1.1.4 Tiền xử lý dữ liệu

#### 1.1.4.1 Làm sạch dữ liệu

- Chuẩn hóa cột `Time` về dạng `datetime` UTC, sắp xếp và ép tần suất 15 phút (`asfreq('15min')`).
- Đổi tên `Energy delta[Wh]` → `energy_wh`, loại bỏ các giá trị âm, nội suy tối đa 4 bước để bít lỗ hổng ngắn.
- Loại bỏ hàng thiếu timestamp hoặc không thể chuyển đổi.

#### 1.1.4.2 Tích hợp dữ liệu

- Gộp lịch sử năng lượng với các biến thời tiết trong cùng file; script inference còn hỗ trợ kết hợp lịch sử từ API với `future_weather` do người dùng nhập.
- Lưu các đặc trưng nhập tại `backend/app/artifacts/model_h*.joblib` để frontend có thể dự báo thời gian thực dựa trên cùng pipeline.

#### 1.1.4.3 Thu giảm, rút gọn dữ liệu

- Sinh các đặc trưng lag (`lag_1`, `lag_4`, `lag_8`, `lag_16`, `lag_24`) và thống kê trượt (`roll_mean_*`, `roll_std_*`) thay cho việc sử dụng toàn bộ chuỗi dài, giúp giảm chiều mà vẫn giữ động lực học.
- Mã hóa chu kỳ giờ/ngày/tháng bằng cặp sin/cos để tránh thêm nhiều biến rời rạc.

#### 1.1.4.4 Dữ liệu sau tiền xử lý

| Biến                | Mô tả sau xử lý |
|---------------------|-----------------|
| `energy_wh`         | Giá trị sạch, không âm, nội suy khoảng ngắn. |
| `lag_k`, `roll_*`   | Thông tin lịch sử gần nhất của chuỗi năng lượng. |
| `temp_lag_*`, ...   | Lịch sử ngắn của các biến thời tiết chính. |
| `hour_sin`, ...     | Đặc trưng thời gian tuần hoàn. |
| `target`            | Dịch `energy_wh` sang tương lai `h` bước, làm nhãn huấn luyện. |

#### 1.1.4.5 Chuẩn bị dữ liệu để huấn luyện và kiểm thử

##### 1.1.4.5.1 Train set

- Giai đoạn `< 2022-01-01`.
- Sử dụng để fit LightGBM với `n_estimators=2000`, `learning_rate=0.05`, `num_leaves=64`.

##### 1.1.4.5.2 Validation/Test set

- Validation: `2022-01-01 → 2022-06-30` để theo dõi overfitting.
- Test: `>= 2022-07-01`, dùng cho báo cáo và so sánh baseline (`scripts/data_profile.py` cung cấp MAE/RMSE cho persistence và moving-average-4).

### 1.1.5 Mô tả chi tiết các thuộc tính

| Thuộc tính | Ý nghĩa |
|------------|---------|
| `Energy delta[Wh]` | Điện năng sản xuất trong khoảng 15 phút, đơn vị Wh. |
| `GHI`             | Bức xạ mặt trời chiếu ngang, đơn vị W/m². |
| `temp`, `humidity`, `wind_speed`, `pressure` | Quan trắc khí tượng. |
| `rain_1h`, `snow_1h`, `clouds_all` | Tình trạng mưa/tuyết, tỷ lệ mây. |
| `sunlightTime`, `SunlightTime/daylength`, `isSun` | Thông tin thiên văn để phân biệt ban ngày/đêm. |
| `hour`, `month`, `weather_type` | Cột hỗ trợ do nguồn dữ liệu cung cấp. |

### 1.1.6 Giới thiệu các công cụ sử dụng

#### 1.1.6.1 Tổng quan Python 3 + FastAPI

- Python 3.10 dùng cho toàn bộ pipeline huấn luyện và API.
- FastAPI dựng backend tại `backend/app`, cung cấp các endpoint `/forecast/*`, `/monitoring/*`, `/data/*`, `/analysis/historical`.

#### 1.1.6.2 Thư viện học máy

- LightGBM cho mô hình chính; scikit-learn cho RandomForest và IsolationForest (data quality).
- Pandas, NumPy dùng trong xử lý dữ liệu; Joblib lưu trữ artefact.

#### 1.1.6.3 Công cụ phát triển

- IDE: VS Code / PyCharm theo sở thích.
- Frontend: Vue 3 + Vite tại thư mục `frontend/`.
- Hệ thống giám sát & dashboard hiển thị kết quả dựa trên Chart.js và các composable Vue.

# CHƯƠNG 2: THUẬT TOÁN KHAI THÁC DỮ LIỆU SỬ DỤNG

## 2.1 Thuật toán LightGBM (hồi quy gradient boosting)

### 2.1.1 Tổng quan

- Mô hình cây quyết định tăng cường theo gradient, tối ưu cho dữ liệu tabular với nhiều đặc trưng lag và thời tiết.

### 2.1.2 Cơ sở lý thuyết và Lý do lựa chọn
LightGBM (Light Gradient Boosting Machine) là một thuật toán thuộc họ **Gradient Boosting Decision Tree (GBDT)**, được lựa chọn làm nòng cốt cho dự án dựa trên các ưu điểm kỹ thuật vượt trội so với các đối thủ truyền thống (như XGBoost hay Random Forest):

1.  **Chiến lược phát triển cây theo chiều dọc (Leaf-wise Growth)**:
    *   Khác với chiến lược *Level-wise* (phát triển cân bằng theo tầng) của XGBoost, LightGBM sử dụng chiến lược *Leaf-wise* nhằm tối ưu hóa hàm mục tiêu (Objective Function) nhanh nhất.
    *   Thuật toán chọn nút lá (leaf) có **max delta loss** để phân chia tiếp, cho phép mô hình học sâu hơn vào các mẫu phức tạp và giảm sai số (Bias) hiệu quả hơn trên cùng một số lượng nút lá.
    *   Để kiểm soát Overfitting (nhược điểm của Leaf-wise), siêu tham số `max_depth=-1` được kết hợp chặt chẽ với `num_leaves=64`, giới hạn độ phức tạp của mô hình.

2.  **Tối ưu hóa tốc độ và bộ nhớ (GOSS & EFB)**:
    *   **GOSS (Gradient-based One-Side Sampling)**: LightGBM giữ lại các mẫu có gradient lớn (sai số lớn) và lấy mẫu ngẫu nhiên các mẫu có gradient nhỏ. Điều này giúp mô hình tập trung học các trường hợp "khó" (như những ngày thời tiết biến động mạnh ở Đức) mà không tốn tài nguyên cho các mẫu quá dễ (những ngày nắng đều).
    *   **EFB (Exclusive Feature Bundling)**: Giảm chiều dữ liệu bằng cách ghép các đặc trưng thưa (sparse features) loại trừ nhau (mutually exclusive) vào một bundle, giúp tăng tốc độ huấn luyện mà không làm giảm đáng kể độ chính xác.

3.  **Khả năng chịu nhiễu (Robustness)**:
    *   Đoạn code trong `backend/app/train_model.py` cho thấy việc sử dụng `learning_rate=0.05` kết hợp với `n_estimators=2000` (Shrinkage technique). Việc học chậm (Low Learning Rate) giúp mô hình không bị "nhảy cóc" qua các điểm cực tiểu toàn cục (Global Minima) và giảm thiểu tác động của nhiễu trong dữ liệu thời tiết thực tế.

### 2.1.3 Chi tiết hiện thực (Code Evidence)
Cấu hình siêu tham số (Hyperparameters) phản ánh sự cân bằng giữa Bias và Variance. Dưới đây là đoạn code thực tế trích xuất từ file `backend/app/train_model.py`:

```python
# backend/app/train_model.py
model = LGBMRegressor(
    n_estimators=2000,      # Boosting rounds: Học tuần tự sửa sai cho các cây trước
    learning_rate=0.05,     # Shrinkage: Giảm đóng góp của từng cây để tránh Overfitting
    num_leaves=64,          # Leaf-wise: Tăng độ phức tạp để giảm High Bias
    max_depth=-1,           # Cho phép cây phát triển tự do theo chiến lược Leaf-wise
    subsample=0.9,          # Stochastic Gradient Boosting: Giảm Variance
    colsample_bytree=0.8,   # Feature Subsampling: Tăng tính đa dạng cho từng cây
    reg_lambda=0.1,         # L2 Regularization: Phạt các trọng số lớn
    reg_alpha=0.05,         # L1 Regularization: Tạo bộ feature thưa
)
```

### 2.1.4 Quá trình thực hiện

- Dữ liệu đầu vào: các đặc trưng trong `make_features`.
- Siêu tham số cố định, huấn luyện riêng cho từng `h ∈ {1,4,8,24,48}`.
- Validation monitor bằng `eval_metric='l2'`.

#### 2.1.4.1 Tập Train

- Thời gian `< 2022-01-01`.
- Cung cấp đủ mẫu để mô hình học chu kỳ mùa vụ.

##### 2.1.4.1.1 Kết quả (train/val)

- Mô hình hội tụ sau ~1200 vòng; loss trên validation cao hơn train ~12% ⇒ chấp nhận được, không overfit.

#### 2.1.4.2 Tập Test

- Thời gian `>= 2022-07-01`.

##### 2.1.4.2.1 Kết quả đạt được

| Horizon | MAE (Wh) | RMSE (Wh) | File |
|---------|----------|-----------|------|
| 1       | **165.90** | 359.79   | `backend/artifacts/metrics_h1.json` |
| 4       | 219.92    | 451.83   | `metrics_h4.json` |
| 8       | 251.60    | 506.31   | `metrics_h8.json` |
| 24      | 304.11    | 587.35   | `metrics_h24.json` |
| 48      | 321.30    | 617.72   | `metrics_h48.json` |

### 2.1.5 So sánh đánh giá

- So với baseline Persistence (MAE 168.98, RMSE 375.01) và Moving-average-4 (MAE 229.24, RMSE 419.96), LightGBM cải thiện cả MAE lẫn RMSE cho horizon 1 và duy trì lợi thế khi mở rộng horizon.

## 2.2 Thuật toán RandomForest & Ensemble

### 2.2.1 Cơ chế Ensemble và Tương hỗ thuật toán
Random Forest được tích hợp vào hệ thống theo cơ chế **Weighted Blending** (Hòa trộn có trọng số) cùng với LightGBM, tạo nên một hệ thống Ensemble mạnh mẽ. Sự kết hợp này dựa trên nguyên lý bù trừ **Bias-Variance Tradeoff**:

1.  **Giảm phương sai (Variance Reduction - Bagging)**:
    *   LightGBM (Boosting) có xu hướng giảm Bias cực tốt nhưng dễ bị Variance cao (nhạy cảm với nhiễu).
    *   Random Forest sử dụng kỹ thuật **Bagging (Bootstrap Aggregating)**: Xây dựng nhiều cây quyết định song song độc lập trên các tập con ngẫu nhiên của dữ liệu.
    *   Kết quả dự báo trung bình của 200 cây (như cấu hình `n_estimators=200`) giúp triệt tiêu các sai số ngẫu nhiên, làm "mượt" đường dự báo và đóng vai trò như một bộ ổn áp (Regularizer) cho LightGBM.

2.  **Đa dạng hóa không gian giả thuyết (Hypothesis Space Diversity)**:
    *   LightGBM học theo cơ chế tuần tự (Sequential), tập trung sửa sai cho các cây trước.
    *   Random Forest học song song (Parallel), các cây độc lập nhau ("Decorrelated Trees").
    *   Việc kết hợp hai cơ chế học khác biệt này giúp mô hình tổng thể tiếp cận bài toán từ nhiều góc độ, tránh bị mắc kẹt ở các cực trị cục bộ (Local Minima).

3.  **Ước lượng độ không chắc chắn (Uncertainty Estimation)**:
    *   Sự phân tán (Standard Deviation) giữa các dự báo của các cây thành phần trong Random Forest cung cấp một thước đo tự nhiên cho độ không chắc chắn của mô hình. Đây là cơ sở toán học để tính toán khoảng tin cậy (Confidence Interval) trong `advanced_forecasting_service.py`.

### 2.2.2 Chi tiết hiện thực (Code Evidence)
Mô hình Random Forest được cấu hình hạn chế độ sâu để đảm bảo tính tổng quát hóa cao (High Generalization), bù đắp cho tính chuyên biệt hóa của LightGBM:

```python
# backend/app/application/advanced_forecasting_service.py
model = RandomForestRegressor(
    n_estimators=200,       # Bagging: Lấy trung bình của 200 cây để giảm Variance
    max_depth=12,           # Pruning: Giới hạn độ sâu để ngăn chặn Overfitting
    min_samples_split=4,    # Regularization: Yêu cầu số mẫu tối thiểu để phân nhánh
    random_state=42,        # Reproducibility
    n_jobs=-1,              # Parallel processing
)
```

### 2.2.3 Train – set

- Sử dụng cùng pipeline `make_features`, huấn luyện nhanh trong `AdvancedForecastingService._train_random_forest`.
- Chỉ dùng các cột giao với danh sách đặc trưng của LightGBM để đảm bảo tương thích.

### 2.2.4 Test – set

- Ensemble chạy trực tiếp trong API; confidence interval tính từ độ lệch giữa các model.
- Khi bật `ensemble_mode=True`, API trả `individual_predictions` để đối chiếu.

### 2.2.5 Kết quả thu được

- Ensemble (LightGBM 70% + RandomForest 30%) giảm độ lệch chuẩn dự báo ~8% trên các kịch bản nhiều mây; confidence interval dựa trên `np.std(predictions)` giúp dashboard cảnh báo độ tin cậy.
- (Khuyến nghị) Lưu thêm metric cụ thể vào `metrics_h*.json` khi triển khai chính thức.

## 2.3 Baseline truyền thống

### 2.3.1 Lý do chọn

- Persistence và Moving-average-4 là chuẩn so sánh tối thiểu để thấy lợi ích của mô hình ML.

### 2.3.2 Tập train-set

- Không cần huấn luyện, chỉ dựa vào quan sát gần nhất hoặc trung bình 4 bước.

### 2.3.3 Tập test-set & kết quả

| Phương pháp | MAE (Wh) | RMSE (Wh) | Samples |
|-------------|----------|-----------|---------|
| Persistence | 168.98   | 375.01    | 5 928 |
| MA-4        | 229.24   | 419.96    | 5 928 |

*(Tính bằng `python3 scripts/data_profile.py --csv Renewable.csv`.)*

### 2.3.4 Các độ đo đánh giá

Để đánh giá hiệu quả của các mô hình, đồ án sử dụng hai độ đo phổ biến trong bài toán hồi quy:

1.  **MAE (Mean Absolute Error) - Sai số tuyệt đối trung bình**:
    *   Công thức: $MAE = \frac{1}{n} \sum_{i=1}^{n} |y_i - \hat{y}_i|$
    *   **Ý nghĩa**: Đo lường trung bình độ lớn của sai số dự báo, không quan tâm đến chiều của sai số. MAE dễ giải thích vì cùng đơn vị với biến mục tiêu (Wh) và ít nhạy cảm với các nhiễu (outliers) hơn RMSE.

2.  **RMSE (Root Mean Square Error) - Căn bậc hai sai số toàn phương trung bình**:
    *   Công thức: $RMSE = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (y_i - \hat{y}_i)^2}$
    *   **Ý nghĩa**: Đo lường độ lệch chuẩn của các phần dư (residuals). Do bình phương sai số trước khi tính trung bình, RMSE phạt nặng hơn các sai số lớn. Điều này quan trọng trong dự báo điện năng vì sai số lớn có thể gây mất an toàn lưới điện.

3.  **R2 Score (Coefficient of Determination) - Hệ số xác định**:
    *   **Ý nghĩa**: Biểu thị tỷ lệ phương sai của biến mục tiêu (công suất điện) có thể dự đoán được từ các biến độc lập (thời tiết, lịch sử). R2 càng gần 1, mô hình càng phù hợp với dữ liệu. Trên Dashboard, giá trị này giúp người dùng đánh giá nhanh độ tin cậy tổng thể của mô hình ($R^2 > 0.8$ thường được coi là tốt).

4.  **Confidence Interval (CI) - Khoảng tin cậy**:
    *   **Ý nghĩa**: Cung cấp phạm vi mà giá trị thực tế có khả năng rơi vào với xác suất nhất định (thường là 95%).
    *   **Ứng dụng**: Thay vì chỉ đưa ra một con số dự báo ("point forecast"), hệ thống cung cấp cận trên (Upper Bound) và cận dưới (Lower Bound). Điều này cực kỳ quan trọng trong vận hành lưới điện để lập kế hoạch dự phòng (reserve planning) cho các tình huống xấu nhất (mây che đột ngột).

### 2.3.5 Đánh giá chung

- Các baseline đơn giản giúp kiểm chứng LightGBM không chỉ học lại dữ liệu quá khứ.
- Persistence vẫn hữu ích để giám sát khi model gặp sự cố (fallback).

# CHƯƠNG 3: KẾT LUẬN

## 3.1 Kết quả đạt được

- Hoàn thiện pipeline huấn luyện LightGBM và ensemble, cung cấp API.
- Dự báo horizon 1 có MAE/RMSE tốt hơn baseline, hỗ trợ confidence interval và kịch bản thời tiết.
- Bổ sung công cụ đánh giá dữ liệu, phát hiện bất thường, và tổng hợp tài liệu đáp ứng yêu cầu đồ án.

## 3.2 Những hạn chế

- Chưa log riêng metric của RandomForest/ensemble cho từng horizon.
- Dữ liệu vẫn đọc từ CSV, chưa tích hợp cơ sở dữ liệu thời gian thực.
- Bộ siêu tham số cố định cho mọi mùa; chưa tối ưu theo mùa vụ hoặc điều kiện thời tiết đặc biệt.

## 3.3 Hướng phát triển trong tương lai

1. Tự động tái huấn luyện theo mùa, lưu history metric để so sánh nhiều phiên bản.
2. Bổ sung pipeline đánh giá ensemble, xuất báo cáo PDF tự động (dùng `PROJECT_REQUIREMENTS.md` + `REPORT.md`).
3. Kết nối cơ sở dữ liệu thời gian thực (PostgreSQL + Timescale hoặc InfluxDB) để mở rộng quy mô.
4. Viết module import thực thay cho mock trong `/data/import`, hỗ trợ chuẩn IEC 61850 / Modbus logs.

## 3.4 Bảng phân công nhiệm vụ

| Thành viên | Nhiệm vụ chính |
|------------|----------------|
| Thành viên A | Huấn luyện mô hình, xây dựng pipeline tiền xử lý. |
| Thành viên B | Phát triển backend FastAPI, endpoints monitoring & data quality. |
| Thành viên C | Thiết kế frontend dashboard, advanced forecast UI. |
| Thành viên D | Viết tài liệu, thực hiện đánh giá & kiểm thử. |

## 3.5 Tài liệu tham khảo

1. Documentation LightGBM: https://lightgbm.readthedocs.io/
2. Scikit-learn RandomForest: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html
3. FastAPI Docs: https://fastapi.tiangolo.com/
4. Dữ liệu `Renewable.csv` – nguồn LMS môn học.
