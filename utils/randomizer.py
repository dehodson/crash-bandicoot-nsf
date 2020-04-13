import sys
sys.path.append('..')
import nsf
import random

if len(sys.argv) > 1:
    nsffile = nsf.read(sys.argv[1])
else:
    print('Usage: python3 {} NSFFILE.NSF')
    exit(1)

# Randomizer
boxtypes = [0, 2, 3, 5, 6, 8, 9, 10, 18, 23]
# boxtypes = [18]
for c in nsffile.chunks:
    for e in c.entries:
        for i in e.items:
            for f in i.fields:
                if f.field_type == 0xAA and i.item_type == 34:
                    if int.from_bytes(f.field_data, byteorder='little') != 4:
                        f.field_data = random.choice(boxtypes).to_bytes(len(f.field_data), byteorder='little')

nsf.write(nsffile, "NEW.NSF")
