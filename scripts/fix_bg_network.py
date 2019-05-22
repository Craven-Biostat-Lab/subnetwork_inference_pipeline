import os
import sys

#usage python fix_bg_network.py inputfilename outputfilename (can be the same)
def main():
    inputfilename = sys.argv[1]
    outfilename = sys.argv[2]
    
    file = open(inputfilename,'rU')
    lines = file.readlines()
    file.close()

    outfile = open(outfilename,'w')

    for l in lines:
        if 'REACT' in l:
            print(l)
            continue
        else:
            outfile.write(l)

    outfile.close()

if __name__ == "__main__":
    main()
