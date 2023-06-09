# 繁体转简体
import opencc
converter = opencc.OpenCC('t2s.json')
# res = converter.convert("汉字")
res = []
with open("GuNER2023_train.txt","r") as tranditional_text:
    readlines = tranditional_text.readlines()
    for line in readlines:
        tempres = converter.convert(line)
        with open("train_simplified.txt","a") as simplified_text:
            simplified_text.write(tempres)

with open("GuNER2023_test.txt","r") as tranditional_text:
    readlines = tranditional_text.readlines()
    for line in readlines:
        tempres = converter.convert(line)
        with open("test_simplified.txt","a") as simplified_text:
            simplified_text.write(tempres)
            

