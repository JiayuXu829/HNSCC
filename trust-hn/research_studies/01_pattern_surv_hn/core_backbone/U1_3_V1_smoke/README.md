# U1.3/V1 structural smoke

This directory contains the frozen, dependency-free structural smoke specification and its
aggregate-only audit for the minimum `Clinical_Residual_Deep_Sets_Cox` backbone.

The smoke reference validates modality-specific adapters, modality identity, status and quality
encoding, arbitrary subsets, permutation-invariant masked-mean pooling, the residual formula
`eta_fused = eta_clinical + delta_eta`, and exact clinical-only fallback when no active modality
token is present.

It uses deterministic synthetic arrays only. It does not fit patient outcomes, perform formal
development cross-validation, estimate prognosis, access official-test/external data, install a
deep-learning framework, or implement calibration/routing. A separate approval is required before
any trainable V1 experiment.
