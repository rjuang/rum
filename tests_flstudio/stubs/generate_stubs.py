#!/usr/bin/python3
import sys

def generate_stubs(filename):
    print(f'Processing {filename}...')
    output = None
    with open(filename, 'r') as f:
        for line in f.readlines():
            if line.strip().startswith('#'):
                if output is not None:
                    output.close()
                filename = line.split('#', 1)[-1].strip()
                print(f'Creating {filename}')
                output = open(filename, 'w')
            if output is not None:
                output.write(line)
    if output:
        output.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Missing input filename. Please specify an input to process.')
        exit(1)
    generate_stubs(sys.argv[1])
    print(f'All done!')
    exit(0)






