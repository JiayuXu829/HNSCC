# U2/V1R locked confirmation stage report

{
  "stage": "U2_V1R_LOCKED_CONFIRMATION_EVALUATION",
  "n": 152,
  "events": 40,
  "delta_V1R_minus_V0": {
    "ipcw_brier_24m": -0.005166106276246446,
    "harrell_c": 0.01958887545344623,
    "uno_c_24m": 0.021663830633940284,
    "auc_24m": 0.01254291042682576,
    "calibration_in_the_large_24m": -0.09478810770011961,
    "calibration_slope_24m": -0.4439028082525125,
    "mean_predicted_risk_24m": 0.012350147261859817
  },
  "bootstrap": {
    "method": "patient_level_stratified_bootstrap",
    "replicates": 2000,
    "seed": 20260825,
    "summary": {
      "ipcw_brier_24m": {
        "replicates": 2000,
        "mean": -0.005222478823298823,
        "ci95_lower": -0.012842760468050893,
        "ci95_upper": 0.0021708097410921626
      },
      "uno_c_24m": {
        "replicates": 2000,
        "mean": 0.021653785947152684,
        "ci95_lower": -0.025964813853084506,
        "ci95_upper": 0.07081620735826019
      },
      "harrell_c": {
        "replicates": 2000,
        "mean": 0.019664829280440287,
        "ci95_lower": -0.0174227715785295,
        "ci95_upper": 0.06119645659209944
      },
      "auc_24m": {
        "replicates": 2000,
        "mean": 0.012725330694394068,
        "ci95_lower": -0.04103088513164902,
        "ci95_upper": 0.06843811792761433
      }
    }
  }
}
