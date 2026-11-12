# Plug guide

One step at a time. The picture for each step is in `steps/`. The wire-by-wire list is `WIRES.md`. Label both ends of every cable before it goes in, the same rule as `HARNESS_BUILD.md`.

Power stays off. The battery plug stays open until `TEST_POLARITY.md` passes.

The old picture in `docs/assembly_guide.md` swaps the eyes and the antennas. Do not follow that picture. Follow the pin numbers here. They are the netlist pins.

## Step 1. Learn the four plugs

Picture: [steps/01_four_plugs.png](steps/01_four_plugs.png)

You make only these four kinds:

1. XT30. The shell shape keeps plus and minus from swapping.
2. Servo plug. Molex Mini-SPOX housing 50-37-5033, contact 08-70-1040. Latch on one side.
3. KK plug. Molex KK 254. The ramp is on one side. Contact 08-50-0114, and only for 22 to 30 AWG wire.
4. Lever. WAGO 221. Lift the orange lever, push the bare wire in, push the lever down.

The camera ribbon and the USB lead are bought whole. Do not cut them.

## Step 2. Pack to the protection board

Picture: [steps/02_pack_to_bms.png](steps/02_pack_to_bms.png)

Solder the pack leads to the board pads:

- Red to the pad printed B+.
- Yellow to the pad printed B1.
- Black to the pad printed B-.

These are cables P1, P3, and P2.

## Step 3. Battery plug

Picture: [steps/03_xt30.png](steps/03_xt30.png)

Solder the XT30 socket on the pack side. Red in the plus cup. Black in the minus cup. Tug each wire. This is cables P6 and P8. Leave it unplugged.

## Step 4. Fuse

Picture: [steps/04_fuse.png](steps/04_fuse.png)

The fuse is in the red wire only, after the battery plug and before the switch board. Fit the 15 A blade in the holder. Black does not go through the fuse. This is cable P7.

## Step 5. Button

Picture: [steps/05_button.png](steps/05_button.png)

Two thin wires, cable P15. White on one small hole of the switch board. Black on the other. The far ends go on the two lugs of the button. The lug count on the button was not checked on the part. BLOCKER until you confirm the two lugs that close when the button is pressed. Use those two. Do not guess a third lug.

## Step 6. Levers

Picture: [steps/06_levers.png](steps/06_levers.png)

Strip 11 mm. That length is on the WAGO sheet. If you see insulation inside the clear body, pull the wire out and strip it again.

Four groups. Red never goes in a black group.

- Ground, one 221-415: four black wires. Ports are listed on cables P14, P10, P13, and P16 in `WIRES.md`.
- Switched plus, one 221-413: three red wires. Cables P9, P10, and P13.
- Servo plus: one 221-415 and one 221-413, six red wires. A short 16 AWG jumper joins them. Its cut length is not set. BLOCKER until the two levers sit side by side and you cut the jumper so 11 mm enters each port.
- Servo ground: the same, in black.

## Step 7. BEC

Picture: [steps/07_bec.png](steps/07_bec.png)

- Input red goes in the switched plus lever.
- Input black goes in the ground lever.
- Join the two output reds together, then one red into the servo plus lever.
- Join the two output blacks together, then one black into the servo ground lever.
- Tape the unused third wire on each output lead. Do not cut it into a live pad.

The BEC lead gauge is not published. BLOCKER for that number. Do not put a BEC lead into a KK pin.

## Step 8. Servo plugs

Picture: [steps/08_servo_plugs.png](steps/08_servo_plugs.png)

Latch on top. The Feetech sheet numbers the servo pin 1 ground, pin 2 plus, pin 3 signal. Which physical hole is pin 1 is not measured on this card. Hold a kit cable beside the plug you made. The colors must land in the same holes. Then the meter checks it.

The adapter data plugs leave the middle hole empty. Ankle feeds SP4 and SP5 leave the signal hole empty.

Every servo plug is the same shape, so a plug can go into the wrong servo. The label on the cable is what stops that. The latch only stops it going in backwards.

## Step 9. Kit cables

Picture: [steps/09_kit_hop.png](steps/09_kit_hop.png)

These cables are already made. Write the cable name on both ends. Plug one hop at a time. Out of BUS 1, into the next servo BUS 2. Left leg, right leg, then neck.

Ten of the kit hops are already marked test-fit BLOCKER in the netlist, because the 150 mm lead is shorter than the length rule. Do not stretch one to make it reach. If it is tight, stop and use the made-lead spare already on the bill (the X1 and X2 lines). Do not invent a new length.

## Step 10. Head power plug

Picture: [steps/10_neck_xt30.png](steps/10_neck_xt30.png)

Cable P13 is the long red and black pair up the neck. The XT30 in that pair is at the neck base so the head can unplug. Do not mate it with the battery plug. The battery plug is the short one in the bay. The neck pair is the long one.

## Step 11. The Pi

Picture: [steps/11_pi.png](steps/11_pi.png)

The square pad is pin 1. The picture shows pins 1 to 20 only, the corner.

Solder, do not crimp, the thick wires. The KK contact takes 22 to 30 AWG only, and these are 20 AWG:

- Pin 2 red, pin 6 black, from the 5 V regulator (cable P12).
- Pin 4 red, pin 14 black, to the head 5 V splice (cable P17).

The 5-pin plug is housing 0022012057. It covers pins 1, 3, 5, 7, and 9.

- Pin 1 red, 3.3 V.
- Pin 3 blue, SDA.
- Pin 5 yellow, SCL.
- Pin 7 empty. Nothing in that hole.
- Pin 9 black, ground.

The Pi header is not a Molex ramp header, so this plug can be turned around. If the empty hole is not on pin 7, it is backwards. Pull it off and turn it. The meter checks the colors.

Other thin wires that share a pin are spliced to the wire that already has the contact. They do not get a second pin. The list is in `WIRES.md`. 26 AWG does not go in a WAGO lever. The WAGO sheet starts at 24 AWG. Use a solder splice and heat shrink.

Before you crimp 26 AWG, measure the outside of the wire. The contact allows 1.57 mm of insulation. The listing used elsewhere for this wire is 1.5 mm plus or minus 0.1 mm, and that listing was not re-opened. BLOCKER for a sure fit. If the wire is over 1.57 mm, solder that end. Do not crimp it.

## Step 12. Camera and USB

Picture: [steps/12_camera_usb.png](steps/12_camera_usb.png)

Do not cut these.

- Camera ribbon, cable D12, 300 mm, bought. Push it into the Pi camera socket and into the camera. Which face touches the contacts is BLOCKER until the sheet in the bag is read. Do not guess.
- USB lead, cable D1. Pi socket marked USB, not the one marked PWR. Other end in the adapter. The plugs only go in one way.

## Step 13. Eyes

Picture: [steps/13_eyes.png](steps/13_eyes.png)

One 3-pin plug, housing 0022012037.

- Position 1, pin 16, white, right eye.
- Position 2, pin 18, yellow, left eye.
- Position 3, pin 20, black, ground.

The other black eye wires join that black wire. They do not get their own pin. The old assembly picture has these eyes swapped. Use this step.

Antennas stay on their own leads, soldered, because the lead gauge is not published. Left antenna signal is pin 33. Right antenna signal is pin 32. That is also swapped against the old picture.

## Step 14. Feet

Picture: [steps/14_feet.png](steps/14_feet.png)

- Left foot signal, green, pin 15.
- Right foot signal, white, pin 13.
- Both grounds join the black wire already on pin 9.

The two switches in one foot are wired in parallel, the same way the netlist already has them.

## Step 15. Meter

Picture: [steps/15_meter.png](steps/15_meter.png)

Do this before step 16 is powered, and before the battery plug closes. The steps are in `TEST_POLARITY.md`.

## Step 16. Charger plug, and the wells

Picture: [steps/16_charger_wells.png](steps/16_charger_wells.png)

From the charger board already drawn in `circuitry/charger_board.yaml`:

- 2-pin plug, housing 0022012027.
- Position 1, blue, Pi pin 29.
- Position 2, green, Pi pin 31.
- Orange 3.3 V joins the red wire of the 5-pin plug.
- Black ground joins the black wire of the 5-pin plug.

The cut length of this neck cable is BLOCKER. Do not copy another cable's length. Route it with cable D13, the same four neck joints, and cut it when it is in place, with the same slack the other neck cables already use.

The five gold wells in the seat have no far plug. The diode part was not chosen. Leave them open. Do not tie them to the pack.
