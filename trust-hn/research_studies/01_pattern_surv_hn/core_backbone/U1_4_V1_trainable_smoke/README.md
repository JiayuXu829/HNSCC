# U1.4/V1 trainable synthetic smoke

This directory freezes the PyTorch runtime and deterministic synthetic optimization protocol for
the trainable `Clinical_Residual_Deep_Sets_Cox` V1 backbone.

U1.4 converts the dependency-free U1.3 structural reference into trainable PyTorch modules while
preserving the same architecture contract: modality-specific adapters; modality identity, status,
and quality encodings; shared `phi`; masked-mean Deep Sets pooling; shared `rho`; and
`eta_fused = eta_clinical + delta_eta`.

The smoke is deliberately limited to synthetic survival data. It verifies gradient flow, parameter
updates, loss reduction, permutation invariance before and after optimization, and exact clinical
fallback when no active modality token is available. It does not train on HANCOCK patients, run
formal development cross-validation, evaluate official-test/external outcomes, save patient model
checkpoints, or implement calibration or routing.

The CPU dependency is frozen in `requirements-pytorch-cpu.txt` rather than `pyproject.toml` because `pyproject.toml` is a registered Phase 6 integrity file and must remain unchanged.
