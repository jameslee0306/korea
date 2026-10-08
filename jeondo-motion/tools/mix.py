"""usage: python3 tools/mix.py music.mp3 keys.json out.wav — 음악 + 타자기 키/벨 + 전환 임팩트 사운드 믹스"""
import json, subprocess, sys
import numpy as np
SR = 44100
music, keys, out = sys.argv[1:4]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', music, '-t', '30', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                     capture_output=True, check=True).stdout
m = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
m = np.pad(m, ((0, max(0, 30 * SR - len(m))), (0, 0)))[:30 * SR]
n = len(m)
t = np.arange(n) / SR
fx = np.zeros_like(m)
rng = np.random.default_rng(3)
K = json.load(open(keys))

def add(at, sig, pan=0.0):
    i = int(at * SR)
    if i >= n: return
    sig = sig[: n - i]
    fx[i:i + len(sig), 0] += sig * (1 - pan) ** .5
    fx[i:i + len(sig), 1] += sig * (1 + pan) ** .5

def keyclick():
    L = int(.06 * SR); x = np.arange(L) / SR
    noise = rng.standard_normal(L)
    noise = np.diff(noise, prepend=0)                       # 고역 강조 → 딸깍
    body = np.sin(2 * np.pi * rng.uniform(1700, 2600) * x) * .5
    thunk = np.sin(2 * np.pi * rng.uniform(140, 190) * x) * np.exp(-x * 90) * .8
    return (noise * np.exp(-x * 900) * .9 + body * np.exp(-x * 260) + thunk) * rng.uniform(.75, 1.1)

for k in K['keys']:
    add(k, keyclick() * .085, rng.uniform(-.3, .3))
for b in K['bells']:
    L = int(.9 * SR); x = np.arange(L) / SR
    add(b, (np.sin(2 * np.pi * 2093 * x) + .4 * np.sin(2 * np.pi * 4186 * x) + .2 * np.sin(2 * np.pi * 6280 * x)) * np.exp(-x * 5) * .045)

B0, BAR = .09, 1.5
cuts = [B0 + 4 * BAR * i for i in range(1, 5)]
for i, c in enumerate(cuts):
    # 리버스 스웰(전환 직전 0.75초 상승하는 노이즈)
    L = int(.75 * SR); x = np.arange(L) / SR
    sw = rng.standard_normal(L); sw = np.convolve(sw, np.ones(12) / 12, 'same')
    add(c - .75, sw * (x / .75) ** 3 * .16)
    # 서브 붐 임팩트
    L = int(1.1 * SR); x = np.arange(L) / SR
    f = 75 * np.exp(-x * 3) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 3.2) * (.42 if i in (0, 3) else .26)
    add(c, boom)

mix = m + fx
fade = np.clip((30 - t) / 1.4, 0, 1) ** 1.5                     # 28.6s~30s 페이드아웃
fade *= np.clip(t / .05, 0, 1)
mix *= fade[:, None]
mix = np.tanh(mix * 1.05) / np.tanh(1.05) * .97                  # 소프트 리미터
pcm = (np.clip(mix, -1, 1) * 32767).astype('<i2')
import wave
w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes()); w.close()
print('peak', float(np.abs(mix).max()), 'keys', len(K['keys']), 'bells', len(K['bells']))
