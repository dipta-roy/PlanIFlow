import sys

spec_file = sys.argv[1]

with open(spec_file, 'r+') as f:
    content = f.read()
    f.seek(0, 0)
    f.write("import sys; sys.setrecursionlimit(sys.getrecursionlimit() * 5)\n" + content)
