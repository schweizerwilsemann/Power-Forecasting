# ALGORITHM DEEP DIVE: The "Cooking" of the Dataset

Tài liệu này giải thích chi tiết từng bước (step-by-step) cách hai thuật toán **LightGBM** và **Random Forest** "tiêu hóa" (cook) bộ dữ liệu năng lượng mặt trời (`Renewable.csv`) để đưa ra dự báo cuối cùng.

---

## 1. Giai đoạn sơ chế (Data "Marination") - Feature Engineering

Trước khi bất kỳ thuật toán nào học, dữ liệu thô (Raw Data) phải được biến đổi để làm nổi bật các mẫu hình (patterns). Đây là bước "tẩm ướp" quan trọng nhất.

### Bước 1.1: Tạo đặc trưng độ trễ (Lag Features)
Hệ thống không chỉ nhìn vào hiện tại, mà còn nhìn lại quá khứ để tìm quán tính.
*   **Input**: Sản lượng điện lúc `t`.
*   **Action**: Tạo thêm các cột `energy_lag_1` (cách đây 15p), `energy_lag_96` (cách đây 1 ngày), `energy_lag_672` (cách đây 1 tuần).
*   **Ý nghĩa**: Giúp mô hình học được quy luật: "Hôm qua giờ này nắng to 1000Wh, hôm nay trời cũng trong xanh thì khả năng cao cũng tầm 1000Wh".

### Bước 1.2: Mã hóa thời gian (Cyclical Encoding)
Máy học không hiểu "23 giờ" gần với "0 giờ". Nó nghĩ 23 rất xa 0.
*   **Action**: Biến đổi giờ (0-23) và tháng (1-12) thành tọa độ hình tròn `(sin, cos)`.
*   **Ý nghĩa**: Giúp mô hình hiểu rằng 23h đêm và 1h sáng là "hàng xóm" của nhau (đều tối thui).

---

## 2. LightGBM - "Bếp trưởng khó tính" (The Executive Chef)

LightGBM chịu trách nhiệm chính (chiếm 70% quyết định) vì nó học rất nhanh và soi rất kỹ các chi tiết nhỏ.

### Implicit Step-by-Step Learning:
1.  **Vòng 1 (Round 1)**: LightGBM đưa ra dự đoán sơ khởi (ví dụ: trung bình toàn bộ dữ liệu là 1300Wh).
    *   *Kết quả*: Sai bét. Thực tế là 0Wh (đêm), dự báo 1300Wh. Sai số (Residual) = -1300.
2.  **Vòng 2 (Round 2) - Học từ sai lầm**: Cây thứ 2 **không** học dự báo điện năng nữa, mà nó học cách **dự báo sai số -1300**.
    *   Nó tìm ra quy luật: "À, nếu `GHI=0` (đêm), thì sai số phải là -1300".
    *   *Correction*: Dự báo mới = 1300 + (-1300) = 0.
3.  **Vòng n (Gradient Boosting)**: Hàng nghìn cây tiếp theo cứ thế soi vào những điểm dữ liệu mà các cây trước dự báo sai (ví dụ: những ngày mây mù thất thường).
    *   **Kỹ thuật GOSS**: Nó vứt bớt những mẫu "dễ" (đã dự báo đúng) để tập trung toàn lực vào những mẫu "khó".
    *   **Chiến lược Leaf-wise**: Nó phát triển cành lá vô tội vạ vào chiều sâu để giảm thiểu sai số tối đa (Greedy algorithm).

---

## 3. Random Forest - "Hội đồng giám khảo" (The Committee)

Random Forest đóng vai trò là người kiểm duyệt (chiếm 30% quyết định) để đảm bảo LightGBM không bị "học vẹt" (Overfitting).

### Implicit Step-by-Step Learning:
1.  **Phân chia dữ liệu (Bagging)**: Nó nhân bản dataset thành 200 bản khác nhau bằng cách lấy mẫu ngẫu nhiên có hoàn lại (bootstrapping). Có bản thiếu ngày này, có bản lặp lại ngày kia.
2.  **Học song song (Parallel Training)**: 200 cây quyết định được "trồng" độc lập cùng lúc.
    *   *Đặc biệt*: Mỗi cây khi phân nhánh chỉ được nhìn thấy một nhóm ngẫu nhiên các đặc trưng (ví dụ: chỉ nhìn thấy Gió và Giờ, không thấy Nắng).
    *   **Mục đích**: Buộc mỗi cây phải "thông minh" theo cách riêng, không được phụ thuộc vào chỉ một đặc trưng mạnh (như GHI).
3.  **Hội ý (Voting/Averaging)**:
    *   Cây 1 bảo: 2000 Wh.
    *   Cây 2 bảo: 2100 Wh.
    *   Cây 3 (bị khuất nẻo) bảo: 1500 Wh.
    *   **Final Output**: Trung bình cộng = 1866 Wh.
    *   *Effect*: Những dự báo quá lố (như 3000 Wh hay 500 Wh) sẽ bị số đông kéo về mức trung bình hợp lý.

---

## 4. Pipeline Hợp nhất (The Plate Presentation)

Đây là cách code `advanced_forecasting_service.py` dọn món ăn ra bàn:

1.  **Input**: Dữ liệu thời tiết tương lai (Scenario).
2.  **Chef (LightGBM) nấu**: Ra món chính với hương vị sắc sảo (bias thấp, dự báo bám sát thực tế).
    *   Ví dụ: 2500 Wh.
3.  **Committee (Random Forest) nếm**: Ra đánh giá tổng quan, an toàn (variance thấp).
    *   Ví dụ: 2300 Wh.
4.  **Plating (Weighted Blending)**:
    *   Công thức: `0.7 * 2500 + 0.3 * 2300 = 1750 + 690 = 2440 Wh`.
5.  **Garnish (Post-processing)**:
    *   *Night Mask*: "Ủa khoan, 7h tối rồi". -> Ép về 0 Wh.
    *   *Confidence Interval*: "Món này ngon nhưng có thể gia giảm mặn nhạt ±10%". -> Vẽ thêm khoảng tin cậy.

-> **Món ăn cuối cùng**: Dữ liệu dự báo chính xác, mượt mà và hợp lý về mặt vật lý.
