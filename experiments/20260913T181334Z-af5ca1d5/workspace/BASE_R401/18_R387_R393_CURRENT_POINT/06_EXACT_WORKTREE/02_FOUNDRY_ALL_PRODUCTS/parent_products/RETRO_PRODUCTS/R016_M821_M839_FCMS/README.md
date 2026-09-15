# FCMS v0.1 — Fine-Compatible Microstructure Synthesizer

FCMS searches first- and higher-order laminate trees built from allowed gradient matrices. Every
mixing edge must be rank-one compatible; ordinary convex averaging is insufficient. The result
contains the hierarchy, phase fractions, realized macro gradient, target error, and estimated
smallest layer relative to a fabrication limit.

This reconstructs the useful convex-integration shell as a finite engineering tool. It distinguishes
mathematical realizability from current manufacturing resolution and returns the nearest compatible
relaxation instead of deleting an unreachable target.

Run `python -m unittest -v test_fcms.py` and `python demo_microstructure.py`.
