#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of TRNG Accelerator accelerator.

This example show the generation of 1MB of random bytes.

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='secureic_trng') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start()

        print("3- Processing")
        myaccel.process(file_out="results/output.bin", nbBytes=1048576)
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
