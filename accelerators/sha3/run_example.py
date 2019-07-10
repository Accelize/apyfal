#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of SHA3 and SHAKE Application accelerator.

This example computes the sha3-224 for the run_example.py file.
Make sure the accelerator.conf file has been completed before running the script.

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='silex_sha3') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start()

        print("3- Processing")
        digest = myaccel.process(file_in="run_example.py", type="sha3-224")
        print("   Result is %s" % digest)
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
