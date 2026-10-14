import sys
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import mujoco
from opentrons.visualization.scene import XML_PATH

m = mujoco.MjModel.from_xml_path(str(XML_PATH))
for disable in (False, True):
    if disable:
        m.opt.disableflags |= mujoco.mjtDisableBit.mjDSBL_CONTACT
    d = mujoco.MjData(m)
    d.ctrl[:3] = [0.15, -0.10, -0.17]
    for _ in range(2000):
        mujoco.mj_step(m, d)
    site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "pipette_tip")
    pairs = {(mujoco.mj_id2name(m, 5, c.geom1), mujoco.mj_id2name(m, 5, c.geom2),
              m.geom_bodyid[c.geom1], m.geom_bodyid[c.geom2]) for c in d.contact[: d.ncon]}
    print(f"contacts_disabled={disable} qpos={d.qpos.round(3)} jnt={[mujoco.mj_id2name(m,3,i) for i in range(m.njnt)]} bodies={[mujoco.mj_id2name(m,1,b) for b in (1,13,14,16)]} tip={d.site_xpos[site].round(3)} ncon={d.ncon} pairs={sorted(pairs)[:6]}")
