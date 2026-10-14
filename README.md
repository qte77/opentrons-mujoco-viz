# Evidence for issues and PRs to PhysicalAIBenchmarks/opentrons-mujoco-viz

Orphan branch on the qte77 fork. It holds only renders, logs and the scripts that produced them; it is never merged or
PR'd. All of it was produced on upstream `main` @ `460169f` (mujoco 3.15.0, `MUJOCO_GL=egl`, 2026-10-13).

| File | Shows | Used in |
|---|---|---|
| `01_parser_all_frames_strip.png` | Every frame of a render from `scripts/sim.txt`; no liquid moves | #2 |
| `03_gantry_slot{1,3,9}_top.png` | Tip after `move_to_slot(slot, work=True)`; stops near the deck centre | gantry issue |
| `04_camera_{iso,side,front,deck,top}.png` | Default renders; only `top` is not black | cameras |
| `05_run_top.mp4`, `05_video_frame01_black.png`, `05_video_frame00_top.png` | `render_protocol(camera="top", hud=True)` mixes black `iso` frames into the video | camera/HUD |
| `06_hud_frame_top.png` | HUD frame (matplotlib installed) | camera/HUD |
| `sdist-wheel-listing.txt` | `uv build` contents (no LICENSE, no `opentrons/__init__.py`); PR #1 `merge-tree` | LICENSE, #3, PR #1 |
| `falsify/orig_*.png`, `falsify/patched_*.png` | Cameras before / after converting the eulers to radians in memory | cameras |
| `falsify/t3_top_run.mp4` | Independent repro of the mixed-camera video | camera/HUD |
| `codefactor/{pylint,bandit,ruff,radon}.txt` | Static analysis output | error handling |
| `scripts/` | `evidence.py`, `probe.py`, `probe2.py`, `falsify/t*.py`: reproduce everything above | all |

`scripts/sim.txt` is built from the Opentrons v7.5.0 message templates, **not** a real `opentrons_simulate` run.
