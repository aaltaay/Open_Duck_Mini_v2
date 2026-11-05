# Third-party code in altaay_lab/software/dock

| What | Upstream | Commit | License | Where here | Changed |
|---|---|---|---|---|---|
| autodock (state machine, utilities) | https://github.com/osrf/autodock | fd9c2a9aa6d05e4df84883008562e49506f690c0 (2022-05-30) | Apache-2.0, LICENSE copied verbatim to autodock/LICENSE; the upstream tree has no NOTICE file | autodock/autodock_utils.py (from autodock_core/scripts/autodock_core/autodock_utils.py), autodock/autodock_base.py (from autodock_server.py), autodock/duck_autodock.py (from simple_autodock.py) | yes: each file keeps the upstream copyright header and states its changes (Apache-2.0 section 4(b)) |

Rules only, no code copied (cited in the code comments):
- Nav2 nav2_docking (navigation2 commit 20b9fa3e77f019cac243cded0dd10e35997c9423, Apache-2.0): a staging pose before the visual approach, retries back to staging, the dock opens the pins before undocking.
- Quchaosheng/ros2-apriltag-docking-demo (commit 5d076fae02ed4ed2b60364db61ba5e94f19718bb, Apache-2.0): reject unknown tags, three-frame confirmation, reject pose jumps.

The duck repo itself is Apache-2.0 (LICENSE at the repo root), so the copy is allowed (DECISIONS.md D43).
