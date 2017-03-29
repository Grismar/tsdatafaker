# Copyright 2017 Jaap van der Velde, BMT WBM Pty Ltd.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
import argparse
import time
import logging
from run_file_args import process_run_file

__version__ = '1.0.1'


def positive_int_type(x):
    x = int(x)
    if x < 1:
        raise argparse.ArgumentTypeError("Minimum value is 1")
    return x

# set up argument parser
argparser = argparse.ArgumentParser(description='Reprocess .dat (text) and output content in small increments.')
argparser.add_argument('input', nargs=1,
                       help='.dat input file.')
argparser.add_argument('-o', '--out_file', default='',
                       help='Write output to a specific file (same as input by default).')
argparser.add_argument('-f', '--folder', default='',
                       help='Folder to write output to (current folder by default).')
argparser.add_argument('-hd', '--header_lines', default=4,
                       help='Number of lines to consider header lines (4 by default).')
argparser.add_argument('-d', '--delay', type=float, default=1,
                       help='Number of seconds to wait between trying to write output (float, 1 by default).')
argparser.add_argument('-l', '--log_level', type=int, default=1, choices=range(1, 4), metavar="[1-4]",
                       help='Level of messages to log (1 = error, 2 = warning, 3 = info, 4 = debug) (1 by default).')
argparser.add_argument('-s', '--skip_empty', action='store_true',
                       help='Whether to skip empty lines in the source file (false by default).')
argparser.add_argument('-ow', '--overwrite', action='store_true',
                       help='Whether to OVERWRITE the output file (false by default).')
argparser.add_argument('-i', '--increment', type=positive_int_type, default=1,
                       help='Number of lines to write to output (1 by default).')
argparser.add_argument('-r', '--run_file', default='',
                       help='Use a run file to configure run (settings in run file override command line arguments).')
argparser.add_argument('-v', '--version', action='version', version='%(prog)s {0}'.format(__version__),
                       help='Number of lines to write to output (1 by default).')

args = argparser.parse_args(sys.argv[1:])


def process(input_filename, output_filename, header_size, delay, skip_empty, overwrite, increment):

    def read_single_line(n):
        l = input_file.readline()
        while skip_empty and (l in ['\n', '\r\n']):
            n += 1
            l = input_file.readline()
        return l, n

    logging.info('tsdatafaker.py, version {0}'.format(__version__))
    logging.warning('Starting processing. Reading from {0}, writing to {1}.'.format(input_filename, output_filename))

    with open(input_filename) as input_file:
        lines = 0
        empty = 0

        # read header of header_size lines
        header = []
        for i in range(header_size):
            header.append(input_file.readline())
        # iterate over remaining lines
        line, empty = read_single_line(empty)
        while line != '':
            # wait for destination file to disappear or wait one cycle if overwriting
            if overwrite:
                logging.info('Waiting before (over)writing target... ({0} sec)'.format(delay))
                time.sleep(delay)
            else:
                while os.path.isfile(output_filename):
                    logging.info('Waiting for output file to be removed... ({0} sec)'.format(delay))
                    time.sleep(delay)
            # write header and data line to output, then move on
            with open(output_filename, mode='w') as output_file:
                output_file.writelines(header)
                for i in range(0, increment):
                    # if there's something left to write
                    if line != '':
                        output_file.write(line)
                        lines += 1
                        line, empty = read_single_line(empty)
                logging.info('Line {0} written'.format(lines))

        logging.warning(
            'Completed writing data, no more lines. '
            'Total lines written: {0} (skipped {1} empty lines)'.format(lines, empty))
    return lines

try:
    # apply run_file to arguments (overriding command line arguments)
    process_run_file(args)

    log_levels = {1: logging.ERROR, 2: logging.WARNING, 3: logging.INFO, 4: logging.DEBUG}
    logging.basicConfig(level=log_levels[args.log_level], format='%(asctime)s %(message)s')

    input_pathname_arg = args.input[0]
    output_filename_arg = args.input[0] if args.out_file == '' else args.out_file
    output_folder_arg = os.getcwd() if args.folder == '' else args.folder

    assert (os.path.isfile(input_pathname_arg)), "Input file not found."
    assert (os.path.isdir(output_folder_arg)), "Output folder not found."
    output_pathname_arg = os.path.join(output_folder_arg, output_filename_arg)
    assert (os.path.realpath(input_pathname_arg) !=
            os.path.realpath(output_pathname_arg)), "Won't overwrite input with output."

    process(input_pathname_arg, output_pathname_arg,
            args.header_lines, args.delay, args.skip_empty, args.overwrite, args.increment)
except AssertionError as e:
    logging.error('Assertion failed: {0}'.format(str(e)))
except TypeError as e:
    logging.error('Unexpected error: {0}'.format(str(e)))
