import os, sys
import logging
import argparse
import apyfal
import shutil
import json
import csv
import re

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
LOG_FMT_DBG = "%(levelname)-8s: %(message)s"


TMPDIR = "/dev/shm/sha3_benchmark"
CSV_OUTPUT = "results.csv"
SUPPORTED_SHA3 = ["sha3-224", "sha3-256", "sha3-384", "sha3-512", "shake-128", "shake-256"]

INFO_DICT = {
        "app": {
            "reset": 1,
            "sw-mode": 1,
            "logging": {
                "format": 0,
                "verbosity": 3
            },
            "specific": {
                "type": "",     # To fulfill with algorithm name
                "length": 0     # To fulfill with expected digest length for shake only
            }
        }
    }


myaccel = apyfal.Accelerator(accelerator='silex_sha3')

def runAccelerator(input_files, input_json):

    # Run accelerator
    info_list = list()
    results = myaccel.process_map(srcs=map(lambda x: x[1], input_files), parameters=input_json, info_list=info_list)

    retList = list()
    for i, fpga_digest in enumerate(results):
        ret = dict()
        # Read and verify output result
        info = info_list[i]
        ret['pkt_size'] = input_files[i][0]
        ret['fpga_bw'] = info['app']['profiling']['input-bandwidth']
        ret['fpga_time'] = info['app']['profiling']['fpga-elapsed-time']
        ret['cpu_bw'] = info['app']['result-sw-comparison']['input-bandwidth']
        ret['cpu_time'] = info['app']['result-sw-comparison']['cpu-elapsed-time']
        ret['acceleration_factor'] = info['app']['result-sw-comparison']['accelerator-factor']
        cpu_digest = info['app']['sw-digest']
        retList.append(ret)

        # Verify result coherency if both CPU and FPGA have been run
        if cpu_digest != fpga_digest:
            logger.error("\t* FPGA and CPU digests are different:\n\tFPGA: %s\n\tCPU: %s", fpga_digest, cpu_digest)
            raise Exception("An error occurred.")
        logger.info("\t* Msg length=%d: FPGA and CPU digests are identical, acceleration=%0.1fx", ret['pkt_size'], ret['acceleration_factor'])

    return retList



def runTestCase(sha3_type, input_files, samples=1):

    # Extract parameters
    m = re.match(r'(\w+)-(\d+)', sha3_type)
    if m is None:
        raise Exception("Unsupported SHA3 algorithm")
    algo = m.group(1)
    security = int(m.group(2))
    sha3_len = security if algo == 'sha3' else 2 * security
    INFO_DICT['app']['specific']['type'] = sha3_type
    INFO_DICT['app']['specific']['length'] = sha3_len

    # Create input parameter file
    infoIn = os.path.join(TMPDIR, "%s.json" % sha3_type)
    with open(infoIn, 'w') as fout:
        json.dump(INFO_DICT, fout)

    # Run in batch
    dataInList = sorted(input_files*samples)
    results = runAccelerator(dataInList, infoIn)

    # Extract result: keep the best of each file
    retList = list()
    for result_slice in zip(*(iter(results),) * samples):
        result = None
        for r in result_slice:
            if result is None:
                result = r
            elif r['acceleration_factor'] > result['acceleration_factor']:
                result = r
        retList.append(result)

    return retList



def saveToCSV(results, csvout):

    # Convert results dictionary to list sorted by ascending packet size
    table = list()
    for pktSize,res in sorted(results.items(), key=lambda x: x[0]):
        res['packet_size'] = float(pktSize)/1024/1024   # Convert packet size from byte to MBytes
        table.append(res)

    # Build CSV file
    with open(csvout, 'w') as csvfile:
        fieldnames = sorted(table[0], key = lambda x: 0 if x=='packet_size' else x)
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in table:
            writer.writerow(row)



if __name__ == "__main__":
    ret = -1

    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=1, help="Specify the number of samples per testcase.")
    parser.add_argument("--min-size", type=int, default=10, help="Specify the power of 2 of the minimum size to hash.")
    parser.add_argument("--max-size", type=int, default=26, help="Specify the power of 2 of the maximum size to hash.")
    parser.add_argument("--algo", type=str, default=','.join(SUPPORTED_SHA3),
        help="Coma separated values specifying the algorithms to test: %s" % ', '.join(SUPPORTED_SHA3))
    parser.add_argument("-o","--output", type=str, default=CSV_OUTPUT, help="Specify path of the CSV output file.")
    args = parser.parse_args()

    # Set logging configuration
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FMT_DBG))
    logging.getLogger().addHandler(console)

    logger.info("Preparing test-set ...")

    pktSizeRange = map(lambda x: 2**x, range(args.min_size, args.max_size+1))

    # Create working directory
    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR)

    # Create input data files
    inputFiles = list()
    for pktSize in pktSizeRange:
        fname = os.path.join(TMPDIR, 'data_%d.in' % pktSize)
        inputFiles.append( (pktSize,fname) )
        with open(fname, 'wb') as fout:
            fout.write(os.urandom(pktSize))

    # Open accelerator
    logger.info("Creating and Initializing Accelerator Instance on CSP...")
    myaccel.start()

    # Run test cases and save results
    total_bytes = 0
    results = dict( zip( pktSizeRange, [{} for _ in pktSizeRange] ) )
    for sha3_type in args.algo.split(','):
        if sha3_type not in SUPPORTED_SHA3:
            logger.error("Unsupported algorithm: %s", sha3_type)
        else:
            logger.info("Processing %s ...", sha3_type)
            for res in runTestCase( sha3_type, inputFiles, args.samples ):
                total_bytes += res['pkt_size'] * args.samples
                results[res['pkt_size']]['Time FPGA '+sha3_type] = res['fpga_time']
                results[res['pkt_size']]['Time CPU '+sha3_type] = res['fpga_time']
                results[res['pkt_size']]['BW FPGA '+sha3_type] = res['fpga_bw']
                results[res['pkt_size']]['BW CPU '+sha3_type] = res['cpu_bw']
                results[res['pkt_size']]['AccelFactor '+sha3_type] = res['acceleration_factor']

    # Stop accelerator
    logger.info("Stopping Accelerator Instance on CSP")
    myaccel.stop()

    # Store results in CSV file
    saveToCSV(results, args.output)
    logger.info("*"*80)
    logger.info("Execution ended: %d bytes have been processed.", total_bytes)
    logger.info("Results has been saved in '%s'.", args.output)
    logger.info("You can now generate your own charts by importing this file in your favorite spreadsheet application.")
    logger.info("*"*80)

    sys.exit(0)
