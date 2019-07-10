import os, sys
import logging
import argparse
import glob
import subprocess
import shlex
import shutil
import json
import re
import binascii
import apyfal
import itertools

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
LOG_FMT_DBG = "%(levelname)-8s: %(message)s"


TMPDIR = "/dev/shm/sha3_nist_test"
NIST_VECTOR_PATH = os.path.join(SCRIPT_PATH, "nist_test_vectors")


myaccel = apyfal.Accelerator(accelerator='silex_sha3')

def runAccelerator(sha3_type, dataInList):

    nb_cases = 0
    nb_err = 0
    nb_bytes = 0

    # Grouping test cases having the same digest length
    for digest_len, dataInGroup in itertools.groupby(sorted(dataInList, key=lambda x: x[3]), lambda x: x[3]):

        # Run accelerator
        dataInGroupList = list(dataInGroup)
        results = myaccel.process_map(srcs=map(lambda x: x[1], dataInGroupList), type=sha3_type, length=digest_len)

        # Verify result
        for i, fpga_digest in enumerate(results):
            idx, _, msg_len, _, exp_digest = dataInGroupList[i]
            if fpga_digest != unicode(exp_digest):
                nb_err += 1
                logger.error("\t* %s: case index %d - Msg Length=%d, Digest Length=%d is incorrect:\n\tGot: %s\n\tExpect: %s", sha3_type, idx, msg_len, digest_len, fpga_digest, exp_digest)
            else:
                logger.info("\t* %s: case index %d - Msg Length=%d, Digest Length=%d is correct", sha3_type, idx, msg_len, digest_len)
            nb_bytes += msg_len
        nb_cases += i

    return nb_cases, nb_err, nb_bytes



def runTestCase(sha3_type, msg_data_list, msg_len_list, digest_len_list, expect_digest_list):

    # Create input data file
    dataInList = list()
    for idx, (msg_data, msg_len, digest_len, expect_digest) in enumerate(zip(msg_data_list, msg_len_list, digest_len_list, expect_digest_list)):
        if msg_len == 0:
            logger.warn("\t* %s: case L=%d is bypassed: message of size 0 is not supported", sha3_type, msg_len)
        else:
            dataIn = os.path.join(TMPDIR, '%s_%d_%d_%d.dat' % (sha3_type, msg_len, digest_len, idx))
            with open(dataIn, 'wb') as fout:
                fout.write(binascii.unhexlify(msg_data))
            dataInList.append((idx, dataIn, msg_len, digest_len, expect_digest))

    # Run test
    return runAccelerator(sha3_type, dataInList)



if __name__ == "__main__":
    # Parse the arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default=NIST_VECTOR_PATH,
        help="Specify the directory constaining the NIST test files (.rsp) or directly the NIST test file.")
    args = parser.parse_args()

    # Set logging configuration
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FMT_DBG))
    logging.getLogger().addHandler(console)

    if os.path.isdir(args.path):
        test_files = glob.glob(os.path.join(args.path, "*.rsp"))
    elif os.path.isfile(args.path):
        test_files = [args.path]

    # Create working directory
    if os.path.isdir(TMPDIR):
        shutil.rmtree(TMPDIR)
    os.makedirs(TMPDIR)

    # Open accelerator
    logger.info("Creating and Initializing Accelerator Instance on CSP...")
    myaccel.start()

    # Parse directory with NIST test vectors
    results = dict()
    for nist_file in sorted(test_files):
        err = 0
        logger.info("Extract test cases from file %s ...", nist_file)
        # Load file content
        with open(nist_file) as fin:
            content = fin.read()
        # Find algo
        if re.search(r'SHAKE', content, re.MULTILINE | re.IGNORECASE):
            algo = "shake"
        else:
            algo = "sha3"
        # Find the security bit
        m = re.search(r'^\[(L|Outputlen|Input Length)\s*=\s*(\d+)\]', content, re.MULTILINE | re.IGNORECASE)
        if m is None:
            logger.error("Format of file %s is not supported", nist_file)
            err += 1
            continue
        security = int(m.group(2))
        sha3_type = "%s-%d" % (algo, security)

        # Extract test cases parameters from file
        msg_len_list = map(int, re.findall(r'^\Len\s*=\s*(\d+)', content, re.MULTILINE | re.IGNORECASE))
        msg_data_list = re.findall(r'^\Msg\s*=\s*(\w+)', content, re.MULTILINE | re.IGNORECASE)
        exp_digest_list = map(lambda x: x[1], re.findall(r'^(MD|Output)\s*=\s*(\w+)', content, re.MULTILINE | re.IGNORECASE))
        digest_len_list = map(int, re.findall(r'^\Outputlen\s*=\s*(\d+)', content, re.MULTILINE | re.IGNORECASE))
        if len(digest_len_list) == 0:
            digest_len_list = [security]*len(msg_data_list)
        if len(msg_len_list) == 0:
            msg_len_list = map(lambda x: len(x)<<2, msg_data_list)
        if len(msg_data_list) != len(exp_digest_list) and len(msg_data_list) != len(digest_len_list) and len(msg_data_list) != len(msg_len_list):
            logger.error("Consistency error in file %s: number of Msg = %d, number of Digest = %d, number of Msg Length = %d, number of Digest Length",
                len(msg_data_list), len(msg_len_list), len(exp_digest_list), len(digest_len_list))
            err += 1
            continue
        # Loop on each test case
        logger.info("Running test on file %s:", nist_file)
        results[nist_file] = runTestCase(sha3_type, msg_data_list, msg_len_list, digest_len_list, exp_digest_list)

    # Stop accelerator
    logger.info("Stopping Accelerator Instance on CSP")
    myaccel.stop()

    # display summary
    total_err = 0
    total_case = 0
    total_byte = 0
    logger.info("*"*32 + " SUMMARY " + "*"*33)
    for k,v in sorted(results.items(), key=lambda x: x[0]):
        txt = "%-24s: %4d cases, %d errors" % (os.path.basename(k),v[0], v[1])
        total_case += v[0]
        total_err += v[1]
        total_byte += v[2]
        lvl = logging.ERROR if v[1] else logging.INFO
        logger.log(lvl, "* %-70s *" % txt)
    logger.info("* %-70s *" % ("=> Total number of test cases = %d" % total_case))
    logger.info("* %-70s *" % ("=> Total bytes processed = %d" % total_byte))
    logger.info("*"*74)

    sys.exit(total_err)
