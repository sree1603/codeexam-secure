import sys

line = sys.stdin.readline()

if line.endswith("\n"):
    line = line[:-1]

print(line[::-1])
