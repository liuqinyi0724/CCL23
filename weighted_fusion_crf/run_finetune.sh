#!/bin/bash
export CUDA_VISIBLE_DEVICES=1

REPO=$PWD

LAN=${1:-"zh"}
ENCODER_MODEL=${2:-"KoichiYasuoka/roberta-classical-chinese-large-char"}
DATA_DIR=${3:-"$REPO/data/"}
OUT_DIR=${4:-"$REPO/output/"}

model_name="ner_${LAN}"
base_dir=${REPO}/../
train_file=${DATA_DIR}/${LAN}_train.conll
dev_file=${DATA_DIR}/${LAN}_dev.conll
gazetteer_path=${base_dir}/gazetteer_demo/${LAN}

ckpt_file_path=${REPO}/output/ner_${LAN}/lightning_logs/version_1/checkpoints/ner_zh_final.ckpt

python -m fine_tune --train "$train_file" --dev "$dev_file" --test "$test_file" --gazetteer "$gazetteer_path" \
                           --out_dir "$OUT_DIR" --model_name "$model_name" --gpus 1 --epochs 15 --encoder_model "$ENCODER_MODEL" \
                           --max_length 256 --model "$ckpt_file_path"  --batch_size 16 --lr 0.00001

