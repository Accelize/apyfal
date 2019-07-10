#! /usr/bin/env python
#  coding=utf-8
"""This shows the use of JPEG Encoder Accelerator accelerator.

Convert an sample BMP image to JPEG
(*[Image source](https://pixabay.com/en/switzerland-zermatt-mountains-snow-862870)*).

Please, set up your configuration file before running following example.

Read Apyfal documentation for more information: https://apyfal.readthedocs.io"""

if __name__ == "__main__":
    from apyfal import Accelerator, get_logger

    # Enable extra information for this demo by logging (Disabled by default)
    get_logger(True)

    # Run example
    print("1- Creating Accelerator...")
    with Accelerator(accelerator='alse_jpegenc') as myaccel:

        print("2- Creating and Initializing Instance...")
        myaccel.start()

        print("3- Processing")
        myaccel.process(file_in="samples/image.bmp", file_out="result/image.jpg")
        print("   Processing completed with success")

        print("4- Stopping Accelerator...")
    print("   Accelerator stopped.")
