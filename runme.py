import sys
import os

BASE_COUNT = 50

def run(dirname, file):
  f = open(dirname + '/' + file)
  entries = []

  for i in range(50):
    entry = f.readline().strip()
    entries.append(entry)
    
  print (file, entries)

def main(argv):
  len_argv = len(argv)
  if len_argv != 1 and len_argv != 2:
    print ('runme.py <dirname> [filename]')
    sys.exit()

  dirname = argv[0]

  if len_argv == 1:
    for file in os.listdir("./" + dirname):
      if file.endswith(".txt"):
        run(dirname, file)
  else:
    assert len_argv == 2
    filename = argv[1]
    run(dirname, filename)

if __name__ == "__main__":
  main(sys.argv[1:])

