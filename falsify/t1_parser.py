"""
Independent falsification check for claims A1, A2, and the parser-fix feasibility
in claim E (planned PR C: Text2WetLab-style regex
  r'([A-P]\d{1,2}) (?:of|in) (.+?)(?: at [\d.]+ uL/sec)?$'
).

Does NOT reuse sim.txt verbatim -- constructs its own line set, independently
derived from the Opentrons v7.5.0 source templates fetched this session:
  - aspirate: "Aspirating {volume} uL from {location} at {flow} uL/sec"
  - dispense: "Dispensing {volume} uL into {location} at {flow} uL/sec"
  - mix:      "Mixing {repetitions} times with a volume of {volume} ul"  (lowercase ul)
  - blow_out: f"Blowing out at {location_text}"
  - pick_up_tip: f"Picking up tip from {location_text}"
  - drop_tip: "Dropping tip into {location}"
  - magnetic engage: "Engaging Magnetic Module"  (NO height field at all)
  - tc block temp: f"Setting Thermocycler well block temperature to {temp} °C"
  - tc profile: f"Thermocycler starting {repetitions} repetitions of cycle composed
                 of the following steps: {steps}"
  - hs shake: f"Setting Heater-Shaker to Shake at {rpm} RPM and waiting until reached"
  - hs temp: f"Setting Target Temperature of Heater-Shaker to {temp} °C"
  - hs open latch: "Unlatching labware on Heater-Shaker"
  - hs close latch: "Latching labware on Heater-Shaker"
  - hs deactivate: "Deactivating Shaker" / "Deactivating Heater" (two separate texts)
  - location_text comes from Well.__repr__ -> core.get_display_name(), docstring
    example: "A1 of Some Labware on 5"  (OT-2, numeric slot, NO "well " prefix,
    NO "slot" word before the number)
"""
import sys
sys.path.insert(0, "/workspaces/qte77/opentrons-mujoco-viz")
import re
from opentrons.visualization.event_driver import parse_simulate_output, _PATTERNS, WELL

MY_LINES = [
    "Picking up tip from A1 of Opentrons 96 Tip Rack 300 µL on 1",
    "Aspirating 50.0 uL from B2 of NEST 12 Well Reservoir 15 mL on 3 at 92.86 uL/sec",
    "Dispensing 50.0 uL into C3 of Corning 96 Well Plate 360 µL Flat on 2 at 92.86 uL/sec",
    "Mixing 5 times with a volume of 25.0 ul",
    "Blowing out at C3 of Corning 96 Well Plate 360 µL Flat on 2",
    "Touching tip",
    "Dropping tip into A1 of Opentrons Fixed Trash on 12",
    "Engaging Magnetic Module",
    "Disengaging Magnetic Module",
    "Setting Temperature Module temperature to 37 °C (rounded off to nearest integer)",
    "Deactivating Temperature Module",
    "Opening Thermocycler lid",
    "Closing Thermocycler lid",
    "Setting Thermocycler well block temperature to 95.0 °C",
    "Setting Thermocycler lid temperature to 105.0 °C",
    "Thermocycler starting 30 repetitions of cycle composed of the following steps: [...]",
    "Deactivating Thermocycler",
    "Setting Heater-Shaker to Shake at 1000 RPM and waiting until reached",
    "Setting Target Temperature of Heater-Shaker to 55 °C",
    "Unlatching labware on Heater-Shaker",
    "Latching labware on Heater-Shaker",
    "Deactivating Shaker",
    "Deactivating Heater",
]

print("=== claim A1/A2: repo's own parser against real-wording lines ===")
events = parse_simulate_output("\n".join(MY_LINES))
matched_types = [e["type"] for e in events]
print(f"input lines: {len(MY_LINES)}  matched events: {len(events)}")
for e in events:
    print(" ", {k: v for k, v in e.items() if k != "_raw"}, "| raw:", e["_raw"][:60])

expect_aspirate = any(e["type"] == "aspirate" for e in events)
expect_dispense = any(e["type"] == "dispense" for e in events)
expect_blowout = any(e["type"] == "blow_out" for e in events)
expect_mix = any(e["type"] == "mix" for e in events)
pick_events = [e for e in events if e["type"] == "pick"]
pick_has_slot = any(e.get("slot") is not None for e in pick_events)
engage_events = [e for e in events if e["type"] == "engage"]
tc_block = any("tc_block_temp" == e["type"] for e in events)
tc_profile = any("tc_execute_profile" == e["type"] for e in events)
hs_any = any(e["type"].startswith("hs_") for e in events)

print()
print("aspirate matched:", expect_aspirate, "(claim: should be False)")
print("dispense matched:", expect_dispense, "(claim: should be False)")
print("blow_out matched:", expect_blowout, "(claim: should be False)")
print("mix matched:", expect_mix, "(claim: should be False)")
print("pick events:", pick_events, "-> any with slot set:", pick_has_slot, "(claim: should be False)")
print("engage events:", engage_events, "(claim: height is fabricated default, never real)")
print("tc_block_temp matched:", tc_block, "(claim: should be False)")
print("tc_execute_profile matched:", tc_profile, "(claim: should be False)")
print("any heater-shaker event matched:", hs_any, "(claim: should be False)")

print()
print("=== WELL regex literal ===")
print(repr(WELL))

print()
print("=== claim E: does the proposed Text2WetLab-style regex fix the location parsing? ===")
LOC_FIX = re.compile(r"([A-P]\d{1,2}) (?:of|in) (.+?)(?: at [\d.]+ uL/sec)?$")
test_locations = [
    "Aspirating 50.0 uL from B2 of NEST 12 Well Reservoir 15 mL on 3 at 92.86 uL/sec",
    "Dispensing 50.0 uL into C3 of Corning 96 Well Plate 360 µL Flat on 2 at 92.86 uL/sec",
    "Blowing out at C3 of Corning 96 Well Plate 360 µL Flat on 2",
    "Picking up tip from A1 of Opentrons 96 Tip Rack 300 µL on 1",
    "Mixing 5 times with a volume of 25.0 ul",
    "Dropping tip into A1 of Opentrons Fixed Trash on 12",
]
for line in test_locations:
    m = LOC_FIX.search(line)
    print(f"  {line[:55]!r:58} -> {m.groups() if m else None}")
