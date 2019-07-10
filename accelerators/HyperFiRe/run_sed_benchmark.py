#! /usr/bin/env python
# coding=utf-8
"""Measure time to replace text with 'sed' command on same
example text as one used in "run_example.py"
"""

import time
import csv
import subprocess


def sed(datafile, file_in, file_out):
    """
    Perform sed and measure time.

    Args:
        datafile (str): CSV containing for each line "word to replace, replacement"
        file_in (str): File where replacing strings.
        file_out (str): Result file.

    Returns:
        float: Time to perform sed (seconds)
    """
    # Prepare command
    command = ["sed "]
    with open(datafile) as filein_csv:
        read_csv = csv.reader(filein_csv, delimiter=',')
        for row in read_csv:
            command.extend([" -e 's/\<", row[0], "\>/", row[1], "/g'"])

    command = "".join(command + [" ", file_in, " > ", file_out])

    # Run command and measure time
    start = time.time()
    subprocess.Popen(command, shell=True).communicate()
    return time.time() - start


if __name__ == "__main__":
    # Run sed
    print("Processing file 'samples/shakespeare.txt'")
    sed_time = sed(datafile="samples/corpus.csv",
                   file_in="samples/shakespeare.txt",
                   file_out="results/shakespeare_sed_out.txt")
    print("Processing completed with success (see: 'results/shakespeare_sed_out.txt')")

    # Execution time
    print("- Total processing time: %.3fs" % sed_time)
