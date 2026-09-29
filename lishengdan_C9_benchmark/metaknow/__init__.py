"""MetaKnow: a metacognition benchmark for LLMs (Track 2, C2A/C9 challenge).

Sub-tests
---------
S1  Confidence calibration  (answerable questions, verbalized confidence)
S2  Boundary awareness      (answerable vs. provably-unanswerable questions, AUROC)
S3  Error monitoring        (post-hoc self-review of own answers)

Zero runtime dependencies (pure standard library).
"""

__version__ = "1.0.0"
