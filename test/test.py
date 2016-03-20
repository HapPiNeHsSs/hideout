def helloWorld(param1):
    var = 1
    var = "sdf"
    var2 = 3
    #varDict = dict()
    varDict = {"val3":{"key1":"val"},\
               "val4":"123"}
    #varlist = list()
    varTuple = ("1", "1" ,2, "1",{"dict":123})
    #varList.insert(1, "test")
    #varList.pop(1)
    listx = list(varTuple)
    #print varList[1:2]
    print listx
    
    for x in listx:
        listx.append(x)
    
    print listx
    
    x = 0
    while x != 10:
        x+=1
        print x
    
    #varDict["val1"] = 45
    #varDict["val2"] = "string"
    #print varDict["val3"]["key1"]
    #print "Hello World %s %s %s" % (var, var2, param1)
    if var2==3 and var==1 or 1==1:
        print "Hello World Again"


helloWorld("par")