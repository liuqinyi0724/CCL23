from typing import List, Dict, Tuple

I_PRE = "I-"
B_PRE = "B-"
S_PRE = "S-"
E_PRE = "E-"
O = "O"

def convert_iobes(labels: List[str]) -> List[str]:
	"""
	Use IOBES tagging schema to replace the IOB tagging schema in the instance
	:param insts:
	:return:
	"""
	for pos in range(len(labels)):
		curr_entity = labels[pos]
		if pos == len(labels) - 1:
			if curr_entity.startswith(B_PRE):
				labels[pos] = curr_entity.replace(B_PRE, S_PRE)
			elif curr_entity.startswith(I_PRE):
				labels[pos] = curr_entity.replace(I_PRE, E_PRE)
		else:
			next_entity = labels[pos + 1]
			if curr_entity.startswith(B_PRE):
				if next_entity.startswith(O) or next_entity.startswith(B_PRE):
					labels[pos] = curr_entity.replace(B_PRE, S_PRE)
			elif curr_entity.startswith(I_PRE):
				if next_entity.startswith(O) or next_entity.startswith(B_PRE):
					labels[pos] = curr_entity.replace(I_PRE, E_PRE)
	return labels

restext = []
reslabels = []
resiobes = []

with open("GuNER2023_train.txt","r") as ori_text: # with open("train_simplified.txt","r") as ori_text
    pretext = ori_text.readlines()
    for line in pretext:
        # 帝曰：「{玄龄|PER}、{如晦|PER}不以勋旧进，特其才可与治天下者，{师合|PER}欲以此离间吾君臣邪？」斥岭表。\n
        templen = len(line)
        text = []
        labels = []
        flag = False # 是否为实体中内容
        entitylen = 0
        for i in range(templen-1):
            ch = line[i]
            if ch == '{':
                startidx = i+1 #实体开始=startidx
                flag = True
            elif ch == '|':
                entityboundary = i
                tempch = line[startidx:entityboundary]
                entitylen = len(tempch)
                for t in tempch:
                    text.append(t)
            elif ch == '}':
                endidx = i #实体结束=endidx-1 因为[:]切片原因可直接取endidx
                templabel = str(line[entityboundary+1:endidx])
                for i in range(entitylen):
                    if i == 0:
                        label = 'B-' + templabel
                    else:
                        label = 'I-' + templabel
                    labels.append(label)
                flag = False
                entitylen = 0
            else:
                if flag == True:
                    continue
                if flag == False:
                    text.append(ch)
                    labels.append("O")
                startidx, endidx, entityboundary = 0, 0, 0
            
        assert len(text) == len(labels)
        restext.append(text)
        reslabels.append(labels)
        assert len(restext) == len(reslabels)

with open("bio_train_t.conll","w") as line_train:
    templen = len(restext)
    for i in range(templen):
        text, label = restext[i], reslabels[i]
        assert len(text) == len(label)
        len2 = len(text)
        for j in range(len2):
            temp = text[j] + "\t" + label[j] + "\n"
            line_train.writelines(temp)
        line_train.writelines("\n")

with open("GuNER2023_test.txt","r") as ori:
    lines = ori.readlines()
    with open("test_enter_t.conll","w") as aft:
        for l in lines:
            temp = l[:-1]
            for ch in temp:
                res = ch + "\t" + "O" + "\n"
                aft.write(res)
            aft.write("\n")
