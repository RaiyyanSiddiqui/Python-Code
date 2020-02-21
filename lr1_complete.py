class Closure:
    def __init__(self, parent, tokens, dIdx, lookahead):
        self.parent = parent
        self.tokens = tokens
        self.dotIndex = dIdx
        self.lookahead = lookahead
    @classmethod
    def fromRule(cls, parent, tokens, lookahead = None):
        if(lookahead == None): lookahead = set()
        return Closure(parent, tokens, 0, lookahead)

    def clone(self):
        c = Closure(self.parent, self.tokens[:], self.dotIndex, self.lookahead.copy())
        return c
    
    def __eq__(self, other):
        if other is self:
            return True
        elif not(isinstance(other, Closure)):
            return False
        return (self.parent == other.parent and 
                self.tokens == other.tokens and 
                self.dotIndex == other.dotIndex and
                self.lookahead == other.lookahead);
    
    def baseEquals(self, other):
        if(self.__eq__(other)):
            return True
        else:
            return (self.parent == other.parent and 
                    self.tokens == other.tokens and 
                    self.dotIndex == other.dotIndex);
                
    def __str__(self):
        out = self.parent + " -> "
        for idx, t in enumerate(self.tokens):
            out += ("." if(idx == self.dotIndex) else " ") + t
        if(len(self.tokens) == self.dotIndex): out += "."
        if(len(self.lookahead) == 0): out += ", $"
        for idx, e in enumerate(self.lookahead):
            out += ("/" if idx != 0 else ", ") + e
        return out

class State:
    def __init__(self, num, kernel, goto):
        self.num = num
        self.goto = {}
        if goto != None:
            self.goto.update({goto[0] : goto[1]})
        self.kernel = kernel # relevant closure
        self.closures = [] # branching closures, (getMatchingClosures)
        
    def __eq__(self, other):
        if other is self:
            return true
        elif not(isinstance(other, State)):
            return false
        return (self.kernel == other.kernel and
                self.closures == other.closures)

    def __str__(self):
        out = str(self.num)
        out += " " + str(self.goto) + "\n"
        for c in self.closures:
            out += "  " + str(c) + "\n"
        return out

class Table:
    def __init__(self, start):
        self.start = start
        self.states = []
        self.closures = []
        
    def printDebug(self):
        if(len(self.closures) == 0): return
        self.printRules()
        print(self.firstAll(self.closures[0].parent))
        print(self.first(self.closures[0].parent))
        print(self)
    def printRules(self):
        if(len(self.closures) == 0): return
        for clo in self.closures:
            print(clo)
    
    def __str__(self):
        out = ""
        for s in self.states:
            out += str(s) + "\n"
        return out
    def addClosure(self, cl):
        self.closures.append(cl)
    # TODO, invalid token firstAll(t) returns an array: [t,], when
    #   it might be preferable to return empty array in that case
    def firstAll(self, nonterminal, parsed = None):
        if(parsed == None): parsed = []
        out = []
        if(nonterminal in parsed): # already handled
            return out
        parsed.append(nonterminal)
        if not(nonterminal.isupper()): # is terminal
            return [nonterminal]
        out.append(nonterminal)
        for c in self.closures: # find relevant branching closures
            if(c.parent == nonterminal):
                token = c.tokens[0]
                if token.isupper(): # if internal token is nonterminal, keep going deeper
                    out += self.firstAll(token, parsed)
                elif not(token in out): # if nonterminal not already handled
                    out.append(token)
        return out
        
    # S -> X X, X -> X a, X -> b, issues with lookahead
    def getLookahead(self, closure):
        reference = closure.tokens[(closure.dotIndex + 1):]
        out = set()
        for r in reference:
            if r == chr(0): continue
            out.update(self.first(r))
        return out if len(out) > 0 else closure.lookahead
    
    def getClosuresLookahead(self, closure, out = None):
        if(out == None): out = []
        if(closure in out): # already handled
            return out
        else: # check for matching closures with different lookaheads
            for outClosure in out:
                if(closure.baseEquals(outClosure)):
                    print("baseMatch: ", closure, " - ", outClosure)
                    outClosure.lookahead.update(closure.lookahead)
                    return out
        out.append(closure)
        if(closure.dotIndex == len(closure.tokens)): # out of index
            return out
        token = closure.tokens[closure.dotIndex]
        
        if(token.islower()): 
            return out
        newLookahead = self.getLookahead(closure)
        print("|||", closure, " - ", newLookahead)
        for c in self.closures: # find relevant branching closures
            if(c.parent == token):
                newC = c.clone()
                newC.lookahead = newLookahead.copy()
                self.getClosuresLookahead(newC, out)
        return out
        
    def first(self, nonterminal):
        result = self.firstAll(nonterminal)
        out = []
        for r in result: 
            if(r.islower()): out.append(r)
        return out
        
    def goto(self, token, sNum):
        pass
       
    def genStates(self, closure, prev = None): # closure == s.kernel
    
        s = State(len(self.states), closure, prev) # create state
        # load state and apply lookaheads
        s.closures = self.getClosuresLookahead(closure)
        for st in self.states: # handle loops (connected to itself)
            if(st == s): # overloaded __eq__
                st.goto.update({st.num : st.kernel.tokens[st.kernel.dotIndex - 1]})
                return
        self.states.append(s)
        if(closure.dotIndex == len(closure.tokens)):
            return
        # transitions
        for closure_temp in s.closures:
            cl = closure_temp.clone()
            
            cl.dotIndex += 1
            self.genStates(cl, (s.num, cl.tokens[cl.dotIndex - 1]) )
    
def main():
    tbl = Table('S\'')
    tbl.addClosure(Closure.fromRule('S\'', ['S']))

    tbl.addClosure(Closure.fromRule('S', ['X','X']))
    tbl.addClosure(Closure.fromRule('X', ['a','X']))
    tbl.addClosure(Closure.fromRule('X', ['b']))
    
    print('\n\n\t\tTEST PROGRAM\n\n')
    tbl.genStates(tbl.closures[0])
    tbl.printDebug()
    
    del(tbl)
    
    print("\n\nFill table with rules, type quit to quit.")
    print('Format: TOKENNAME -> TOKEN token token TOKEN etc')
    tbl = loadTable()
    if(tbl != None):
        tbl.genStates(tbl.closures[0])
        tbl.printDebug()
def loadTable():
    isFirstLoop = True
    tbl = None
    while(True):
        rule = input('Enter rule: ')
        rule = rule.split(' ')
        if(rule[0] == 'quit'):
            break
        elif(isFirstLoop):
            tbl = Table(rule[0])
            isFirstLoop = False
        tbl.addClosure(Closure.fromRule(rule[0], rule[2:]))
    return tbl

if __name__ == "__main__":
    print('issues with lookahead')
    main()
input('Enter any key to quit...')

