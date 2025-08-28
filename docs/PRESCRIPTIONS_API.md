## API Đơn thuốc (Prescription)

### Mô tả các field của Prescription (theo `PrescriptionSerializer`)

- **id**: UUID của đơn thuốc.
- **prescription_number**: Mã số đơn thuốc dạng `DTYYYYMMDDxxxxxx`.
- **patient**: UUID bệnh nhân.
- **patient_name**: Họ tên bệnh nhân.
- **patient_code**: Mã hồ sơ bệnh nhân.
- **patient_phone**: SĐT bệnh nhân.
- **doctor**: UUID bác sĩ kê đơn (liên kết `appointments.DoctorProfile`).
- **doctor_name**: Họ tên bác sĩ.
- **doctor_specialization**: Chuyên khoa của bác sĩ.
- **appointment**: UUID lịch hẹn liên quan (có thể null).
- **prescription_date**: Thời điểm tạo đơn thuốc.
- **prescription_type**: Loại đơn thuốc. Giá trị:
  - `OUTPATIENT`: Ngoại trú
  - `INPATIENT`: Nội trú
  - `EMERGENCY`: Cấp cứu
  - `DISCHARGE`: Ra viện
- **prescription_type_display**: Nhãn hiển thị của loại đơn.
- **status**: Trạng thái đơn thuốc. Giá trị:
  - `DRAFT`: Nháp
  - `ACTIVE`: Có hiệu lực
  - `PARTIALLY_DISPENSED`: Cấp thuốc một phần
  - `FULLY_DISPENSED`: Đã cấp thuốc đầy đủ
  - `CANCELLED`: Đã hủy
  - `EXPIRED`: Hết hạn
- **status_display**: Nhãn hiển thị của trạng thái.
- **diagnosis**: Chẩn đoán.
- **notes**: Ghi chú của bác sĩ.
- **special_instructions**: Hướng dẫn đặc biệt.
- **valid_from**: Có hiệu lực từ thời điểm.
- **valid_until**: Hết hiệu lực tại thời điểm.
- **is_valid**: Boolean. Chỉ true khi `status='ACTIVE'` và thời gian hiện tại nằm trong [`valid_from`, `valid_until`].
- **days_until_expiry**: Số ngày còn lại trước khi hết hạn (0 nếu đã quá hạn).
- **total_amount**: Tổng tiền thuốc của đơn (VNĐ).
- **insurance_covered_amount**: Số tiền BHYT chi trả (VNĐ).
- **patient_payment_amount**: Số tiền bệnh nhân phải trả (VNĐ).
- **items**: Danh sách chi tiết thuốc trong đơn, mỗi phần tử có các field (theo `PrescriptionItemSerializer`):
  - `id`: UUID của chi tiết đơn.
  - `prescription`: UUID đơn thuốc (read-only trong response).
  - `drug`: UUID thuốc.
  - `drug_name`: Tên thuốc.
  - `drug_code`: Mã thuốc.
  - `drug_unit`: Đơn vị hiển thị của thuốc.
  - `quantity`: Số lượng kê.
  - `dosage_per_time`: Liều dùng mỗi lần (ví dụ: "1 viên").
  - `frequency`: Tần suất dùng (giá trị enum, xem `FREQUENCY_CHOICES`).
  - `frequency_display`: Nhãn hiển thị của tần suất dùng.
  - `route`: Đường dùng thuốc (enum, xem `ROUTE_CHOICES`).
  - `route_display`: Nhãn hiển thị đường dùng.
  - `duration_days`: Số ngày sử dụng.
  - `instructions`: Hướng dẫn chi tiết.
  - `special_notes`: Ghi chú đặc biệt.
  - `unit_price`: Đơn giá tại thời điểm kê đơn.
  - `total_price`: Thành tiền.
  - `quantity_dispensed`: Số lượng đã cấp.
  - `quantity_remaining`: Số lượng còn lại chưa cấp.
  - `is_fully_dispensed`: Đã cấp đủ hay chưa (boolean).
  - `dispensing_progress`: Tiến độ cấp thuốc (%).
  - `is_substitutable`: Có thể thay thế thuốc tương đương (boolean).
  - `created_at`: Thời điểm tạo chi tiết đơn.
- **items_count**: Tổng số dòng thuốc trong đơn.
- **created_by**: UUID người tạo đơn.
- **created_by_name**: Họ tên người tạo đơn.
- **created_at**: Thời điểm tạo đơn.
- **updated_at**: Thời điểm cập nhật gần nhất.

Ghi chú liên quan tới cấp thuốc (dispensing):
- Khi có bản ghi cấp thuốc (`PrescriptionDispensing`) với `status='DISPENSED'`, hệ thống tự cập nhật `quantity_dispensed` cho từng `item` và tự động cập nhật `status` của đơn là `PARTIALLY_DISPENSED` hoặc `FULLY_DISPENSED` tùy tiến độ.
- Trước khi cấp thuốc, cần có thanh toán `PAID` (từ app payments) và đơn còn hiệu lực (`is_valid=True`).

---

### Endpoint: Kích hoạt đơn thuốc

- Method: `POST`
- Path: `/api/prescriptions/{id}/activate/`
- Quy tắc:
  - Chỉ kích hoạt được khi đơn đang ở trạng thái `DRAFT`. Nếu không, trả 400.
  - Sau khi kích hoạt, `status` chuyển thành `ACTIVE`.
- Response: 200 với toàn bộ object `Prescription` (theo `PrescriptionSerializer`).

Ví dụ response 200:
```json
{
  "id": "8a3b2b6f-1a2b-4dcd-9c6e-4d38f2a6a9b1",
  "prescription_number": "DT20250101000001",
  "patient": "3e2cb3bc-6e2a-470f-9d38-1f38d6e1a111",
  "patient_name": "Nguyễn Văn A",
  "patient_code": "BN000123",
  "patient_phone": "0900000000",
  "doctor": "5f8c9e7a-1b2c-4d3e-8f9a-0b1c2d3e4f5a",
  "doctor_name": "BS. Trần B",
  "doctor_specialization": "Nội tổng quát",
  "appointment": null,
  "prescription_date": "2025-01-01T08:00:00Z",
  "prescription_type": "OUTPATIENT",
  "prescription_type_display": "Ngoại trú",
  "status": "ACTIVE",
  "status_display": "Có hiệu lực",
  "diagnosis": "Viêm họng cấp",
  "notes": "",
  "special_instructions": "Uống sau ăn",
  "valid_from": "2025-01-01T08:00:00Z",
  "valid_until": "2025-01-31T08:00:00Z",
  "is_valid": true,
  "days_until_expiry": 20,
  "total_amount": 150000,
  "insurance_covered_amount": 0,
  "patient_payment_amount": 150000,
  "items": [
    {
      "id": "2b3c4d5e-6f70-4a8b-9c0d-1e2f3a4b5c6d",
      "prescription": "8a3b2b6f-1a2b-4dcd-9c6e-4d38f2a6a9b1",
      "drug": "9c0d1e2f-3a4b-5c6d-7e8f-9012a3b4c5d6",
      "drug_name": "Paracetamol 500mg",
      "drug_code": "PARA500",
      "drug_unit": "Viên",
      "quantity": 10,
      "dosage_per_time": "1 viên",
      "frequency": "3X_DAILY",
      "frequency_display": "3 lần/ngày",
      "route": "ORAL",
      "route_display": "Uống",
      "duration_days": 5,
      "instructions": "",
      "special_notes": "",
      "unit_price": 5000,
      "total_price": 50000,
      "quantity_dispensed": 0,
      "quantity_remaining": 10,
      "is_fully_dispensed": false,
      "dispensing_progress": 0.0,
      "is_substitutable": true,
      "created_at": "2025-01-01T08:00:00Z"
    }
  ],
  "items_count": 1,
  "created_by": "11111111-2222-3333-4444-555555555555",
  "created_by_name": "Điều phối viên",
  "created_at": "2025-01-01T08:00:00Z",
  "updated_at": "2025-01-01T08:10:00Z"
}
```

Response lỗi 400 (đơn không ở trạng thái DRAFT):
```json
{
  "error": "Chỉ có thể kích hoạt đơn thuốc ở trạng thái nháp"
}
```

---

### Endpoint: Hủy đơn thuốc

- Method: `POST`
- Path: `/api/prescriptions/{id}/cancel/`
- Request body:
```json
{
  "reason": "Bệnh nhân đổi phác đồ"
}
```
- Quy tắc:
  - Không thể hủy nếu đơn ở `FULLY_DISPENSED` hoặc đã `CANCELLED`.
  - Khi hủy, `status` chuyển thành `CANCELLED` và nội dung `reason` sẽ được nối thêm vào trường `notes` (ghi chú) của đơn.
- Response: 200 với toàn bộ object `Prescription` (theo `PrescriptionSerializer`).

Ví dụ response lỗi 400 (đã cấp đủ hoặc đã hủy):
```json
{
  "error": "Không thể hủy đơn thuốc đã cấp đầy đủ hoặc đã hủy"
}
```

Ví dụ response 200 (đã hủy):
```json
{
  "id": "8a3b2b6f-1a2b-4dcd-9c6e-4d38f2a6a9b1",
  "status": "CANCELLED",
  "status_display": "Đã hủy",
  "notes": "\n\nĐã hủy: Bệnh nhân đổi phác đồ",
  "...": "các field khác giống như response của Prescription ở trên"
}
```

---

### Ghi chú triển khai

- Khi tạo mới đơn bằng API `POST /api/prescriptions/`, hệ thống hiện tại tự gán `status='ACTIVE'` trong `perform_create`. Nếu cần quy trình duyệt theo `DRAFT -> ACTIVE`, có thể thay đổi logic tạo để mặc định DRAFT và dùng endpoint activate để chuyển sang ACTIVE.


