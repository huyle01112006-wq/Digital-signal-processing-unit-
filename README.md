# 3-Band Digital Audio Equalizer on Arty Z7-20 FPGA

A 3-band digital audio equalizer design implementing a pipelined serial FIR filter architecture on the Digilent Arty Z7-20 FPGA development board (AMD/Xilinx Zynq-7000 SoC).

## 🚀 Key Features
- **Serial FIR Architecture:** Shares a single Multiply-Accumulate (MAC) unit across order $N=255$ filter taps, minimizing FPGA logic cell utilization.
- **Hardware Pipeline Optimization:** Fully utilizes internal DSP48 pipeline register stages (`MREG`, `PREG`) to break long combinational timing paths, achieving complete Timing Closure (WNS > 0) at the target clock period (15 ns).
- **Fixed-Point Processing:** Uses Q1.15 fixed-point representation combined with saturation logic to prevent arithmetic overflow during accumulator shifts.
- **Visual Output Monitoring:** Real-time visual audio level representation via onboard LEDs using peak detection logic.

## 🛠️ Development Environment
- **EDA Tool:** AMD/Xilinx Vivado 2024.2
- **Target Device:** `xc7z020clg400-1` (Arty Z7-20)
- **HDL Language:** Verilog HDL

## 📂 Repository Structure
```text
├── src/
│   ├── arty_top.v           # Top-level module: manages clocks, reset, onboard LEDs, and multiplexes internal buses to solve physical IO pin limitations
│   └── filter_control.v     # Pipelined FIR filter controller with full DSP48 register inferencing
├── constraints/
│   └── arty_z7.xdc          # Hardware constraints defining physical pin locations and clock period (15ns)
├── data/
│   ├── coeff_bass.mem       # Q1.15 coefficient memory file for Bass band
│   ├── coeff_mid.mem        # Q1.15 coefficient memory file for Midrange band
│   └── coeff_treble.mem     # Q1.15 coefficient memory file for Treble band
└── README.md
