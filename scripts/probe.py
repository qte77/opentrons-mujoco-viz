import os, sys
os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import mujoco, numpy as np
from opentrons.visualization import WetLabScene, SLOT_XY, render_protocol, parse_simulate_output

out = sys.argv[1]
with WetLabScene() as s:
    m, d = s.model, s.data
    site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "pipette_tip")
    for slot in (1, 2, 3, 5, 9, 11):
        s.move_to_slot(slot, work=True, steps=400)
        tip = d.site_xpos[site]
        sx, sy = SLOT_XY[slot]
        print(f"slot {slot}: target xy=({sx:+.3f},{sy:+.3f})  tip=({tip[0]:+.3f},{tip[1]:+.3f},{tip[2]:+.3f})  ctrl_y={d.ctrl[s._ay]:+.3f}")
    for cam in ("iso", "side", "top", "front", "deck"):
        img = s.render(cam)
        import imageio
        imageio.imwrite(f"{out}/cam_{cam}.png", img)
        print(cam, "mean px", round(float(img.mean()), 1), "std", round(float(img.std()), 1))
    f1 = s.apply_event({"type": "pick", "slot": 1})
    h = s.render_with_hud()
    print("apply_event frame", f1[0].shape, "hud frame", h.shape)

ev = parse_simulate_output(open(sys.argv[2]).read())
print("parsed:", [(e["type"], e.get("slot"), e.get("well")) for e in ev])
r = render_protocol(ev, f"{out}/run.mp4", camera="top")
print("render ok", r["frame_count"])
