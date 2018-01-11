#!/usr/bin/env python3

import argparse
import sys


parser = argparse.ArgumentParser(
    description="""
The NDDPEF format is used to load an arbitary file with a few kB in size, into
a single paged PDF, which can be printed out on paper. The printed NDDPEF page
contains a few QR codes and could be scanned and joint together to reform the
original file.  With this tool, both data-to-paper and paper-to-data
conversions could be done.
""",
    usage="python -m NDDPEF {encode|decode} <INPUT> [options]"
)

parser.add_argument("action", choices=["encode", "decode"])
parser.add_argument(
    "input",
    help="""
    Input file for encoding/decoding. For encoding, any type of file can be
    accepted. For decoding, a text-format file containing all scan results is
    expected.
    """
)
parser.add_argument(
    "-o", "--output",
    help="""Output file for encoding/decoding. For encoding, default will be a
    filename suffixed from input filename with ".nddpef.pdf". For decoding, the
    suggested filename in metadata will be used(and if that file exists,
    abort). You may use this option to change both behaviour.
    """
)
parser.add_argument(
    "-t", "--title",
    help="""For encoding: add human-readable title for print-out, default is
    empty. Must be ASCII printable charset and <= 64 chars."""
)
parser.add_argument(
    "-s", "--size",
    choices=range(5,8),
    default=6,
    type=int,
    help="""(Experimental) For encoding: how many data blocks (as QR codes)
    will be printed per row and column. Default is 6 and printed paper will
    carry at most 6x6=36 blocks. The more blocks you specify, the higher is the
    requirement on printer's resolution."""
)

args = parser.parse_args()

##############################################################################

print(args)
