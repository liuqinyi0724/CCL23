templen = []
with open("GuNER2023_test.txt","r") as ori:
    lines = ori.readlines()
    with open("test_enter2.txt","w") as aft:
        for l in lines:
            temp = l[:-1]
            tempnum = len(temp)
            templen.append(tempnum)
            for ch in temp:
                res = ch + "\t" + "O" + "\n"
                aft.write(res)
            aft.write("\n")

print(templen)