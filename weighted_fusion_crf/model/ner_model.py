from typing import List, Any

from pytorch_lightning import LightningModule
# import pytorch_lightning.core.lightning as pl

import torch
import torch.nn.functional as F
import numpy as np

from allennlp.modules import ConditionalRandomField
from allennlp.modules.conditional_random_field import allowed_transitions
from torch import nn
from torch.utils.data import DataLoader
from transformers import get_linear_schedule_with_warmup, AutoModel

from log import logger
from utils.metric import SpanF1
from utils.reader_utils import extract_spans

import pdb


class NERBaseAnnotator(LightningModule):
# class NERBaseAnnotator(pl.LightningModule):
    def __init__(self,
                 train_data=None,
                 dev_data=None,
                 lr=1e-5,
                 dropout_rate=0.1,
                 batch_size=16,
                 tag_to_id=None,
                 stage='fit',
                 pad_token_id=1,
                 encoder_model='xlm-roberta-large',
                 num_gpus=1):
        super(NERBaseAnnotator, self).__init__()

        self.train_data = train_data
        self.dev_data = dev_data

        self.training_step_outputs = []
        self.validation_step_outputs = []
        self.test_step_outputs = []

        self.id_to_tag = {v: k for k, v in tag_to_id.items()}
        self.tag_to_id = tag_to_id
        self.batch_size = batch_size

        self.stage = stage
        self.num_gpus = num_gpus
        self.target_size = len(self.id_to_tag)

        # set the default baseline model here
        self.pad_token_id = pad_token_id

        self.encoder_model = encoder_model
        self.encoder = AutoModel.from_pretrained(encoder_model, return_dict=True)

        rnn_dim = self.encoder.config.hidden_size // 2
        self.feature_embed = nn.Linear(self.target_size, self.encoder.config.hidden_size)
        self.birnn = nn.LSTM(self.encoder.config.hidden_size, rnn_dim, num_layers=1, bidirectional=True,
                             batch_first=True)
        self.w_omega = nn.Parameter(torch.Tensor(self.encoder.config.hidden_size*2, 1))  # 用于门机制学习的矩阵
        nn.init.uniform_(self.w_omega, -0.1, 0.1)

        self.feedforward = nn.Linear(in_features=self.encoder.config.hidden_size, out_features=self.target_size)
        self.crf_layer = ConditionalRandomField(num_tags=self.target_size,
                                                constraints=allowed_transitions(constraint_type="BIO", # iob
                                                                                labels=self.id_to_tag))

        self.lr = lr
        self.dropout = nn.Dropout(dropout_rate)

        self.span_f1 = SpanF1()
        self.setup_model(self.stage)
        self.save_hyperparameters('pad_token_id', 'encoder_model')

    def setup_model(self, stage_name):
        if stage_name == 'fit' and self.train_data is not None:
            # Calculate total steps
            train_batches = len(self.train_data) // (self.batch_size * self.num_gpus)
            self.total_steps = 50 * train_batches

            self.warmup_steps = int(self.total_steps * 0.01)

    def collate_batch(self, batch):
        batch_ = list(zip(*batch))
        tokens, masks, gold_spans, tags, feature_input, head_pos = batch_[0], batch_[1], batch_[2], batch_[3], batch_[
            4], batch_[5]

        max_len = max([len(token) for token in tokens])
        token_tensor = torch.empty(size=(len(tokens), max_len), dtype=torch.long).fill_(self.pad_token_id)
        tag_tensor = torch.empty(size=(len(tokens), max_len), dtype=torch.long).fill_(self.tag_to_id['O'])
        mask_tensor = torch.zeros(size=(len(tokens), max_len), dtype=torch.bool)
        feature_tensor = torch.zeros(size=(len(tokens), max_len, self.target_size), dtype=torch.float32)

        for i in range(len(tokens)):
            token_tensor[i] = tokens[i]
            tag_tensor[i] = tags[i]
            mask_tensor[i] = masks[i]
            feature_tensor[i] = feature_input[i]

        return token_tensor, tag_tensor, mask_tensor, gold_spans, feature_tensor, head_pos

    def configure_optimizers(self):
        optimizer_grouped_parameters = [{'params': self.encoder.parameters(), 'lr': self.lr},
                                        {'params': self.feedforward.parameters(), 'lr': self.lr},
                                        {'params': self.crf_layer.parameters(), 'lr': self.lr * 100},
                                        {'params': self.feature_embed.parameters(), 'lr': self.lr * 10},
                                        {'params': self.birnn.parameters(), 'lr': self.lr * 10},
                                        {'params': self.w_omega, 'lr': self.lr * 10}]
        optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=self.lr, weight_decay=0.01)
        if self.stage == 'fit':
            scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=self.warmup_steps,
                                                        num_training_steps=self.total_steps)
            scheduler = {
                'scheduler': scheduler,
                'interval': 'step',
                'frequency': 1
            }
            return [optimizer], [scheduler]
        return [optimizer]

    def train_dataloader(self):
        loader = DataLoader(self.train_data, batch_size=self.batch_size, collate_fn=self.collate_batch, num_workers=10)
        return loader

    def val_dataloader(self):
        if self.dev_data is None:
            return None
        loader = DataLoader(self.dev_data, batch_size=self.batch_size, collate_fn=self.collate_batch, num_workers=10)
        return loader

    def on_train_epoch_end(self) -> None:
        pred_results = self.span_f1.get_metric(True)
        # avg_loss = np.mean(self.training_step_outputs)
        avg_loss = torch.stack(self.training_step_outputs).mean()
        self.log_metrics(pred_results, loss=avg_loss, suffix='', on_step=False, on_epoch=True)
        self.training_step_outputs.clear() # free memory

    def on_validation_epoch_end(self) -> None:
        pred_results = self.span_f1.get_metric(True)
        avg_loss = torch.stack(self.validation_step_outputs).mean()
        self.log_metrics(pred_results, loss=avg_loss, suffix='val_', on_step=False, on_epoch=True)
        self.validation_step_outputs.clear()

    def validation_step(self, batch, batch_idx):
        output = self.perform_forward_step(batch)
        self.validation_step_outputs.append(output['loss'])
        self.log_metrics(output['results'], loss=output['loss'], suffix='val_', on_step=True, on_epoch=False)
        return output

    def training_step(self, batch, batch_idx):
        output = self.perform_forward_step(batch)
        self.training_step_outputs.append(output['loss'])
        self.log_metrics(output['results'], loss=output['loss'], suffix='', on_step=True, on_epoch=False)
        return output

    def log_metrics(self, pred_results, loss=0.0, suffix='', on_step=False, on_epoch=True):
        for key in pred_results:
            self.log(suffix + key, pred_results[key], on_step=on_step, on_epoch=on_epoch, prog_bar=True, logger=True)

        self.log(suffix + 'loss', loss, on_step=on_step, on_epoch=on_epoch, prog_bar=True, logger=True)

    def perform_forward_step(self, batch, mode=''):
        tokens, tags, token_mask, metadata, feature_input, head_pos = batch
        if mode == 'predict':
            _device = self.device
            tokens = tokens.to(_device)
            tags = tags.to(_device)
            token_mask = token_mask.to(_device)
            feature_input = feature_input.to(_device)
        batch_size = tokens.size(0)
        # pdb.set_trace()

        embedded_text_input = self.encoder(input_ids=tokens, attention_mask=token_mask)
        embedded_text_input = embedded_text_input.last_hidden_state
        embedded_text_input = self.dropout(F.leaky_relu(embedded_text_input))

        feature_express_linear = self.feature_embed(feature_input)
        feature_express_rnn, _ = self.birnn(feature_express_linear)
        We= torch.sigmoid(torch.matmul(torch.cat([embedded_text_input,feature_express_rnn],2),self.w_omega))

        embedded_text_input = We*embedded_text_input + (1-We)*feature_express_rnn

        # project the token representation for classification
        token_scores = self.feedforward(embedded_text_input)

        # compute the log-likelihood loss and compute the best NER annotation sequence
        output = self._compute_token_tags(token_scores=token_scores, tags=tags, token_mask=token_mask,
                                          metadata=metadata, batch_size=batch_size, head_pos=head_pos, mode=mode)
        return output

    def _compute_token_tags(self, token_scores, tags, token_mask, metadata, batch_size, head_pos, mode=''):
        # compute the log-likelihood loss and compute the best NER annotation sequence
        loss = -self.crf_layer(token_scores, tags, token_mask) / float(batch_size)
        best_path = self.crf_layer.viterbi_tags(token_scores, token_mask) # logits-prediction, mask-prediction_mask

        pred_results, pred_tags = [], []
        for i in range(batch_size):
            false_tag_seq, _ = best_path[i]
            assert len(head_pos[i]) == len(false_tag_seq)
            tag_seq = []
            for ifhead, f_tag in zip(head_pos[i], false_tag_seq):
                if ifhead == 1:
                    tag_seq.append(f_tag)
            pred_tags.append([self.id_to_tag[x] for x in tag_seq])
            pred_results.append(extract_spans([self.id_to_tag[x] for x in tag_seq if x in self.id_to_tag]))

        self.span_f1(pred_results, metadata)
        output = {"loss": loss, "results": self.span_f1.get_metric()}

        if mode == 'predict':
            output['token_tags'] = pred_tags

        return output

    def predict_tags(self, batch):
        pred_tags = self.perform_forward_step(batch, mode='predict')['token_tags']

        return pred_tags 
