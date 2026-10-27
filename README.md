# 3-Band Digital Audio Equalizer on Arty Z7-20 FPGA

Dự án triển khai bộ lọc cân bằng âm thanh số (Digital Audio Equalizer) 3 băng tần sử dụng kiến trúc bộ lọc FIR nối tiếp trên bo mạch phát triển FPGA Digilent Arty Z7-20 (Zynq-7000 SoC).

## 🚀 Tính năng chính
- **Kiến trúc Serial FIR:** Sử dụng chung một khối MAC (Multiply-Accumulate) với số bậc N=255, giúp tiết kiệm tối đa tài nguyên Logic Cells trên FPGA.
- **Tối ưu Pipeline phần cứng:** Tận dụng các tầng thanh ghi trong khối DSP48 (`MREG`, `PREG`) nhằm bẻ gãy đường logic tổ hợp dài, giúp mạch đạt tiêu chuẩn Timing Closure (WNS > 0) tại chu kỳ xung nhịp tối ưu.
- **Xử lý số học cố định (Fixed-Point):** Sử dụng định dạng Q1.15 kết hợp cơ chế bão hòa biên độ (Saturation Logic) chống tràn dữ liệu.
- 
## 🛠️ Môi trường phát triển
- **Công cụ thiết kế:** Xilinx/AMD Vivado 2024.2
- **Thiết bị mục tiêu (Target Device):** `xc7z020clg400-1` (Arty Z7-20)
- **Ngôn ngữ:** Verilog HDL

## 📂 Cấu trúc thư mục dự án
```text
├── src/
│   ├── arty_top.v           # Module cấp cao (Top-level), quản lý xung nhịp, reset và LED // nhắm khắc phục tính trạng đầu vào khối xử lý yêu cầu 84 chân nhiều hơn chân board.
│   └── filter_control.v     # Điều khiển bộ lọc FIR, tích hợp Pipeline DSP48 đầy đủ
├── constraints/
│   └── arty_z7.xdc          # Ràng buộc phần cứng, định nghĩa chân và chu kỳ clock (15ns)
├── data/
│   ├── coeff_bass.mem       # Bảng hệ số bộ lọc dải Bass
│   ├── coeff_mid.mem        # Bảng hệ số bộ lọc dải Mid
│   └── coeff_treble.mem     # Bảng hệ số bộ lọc dải Treble
└── README.md
