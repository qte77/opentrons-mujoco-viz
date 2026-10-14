"""Render per-issue evidence PNGs for the opentrons-mujoco-viz assessment."""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import imageio.v2 as imageio
import mujoco
import numpy as np
from opentrons.visualization import WetLabScene, SLOT_XY, parse_simulate_output, render_protocol

out = sys.argv[1]
os.makedirs(out, exist_ok=True)


def save(name, img):
    p = f"{out}/{name}.png"
    imageio.imwrite(p, img)
    print(p, f"mean={img.mean():.1f}")


with WetLabScene() as s:
    # Issue 4: every named camera at the initial pose
    for cam in ("iso", "side", "top", "front", "deck"):
        save(f"04_camera_{cam}", s.render(cam))
    # Issue 3: gantry commanded to slots, top view (the one working camera)
    site = mujoco.mj_name2id(s.model, mujoco.mjtObj.mjOBJ_SITE, "pipette_tip")
    for slot in (1, 3, 9):
        s.move_to_slot(slot, work=True, steps=400)
        tip = s.data.site_xpos[site]
        print(f"slot {slot} target={SLOT_XY[slot]} tip={tip.round(3)}")
        save(f"03_gantry_slot{slot}_top", s.render("top"))
    # Issue 6: HUD frame (matplotlib present here; without it the same call returns a bare render)
    s.apply_event({"type": "pick", "slot": 1})
    save("06_hud_frame_iso", s.render_with_hud("top"))

# Issues 1/2/5: full pipeline on template-accurate simulate output, camera="top"
events = parse_simulate_output(open(sys.argv[2]).read())
print("parsed events:", [(e["type"], e.get("slot")) for e in events])
r = render_protocol(events, f"{out}/05_run_top.mp4", camera="top", hud=True)
frames = imageio.mimread(f"{out}/05_run_top.mp4", memtest=False)
means = [round(float(f.mean()), 1) for f in frames]
print("video frame means:", means)
black = [i for i, m in enumerate(means) if m < 5]
lit = [i for i, m in enumerate(means) if m >= 5]
save(f"05_video_frame{black[0]:02d}_black", frames[black[0]])
save(f"05_video_frame{lit[0]:02d}_top", frames[lit[0]])
# Issue 1: strip of all video frames so the missing aspirate/dispense moves are visible
thumbs = [f[::4, ::4] for f in frames]
save("01_parser_all_frames_strip", np.concatenate(thumbs, axis=1))
