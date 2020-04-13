import sys
sys.path.append('..')
import nsf

if len(sys.argv) > 1:
    nsffile = nsf.read(sys.argv[1])
else:
    print('Usage: python3 {} NSFFILE.NSF')
    exit(1)

for c in nsffile.chunks:
    print(c)
