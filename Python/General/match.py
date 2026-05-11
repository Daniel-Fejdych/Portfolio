def getMatches(word1, word2):
    res2d = [["" for i in range(len(word1) + 1)] for ii in range(len(word2) + 1)]
    for i in range(1, len(word1) + 1):
        for ii in range(1, len(word2) + 1):
            if (word1[i-1] == word2[ii-1]):
                res2d[ii][i] = res2d[ii - 1][i - 1] + word1[i-1]
            else:
                res2d[ii][i] = max(res2d[ii][i - 1], res2d[ii - 1][i])
    return res2d[len(word2)][len(word1)]
while (input("Type e to exit: ") != "e"):
    print(getMatches(input("\nFirst word:\n"), input("\nSecond word:\n")))
