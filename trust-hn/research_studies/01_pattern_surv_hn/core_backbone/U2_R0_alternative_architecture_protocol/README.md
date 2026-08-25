# U2-R0 sequential alternative-architecture protocol

U2-R0 freezes how alternative fusion architectures will be investigated after the minimum V1
Deep Sets residual backbone failed its prespecified development complexity gate. This stage is a
protocol/governance stage only: it does not train a new model and does not access official-test or
external outcomes.

The retained safety anchor is V0. Candidate architectures are evaluated sequentially rather than
selected from an unrestricted architecture search. Every candidate receives its own directory,
frozen implementation specification, structural/trainable smoke stage, development cross-validation
stage, report, and researcher approval gate.

Frozen candidate order:

1. **R1/CARS** — Cross-fitted Clinical-Anchored Residual Stacking. A low-variance non-neural
   diagnostic/control that tests whether modality-specific prognostic scores contain stable
   incremental signal before spending complexity on another network.
2. **R2/CCADS** — Clinical-Conditioned Attentive Deep Sets. A minimal neural redesign that adds
   the clinical score as context and replaces equal masked-mean pooling with quality-aware masked
   attention plus a shrinkage gate.
3. **R3/NE-GRME** — Null-Expert Gated Residual Mixture of Experts. Separate blood, ICD, and TMA
   residual experts are combined with an exact zero-residual NULL expert through a masked gate.
4. **R4/CC-RST** — Clinical-Conditioned Residual Set Transformer. A small interaction model that
   is conditional on evidence from earlier candidates that cross-modality interactions are worth
   additional complexity.

The order is scientific rather than performance-adaptive: low-variance signal extraction precedes
attention, explicit expert selection, and finally higher-order interaction modeling. A failed
candidate is preserved as a negative result. Gate thresholds may not be changed after results are
seen, and a failed candidate cannot be promoted by choosing a favorable seed or acquisition pattern.

The common primary comparison remains paired development OOF performance against the frozen V0
reference. Official-test outcomes, all external outcomes, calibration bridge fitting, final
FUSE/FALLBACK/RANK_ONLY/ABSTAIN action labels, and clinical-utility claims remain outside this
protocol unless separately approved after a candidate earns complexity.
