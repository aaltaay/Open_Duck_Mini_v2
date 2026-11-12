# The 2026-07-28 Covered List notice on foreign-made robots

This is not legal advice. It needs a lawyer. Nothing was bought. No one was contacted. A sentence is quoted only from a page that was opened. A number is marked cited or calc only. Where the page does not answer the question, the line says BLOCKER.

The primary notice was found. It is not inferred.

## The document

FCC document number: DA 26-786 (cited, from the first page of the PDF).

Title, cited from that page, in the notice's own capitals: "FCC'S PUBLIC SAFETY AND HOMELAND SECURITY BUREAU ANNOUNCES ADDITION OF FOREIGN-PRODUCED POWER INVERTERS AND ADVANCED ROBOTIC DEVICES TO FCC COVERED LIST."

Dockets, cited: WC Docket No. 18-89, ET Docket No. 21-232, EA Docket No. 21-233.

Links that were opened:

- PDF: https://docs.fcc.gov/public/attachments/DA-26-786A1.pdf
- Text of the same notice: https://docs.fcc.gov/public/attachments/DA-26-786A1.txt
- The Bureau's list page named in the notice: https://www.fcc.gov/supplychain/coveredlist

Pages 1 through 6 of the PDF have a text layer. Quotes from the body and from Appendix A below are from that layer. Appendix B and Appendix C are page images in the same PDF, with no text layer. Quotes from those appendices are read from those page images. The notice names a staff contact. No one was contacted.

## Dates the notice actually prints

The first page says "Released: July 28, 2026" (cited).

Appendix A is headed "COVERED LIST (Updated July 28, 2026)" (cited). The column is "Date of Inclusion on Covered List". The row for the robots reads, cited:

"Foreign-produced advanced robotic devices, except advanced robotic devices which have been granted a Conditional Approval by DoW. July 28, 2026."

The word "effective" does not appear in the text layer of pages 1 through 6. A separate effective date was not found. BLOCKER for any date other than the release date and the inclusion date printed above.

The determinations attached as the appendices are dated July 27, 2026, in the body of the notice (cited: "On July 27, 2026, the Executive Branch interagency body sent the FCC two National Security Determinations").

## What the notice adds, in its own words

Cited from the body:

"PSHSB announces the addition of foreign-produced power inverters and advanced robotic devices to the Covered List."

Cited from the body:

"We update the Covered List to include:

'Foreign-produced power inverters, except power inverters which have been granted a Conditional Approval by DoW or DHS'; and

'Foreign-produced advanced robotic devices, except advanced robotic devices which have been granted a Conditional Approval by DoW.'

We accept the National Security Determinations' definitions of 'foreign-produced,' 'power inverters,' and 'advanced robotic devices,' as provided in the Appendices below."

Those are the two equipment classes this notice adds. The rest of Appendix A is older entries (Huawei, ZTE, Hytera, Hikvision, Dahua, Kaspersky, named telephone companies, uncrewed aircraft, routers, and others). This note does not re-quote those older rows.

A footnote on Appendix A, cited, says:

"Where equipment or services on the list are identified by category, such category should be construed to include only equipment or services capable of the functions outlined in sections 2(b)(2)(A), (B), or (C) of the Secure and Trusted Communications Networks Act of 2019, 47 U.S.C. 1601(b)(2)(A)-(C)."

The text of those three statutory functions was not opened. BLOCKER for what (A), (B), and (C) say. The footnote is real. What it cuts out of the robot class is not settled in this note.

## The robot definition, read from Appendix C

Appendix C is the "National Security Determination on the Threat Posed by Foreign-Produced Advanced Robotic Devices". The definition, read from the page image:

"Advanced Robotic Devices: For the purpose of this determination, the term 'advanced robotic devices' means:

(A) A mechanical mobile device, including autonomous mobile robots, humanoid robots, and quadrupeds, that

i. Is capable of locomotion, obstacle avoidance, navigation, or movement on the ground;

ii. Operates at a distance from a human operator or supervisor based on commands or in response to sensor data or any combination thereof; and

iii. The combined weight of the device and, if applicable, ground station or docking station is over 4.4lbs; and

iv. Contains a component falling within each of the below subparagraphs:

i. a sensor capable of perceiving its environment;

ii. a component that is capable of providing network connectivity (wired or wireless, including Bluetooth, WiFi, cellular, or satellite) with connection speeds of at least 200 kbps in either direction; and

iii. software running either locally or remotely, including firmware and AI or machine-learning model weights, that controls the robot's autonomous navigation or movement perception, data collection, or remote command-and-control; and

(B) Does not include:

i. A 'connected vehicle,' as that term is defined in 15 CFR 791.301, but including a connected vehicle of any gross weight;

ii. A vehicle operated only on a rail line;

iii. An 'uncrewed aircraft' or 'uncrewed aircraft system,' as defined in 47 CFR 88.5;

iv. An unmanned underwater vehicle that is able to operate without a human occupant;

v. Items that are classified as devices under section 513 of the Federal Food, Drug, and Cosmetic Act (21 U.S.C. 360c), including surgical instruments, medical and surgical robotic systems, external limb prostheses and their components, and ambulatory and mobility assistive devices (such as canes, crutches, walkers, and wheelchairs), whether or not powered, and whether the item was cleared under section 510(k), approved under section 515, classified under section 513(f)(2), or exempt from premarket notification; and

vi. A fixed, stationary, non-mobile robot, including articulating, parallel/delta, Cartesian/gantry, or Selective Compliance Assembly, or Articulated, Robot Arm (SCARA) robots intended for industrial or medical use."

The same page image says:

"Foreign-Produced: For the purpose of this determination, the term 'foreign-produced' refers to any article that would not qualify as a 'domestic end product,' as that term is defined in 48 CFR 25.101(a)."

The power-inverter definition is in Appendix B, also a page image. It says a power inverter is a device that converts direct current to alternating current, or alternating current to direct current, including microinverters, string inverters, central inverters, and hybrid battery inverters, and that has Wi-Fi, cellular, Bluetooth, or a similar link for remote communication, control, sensing, data collection, or monitoring. An STS3215 servo is a motor on the bill. It is not that inverter on the words that were read. The Pi is a computer. The brief opened for COMPLIANCE.md says it has 2.4 GHz 802.11 b/g/n and Bluetooth 4.2. The brief does not call the board a power inverter.

## Does this duck fall inside the robot class

The question posed here is a small home robot with a Pi, the Pi's Wi-Fi, STS3215 servos, and all foreign-made parts. "All foreign-made parts" is the question's premise. It is not a customs ruling.

Element by element, against the definition that was read:

- Movement on the ground. The duck is the walking machine in this repo. That matches clause (A)(i) on the lab's own description. It is not an FCC test.
- It operates at a distance, on commands or on sensor data. The lab drives the walk from a controller, and it runs a walk policy from sensors. That matches clause (A)(ii) on the lab's own description.
- Weight over 4.4lbs. The determination states that number (cited, from the page image). sim/MASS_BUDGET.md states Our build as 2.81 kg. That figure is a model, not a scale. 2.81 times 2.2046 is 6.19 lb (calc only, rounded to two decimals). The model is over 4.4 lb. A scale reading does not exist. If a real unit weighs 4.4 lb or less, clause (A)(iii) is not met. Until it is weighed, the scale result is BLOCKER, and the model is over the line.
- A sensor. The bill includes a camera and an IMU. That matches the sensor subparagraph on the parts that are named.
- A network link of at least 200 kbps. The number 200 kbps is cited from the page image. The Pi brief names 802.11 b/g/n and Bluetooth 4.2. The brief lines that were read do not state a speed in kbps. BLOCKER for the speed number. This note does not treat the word Wi-Fi as a substitute for that number.
- Software for navigation, perception, data collection, or remote command. The walk policy and the controller exist in the repo. That matches the software subparagraph on the lab's own description.
- The exclusions. On the lab description, the duck is not a car, a train, an aircraft, an underwater vehicle, an FDA device, or a fixed factory arm. The connected-vehicle definition in 15 CFR 791.301 was not opened. BLOCKER for the legal meaning of that exclusion. It does not, on its label, describe this duck.

The footnote that points at 47 USC 1601(b)(2) is still open, because the statute text was not opened. BLOCKER for whether that footnote takes this duck back out of the class.

On the elements that have a source, the duck matches the robot definition except the speed number, which is BLOCKER, and except the statute footnote, which is BLOCKER. A lawyer has to apply it. This note does not say the FCC has ruled on this duck.

## Domestic product, and US assembly

The notice does not use the phrase "US-assembled exemption". A search of the text layer found no such sentence.

What the notice does is point at 48 CFR 25.101(a). That section was opened, eCFR as of 2026-11-10. Cited from it: a domestic end product that is manufactured has two parts. It must be manufactured in the United States. And, if it is not mostly iron or steel, the cost of domestic components exceeds 65 percent of the cost of all components for items delivered in calendar years 2024 through 2028 (cited). The percentage is 75 percent starting in calendar year 2029 (cited). The same paragraph says that content test "has been waived for acquisitions of COTS items". That sentence is about government acquisitions.

The glossary that actually says "Domestic end product means" is 48 CFR 25.003, also opened. Cited from it: an end product manufactured in the United States qualifies if the domestic-component percentage above is met, or if "the end product is a COTS item". Components of unknown origin are treated as foreign (cited). "Cost of components does not include any costs associated with the manufacture of the end product" (cited).

So US assembly labor on the finished duck is not a domestic component. If every incorporated part is foreign, as the question assumes, the 65 percent test is not met. Assembly in the United States does not, by itself, satisfy that test.

COTS is defined in 48 CFR 2.101, opened. Cited: a COTS item is a commercial product that is sold in substantial quantities in the commercial marketplace, and offered to the Government, under a contract or subcontract, without modification, in the same form in which it is sold in the commercial marketplace. This duck is not built and is not for sale (COMPLIANCE_FIRST_PASS.md). It is not, on those facts, sold in substantial quantities, and it is not offered to the Government. The COTS path is not met on the record in this repo.

The exemption the notice itself writes, besides qualifying as a domestic end product, is a Conditional Approval by the Department of War. Cited from the body: entities that produce these devices in a foreign country can request an evaluation, and DoW evaluates the robot requests. The guidance document named in the notice was not opened. BLOCKER for the form, the fee, and the time.

## New authorizations, and sales of a module that already has one

The notice's own words, cited, are about receiving an authorization, not about a sale:

"Under the Commission's existing rules in section 2.903(a), once added to the Covered List, 'covered' equipment is prohibited from receiving equipment authorizations."

Also cited: "all applications seeking equipment authorization from the Commission must certify that the equipment is not prohibited from receiving an equipment authorization by virtue of being 'covered equipment.'"

The text layer of pages 1 through 6 does not contain the words "sale", "market", "import", "revoke", or "grandfather". Counted from that layer. The notice does not, in those pages, say that an existing grant is cancelled.

47 CFR 2.903, opened, eCFR as of 2026-11-10, says covered equipment "is prohibited from obtaining an equipment authorization". That includes equipment that "has been certified as a modular transmitter" or that could be certified as one under 47 CFR 15.212. Paragraph (c) applies that ban to certification, to a Supplier's Declaration of Conformity, and to equipment that would otherwise be exempt.

Paragraph (b) is narrower. It bars a device from obtaining an authorization when the device incorporates a modular transmitter described in paragraph (a) and a logic-bearing part from an entity identified on the Covered List. Both are required. The Pi is not Huawei, ZTE, Hytera, Hikvision, Dahua, or the other named producers. Paragraph (b) does not, on those words, ban a host merely because a Pi is inside it.

47 CFR 2.803, opened, is the marketing rule. Cited: "Marketing, as used in this section, includes sale or lease, or offering for sale or lease". The general rule: "No person may market a radio frequency device unless the radio frequency device is authorized pursuant to a valid FCC equipment authorization that has not been limited through the procedures described in 2.939(e)".

47 CFR 2.939(e), opened, says the Office of Engineering and Technology and the Public Safety and Homeland Security Bureau may limit an existing authorization "to prohibit continued importation or marketing", and only after a public notice, an impact assessment, a comment period of no less than 30 days (cited), and a later determination. DA 26-786 does not say that it is that notice. It does not open a comment period. A later 2.939(e) notice for this class was not opened in this session. BLOCKER for a claim that no such later notice exists.

What that leaves, on the pages that were opened:

- If the finished duck is covered equipment, 2.903(a) says the duck cannot obtain an authorization, including an SDoC. 2.803 says an RF device is not to be marketed without a valid authorization. The notice does not say whether the Pi's existing grant is that authorization for the assembled duck. 47 CFR 15.212, the modular-host rule, was opened for COMPLIANCE_FIRST_PASS.md and was not re-read line by line this session. BLOCKER for whether the Pi grant covers this body.
- Selling the Pi board by itself is a different question. Clause (A)(i) of the robot definition requires movement on the ground. A bare Pi does not do that. The notice does not call the Pi an advanced robotic device. This note does not say the Pi's existing grant is void.
- Selling an STS3215 by itself is not covered by the inverter definition that was read, and a servo is not the mobile device in clause (A).

The notice also says, cited, that these updates "will not implicate various rules and programs applicable to entities 'identified' on the Covered List, because this newly-covered equipment is identified by place of production, not by entity." The sections it lists there are 2.903, 2.906, 2.907, 2.911, 2.929, 2.932, 2.938, 2.1033, and 2.1043. It does not list 2.803 or 2.939 in that sentence.

## What a lawyer still has to close

- The text of 47 USC 1601(b)(2)(A) through (C).
- A kilobit rate for the Pi radio, from a grant or a brief line that states one.
- A scale weight.
- Whether 15.212 lets this body use the Pi's existing grant.
- Whether any later public notice under 2.939(e) has limited existing grants for this class.
- The Department of War guidance for a conditional approval.

Sources: the DA 26-786 PDF and text links above, https://www.ecfr.gov/current/title-47/section-2.903 , https://www.ecfr.gov/current/title-47/section-2.803 , https://www.ecfr.gov/current/title-47/section-2.939 , https://www.ecfr.gov/current/title-48/section-25.101 , https://www.ecfr.gov/current/title-48/section-25.003 , and https://www.ecfr.gov/current/title-48/section-2.101 .
