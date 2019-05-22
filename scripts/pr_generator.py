import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import beta

#clopper_pearson
def binom_interval(success, total, confint=0.90):
    quantile = (1 - confint) / 2.
    lower = beta.ppf(quantile, success, total - success + 1)
    upper = beta.ppf(1 - quantile, success + 1, total - success)
    return (lower, upper)

def get_lines(filename):
    file = open(filename,'rU')
    lines = file.readlines()

    file.close()
    positive = 0
    negative = 0
    for l in range(2,len(lines)):
        line = lines[l].split()
            #if float(line[0]) == 0:
            #break
        if line[1] == '1':
            positive +=1
        else:
            negative +=1

    print(positive)
    print(negative)

    fp = 0
    print(fp)
    tp = 0
    fn = positive
    tn = negative
    plist = []
    rlist = []
    llist = []
    ulist = []
    er = []
    ep = []
    
    current = '1'
    for l in range(2,len(lines)):
        line = lines[l].split()
        if float(line[0]) == 0:
            break
        if line[1] == '1':
            tp += 1
            fn -= 1
        else:
            fp += 1
            tn -= 1
        if line[1] != current:
            current = line[1]
            precision = float(tp)/(tp+fp)
            plist.append(precision)
            recall = float(tp)/(tp+fn)
            rlist.append(recall)
        if l%100 == 0:
            lower,upper = binom_interval(tp,tp+fp)
            lower = precision-lower
            upper = upper-precision
            llist.append(lower)
            ulist.append(upper)
            er.append(recall)
            ep.append(precision)




    return rlist, plist, llist,ulist,er,ep
#print(str(recall) + '\t' + str(precision))
rlist,plist,llist,ulist,er,ep = get_lines('dec11_0.75_750_baseline_results_by_dk.list')
x = numpy.array(rlist)
y = numpy.array(plist)
plt.plot(x, y,linewidth=5,color='blue',label='W/O Literature Extracted Genes')


rlist,plist,llist,ulist,er,ep = get_lines('feb10_0.75_750_gadget_results_by_dk.list')
l = numpy.array(llist)
u = numpy.array(ulist)
asym = [l,u]
x = numpy.array(rlist)
y = numpy.array(plist)
rx = numpy.array(er)
py = numpy.array(ep)
plt.errorbar(rx, py, yerr=asym,color='black')
plt.plot(x, y,linewidth=5,color='red',label='With Literature Extracted Genes')
plt.axis([0,1.01,0,1.01])
#red_patch = mpatches.Patch(color='red', label='The red data')
#blue_patch = mpatches.Patch(color='blue',label='The blue data')
plt.legend()
plt.show()
#precisionlist = list(reversed(plist))
#recalllist = list(reversed(rlist))


            
