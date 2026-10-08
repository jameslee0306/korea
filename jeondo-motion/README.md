# 전도 — 30초 모션 그래픽 (Motion Reel)

- **완성 영상**: `jeondo_motion_30s.mp4` (1920×1080, 60fps, 30초, 첨부 음악 + 타자기 효과음)
- **인터랙티브 버전**: `index.html` — 로컬 서버로 열고(`python3 -m http.server`) ▶ PLAY

## 구성 (160 BPM · 4마디 = 6초 단위, 모든 컷이 다운비트에 맞춰짐)
| 시간 | 씬 | 내용 |
|---|---|---|
| 0–6s | 01 DARKNESS → LIGHT | 어둠 속 심장 박동 같은 빛 → 1,500개 입자가 모여 십자가 형성, 갓레이 |
| 6–12s | 02 GO | 비트마다 "이제 / 내가 / 전할 / 차례" 슬램 타이포 → 마가복음 16:15 + 회전하는 원형 텍스트 |
| 12–18s | 03 ONE TO ONE | 3D 점 지구본, 한국에서 복음이 퍼져나가는 아크, 비트마다 1→2→4…32,768 배가 → "땅 끝까지" 글리치 |
| 18–24s | 04 BEAUTIFUL FEET | 신스웨이브 지평선, 비트마다 찍히는 빛의 발자국, 로마서 10:15 |
| 24–30s | 05 전도 | 화이트 플래시 → "전도" 글자별 슬램, 골드 샤인, 충격파, "오늘, 당신이 그 한 사람입니다." |

타자기 가사는 한글을 자모 단위로 분해해 `ㅈ → 저 → 전`처럼 실제로 타이핑되는 과정을 보여주며,
키 하나하나에 타자 소리, 줄 끝에 타자기 벨이 울립니다.

## 다시 렌더하기
```bash
NODE_PATH=$(npm root -g) node tools/render.js out 60      # 프레임 → out/video.mp4, out/keys.json
python3 tools/mix.py music.mp3 out/keys.json out/mix.wav   # 음악 + 효과음 믹스
ffmpeg -i out/video.mp4 -i out/mix.wav -c:v libx264 -crf 21 -pix_fmt yuv420p -c:a aac -shortest jeondo_motion_30s.mp4
```
가사는 `index.html`의 `LY` 객체에서 바꿀 수 있습니다.
