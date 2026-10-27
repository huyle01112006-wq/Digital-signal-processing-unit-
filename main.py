#!/usr/bin/env python3
"""
  python main.py nhac.wav                       # mặc định: N=255, Hamming, gain 2.0/1.0/0.5, 3 giây
  python main.py nhac.wav --seconds 5 --gb 1.5 --gm 1.0 --gt 0.8
  python main.py                                # không có wav -> tự tạo tín hiệu thử (100Hz+1kHz+8kHz)
  python main.py nhac.wav --hw output_audio.mem # SAU khi chạy mô phỏng Verilog: so sánh + tạo wav + FFT
"""
import argparse
import argparse as _ap
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal
from scipy.io import wavfile

import golden_model as gm
import Filter_quantization as s1

FS = s1.FS


# ---------------------------------------------------------------
# Xử lý file wav đầu vào
# ---------------------------------------------------------------
def load_wav_int16_mono_48k(path):
    """Đọc wav bất kỳ -> int16, mono, 48 kHz."""
    rate, d = wavfile.read(path)
    if d.ndim > 1:
        print("  Stereo -> lấy trung bình 2 kênh thành mono")
        d = d.astype(np.float64).mean(axis=1)
    # đưa về float [-1, 1]
    if d.dtype == np.uint8:
        d = (d.astype(np.float64) - 128) / 128
    elif np.issubdtype(d.dtype, np.integer):
        d = d.astype(np.float64) / np.iinfo(d.dtype).max
    elif d.dtype.kind == "f":
        d = d.astype(np.float64)
    else:  # float64 sau mean
        peak = np.max(np.abs(d)) or 1
        d = d / (32768 if peak > 1 else 1)
    if rate != FS:
        g = math.gcd(rate, FS)
        print(f"  Resample {rate} Hz -> {FS} Hz")
        d = signal.resample_poly(d, FS // g, rate // g)
    return np.clip(np.round(d * 32767), -32768, 32767).astype(np.int16)


def make_demo_signal(seconds):
    t = np.arange(int(FS * seconds)) / FS
    x = sum(0.25 * np.sin(2 * np.pi * f * t) for f in (100, 1000, 8000))
    x += 0.02 * np.random.default_rng(0).standard_normal(len(t))
    return np.round(x * 32767).astype(np.int16)


# ---------------------------------------------------------------
# Đồ thị phổ FFT trước/sau
# ---------------------------------------------------------------
def plot_spectrum(x, y, label_y, path):
    fig, ax = plt.subplots(figsize=(10, 5))
    for sig, lab in ((x, "Trước (input)"), (y, f"Sau ({label_y})")):
        f, p = signal.welch(sig.astype(np.float64) / 32768, FS, nperseg=8192)
        ax.plot(f, 10 * np.log10(p + 1e-20), label=lab, lw=1.3)
    ax.set_xscale("log")
    ax.set_xlim(20, FS / 2)
    ax.axvline(s1.FC1, color="gray", ls="--", alpha=.6)
    ax.axvline(s1.FC2, color="gray", ls="--", alpha=.6)
    ax.set_xlabel("Tần số (Hz)")
    ax.set_ylabel("Mật độ công suất (dB/Hz)")
    ax.set_title("Phổ tần số trước và sau khi qua Equalizer")
    ax.grid(True, which="both", alpha=.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=s1.DPI)
    plt.close(fig)
    print(f"  -> {path}")


# ---------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------
def main():
    ap = _ap.ArgumentParser(description=__doc__, formatter_class=_ap.RawDescriptionHelpFormatter)
    ap.add_argument("wav", nargs="?", help="file .wav đầu vào (bỏ trống = tín hiệu thử)")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--taps", type=int, default=255)
    ap.add_argument("--window", default="hamming", choices=["hamming", "hann", "blackman"])
    ap.add_argument("--seconds", type=float, default=3.0, help="cắt độ dài (s); 0 = giữ nguyên")
    ap.add_argument("--gb", type=float, default=2.0, help="Gain Bass")
    ap.add_argument("--gm", type=float, default=1.0, help="Gain Mid")
    ap.add_argument("--gt", type=float, default=0.5, help="Gain Treble")
    ap.add_argument("--hw", help="output_audio.mem từ mô phỏng Verilog (để so sánh)")
    ap.add_argument("--no-plots", action="store_true", help="bỏ qua 6 đồ thị thiết kế")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    P = lambda name: os.path.join(a.outdir, name)
    n = a.taps

    # ---- Stage 1: thiết kế + xuất hệ số ----
    print(f"[1/4] Thiết kế bộ lọc: N={n}, {a.window}, Fs={FS} Hz")
    hf = s1.design_filters(n, a.window)
    hq = {k: s1.quantize(v) for k, v in hf.items()}
    for k in hf:
        s1.report(k, hf[k], hq[k], n)
        s1.export_mem(P(f"coeff_{k}.mem"), hq[k])
    print(f"  -> coeff_bass/mid/treble.mem ({n} dòng mỗi file)")
    s1.sine_test(hq, n)
    if not a.no_plots:
        s1.plot_responses(hf, hq, n, a.outdir)
        s1.plot_sum(hf, hq, n, a.outdir)
        s1.plot_impulse(hf, n, a.outdir)
        s1.plot_phase(hf, n, a.outdir)
        s1.plot_windows(n, a.outdir)

    # ---- Stage 3: chuẩn bị input ----
    print("\n[2/4] Chuẩn bị tín hiệu vào")
    if a.wav:
        print(f"  Đọc {a.wav}")
        x = load_wav_int16_mono_48k(a.wav)
    else:
        print("  Không có wav -> dùng tín hiệu thử 100Hz + 1kHz + 8kHz + nhiễu")
        x = make_demo_signal(a.seconds or 3.0)
    if a.seconds:
        x = x[: int(a.seconds * FS)]
    gm.write_mem(P("input_audio.mem"), x)
    wavfile.write(P("input_48k_mono.wav"), FS, x)
    print(f"  -> input_audio.mem: {len(x)} mẫu ({len(x) / FS:.2f} s)")
    print(f"  >>> Đặt NUM_SAMPLES = {len(x)} trong testbench <<<")

    # ---- Golden model ----
    print(f"\n[3/4] Golden model (gain B/M/T = {a.gb}/{a.gm}/{a.gt})")
    y_gold = gm.equalizer(x, hq["bass"], hq["mid"], hq["treble"], a.gb, a.gm, a.gt)
    gm.write_mem(P("golden_output.mem"), y_gold)
    wavfile.write(P("golden_output.wav"), FS, y_gold)
    clipped = int(np.sum(np.abs(y_gold.astype(np.int64)) >= 32767))
    print(f"  -> golden_output.mem / golden_output.wav | mẫu bị clip: {clipped}")
    plot_spectrum(x, y_gold, "golden", P("spectrum_golden.png"))

    # ---- Stage 4: so sánh với phần cứng ----
    print("\n[4/4] So sánh với phần cứng")
    if a.hw:
        if not os.path.exists(a.hw):
            raise SystemExit(f"Không tìm thấy file '{a.hw}'. Hãy chạy mô phỏng Verilog để tạo output_audio.mem trước.")
        gm.cmd_compare(_ap.Namespace(dir=a.outdir, hw=a.hw))
        y_hw = gm.read_mem(a.hw).astype(np.int16)
        wavfile.write(P("output_processed.wav"), FS, y_hw)
        print(f"  -> output_processed.wav")
        s = min(len(x), len(y_hw))
        plot_spectrum(x[:s], y_hw[:s], "Verilog", P("spectrum_verilog.png"))
    else:
        print("  (chưa có --hw) Sau khi mô phỏng Verilog xong, chạy lại:")
        print(f"  python main.py {a.wav or ''} --outdir {a.outdir} --hw output_audio.mem".replace("  ", " "))

    print(f"\nXong mọi file nằm trong thư mục '{a.outdir}/'.")


if __name__ == "__main__":
    main()