"""Joint names, servo IDs and the three bus chains of our build.

JOINTS copies the Runtime HWI map in its order (mini_bdx_runtime/rustypot_position_hwi.py lines
14 to 31 at 376de65); tests/test_crosscheck.py parses that file and fails if they differ.
CHAINS is our wiring (WIRING.md section 2, D15): each chain gets its servo power at its first
servo (SP1 at ID 20, SP3 at ID 30, SP2 at ID 10), so the last servo of each chain sees the
largest drop.
"""
import ast
from pathlib import Path

JOINTS = {
    "left_hip_yaw": 20, "left_hip_roll": 21, "left_hip_pitch": 22, "left_knee": 23, "left_ankle": 24,
    "neck_pitch": 30, "head_pitch": 31, "head_yaw": 32, "head_roll": 33,
    "right_hip_yaw": 10, "right_hip_roll": 11, "right_hip_pitch": 12, "right_knee": 13, "right_ankle": 14,
}
IDS = list(JOINTS.values())
NAME = {v: k for k, v in JOINTS.items()}

CHAINS = {
    "left_leg": [20, 21, 22, 23, 24],
    "neck": [30, 31, 32, 33],
    "right_leg": [10, 11, 12, 13, 14],
}
ANKLES = {"left_ankle": 24, "right_ankle": 14}
CHAIN_ENDS = {"left_leg": 24, "neck": 33, "right_leg": 14}
FACTORY_ID = 1       # configure_motor.py DEFAULT_ID = 1 "A brand new motor should have id 1"
BAUD = 1_000_000     # rustypot_position_hwi.py line 77, check_voltage.py line 5


def runtime_joint_map(runtime_dir):
    """Parse self.joints = {...} out of the Runtime HWI source (no import, no hardware)."""
    src = Path(runtime_dir) / "mini_bdx_runtime" / "mini_bdx_runtime" / "rustypot_position_hwi.py"
    tree = ast.parse(src.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            t = node.targets[0]
            if isinstance(t, ast.Attribute) and t.attr == "joints" and isinstance(node.value, ast.Dict):
                return {ast.literal_eval(k): ast.literal_eval(v) for k, v in zip(node.value.keys, node.value.values)}
    raise ValueError(f"self.joints not found in {src}")


def runtime_baud(runtime_dir):
    """The baud rate the HWI passes to rustypot.feetech(port, baud)."""
    src = (Path(runtime_dir) / "mini_bdx_runtime" / "mini_bdx_runtime" / "rustypot_position_hwi.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "feetech"
                and len(node.args) == 2):
            return ast.literal_eval(node.args[1])
    raise ValueError("rustypot.feetech(...) call not found")
