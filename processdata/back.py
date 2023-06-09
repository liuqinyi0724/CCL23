temptext = []
with open("test_enter2.txt","r") as text: #14744
    l = text.readlines()
    for ch in l:
        ch = str(ch).split()
        if len(ch) == 0:       
            temptext.append("\n")
        else:
            temptext.append(ch[0])


templabel = []
total = 0
with open("result.txt","r") as orilabel: 
    labels = orilabel.readlines()
    for ch in labels:
        ch = ch[:-1]
        if ch == "\n":
            templabel.append("\n")
        else:
            templabel.append(ch)


with open("test_second.txt","w") as final:
    len1 = len(temptext)
    len2 = len(templabel)
    assert len1 == len2
    for i in range(len2):
        ch = temptext[i]
        l = templabel[i]
        if ch == "\n":
            final.write(ch)
        else:
            temp = ch + "\t" + l + "\n"
            final.write(temp)

with open("test_second.txt","r") as bef_concat:
    with open("predict_simplifed.txt","w") as aft_concat:
        # {丞相|OFI}{伯颜|PER}命以所部兵取宁国，
        chline = bef_concat.readlines()
        flag = False # 是否为entity
        chlen = len(chline)
        for i in range(chlen-1):
            samelabel = False # 前后是否为同一label
            ch = chline[i]
            ch = ch.split()
            if len(ch) == 0:
                aft_concat.write("\n")
                continue
            chtext = ch[0]
            chlabel = ch[1]
            aftch = chline[i+1].split()
            aftchlabel = aftch[1] if len(aftch) > 0 else ""
            if aftchlabel != "":
                if aftchlabel == "O":
                    if chlabel == "O":
                        samelabel = True
                else:
                    if chlabel[2:] == aftchlabel[2:]:
                        if aftchlabel[0] != "B":
                            samelabel = True
            # temp = chtext
            if chlabel[0] == "B":
                flag = True
                reallabel = chlabel[2:]
                if samelabel is True:
                    temp = "{" + chtext
                else:
                    temp = "{" + chtext + "|" + reallabel + "}"
            elif chlabel[0] == "I":
                if samelabel is True:
                    temp = chtext
                else:
                    temp = chtext + "|" + reallabel + "}"
                    flag = False
                # if i == 1:
                #     print(temp)
                #     print()
            elif chlabel[0] == "O":    
                temp = chtext

                    
            aft_concat.write(temp)



