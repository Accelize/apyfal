#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of GZIP Accelerator accelerator.

This example compress a file of 1 MB.

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='cast_gzip') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start()

        print("3- Processing")
        myaccel.process(file_in="samples/sample_1_1MB.txt", file_out="results/sample_1_1MB.gz")
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
