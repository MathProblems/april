import signal
import sys
import json
import jsonrpclib
import entity as ENTITY
from entity import entity
import setmaker
import pickle
sys.path.insert(0, './treebuilder')
from Solver import Solver
from sympy.solvers.solvers import solve

class StanfordNLP:
    def __init__(self, port_number=8080):
        self.server = jsonrpclib.Server("http://localhost:%d" % port_number)

    def parse(self, text):
        return json.loads(self.server.parse(text))

nlp = StanfordNLP()


def training(trips,problem,target):
    #this function take the trips and creates positive and negative training instances from them
    
    texamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    for op,a,b in trips:
        vec = ENTITY.vector(a,b,problem,target)
        texamples[op][0].append(vec)

    return texamples

def cleannum(n):
    return ''.join([x for x in n if x.isdigit() or x=='.' or x=='x'])

def mkgoodtrain():
    wps = open("../all_a.txt").readlines()
    answs = open("../all_aa.txt").readlines()
    goodtrain = open("goodp.txt",'w')
    goodtraina = open("gooda.txt",'w')

    for k in range(len(wps)):
        print(k)
        problem = wps[k].lower()
        try:
            story = nlp.parse(problem)
            numbs = setmaker.setmaker(story)
            numlist = [cleannum(v.num) for k,v in numbs if setmaker.floatcheck(v.num)]
            numlist = [x for x in numlist if x!='']
        except:
            continue
        print(numlist)
        signal.signal(signal.SIGALRM, kill)
        signal.alarm(10)
        try:
            ST = Solver(numlist)
            answers = ST.solveEquations(float(answs[k]))

            print(answers)
        except:
            continue
        if answers != []:
            goodtrain.write(problem)
            goodtraina.write(answs[k])
    goodtrain.close();goodtraina.close()



def kill(signum, frame):
    raise Exception("end of time")

def dotrain():
    wps = open("data/trainingp.txt").readlines()
    answs = open("data/traininga.txt").readlines()
    bigtexamples = {x:([],[]) for x in ["+","*",'/','-','=']}
    problematic = open('data/nogoodtrainproblems','w')

    for k in range(len(wps)):
        print(k)
        problem = wps[k].lower()
        story = nlp.parse(problem)
        numbs = setmaker.setmaker(story)
        numlist = [(cleannum(v.num),v) for k,v in numbs if setmaker.floatcheck(v.num) or v.num=='x']
        numlist = [x for x in numlist if x[0]!='']
        allnumbs = {str(v.num):v for k,v in numbs if setmaker.floatcheck(v.num) or v.num=='x'}
        if 'x' not in allnumbs:
            problematic.write('no x :'+problem); continue
            

        objs = {k:(0,v) for k,v in numlist}

        print('start solving')
        print(numlist)
        if len(numlist)<2:
            problematic.write("not enough numbers : "+problem);continue
            
        ST = Solver([x[0] for x in numlist if x[0]!='x'])
        answers = ST.solveEquations(float(answs[k]))
        print('done solving')
        #filter out where = in middle if simpler eq exists
        simpleranswers = [x for x in answers if x.split(" ")[1] == '=' or x.split(" ")[-2]=="="]
        if not answers:
            continue
        if simpleranswers:
            answers = simpleranswers
        else:
            print(answers)
            problematic.write("not simple : "+problem);continue

        answervals = [x for x in answers[0].split(" ") if x not in ['+','-','/','=',')','(','*']]
        numvals = [x[0] for x in numlist if x[0] in answervals]
        xidx = numvals.index("x")
        rightidx = [i for i,x in enumerate(answers) if [z for z in x.split(" ") if z not in ['+','-','/','=',')','(','*']].index('x')==xidx]
        xrightanswers = [answers[i] for i in rightidx]
        if xrightanswers:
            answers = xrightanswers

        for j,eq in enumerate(answers):
            trips = []
            print(j,eq)
            l,r = [x.strip().split(' ') for x in eq.split('=')]
            
            compound = l if len(r)==1 else r
            simplex = l if len(l)==1 else r
            target = simplex[0]
            target = (target,objs[target])

            #find innermost parens?
            while len(compound)>1:
                if "(" in compound:
                    rpidx = (len(compound) - 1) - compound[::-1].index('(')
                    lpidx = rpidx+compound[rpidx:].index(")")
                    subeq = compound[rpidx+1:lpidx]
                    substr = "("+''.join(subeq)+")"
                    compound = compound[:rpidx]+[substr]+compound[lpidx+1:]
                else:
                    subeq = compound[0:3]
                    substr = "("+''.join(subeq)+")"
                    compound = [substr]+compound[3:]
                if True:
                    p,op,e = subeq
                    #print(p,op,e)
                    p = objs[p]
                    e = objs[e]
                    op = op.strip()
                    trips.append((op,p,e))
                    pute = (0,setmaker.combine(p[1],e[1],op))
                    #print("OPERATION SELECTED: ",op)
                    #p.details()
                    #e.details()
                    #print(substr,pute[1].num)
                    objs[substr]=pute
                if pute == -1:
                    exit()
            if simplex == l:
                trips.append(("=",objs[simplex[0]],objs[compound[0]]))
            else:
                trips.append(("=",objs[compound[0]],objs[simplex[0]]))
            t = training(trips,problem,target)
            for op in t:
                bigtexamples[op][0].extend(t[op][0])
                bigtexamples[op][1].extend(t[op][1])
            print(op,len(bigtexamples[op][0]))
    pickle.dump(bigtexamples,open('data/training.pickle','wb'))




            




if __name__=="__main__":
    dotrain()



else:
    exit()
    #if __name__ == "__main__":
    
    raw_counts = {x:" " for x in ["+","*"]}
    if len(sys.argv)<2:
        print("args");exit()
    if sys.argv[1]=='a':
        f2 = open("data/4.7.a",'wb')
        wps = open('add.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('sub.problems').readlines()])
        wps.extend([x for x in open('mult.problems').readlines()])
        wps.extend([x for x in open('div.problems').readlines()])
    elif sys.argv[1]=='s':
        f2 = open("data/4.7.s",'wb')
        wps = open('sub.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('add.problems').readlines()])
        wps.extend([x for x in open('mult.problems').readlines()])
        wps.extend([x for x in open('div.problems').readlines()])
    elif sys.argv[1]=='m':
        f2 = open("data/4.7.m",'wb')
        wps = open('mult.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('add.problems').readlines()])
        wps.extend([x for x in open('sub.problems').readlines()])
        wps.extend([x for x in open('div.problems').readlines()])
    elif sys.argv[1]=='d':
        f2 = open("data/4.7.d",'wb')
        wps = open('div.problems').readlines()
        addlen = len(wps)
        wps.extend([x for x in open('add.problems').readlines()])
        wps.extend([x for x in open('mult.problems').readlines()])
        wps.extend([x for x in open('sub.problems').readlines()])
    pos = []
    neg = []
    texamples = {x:([],[],[]) for x in ["+","*"]}
    for j in range(len(wps)):
        print(wps[j])
        problem = wps[j]
        problem = problem.lower()
        story = nlp.parse(problem)
        numbs = setmaker.setmaker(story)
        allnumbs = {str(v.num):v for k,v in numbs if setmaker.floatcheck(v.num)}
        xes = [x[1] for x in numbs if x[1].num == 'x']
        if xes:
            allnumbs['x']=xes[0]
        print(allnumbs)


        #print(allnumbs.keys())
        prblmnumbs = [v.num for k,v in numbs if setmaker.floatcheck(v.num)]

        if len(prblmnumbs)<2: continue
        if j < addlen:
            equation = str(prblmnumbs[0])+" + "+str(prblmnumbs[1])+" = x"
        else:
            equation = str(prblmnumbs[0])+" * "+str(prblmnumbs[1])+" = x"

        objs = {k:(0,v) for k,v in numlist}

        #parse eq:
        old_op = None
        parens = False
        trips = []
        cmplx,simple = equation.split("=")
        simple = simple.strip()
        cmplx = cmplx.split()
        i=0
        state = []
        opstack = []
        print(cmplx)

        while i<len(cmplx):
            c = cmplx[i]
            #print(i,c,state)
            #raw_input()
            if state == [] and not (setmaker.floatcheck(c) or c=='x'): 
                i+=1; continue

            if state == [] and (setmaker.floatcheck(c) or c=='x'):
                state = [(c,allnumbs[c])]
                i+=1;continue

            if c in ["+","-","/","*"]:
                op = c
                c = state[-1]
                d = cmplx[i+1]
                if d == "(":
                    j=1
                    while not setmaker.floatcheck(d):
                        d = cmplx[i+j]
                        j+=1
                    opstack.append((op,state.index(c)))
                    trips.append(("No Operation",c,(d,allnumbs[d])))
                    state.append((d,allnumbs[d]))
                    i+=j
                else:
                    trips.append((op,c,(d,allnumbs[d])))
                    state = state[:-1]
                    state.append((c[0]+op+d,setmaker.combine(c[1],allnumbs[d],op)))
                    #print(i,c,state)
                    i+=2
                    continue
            if c == ")":
                if opstack == []:
                    i+=1
                    continue
                else:
                    op,c = opstack.pop()
                    c = state[c]
                    d = state[-1]
                    # this is c,d rather than d,c above because 
                    # perhaps the operation is more based on the first sentence?
                    trips.append((op,c,d))
                    state = [x for x in state[:-1] if x!= c]
                    state.append((c[0]+op+d[0],setmaker.combine(c[1],d[1],op)))
                    i+=1

        problem = problem.split(". ")[-1]
        target = allnumbs['x'].ent if 'x' in allnumbs else "???"
        tmpexamples = training(trips,problem,target)
        for k in texamples:
            texamples[k][0].extend(tmpexamples[k][0])
            texamples[k][1].extend(tmpexamples[k][1])
            texamples[k][2].append(problem)


    #Do stuff with the training data
    pickle.dump(texamples,f2)
    #for 2.11 stuff, exit and run diff code:
    exit()
    #build_d(texamples)

