# Main-figure framework placeholder for V1R

## Proposed left-to-right flow

1. **Clinical-pathological anchor (V0)**
   - age, sex, smoking, site, grade, p16, resection, pT and pN;
   - produces a prediction for every eligible postoperative patient.
2. **Usable optional-modality set**
   - blood, ICD and TMA tokens;
   - each token carries availability/usability and quality indicators;
   - order-invariant set pooling.
3. **Residual Deep Sets block**
   - estimates incremental evidence beyond V0;
   - inner-CV selects residual penalty, optimization checkpoint and residual scale.
4. **Shrinkage fusion**
   - `eta_V1R,i = eta_V0,i + lambda_f * delta_eta_V1,i`;
   - `lambda_f` is selected in the inner cross-validation of outer fold `f` and controls how much optional evidence is allowed to alter the clinical anchor.
5. **Output and safety paths**
   - usable optional evidence: V1R fused risk;
   - no usable optional modality: exact V0 fallback;
   - all patients remain covered in the completed development analysis.

## Suggested annotation panel

- `n = 610`, `events = 173`;
- `coverage = 100%`;
- `Uno C24: 0.6442 -> 0.6655`;
- `AUC24: 0.6620 -> 0.6825`;
- `Brier24: 0.1247 -> 0.1243`;
- `worst supported-pattern regret = +0.00985`;
- `5/5 seeds improved Uno C`.

The final visual should be drawn by the authors; this file is a framework specification rather than artwork.
