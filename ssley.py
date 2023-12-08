# Copyright (c) James Chapman, Lennie Wells
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.


import torch
from torch import nn

import resnet
from main_ssley import Projector, FullGatherLayer


class SSLEY(nn.Module):
    def __init__(self, args):
        super().__init__()
        self.args = args
        self.num_features = int(args.mlp.split("-")[-1])
        self.backbone, self.embedding = resnet.__dict__[args.arch](
            zero_init_residual=True
        )
        self.projector = Projector(args, self.embedding)

    def forward(self, x, y):
        x = self.projector(self.backbone(x))
        y = self.projector(self.backbone(y))

        x = torch.cat(FullGatherLayer.apply(x), dim=0)
        y = torch.cat(FullGatherLayer.apply(y), dim=0)
        x = x - x.mean(dim=0)
        y = y - y.mean(dim=0)

        C = 2*(x.T @ y) / (self.args.batch_size - 1)
        V = (x.T @ x) / (self.args.batch_size - 1) + (y.T @ y) / (self.args.batch_size - 1)

        loss = -2*torch.trace(C)+torch.trace(V@V)
        return loss