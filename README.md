# CCL23
## Getting Started

### Setting up the code environment

```
$ pip install -r requirements.txt
```
### Running

**1. Move into the folder of method you chose**

`cd weighted_fusion_crf`

#### Before you running any shell file, you need to modify the arguments to your own paths or hyper-parameters at first.

**2. Training**

Train a roberta-classical-chinese-large-char based model. 

`bash run_train.sh`

**3. Fine-Tuning**

Fine-tuning from a pretrained NER model.

`bash run_finetune.sh`

**4. Predicting**

Predicting the tags from a pretrained model. 

`bash run_predict.sh`
