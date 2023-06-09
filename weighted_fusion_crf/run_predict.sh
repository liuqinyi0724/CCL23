#!/bin/bash
export CUDA_VISIBLE_DEVICES=1

REPO=$PWD

LAN=${1:-"zh"}
ENCODER_MODEL=${2:-"KoichiYasuoka/roberta-classical-chinese-large-char"}
DATA_DIR=${3:-"$REPO/data/"}
OUT_DIR=${4:-"$REPO/output/"}

model_name="ner_${LAN}"
base_dir=${REPO}/../
test_file=${DATA_DIR}/${LAN}_test.conll
gazetteer_path=${base_dir}/gazetteer_demo/${LAN}

model_file_path=${REPO}/output/ner_${LAN}/lightning_logs/version_2/checkpoints/ner_zh_final.ckpt

# TRANSFORMERS_OFFLINE=1
# HF_DATASETS_OFFLINE=1

python -m do_predict --test "$test_file" --gazetteer "$gazetteer_path" --out_dir "$OUT_DIR" --model_name "$model_name" --gpus 1 \
                                    --max_length 256 --encoder_model "$ENCODER_MODEL" --model "$model_file_path" --batch_size 1
