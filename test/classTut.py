class new():
    def __init__(self, param1, param2):
        self.x = 100
        self.param1 = param1
        self.param2 = param2
        pass
    
    def __test__(self):
        pass
    
    def display(self, data):
        print data

class child(new):
    def __init__(self):
        new(1, 1)
    
    def disp(self, data):
        child.display(self, data)
    
newClass = child()
x = raw_input()

newClass.disp(x)