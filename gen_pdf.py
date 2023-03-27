'''
Generate PDF of music from given music file.
'''

import argparse
import music21
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='midi/musicXML file')
    args = parser.parse_args()

    file = args.file
    out_file = os.path.splitext(file)[0] + '.pdf'

    score = music21.converter.parse(file)
    score.write('mxl.pdf', fp=out_file)

if __name__ == '__main__':
    main()
