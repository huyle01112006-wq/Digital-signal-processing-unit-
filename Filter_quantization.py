#!/usr/bin/env python3
"""
you can use one of three types including hamming, hann,blackman following your target but in this project that i
choose hamming with N = 255 so as to ensure the balance between main lope and any things. 
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")  # không cần GUI
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal

# ==========================================
# 1. CẤU HÌNH
# ==========================================
FS = 48000            # Hz
FC1 = 300             # Bass | Mid
FC2 = 3000            # Mid | Treble
BITS = 16
SCALE = 2 ** (BITS - 1) - 1   # 32767 (theo đề: round(h * (2^15 - 1)))
DPI = 200


# ==========================================
# 2. THIẾT KẾ BỘ LỌC
# ==========================================
def design_filters(n, window="hamming"):
    """Trả về dict 3 bộ lọc float. Mid = phần bù => tổng 3 dải = xung đơn vị."""
    if n % 2 == 0:
        raise ValueError("numtaps phải lẻ (FIR Type I, pha tuyến tính, độ trễ nguyên)")
    lp1 = signal.firwin(n, FC1, fs=FS, window=window, scale=False)
    lp2 = signal.firwin(n, FC2, fs=FS, window=window, scale=False)
    delta = np.zeros(n)
    delta[n // 2] = 1.0 #inital array of element with value 1 before substracting lp2 (<= 3000 Hz)-> creating high filter
    return {
        "bass": lp1,             # low-pass  < 300 Hz
        "mid": lp2 - lp1,        # band-pass 300 - 3000 Hz
        "treble": delta - lp2,   # high-pass > 3000 Hz
    }


def quantize(h):
    """Float -> int16 Q1.15."""
    q = np.round(h * SCALE).astype(np.int64)
    if q.max() > 32767 or q.min() < -32768:
        raise OverflowError("Hệ số tràn int16!")
    return q.astype(np.int16)


def export_mem(path, q):
    with open(path, "w") as f:
        for v in q:
            f.write(f"{int(v) & 0xFFFF:04X}\n")


# ==========================================
# 3. KIỂM TRA & THÔNG SỐ CHO VERILOG
# ==========================================
def report(name, h, q, n):
    sym = np.allclose(h, h[::-1])
    sum_abs = int(np.sum(np.abs(q.astype(np.int64))))
    worst = 32768 * sum_abs                       # |x|max * sum|h|
    acc_bits = int(np.ceil(np.log2(worst))) + 1   # +1 bit dấu
    print(f"[{name:6s}] taps={len(q)} | max={int(q.max()):6d} min={int(q.min()):6d} "
          f"| đối xứng={sym} | sum|h|={sum_abs} | accumulator >= {acc_bits} bit")
    assert len(q) == n and sym
    return acc_bits


def sine_test(qs, n, freqs=(100, 1000, 8000), amp=0.5, dur=0.5):
    """Cho sin qua từng bộ lọc fixed-point, đo độ lợi (dB) -> đưa vào báo cáo."""
    print("\nKiểm thử tín hiệu sin (độ lợi đo được, dB):")
    print(f"{'f (Hz)':>8s} | " + " | ".join(f"{k:>8s}" for k in qs))
    t = np.arange(int(FS * dur)) / FS
    for f in freqs:
        x = np.round(amp * SCALE * np.sin(2 * np.pi * f * t)).astype(np.int64)
        row = []
        for q in qs.values():
            y = np.convolve(x, q.astype(np.int64))[: len(x)] >> 15
            xs, ys = x[n:], y[n:]                       # bỏ phần quá độ
            row.append(20 * np.log10(np.std(ys) / np.std(xs) + 1e-12))
        print(f"{f:>8d} | " + " | ".join(f"{g:8.1f}" for g in row))


# ==========================================
# 4. ĐỒ THỊ
# ==========================================
COLORS = {"bass": "tab:blue", "mid": "tab:green", "treble": "tab:red"}


def _save(fig, outdir, name):
    fig.tight_layout()
    p = os.path.join(outdir, name)
    fig.savefig(p, dpi=DPI)
    plt.close(fig)
    print(f"-> {p}")


def _setup_freq_axis(ax, ylim=(-80, 5)):
    ax.set_xscale("log")
    ax.set_xlim(20, FS / 2)
    ax.set_ylim(*ylim)
    ax.axvline(FC1, color="gray", ls="--", alpha=.6)
    ax.axvline(FC2, color="gray", ls="--", alpha=.6)
    ax.set_xlabel("Tần số (Hz)")
    ax.set_ylabel("Biên độ (dB)")
    ax.grid(True, which="both", alpha=.4)


def mag_db(h):
    w, r = signal.freqz(h, worN=16384, fs=FS)
    return w, 20 * np.log10(np.abs(r) + 1e-12)


def plot_responses(hf, hq, n, outdir):
    fig, ax = plt.subplots(figsize=(10, 6))
    for k in hf:
        w, d = mag_db(hf[k])
        ax.plot(w, d, color=COLORS[k], lw=2, label=k)
    ax.set_title(f"Đáp ứng tần số 3 bộ lọc FIR (N={n}, float)")
    _setup_freq_axis(ax)
    ax.legend()
    _save(fig, outdir, "filter_responses.png")

    fig, axs = plt.subplots(3, 1, figsize=(10, 10), sharex=True)
    for ax, k in zip(axs, hf):
        w, d = mag_db(hf[k])
        _, dq = mag_db(hq[k].astype(float) / SCALE)
        ax.plot(w, d, lw=2, label="Float")
        ax.plot(w, dq, "--", lw=1.2, label="Q1.15 (16-bit)")
        ax.set_title(k)
        _setup_freq_axis(ax)
        ax.legend()
    _save(fig, outdir, "float_vs_quantized.png")


def plot_sum(hf, hq, n, outdir):
    sf = sum(hf.values())
    sq = sum(v.astype(np.int64) for v in hq.values()) / SCALE
    fig, ax = plt.subplots(figsize=(10, 4))
    w, d = mag_db(sf)
    _, dq = mag_db(sq)
    ax.plot(w, d, lw=2, label="Tổng 3 dải (float)")
    ax.plot(w, dq, "--", label="Tổng 3 dải (Q1.15)")
    ax.set_xscale("log")
    ax.set_xlim(20, FS / 2)
    ax.set_ylim(-0.05, 0.05)
    ax.set_title("Kiểm tra tính bù: tổng 3 dải khi Gain = 1.0 (phải phẳng ~0 dB)")
    ax.set_xlabel("Tần số (Hz)")
    ax.set_ylabel("dB")
    ax.grid(True, which="both", alpha=.4)
    ax.legend()
    _save(fig, outdir, "sum_of_bands.png")


def plot_impulse(hf, n, outdir):
    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, k in zip(axs, hf):
        ax.stem(np.arange(n), hf[k], basefmt=" ")
        ax.set_title(f"Đáp ứng xung - {k}")
        ax.grid(alpha=.4)
    axs[-1].set_xlabel("n")
    _save(fig, outdir, "impulse_responses.png")


def plot_phase(hf, n, outdir):
    fig, ax = plt.subplots(figsize=(10, 5))
    for k, h in hf.items():
        w, r = signal.freqz(h, worN=4096, fs=FS)
        ax.plot(w, np.unwrap(np.angle(r)), color=COLORS[k], label=k)
    ax.set_title(f"Đáp ứng pha (tuyến tính) - độ trễ nhóm = {(n - 1) // 2} mẫu "
                 f"= {(n - 1) / 2 / FS * 1000:.2f} ms")
    ax.set_xlabel("Tần số (Hz)")
    ax.set_ylabel("Pha (rad)")
    ax.grid(alpha=.4)
    ax.legend()
    _save(fig, outdir, "phase_response.png")


def plot_windows(n, outdir):
    fig, axs = plt.subplots(1, 2, figsize=(13, 5))
    for win in ("hamming", "hann", "blackman"):
        for ax, fc, ttl in zip(axs, (FC1, FC2), ("Low-pass 300 Hz", "Low-pass 3000 Hz")):
            h = signal.firwin(n, fc, fs=FS, window=win, scale=False)
            w, d = mag_db(h)
            ax.plot(w, d, label=win)
            ax.set_title(f"{ttl} (N={n})")
    for ax in axs:
        _setup_freq_axis(ax, (-120, 5))
        ax.legend()
    _save(fig, outdir, "window_comparison.png")


# ==========================================
# 5. MAIN
# ==========================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taps", type=int, default=255, help="số hệ số (lẻ): 127/255/511")
    ap.add_argument("--window", default="hamming", choices=["hamming", "hann", "blackman"])
    ap.add_argument("--outdir", default=".")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    n = a.taps

    print(f"Fs={FS} Hz | N={n} | window={a.window} | độ trễ nhóm={(n - 1) // 2} mẫu")
    print(f"Dải chuyển tiếp ước tính (Hamming ~3.3*Fs/N) = {3.3 * FS / n:.0f} Hz\n")

    hf = design_filters(n, a.window)
    hq = {k: quantize(v) for k, v in hf.items()}

    acc = max(report(k, hf[k], hq[k], n) for k in hf)
    print(f"=> Chọn accumulator = {acc} bit (thực tế dùng 40 bit cho dư)\n")

    for k in hq:
        p = os.path.join(a.outdir, f"coeff_{k}.mem")
        export_mem(p, hq[k])
        with open(p) as f:
            assert sum(1 for _ in f) == n
        print(f"-> {p}  ({n} dòng)")

    sine_test(hq, n)

    print()
    plot_responses(hf, hq, n, a.outdir)
    plot_sum(hf, hq, n, a.outdir)
    plot_impulse(hf, n, a.outdir)
    plot_phase(hf, n, a.outdir)
    plot_windows(n, a.outdir)


if __name__ == "__main__":
    main()