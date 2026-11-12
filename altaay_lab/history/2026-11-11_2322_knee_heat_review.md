# 2026-11-11 11:22 PM ET: knee heat review fixes

Two review notes on the knee heat guard, both taken.

A failed turn_off is no longer counted and ignored. The walk runs the same hard stop as the older thermal stop (low gains, torque off, then a read-back of register 40). Exit 11 if that stop runs, or 10 if torque is still on.

A cool staggered group no longer clears the rest. After a stop, every watched servo must have two of its own readings strictly under 45 C. The walk watches all 14 joint ids. A servo that has not answered since the stop does not count as cool.

21 unit tests passed with no hardware. c9_docs.py passed. The guard has not run on a servo.
