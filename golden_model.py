#!/usr/bin/env python3
"""
Golden model fixed-point (bit-accurate) 
  python golden_model.py wav2mem  music.wav  [--seconds 3]   -> input_audio.mem
  python golden_model.py golden   [--gb 2.0 --gm 1.0 --gt 0.5] -> golden_output.mem/.wav
  python golden_model.py compare  output_audio.mem           so với golden_output.mem
  python golden_model.py mem2wav  output_audio.mem output_processed.wav

QUY ƯỚC PHẦN CỨNG :
  1. acc = sum(h[k] * x[n-k])  (signed, accumulator rộng >= 40 bit)
  2. y_fir = saturate16(acc >>> 15)          (dịch phải SỐ HỌC, cắt bớt, không làm tròn)
  3. y_g   = saturate16((y_fir * gain_q) >>> GAIN_FRAC),  gain_q = round(gain * 2^GAIN_FRAC)
  4. y     = saturate16(y_bass + y_mid + y_treble)   (cộng ở độ rộng >= 18 bit rồi mới clip)
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

FS = 48000
GAIN_FRAC = 8   # gain Q8: 1.0 = 256, 2.0 = 512, 0.5 = 128 (đổi nếu Verilog dùng khác)


# ---------- I/O ----------
def read_mem(path):
    vals = []
    with open(path) as f:
        for line in f:
            s = line.split("//")[0].strip()
            if s:
                vals.append(int(s, 16))
    a = np.array(vals, dtype=np.int64)
    return np.where(a >= 0x8000, a - 0x10000, a)


def write_mem(path, x):
    with open(path, "w") as f:
        for v in x:
            f.write(f"{int(v) & 0xFFFF:04X}\n")


# ---------- Mô hình bit-accurate ----------
def sat16(x):
    return np.clip(x, -32768, 32767)


def fir_fixed(x, h):
    acc = np.convolve(x.astype(np.int64), h.astype(np.int64))[: len(x)]
    return sat16(acc >> 15)


def gain_fixed(x, g):
    gq = int(round(g * (1 << GAIN_FRAC)))
    return sat16((x.astype(np.int64) * gq) >> GAIN_FRAC)


def equalizer(x, hb, hm, ht, gb, gm, gt):
    yb = gain_fixed(fir_fixed(x, hb), gb)
    ym = gain_fixed(fir_fixed(x, hm), gm)
    yt = gain_fixed(fir_fixed(x, ht), gt)
    return sat16(yb + ym + yt).astype(np.int16)


# ---------- Lệnh ----------
def cmd_wav2mem(a):
    rate, d = wavfile.read(a.wav)
    if d.dtype != np.int16:
        sys.exit(f"File phải là PCM 16-bit (hiện là {d.dtype}).")
    if rate != FS:
        print(f"CẢNH BÁO: sample rate = {rate}, cần {FS} Hz (hãy resample trước).")
    if d.ndim > 1:
        print("File stereo -> lấy kênh trái.")
        d = d[:, 0]
    if a.seconds:
        d = d[: int(a.seconds * rate)]
    write_mem(os.path.join(a.dir, "input_audio.mem"), d)
    print(f"-> input_audio.mem: {len(d)} mẫu ({len(d) / rate:.2f} s). "
          f"Ghi số này vào testbench làm NUM_SAMPLES.")


def cmd_golden(a):
    d = a.dir
    x = read_mem(os.path.join(d, "input_audio.mem"))
    h = [read_mem(os.path.join(d, f"coeff_{k}.mem")) for k in ("bass", "mid", "treble")]
    y = equalizer(x, *h, a.gb, a.gm, a.gt)
    write_mem(os.path.join(d, "golden_output.mem"), y)
    wavfile.write(os.path.join(d, "golden_output.wav"), FS, y)
    print(f"-> golden_output.mem/.wav ({len(y)} mẫu) | gain B/M/T = {a.gb}/{a.gm}/{a.gt}")
    print(f"   Số mẫu bị clip: {int(np.sum(np.abs(y) >= 32767))}")


def cmd_compare(a):
    gold = read_mem(os.path.join(a.dir, "golden_output.mem"))
    hw = read_mem(a.hw)
    n = min(len(gold), len(hw))
    print(f"Golden: {len(gold)} mẫu | Verilog: {len(hw)} mẫu")
    best = None
    for s in range(0, 33):   # thử độ trễ pipeline của phần cứng
        m = int(np.sum(gold[: n - s] != hw[s:n]))
        if best is None or m < best[1]:
            best = (s, m)
    s, m = best
    diff = np.abs(gold[: n - s] - hw[s:n])
    print(f"Dịch (latency pipeline) tốt nhất: {s} mẫu")
    print(f"Số mẫu lệch: {m}/{n - s} | sai số lớn nhất: {int(diff.max())} LSB")
    if m == 0:
        print("KHỚP HOÀN TOÀN -> phần cứng đúng.")
    else:
        i = int(np.argmax(diff != 0))
        print(f"Mẫu lệch đầu tiên: n={i}  golden={gold[i]}  verilog={hw[i + s]}")
        print("Gợi ý: kiểm tra >>> (số học), thứ tự cắt bit, độ rộng accumulator, Q của gain.")


def cmd_mem2wav(a):
    y = read_mem(a.mem).astype(np.int16)
    wavfile.write(a.out, FS, y)
    print(f"-> {a.out} ({len(y)} mẫu)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=".", help="thư mục chứa .mem")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("wav2mem"); p.add_argument("wav"); p.add_argument("--seconds", type=float)
    p.set_defaults(f=cmd_wav2mem)
    p = sub.add_parser("golden")
    for g, v in (("--gb", 2.0), ("--gm", 1.0), ("--gt", 0.5)):
        p.add_argument(g, type=float, default=v)
    p.set_defaults(f=cmd_golden)
    p = sub.add_parser("compare"); p.add_argument("hw"); p.set_defaults(f=cmd_compare)
    p = sub.add_parser("mem2wav"); p.add_argument("mem"); p.add_argument("out")
    p.set_defaults(f=cmd_mem2wav)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
