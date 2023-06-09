# 简转繁体
import opencc
converter = opencc.OpenCC('s2t.json')
# res = converter.convert("汉字")
res = []
with open("BOOK.txt","r") as simplified_text: #PER、OFI
    readlines = simplified_text.readlines()
    for line in readlines:
        tempres = converter.convert(line)
        with open("BOOK_t.txt","a") as tranditional_text:
            tranditional_text.write(tempres)
