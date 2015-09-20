import sys
import os

def run(file):
	print (file)

def main(argv):
	if len(argv) != 1:
		print ('runme.py <dirname>')
		sys.exit()

	dirname = argv[0]

	for file in os.listdir("./" + dirname):
		if file.endswith(".txt"):
			run(file)

if __name__ == "__main__":
	main(sys.argv[1:])

