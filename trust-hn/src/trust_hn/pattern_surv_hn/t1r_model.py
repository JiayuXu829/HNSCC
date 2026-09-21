"""PyTorch single-modality transcriptome residual head for the T1R method port.

T1R is the faithful single-modality reduction of the V1R shrinkage-controlled residual
fusion: a fixed clinical anchor score plus a nonlinear residual head over a dense
transcriptome vector, with the residual shrinkage scale selected inside inner CV.

This module contains only the model; development cross-validation, shrinkage selection and
governance live in :mod:`trust_hn.pattern_surv_hn.t1r_development_cv`.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor, nn


@dataclass(frozen=True)
class T1RForward:
    clinical_score: Tensor
    residual_score: Tensor
    fused_score: Tensor


class TrainableClinicalResidualTranscriptomeCox(nn.Module):
    """Fixed clinical anchor plus a two-layer Tanh transcriptome residual head.

    The anchor is passed as a fixed ``clinical_score`` input and never jointly re-fit;
    the model only learns ``residual_score`` so that ``fused_score = clinical_score +
    residual_score`` maximises the Cox partial likelihood. When a patient's transcriptome
    is absent (``active`` is false), the residual is exactly zero and the fused score
    equals the clinical anchor.
    """

    def __init__(self, input_dim: int, hidden_dim: int, *, seed: int):
        super().__init__()
        if int(input_dim) < 1:
            raise ValueError("input_dim must be positive")
        if int(hidden_dim) < 1:
            raise ValueError("hidden_dim must be positive")
        self.input_dim = int(input_dim)
        self.hidden_dim = int(hidden_dim)
        torch.manual_seed(int(seed))
        self.residual_head = nn.Sequential(
            nn.Linear(self.input_dim, self.hidden_dim),
            nn.Tanh(),
            nn.Linear(self.hidden_dim, 1),
        )
        self.to(dtype=torch.float64, device="cpu")

    @property
    def parameter_count(self) -> int:
        return int(sum(parameter.numel() for parameter in self.parameters()))

    def forward(
        self,
        clinical_score: Tensor,
        transcriptome: Tensor,
        active: Tensor,
    ) -> T1RForward:
        if clinical_score.ndim != 1 or clinical_score.numel() < 1:
            raise ValueError("clinical_score must be a non-empty vector")
        if not bool(torch.all(torch.isfinite(clinical_score))):
            raise ValueError("clinical_score must be finite")
        rows = clinical_score.numel()
        if transcriptome.ndim != 2 or transcriptome.shape[0] != rows:
            raise ValueError("transcriptome must have shape (rows, input_dim)")
        if transcriptome.shape[1] != self.input_dim:
            raise ValueError("transcriptome width differs from model input_dim")
        if active.shape != (rows,) or active.dtype != torch.bool:
            raise ValueError("active must be a boolean vector of length rows")
        if bool(active.any()) and not bool(torch.all(torch.isfinite(transcriptome[active]))):
            raise ValueError("active transcriptome values must be finite")
        residual = torch.zeros_like(clinical_score)
        if bool(active.any()):
            head = self.residual_head(transcriptome[active]).squeeze(-1)
            residual[active] = head
        return T1RForward(
            clinical_score=clinical_score,
            residual_score=residual,
            fused_score=clinical_score + residual,
        )
