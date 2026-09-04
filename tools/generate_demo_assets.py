#!/usr/bin/env python3
"""Generate small, clearly synthetic SVG waveforms for the bundled demo."""

from __future__ import annotations

import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "examples" / "demo" / "assets"
WIDTH, HEIGHT = 1400, 760
LEFT, RIGHT = 170, 1360
TOP, ROW_GAP = 120, 64
STATIONS = ["XX.DEMO1", "XX.DEMO2", "XX.DEMO3"]
COMPONENTS = ["E", "N", "Z"]


def gaussian(x: float, center: float, width: float) -> float:
    return math.exp(-((x - center) / width) ** 2)


def trace(seed: int, row: int, strength: float, noise_only: bool) -> str:
    rng = random.Random(seed * 100 + row)
    points = []
    baseline = TOP + row * ROW_GAP
    phase_shift = row * 0.35
    for index in range(430):
        t = index / 429 * 17 - 2
        noise = rng.uniform(-1, 1) * (3.2 if noise_only else 1.8)
        signal = 0.0
        if not noise_only:
            p = gaussian(t, 2.2 + row * .035, .7)
            s = gaussian(t, 6.4 + row * .045, 1.3)
            signal = strength * (
                p * 11 * math.sin(18 * t + phase_shift)
                + s * 22 * math.sin(13 * t + phase_shift * .7)
            )
        x = LEFT + index / 429 * (RIGHT - LEFT)
        y = baseline - signal - noise
        points.append((x, y))
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points)


def make_svg(name: str, title: str, seed: int, strength: float, noise_only: bool) -> None:
    rows = []
    for station_index, station in enumerate(STATIONS):
        for component_index, component in enumerate(COMPONENTS):
            row = station_index * 3 + component_index
            baseline = TOP + row * ROW_GAP
            label = f"{station}  {component}"
            rows.append(
                f'<line x1="{LEFT}" y1="{baseline}" x2="{RIGHT}" y2="{baseline}" '
                'stroke="#ececf0" stroke-width="1"/>'
            )
            rows.append(
                f'<text x="24" y="{baseline + 5}" fill="#6e6e73" '
                f'font-size="15">{label}</text>'
            )
            rows.append(
                f'<path d="{trace(seed, row, strength, noise_only)}" '
                'fill="none" stroke="#222226" stroke-width="1.15"/>'
            )

    p_x = LEFT + (2.2 + 2) / 17 * (RIGHT - LEFT)
    s_x = LEFT + (6.4 + 2) / 17 * (RIGHT - LEFT)
    markers = "" if noise_only else (
        f'<line x1="{p_x:.1f}" y1="92" x2="{p_x:.1f}" y2="684" '
        'stroke="#0071e3" stroke-width="2"/>'
        f'<text x="{p_x + 6:.1f}" y="107" fill="#0071e3" font-size="14">P pick</text>'
        f'<line x1="{s_x:.1f}" y1="92" x2="{s_x:.1f}" y2="684" '
        'stroke="#ff7a00" stroke-width="2"/>'
        f'<text x="{s_x + 6:.1f}" y="107" fill="#d76100" font-size="14">S pick</text>'
    )
    ticks = []
    for second in [-2, 0, 2, 4, 6, 8, 10, 12, 14]:
        x = LEFT + (second + 2) / 17 * (RIGHT - LEFT)
        ticks.append(
            f'<line x1="{x:.1f}" y1="700" x2="{x:.1f}" y2="706" stroke="#777" />'
            f'<text x="{x:.1f}" y="728" text-anchor="middle" fill="#6e6e73" '
            f'font-size="13">{second}</text>'
        )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<rect width="100%" height="100%" fill="#ffffff"/>
<text x="24" y="34" fill="#1d1d1f" font-size="23" font-family="Arial, sans-serif" font-weight="600">{title}</text>
<text x="24" y="61" fill="#86868b" font-size="13" font-family="Arial, sans-serif">SYNTHETIC DEMO · not real seismic data · 1–15 Hz display example</text>
<g font-family="Arial, sans-serif">{''.join(rows)}{markers}{''.join(ticks)}
<text x="{(LEFT + RIGHT) / 2:.1f}" y="752" text-anchor="middle" fill="#6e6e73" font-size="13">Time relative to origin (s)</text>
</g></svg>'''
    (OUT / name).write_text(svg, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = [
        ("known_reference.svg", "Known reference · clear P and S", 1, 1.0, False),
        ("candidate_reference.svg", "Candidate reference · moderate signal", 2, .72, False),
        ("review_clear.svg", "REVIEW-001 · coherent arrivals", 3, .83, False),
        ("review_weak.svg", "REVIEW-002 · weak arrivals", 4, .38, False),
        ("review_noise.svg", "REVIEW-003 · noise example", 5, 0.0, True),
    ]
    for case in cases:
        make_svg(*case)
    print(f"Generated {len(cases)} synthetic demo SVG files in {OUT}")


if __name__ == "__main__":
    main()
