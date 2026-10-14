"""
Independent falsification check for claim A3 (gantry reach / collisions / Z) and
planned PR E feasibility (fix Y range + disable gantry<->deck contacts; find Z cause).

Own methodology, not copied from probe2.py: steps through EVERY slot (1-12) with
contacts enabled vs disabled, and separately isolates the Z-axis behavior by
driving Z alone with X/Y pinned at 0, to find whether the "tip below deck" effect
is caused by the Y clamp, by contact forces, or by something independent of both.
"""
import sys, os
os.environ.setdefault("MUJOCO_GL", "egl")
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import mujoco
import numpy as np
from opentrons.visualization.scene import XML_PATH, SLOT_XY, _slot_ctrl_y, SAFE_Z, WORK_Z

m = mujoco.MjModel.from_xml_path(str(XML_PATH))
site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "pipette_tip")

print("=== actuator / joint ranges from the live compiled model (not just XML text) ===")
for nm in ("act_x", "act_y", "act_z"):
    aid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_ACTUATOR, nm)
    print(f"  {nm}: ctrlrange={m.actuator_ctrlrange[aid]}")
for nm in ("j_x", "j_y", "j_z"):
    jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, nm)
    print(f"  {nm}: range={m.jnt_range[jid]}")

print()
print("=== per-slot Y-reachability, X/Y/Z tip position, contacts ON vs OFF ===")
for disable_contact in (False, True):
    m.opt.disableflags = int(mujoco.mjtDisableBit.mjDSBL_CONTACT) if disable_contact else 0
    d = mujoco.MjData(m)
    print(f"-- contacts_disabled={disable_contact} --")
    for slot in range(1, 13):
        sx, sy = SLOT_XY[slot]
        cy = _slot_ctrl_y(sy)
        mujoco.mj_resetData(m, d)
        d.ctrl[0] = sx
        d.ctrl[1] = cy
        d.ctrl[2] = WORK_Z
        for _ in range(1500):
            mujoco.mj_step(m, d)
        tip = d.site_xpos[site]
        err_xy = ((tip[0] - sx) ** 2 + (tip[1] - sy) ** 2) ** 0.5
        print(f"   slot {slot:2d} target=({sx:+.3f},{sy:+.3f}) ctrl_y={cy:+.3f} "
              f"-> tip=({tip[0]:+.3f},{tip[1]:+.3f},{tip[2]:+.3f}) xy_err={err_xy:.3f} ncon={d.ncon}")

print()
print("=== isolating Z: drive X=0,Y=ctrl_y(slot2) and sweep Z ctrl, contacts off ===")
m.opt.disableflags = int(mujoco.mjtDisableBit.mjDSBL_CONTACT)
d = mujoco.MjData(m)
cy2 = _slot_ctrl_y(SLOT_XY[2][1])
for zc in (SAFE_Z, WORK_Z, -0.05, 0.0):
    mujoco.mj_resetData(m, d)
    d.ctrl[0] = 0.0
    d.ctrl[1] = cy2
    d.ctrl[2] = zc
    for _ in range(1500):
        mujoco.mj_step(m, d)
    jz = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "j_z")
    qadr = m.jnt_qposadr[jz]
    tip = d.site_xpos[site]
    print(f"  z_ctrl={zc:+.3f} -> qpos_z={d.qpos[qadr]:+.4f} tip_world_z={tip[2]:+.4f}  "
          f"(0.345 + qpos_z - 0.138 = {0.345 + d.qpos[qadr] - 0.138:+.4f})")

print()
print("=== deck-top / plate-top reference z values (static, from model geoms) ===")
for gname in ("w_A1",):
    gid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, gname)
    print(f"  geom {gname} local pos (within 'plate' body) z-half-size={m.geom_size[gid][1]:.4f}")
bid_deck = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "deck")
print(f"  deck body pos: {m.body_pos[bid_deck]}")
