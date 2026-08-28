# Main-figure framework specification for V1R and U5R7

## Proposed left-to-right flow

1. **Clinical-pathological anchor**
   - postoperative clinical and pathological variables;
   - produces a prediction for every eligible patient.
2. **Usable optional-modality set**
   - blood, ICD and TMA tokens;
   - each token carries availability/usability and quality indicators;
   - order-invariant set pooling.
3. **Residual Deep Sets block**
   - estimates incremental evidence beyond the clinical anchor.
4. **Inner-CV-selected shrinkage**
   - selects residual penalty, optimisation checkpoint and fold-specific residual scale.
5. **Raw V1R fusion**
   - `eta_V1R,i = eta_V0,i + lambda_f * delta_eta_res,i`.
6. **Safety paths**
   - usable optional evidence: raw V1R fused risk;
   - no usable optional modality: exact clinical-anchor fallback;
   - all patients remain covered.
7. **U5R7 development calibration bridge**
   - `x_raw = logit(p_V1R)`;
   - `x_bridge = alpha_logloss,f + 0.90 * x_raw`;
   - `p_bridge = sigmoid(x_bridge)`;
   - global-only, strictly monotone, rank-preserving, no pattern-specific adjustment;
   - labelled **development-only cross-fitted diagnostic**.
8. **Completed development readouts**
   - V1R: n=610, events=173, Uno C +0.021303, AUC +0.020488, Brier -0.000407, 100% coverage;
   - U5R7: bridge-evaluable rows=2,460, events=415, Brier delta +0.000147, CITL absolute-error improvement 0.007884, slope absolute-error improvement 0.055665, 100% coverage, ranking preserved.
9. **Separate locked confirmation readout**
   - raw V1R only: n=152, events=40, Uno C +0.021664, Brier -0.005166, 100% coverage;
   - annotate as positive directional point-estimate evidence with bootstrap intervals crossing zero;
   - bridge application to confirmation shown only as U5R8 secondary post-unseal validation, with failed calibration gates; raw V1R remains the primary confirmation readout.
10. **Future modules**
   - confirmation bridge application, reliability router and clinical utility evaluation; label as planned/future.

The final visual should be drawn by the authors; this file is a framework specification rather than artwork.
