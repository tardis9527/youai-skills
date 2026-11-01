"""Beat, bar and energy analysis of the selected song."""

from __future__ import annotations

from pathlib import Path

from .common import MVError


def analyze(path: Path, beats_per_bar: int = 4) -> dict:
    try:
        import librosa
        import numpy as np
    except ImportError as exc:
        raise MVError("缺少 librosa，按 references/setup.md 安装 requirements.txt") from exc

    y, sr = librosa.load(str(path), sr=22050, mono=True)
    duration = float(len(y) / sr)
    if duration < 1:
        raise MVError(f"音频太短或无法解码: {path}")

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    tempo = float(np.atleast_1d(tempo)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    if len(beat_times) < beats_per_bar * 2:
        raise MVError("检测到的拍点太少，无法估算小节（歌曲可能节奏不明显）")

    # Downbeat phase: the beat offset whose beats carry the strongest onsets.
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    strength = onset[np.clip(beat_frames, 0, len(onset) - 1)]
    phase = int(np.argmax([strength[k::beats_per_bar].mean() for k in range(beats_per_bar)]))
    bar_starts = [float(t) for t in beat_times[phase::beats_per_bar]]

    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.times_like(rms, sr=sr)
    peak = float(rms.max()) or 1.0
    bars = []
    for index, start in enumerate(bar_starts):
        end = bar_starts[index + 1] if index + 1 < len(bar_starts) else duration
        mask = (rms_times >= start) & (rms_times < end)
        energy = float(rms[mask].mean() / peak) if mask.any() else 0.0
        bars.append({"index": index + 1, "start": round(start, 3), "end": round(end, 3),
                     "energy": round(energy, 3)})

    return {
        "file": Path(path).name,
        "duration": round(duration, 3),
        "tempo": round(tempo, 2),
        "beats_per_bar": beats_per_bar,
        "downbeat_phase": phase,
        "beats": [round(float(t), 3) for t in beat_times],
        "bars": bars,
        "note": "小节线按拍点与起音强度估算，可能整体偏移一拍；能量为相对值（0–1），"
                "高能量连续段通常是副歌。",
    }


def energy_sketch(bars: list[dict], width: int = 20) -> list[str]:
    """Plain-text bar chart so the agent and user can spot the chorus."""
    return [f"  小节{b['index']:>3}  {b['start']:>7.2f}s  {'#' * round(b['energy'] * width)}"
            for b in bars]
