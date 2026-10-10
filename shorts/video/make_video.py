"""전원 풀백 쇼츠 영상 생성: 상단 제목 고정 + 그림 켄번스(확대/이동) + 내레이션.

python3 make_video.py  →  fullback-shorts.mp4
"""
import subprocess
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
HEADER_H = 400
VIEW_W, VIEW_H = W, H - HEADER_H
ASPECT = VIEW_W / VIEW_H

photo = Image.open(HERE.parent / "fullback.jpg").convert("RGB")
header = Image.open(HERE / "header.png").convert("RGB")
PW, PH = photo.size

# (초, 중심 x, 중심 y, 잘라낼 폭) — 원본 그림 좌표 기준
KEYS = [
    (0.0, 470, 1000, 940),   # 전체
    (3.0, 470, 1000, 940),
    (21.0, 360, 720, 560),   # 6번 "포지션 어떻게 짜야하나.."
    (24.0, 360, 720, 560),
    (33.0, 660, 760, 560),   # 3번 "나도 풀백인데"
    (44.0, 280, 700, 560),   # 2번 "나도 풀백인데"
    (47.5, 280, 700, 560),
    (58.0, 470, 1100, 760),  # 아래쪽 선수들
    (68.0, 470, 1100, 760),
    (71.0, 470, 1000, 940),  # 다시 전체
]


def ease(u):
    return u * u * (3 - 2 * u)


def view_at(t):
    if t <= KEYS[0][0]:
        k = KEYS[0]
        return k[1:]
    for a, b in zip(KEYS, KEYS[1:]):
        if a[0] <= t <= b[0]:
            u = ease((t - a[0]) / (b[0] - a[0]))
            return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return KEYS[-1][1:]


def clamp_box(cx, cy, w):
    h = w / ASPECT
    cx = min(max(cx, w / 2), PW - w / 2)
    cy = min(max(cy, h / 2), PH - h / 2)
    return cx - w / 2, cy - h / 2, w, h


def frame(t):
    x0, y0, w, h = clamp_box(*view_at(t))
    s = w / VIEW_W
    view = photo.transform((VIEW_W, VIEW_H), Image.AFFINE, (s, 0, x0, 0, s, y0), Image.BICUBIC)
    out = Image.new("RGB", (W, H))
    out.paste(header, (0, 0))
    out.paste(view, (0, HEADER_H))
    return out


def main():
    audio = HERE / "narration.m4a"
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(audio)]))
    n = int(dur * FPS)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio),
        "-vf", f"fade=t=out:st={dur - 0.6:.2f}:d=0.6",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
        str(HERE / "fullback-shorts.mp4"),
    ], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()
