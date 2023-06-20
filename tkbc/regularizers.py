# Copyright (c) Facebook, Inc. and its affiliates.

from abc import ABC, abstractmethod
from typing import Tuple, Optional

import torch
from torch import nn

NORM = {
    'N3': lambda factors: torch.abs(factors)**3,
    'Lambda3': lambda factors: torch.sqrt(ddiff[:, :int(factors.shape[1] / 2)]**2 + ddiff[:, int(factors.shape[1] / 2):]**2)**3,
    'L1': lambda factors: torch.abs(factors),
    'L2': lambda factors: (torch.sum(torch.abs(ddiff)**2))**1/2,
    'F2': lambda factors: factors**2,
}

class Regularizer(nn.Module, ABC):
    @abstractmethod
    def forward(self, factors: Tuple[torch.Tensor],  *args, **kwargs):
        pass

class N3(Regularizer):
    """
    N3 regularizer for embeddings (no time regularization)
    """
    def __init__(self, weight: float):
        super(N3, self).__init__()
        self.weight = weight

    def forward(self, factors,  *args, **kwargs):
        norm = 0
        for f in factors:
            norm += self.weight * torch.sum(torch.abs(f) ** 3)
        return norm / factors[0].shape[0]

class TimeRegularizer(Regularizer, ABC):
    def __init__(self, weight: float, norm: str):
        super(TimeRegularizer, self).__init__()
        self.weight = weight
        self.norm = NORM[norm]
    @abstractmethod
    def time_regularize(self, factors: Tuple[torch.Tensor], *args, **kwargs):
        pass

    def forward(self, factors: Tuple[torch.Tensor], norm, *args, **kwargs):
        ddiff = self.time_regularize(factors, args, kwargs)
        diff = norm(ddiff)
        return self.weight * torch.sum(diff) / (factors.shape[0] - 1)

class SmoothRegularizer(TimeRegularizer):
    def __init__(self, weight: float, norm: str):
        super(SmoothRegularizer, self).__init__(weight, norm)

    def time_regularize(self, factors: Tuple[torch.Tensor]):
        return factors[1:] - factors[:-1]
    def forward(self, factors: Tuple[torch.Tensor], norm, *args, **kwargs):
        return super().forward(factors, norm)

class ExpDecayRegularizer(TimeRegularizer):
    def __init__(self, weight: float, norm: str, decay_factor=1e-1):
        super(ExpDecayRegularizer, self).__init__(weight, norm)
        self.decay_factor = decay_factor
    def time_regularize(self, factors: Tuple[torch.Tensor]):
        ddiff = tuple()
        for i,factor in enumerate(factors):
            if i>0:
                aux = tuple()
                for j in range(i, 0, -1):
                    f = factor[j]*(1-self.decay_factor)**(i-j)
                    aux += (f,)
                past_contrib = sum(aux)
                ddiff += (f-past_contrib,)
        return ddiff

    def forward(self, factors: Tuple[torch.Tensor], norm):
        super().forward(factors, norm)


"""
class Lambda3(Regularizer):
    def __init__(self, weight: float):
        super(Lambda3, self).__init__()
        self.weight = weight

    def forward(self, factors: Tuple[torch.Tensor]):
        ddiff = factor[1:] - factor[:-1]
        rank = int(ddiff.shape[1] / 2)
        diff = torch.sqrt(ddiff[:, :rank]**2 + ddiff[:, rank:]**2)**3
        return self.weight * torch.sum(diff) / (factor.shape[0] - 1)

class L1(Regularizer):
    def __init__(self, weight: float):
        super().__init__()
        self.weight = weight

    def forward(self, factor: Tuple[torch.Tensor]):
        ddiff = factor[1:] - factor[:-1]
        diff = torch.abs(ddiff)
        return self.weight * torch.sum(diff) / (factor.shape[0]-1)

class L2(Regularizer):
    def __init__(self, weight: float):
        super().__init__()
        self.weight = weight

    def forward(self, factor: Tuple[torch.Tensor]):
        ddiff = factor[1:] - factor[:-1]
        diff = (torch.sum(torch.abs(ddiff)**2))**1/2
        return self.weight * torch.sum(diff) / (factor.shape[0]-1)

class F2(Regularizer):
    def __init__(self, weight: float):
        super().__init__()
        self.weight = weight

    def forward(self, factor: Tuple[torch.Tensor]):
        ddiff = factor[1:] - factor[:-1]
        diff = ddiff**2
        return self.weight * torch.sum(diff) / (factor.shape[0]-1)

class N3Temp(Regularizer):
    def __init__(self, weight: float):
        super().__init__()
        self.weight = weight

    def forward(self, factor: Tuple[torch.Tensor]):
        ddiff = factor[1:] - factor[:-1]
        diff = torch.abs(ddiff)**3
        return self.weight * torch.sum(diff) / (factor.shape[0]-1)
"""