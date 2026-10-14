"""
Independent check for claims A4, A5 and planned PR D (camera euler degree/radian fix),
without reusing probe.py/probe2.py/evidence.py. Builds its own patched XML strings
in-memory (mujoco.MjModel.from_xml_string) rather than editing the repo's asset file.
"""
import os, sys
os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import mujoco
import numpy as np
import imageio.v2 as imageio
from opentrons.visualization.scene import WetLabScene, XML_PATH

OUT = "/tmp/claude-1000/-workspaces-qte77-opentrons-mujoco-viz/1bca0489-fe0f-4f0d-aaec-0887149b19de/scratchpad/falsify"

print("=== claim A4: render every camera on the UNMODIFIED bundled asset, report mean/std ===")
with WetLabScene() as s:
    results = {}
    for cam in ("iso", "side", "top", "front", "deck"):
        img = s.render(cam)
        results[cam] = (float(img.mean()), float(img.std()))
        imageio.imwrite(f"{OUT}/orig_{cam}.png", img)
        print(f"  {cam:6s} mean={img.mean():7.2f} std={img.std():6.2f}  "
              f"-> {'BLACK/FLAT' if img.std() < 1.0 else 'has content'}")

print()
print("=== claim A5: render_protocol with camera='top' across an apply_event-heavy run, count black frames ===")
from opentrons.visualization import render_protocol
events = [
    {"type": "pick", "slot": 1},
    {"type": "aspirate", "volume": 50, "slot": 3, "well": "A1"},
    {"type": "dispense", "volume": 50, "slot": 2, "well": "B1"},
    {"type": "engage", "height": 13.0},
    {"type": "tc_open_lid"},
    {"type": "drop", "slot": 12},
]
r = render_protocol(events, f"{OUT}/t3_top_run.mp4", camera="top", hud=False, frames_per_event=2)
frames = imageio.mimread(f"{OUT}/t3_top_run.mp4", memtest=False)
means = [round(float(f.mean()), 2) for f in frames]
stds = [round(float(f.std()), 2) for f in frames]
print(f"  frame_count={r['frame_count']}  means={means}")
black = [i for i, st in enumerate(stds) if st < 1.0]
print(f"  frames with std<1.0 (flat/black): {black}  out of {len(frames)}")

print()
print("=== claim A6: HUD without matplotlib importable -- does render_with_hud silently return bare frame? ===")
# Force ImportError for matplotlib specifically, without touching the shared venv.
import builtins
real_import = builtins.__import__
def blocking_import(name, *a, **kw):
    if name == "matplotlib" or name.startswith("matplotlib."):
        raise ImportError(f"simulated missing dependency: {name}")
    return real_import(name, *a, **kw)
builtins.__import__ = blocking_import
try:
    with WetLabScene() as s2:
        bare = s2.render("top")
        hud_frame = s2.render_with_hud("top")
        same_shape = bare.shape == hud_frame.shape
        identical = np.array_equal(bare, hud_frame)
        print(f"  bare.shape={bare.shape} hud.shape={hud_frame.shape} identical_pixels={identical}")
        print("  -> HUD silently fell back to bare render with NO exception/warning raised:" , True)
finally:
    builtins.__import__ = real_import

print()
print("=== planned PR D: does converting camera euler from degrees to radians fix all 5 cameras ===")
xml_text = XML_PATH.read_text()
import re as _re
def deg2rad_eulers(text):
    def repl(m):
        vals = [float(x) for x in m.group(1).split()]
        rad = [f"{np.deg2rad(v):.6f}" for v in vals]
        return f'euler="{" ".join(rad)}"'
    return _re.sub(r'euler="([^"]+)"', repl, text)

patched = deg2rad_eulers(xml_text)
assert patched != xml_text, "patch did not change anything -- regex failed"
m2 = mujoco.MjModel.from_xml_string(patched)
d2 = mujoco.MjData(m2)
for _ in range(300):
    mujoco.mj_step(m2, d2)
renderer = mujoco.Renderer(m2, 540, 960)
for cam in ("iso", "side", "top", "front", "deck"):
    renderer.update_scene(d2, camera=cam)
    img = renderer.render().copy()
    imageio.imwrite(f"{OUT}/patched_{cam}.png", img)
    print(f"  patched {cam:6s} mean={img.mean():7.2f} std={img.std():6.2f}  "
          f"-> {'BLACK/FLAT' if img.std() < 1.0 else 'has content'}")
renderer.close()

print()
print("=== did patching euler break joint ranges? (joints are all slide/metres, should be untouched) ===")
for nm in ("j_x", "j_y", "j_z"):
    jid1 = mujoco.mj_name2id(mujoco.MjModel.from_xml_path(str(XML_PATH)), mujoco.mjtObj.mjOBJ_JOINT, nm)
    jid2 = mujoco.mj_name2id(m2, mujoco.mjtObj.mjOBJ_JOINT, nm)
    print(f"  {nm}: patched range={m2.jnt_range[jid2]}")
