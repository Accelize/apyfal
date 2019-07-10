#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of TAR.GZ Accelerator accelerator.

This example show how make a TAR.GZ file containing 3 files.

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='aclz_tgz') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start(mode=3)

        print("3- Processing")
        myaccel.process(file_in="samples/sample_1_1MB.txt", startOfTx=1, endOfTx=0)
        myaccel.process(file_in="samples/sample_1_1MB.txt", startOfTx=0, endOfTx=0)
        myaccel.process(file_in="samples/sample_1_1MB.txt", file_out="results/out.tar.gz", startOfTx=0, endOfTx=1)
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
