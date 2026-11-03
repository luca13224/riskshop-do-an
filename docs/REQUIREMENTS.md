# REQUIREMENTS

> Cập nhật: 2026-11-03 · Trạng thái: **Bản 1, viết lại từ sản phẩm đã xây** (DEMO_SCRIPT "Phạm vi MVP", ADR-003 → ADR-011, mã nguồn `backend/app/modules`).
> Cột **Mức**: MVP / Recommended / Advanced. Cột **Kiểm chứng**: test tự động (`backend/tests`), thực nghiệm (`docs/TEST_PLAN.md`) hoặc demo (`docs/DEMO_SCRIPT.md`).
> Mã mục tiêu O1–O9 ở `docs/PROJECT_OVERVIEW.md` mục 3. Mã vấn đề P1–P5 ở cùng file, mục 2.

## 1. Stakeholders và tác nhân
| Stakeholder | Tác nhân trong hệ thống | Quan tâm chính |
|---|---|---|
| Người mua hợp lệ | Customer | Mua nhanh, không bị chặn nhầm; bị chặn thì khiếu nại được |
| Người bán / sàn | (gián tiếp, qua Reports) | Giảm thất thoát voucher và đơn COD bị bùng |
| Nhân viên rủi ro | Analyst | Hàng đợi case, giải thích quyết định rõ ràng |
| Quản lý rủi ro | Risk Manager | Sửa luật, kết luận khiếu nại, khóa / gỡ khóa, xem liên hệ đầy đủ |
| Quản trị hệ thống | Admin | Mọi quyền của Risk Manager, Attack Lab, quản lý vận hành |
| Hệ thống nền | Worker | Mở / gom case, chạy kịch bản Attack Lab |

## 2. Functional Requirements

### 2.1 Shop (khách hàng)
| Mã | Yêu cầu | Mức | Kiểm chứng |
|---|---|---|---|
| FR-01 | Đăng ký, đăng nhập, đăng xuất; phiên lưu trong CSDL; ghi nhận thiết bị và IP mỗi lần đăng nhập | MVP | `test_auth.py` |
| FR-02 | Xem danh sách sản phẩm: tìm kiếm, lọc danh mục, lọc khoảng giá, sắp xếp, phân trang; xem chi tiết sản phẩm | MVP | `test_catalog.py` |
| FR-03 | Giỏ hàng: thêm, sửa số lượng, xóa | MVP | `test_cart.py` |
| FR-04 | Áp / gỡ voucher; hệ thống tự gỡ voucher khi giỏ không còn đủ điều kiện | MVP | `test_cart.py` |
| FR-05 | Túi voucher: tài khoản mới được cấp sẵn NGUOIMOI; hiển thị trạng thái dùng được / đã dùng / bị khóa / không đủ điều kiện; áp bằng một chạm | Recommended | `test_trust.py` |
| FR-06 | Checkout: nhập địa chỉ nhận, chọn COD hoặc trả trước; chống đặt trùng (idempotency); khóa tồn kho và lượt dùng voucher chống race condition | MVP | `test_order.py` |
| FR-07 | Lịch sử đơn, chi tiết đơn, có trạng thái "Chờ xác minh" khi đơn bị giữ | MVP | `test_order.py`, demo cảnh 5 |
| FR-08 | Khiếu nại một quyết định hạn chế của chính mình trong 30 ngày; xem kết quả và câu trả lời | MVP | `test_appeals.py` |

### 2.2 Risk Engine
| Mã | Yêu cầu | Mức | Kiểm chứng |
|---|---|---|---|
| FR-10 | Chấm điểm đồng bộ tại 3 điểm kiểm soát: áp voucher, lấy phương thức thanh toán, đặt hàng | MVP | `test_risk_scenarios.py` |
| FR-11 | Tính đặc trưng F01–F17 từ dữ liệu các module khác ở chế độ chỉ đọc (ADR-004) | MVP | `test_risk_rules.py` |
| FR-12 | Luật là dữ liệu có phiên bản (R01–R16), 3 kiểu: ngưỡng đếm, ngưỡng tỉ lệ, kết hợp | MVP | `test_risk_rules.py` |
| FR-13 | Điểm theo từng chính sách (voucher, COD) + ma trận quyết định ALLOW / STEP_UP / REVIEW / BLOCK; REVIEW, BLOCK bắt buộc có luật mạnh | MVP | `test_risk_rules.py` |
| FR-14 | Điểm tin cậy tài khoản = 100 − tổng điểm luật đã khớp; cắt quyền lợi theo bậc (khóa voucher theo `min_trust`, mở case, tắt COD) (ADR-009) | Recommended | `test_trust.py` |
| FR-15 | Lưu mỗi quyết định kèm luật đã khớp, giá trị đặc trưng, phiên bản luật; bản ghi không bị sửa sau khi tạo | MVP | `test_risk_rules.py` |
| FR-16 | Khi Risk Engine lỗi: fail-open cho voucher, fail-closed cho COD từ 3 triệu (yêu cầu trả trước); mọi lần lỗi đều ghi lại | MVP | `test_risk_rules.py` |
| FR-17 | Tự khóa quyền mua 24 giờ khi bị từ chối đặt hàng lần thứ 4 trong 24 giờ; tái phạm trong 30 ngày thì khóa vô thời hạn (ADR-010) | Recommended | `test_restrictions.py` |
| FR-18 | Truy vết tài khoản mới liên kết (thiết bị, SĐT nhận, địa chỉ; không tính IP) với tài khoản đang bị khóa vô thời hạn; khóa thanh toán 30 ngày, tái phạm 60 ngày (ADR-011) | Recommended | `test_linked_ban.py` |
| FR-19 | Miễn trừ hành động của một chính sách trong 30 ngày khi khiếu nại được chấp nhận; luật vẫn chạy và vẫn ghi đã khớp (ADR-006) | MVP | `test_appeals.py` |

### 2.3 Risk Console (nhân viên)
| Mã | Yêu cầu | Mức | Kiểm chứng |
|---|---|---|---|
| FR-20 | Dashboard tổng quan: tình hình shop, rủi ro, việc cần xử lý | MVP | `test_dashboard.py`, demo cảnh 7 |
| FR-21 | Live Monitor: dòng quyết định gần nhất, lọc theo kết quả | MVP | demo cảnh 1, 2 |
| FR-22 | Worker tự mở case và gom theo cụm tài khoản liên quan | MVP | `test_cases.py` |
| FR-23 | Case Queue, Case Detail: nhận xử lý, xem phân rã điểm, sổ trừ điểm tin cậy, timeline; kết luận bắt buộc ghi lý do; duyệt / từ chối đơn đang giữ | MVP | `test_cases.py` |
| FR-24 | Đồ thị liên kết tài khoản 2 bước trong 30 ngày, đánh dấu tài khoản đang bị khóa | Advanced | `test_link_graph.py`, demo cảnh 3 |
| FR-25 | Khóa thủ công / gỡ khóa tài khoản, bắt buộc lý do (Risk Manager, Admin) | Recommended | `test_restrictions.py` |
| FR-26 | Xử lý khiếu nại: Analyst xem; Risk Manager / Admin kết luận (bốn mắt), bắt buộc trả lời khách | MVP | `test_appeals.py` |
| FR-27 | Trang luật: xem luật dạng câu dễ đọc, số lần khớp 7 ngày, sửa con số tạo phiên bản mới, xem lịch sử phiên bản | MVP | `test_rules_admin.py` |
| FR-28 | Quản lý đơn: lọc trạng thái, tìm mã đơn, đếm theo trạng thái, giả lập giao hàng | MVP | `test_order.py` |
| FR-29 | Reports / KPI: phân bố quyết định, độ trễ p50/p95/p99, case, hiệu quả từng luật, tác động nghiệp vụ ước tính (ghi rõ giả định) | MVP | `test_reports.py` |
| FR-30 | Audit Log: xem nhật ký thao tác của nhân viên (Risk Manager, Admin) | MVP | `test_reports.py` |
| FR-31 | Attack Lab: chạy kịch bản tấn công / hợp lệ dễ nhầm qua API thật, so sánh kỳ vọng và thực tế; chỉ khi `DEMO_MODE` | MVP | `test_lab.py`, demo cảnh 2, 4 |

### 2.4 Thực nghiệm
| Mã | Yêu cầu | Mức | Kiểm chứng |
|---|---|---|---|
| FR-40 | Simulator sinh persona hợp lệ, hard negative, lạm dụng đã biết và biến thể chưa biết; gọi đúng API của shop; nhãn thật lưu riêng, Risk Engine không đọc | MVP | `test_simulator.py` |
| FR-41 | Tách tập dev / test, tái lập theo seed, ghi dấu vân tay bộ luật; báo cáo precision, recall, FPR kèm khoảng tin cậy Wilson | MVP | `docs/experiments/` |
| FR-42 | Tắt từng luật (`--disable-rule`) hoặc tắt lớp Trust (`--no-trust`) để so sánh trên cùng dân số | Recommended | TEST_PLAN 3c, 3d |

## 3. Non-functional Requirements
| Mã | Nhóm | Yêu cầu | Mục tiêu liên quan | Trạng thái |
|---|---|---|---|---|
| NFR-01 | Hiệu năng | p95 thời gian chấm điểm ≤ 50 ms trên máy phát triển; đo thêm p95 request đặt hàng ở 1 / 10 / 50 người đồng thời | O5 | Chấm điểm đã đo 7,8–11,5 ms; đo đồng thời **[CẦN ĐO]** |
| NFR-02 | Giải thích được | 100% quyết định khác ALLOW có luật đã khớp, giá trị thực tế, phiên bản luật | O6 | Có test; script đối chiếu toàn bộ **[CẦN ĐO]** |
| NFR-03 | Truy vết | Mọi thao tác nhân viên làm đổi trạng thái (kết luận case, khiếu nại, sửa luật, khóa / gỡ khóa, xem liên hệ) đều ghi audit | O6 | Có test |
| NFR-04 | Phân quyền | RBAC 4 vai trò; quyền tối thiểu: Analyst không sửa luật, không gỡ khóa, không kết luận khiếu nại | — | Có test |
| NFR-05 | Bảo mật đăng nhập | Mật khẩu băm; phiên trong CSDL, cookie HttpOnly; giới hạn sai 5 lần / tài khoản, 20 lần / IP trong 15 phút | — | Có test |
| NFR-06 | Quyền riêng tư | Che email trên Console; xem liên hệ đầy đủ phải ghi lý do và để lại audit; IP băm bằng HMAC; dữ liệu demo đều là giả | — | Có test |
| NFR-07 | Công bằng | Không khóa chỉ vì chung IP; khóa liên kết cần ≥ 2 điểm chung hoặc 1 điểm kèm spam; lệnh khóa đã gỡ không tính là tiền sử | O2, O3 | Có test |
| NFR-08 | Khả năng phục hồi | Lỗi Risk Engine không làm hỏng checkout (FR-16) | — | Có test |
| NFR-09 | Toàn vẹn dữ liệu | Giao dịch ACID cho đơn, tồn kho, lượt dùng voucher; ràng buộc UNIQUE chống trùng | — | Có test |
| NFR-10 | Cấu hình được | Luật và ngưỡng quyết định là dữ liệu, sửa qua Console, không cần sửa code | — | Có test |
| NFR-11 | Khả dụng | Shop dùng được ở 375 px và 1440 px, dùng được bằng bàn phím, có chế độ giảm chuyển động | — | Kiểm thủ công (TEST_PLAN 3b); 768 px chưa kiểm |
| NFR-12 | Khả năng kiểm thử | Toàn bộ test tự động chạy trên CSDL riêng, qua migration thật | — | 190 test qua (2026-10-31) |

## 4. Business Rules
| Mã | Quy tắc | Nguồn |
|---|---|---|
| BR-01 | NGUOIMOI: −50.000đ, đơn từ 200.000đ, chỉ tài khoản tạo trong 30 ngày gần nhất, cần điểm tin cậy ≥ 50 | `promotion/seed.py`, `promotion/service.py`, ADR-009 |
| BR-02 | GIAM10: −10%, tối đa 100.000đ, đơn từ 500.000đ, cần điểm tin cậy ≥ 70 | `promotion/seed.py`, ADR-009 |
| BR-03 | Bậc tin cậy: ≥ 70 bình thường · 50–69 theo dõi · 30–49 hạn chế · < 30 mở case khi đặt hàng · ≤ 0 tắt COD | ADR-009 |
| BR-04 | REVIEW / BLOCK chỉ được ra khi có ít nhất một luật mạnh | RULES_V0 |
| BR-05 | Risk Engine lỗi: voucher fail-open; COD từ 3.000.000đ fail-closed | RULES_V0 |
| BR-06 | Lần đặt hàng bị từ chối thứ 4 trong 24 giờ → khóa mua 24 giờ; tái phạm trong 30 ngày (lệnh trước chưa được gỡ) → khóa vô thời hạn | ADR-010 |
| BR-07 | Tài khoản mới chung ≥ 2 điểm (thiết bị, SĐT nhận, địa chỉ) với tài khoản đang bị khóa vô thời hạn, hoặc chung 1 điểm và spam mã người mới → khóa thanh toán 30 ngày, tái phạm 60 ngày; chung 1 điểm không spam → chỉ trừ điểm và mở case | ADR-011 |
| BR-08 | Khiếu nại trong 30 ngày; mỗi chính sách chỉ một khiếu nại đang mở; chấp nhận → miễn trừ chính sách đó 30 ngày, duyệt đơn đang giữ, gỡ khóa nếu quyết định có khóa | ADR-006, ADR-010 |
| BR-09 | Kết luận case, khiếu nại, gỡ khóa, xem liên hệ đầy đủ: bắt buộc ghi lý do | ADR-006, ADR-010 |
| BR-10 | Sửa luật tạo phiên bản mới; quyết định cũ giữ nguyên phiên bản đã dùng | RULES_V0 |

## 5. Use Cases
| Mã | Tác nhân | Use case | FR |
|---|---|---|---|
| UC-01 | Customer | Mua hàng có áp voucher | FR-02 → FR-07, FR-10 |
| UC-02 | Customer | Khiếu nại quyết định hạn chế | FR-08, FR-19 |
| UC-03 | Worker | Mở / gom case tự động | FR-22 |
| UC-04 | Analyst | Xử lý case (nhận, xem lý do, kết luận, duyệt / từ chối đơn) | FR-23, FR-24 |
| UC-05 | Risk Manager | Kết luận khiếu nại | FR-26 |
| UC-06 | Risk Manager | Sửa ngưỡng luật | FR-27 |
| UC-07 | Risk Manager | Khóa / gỡ khóa tài khoản | FR-25 |
| UC-08 | Admin | Chạy kịch bản Attack Lab | FR-31 |
| UC-09 | Risk Manager | Xem báo cáo KPI và audit log | FR-29, FR-30 |

Biểu đồ use case: vẽ bằng PlantUML hoặc draw.io khi viết Chương 2.2 (Archify không có kiểu use case UML).
