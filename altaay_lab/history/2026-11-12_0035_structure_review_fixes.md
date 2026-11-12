# Structure review fixes

2026-11-12 12:35 AM ET. Follows 2026-11-12_0022_structure_margin_topology.md.

The hip pitch clearance now uses the joint origin times a rotation about the child frame. The joint origin turns about 90 degrees about y, so the earlier sweep was not the thigh. With that sweep the ear-wall pad is 2.62 mm from the thigh sheets and 2.66 to 2.75 mm from the hip pitch servo (CAD check only).

The right ear wall overlap now follows the face direction. That STL had loose shells (30 components against 5 in the stock file). It now matches the stock component count. Re-FEA of the left part on the kept pad: walk 2.41, soft-fall worst 0.78, 3 of 11 under 1.2 (FEA pass only). PrusaSlicer delta for the kept set is +44.09 g and +5.39 h.

The foot study loads its support meshes with the same print-directory fallback as the member STL.
