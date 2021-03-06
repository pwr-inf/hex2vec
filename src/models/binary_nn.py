import torch
from torch import nn
import torch.nn.functional as F
import pytorch_lightning as pl
from typing import List, Tuple
from torchmetrics.functional import f1

class BinaryNN(pl.LightningModule):
    def __init__(self, encoder_sizes):
        super().__init__()

        def create_layers(sizes: List[Tuple[int]]) -> nn.Sequential:
            layers = []
            for i, (input_size, output_size) in enumerate(sizes):
                linear = nn.Linear(input_size, output_size)
                nn.init.xavier_uniform_(linear.weight)
                layers.append(nn.Linear(input_size, output_size))
                if i != len(sizes)-1:
                    layers.append(nn.ReLU())
            return nn.Sequential(*layers)
        
        sizes = list(zip(encoder_sizes[:-1], encoder_sizes[1:]))
        self.encoder = create_layers(sizes)


    def forward(self, Xt: torch.Tensor, Xc: torch.Tensor):
        Xt_em = self.encoder(Xt)
        Xc_em = self.encoder(Xc)
        scores = torch.mul(Xt_em, Xc_em).sum(dim=1)
        return scores
    
    def predict(self, Xt: torch.Tensor, Xc: torch.Tensor):
        probas = F.sigmoid(self(Xt, Xc))
        return probas

    def training_step(self, batch, batch_idx):
        Xt, Xc, Xn, y_pos, y_neg, *_ = batch
        scores_pos = self(Xt, Xc)
        scores_neg = self(Xt, Xn)

        scores = torch.cat([scores_pos, scores_neg])
        y = torch.cat([y_pos, y_neg])

        loss = F.binary_cross_entropy_with_logits(scores, y)
        f_score = f1(F.sigmoid(scores), y.int())
        self.log('train_loss', loss, on_step=True, on_epoch=True)
        self.log('train_f1', f_score, on_step=True, on_epoch=True)
        return loss
    
    def validation_step(self, batch, batch_idx):
        Xt, Xc, Xn, y_pos, y_neg, *_ = batch
        scores_pos = self(Xt, Xc)
        scores_neg = self(Xt, Xn)

        scores = torch.cat([scores_pos, scores_neg])
        y = torch.cat([y_pos, y_neg])

        loss = F.binary_cross_entropy_with_logits(scores, y)
        f_score = f1(F.sigmoid(scores), y.int())
        self.log('val_loss', loss, on_step=True, on_epoch=True)
        self.log('val_f1', f_score, on_step=True, on_epoch=True)
        return loss

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer
