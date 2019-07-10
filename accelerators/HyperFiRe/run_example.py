#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of Hyper FiRe (Find/Replace) accelerator.

For this example, we will process the complete shakespeare work (`samples/shakespeare.txt`) with a corpus of 2500 words
(`samples/corpus.csv`).

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='axonerve_hyperfire') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start(datafile="samples/corpus.csv")

        print("3- Processing")
        myaccel.process(file_in="samples/shakespeare.txt", file_out="results/shakespeare_out.txt")
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
