![AWS](https://img.shields.io/badge/AWS-Supported-orange.svg)

# Hyper FiRe (Find/Replace)

The Hyper FiRe engine accelerates whole words Find/Replace operations in ASCII files.
This engine runs up to 6,000 times faster than a sed (stream editor) command.

As an example, one can search 2,500 distinct entries in the entire Wikipedia archive (60 GB) in just 6 minutes.
In comparison, it would take over 16 days on a traditional CPU.

## Features

- Whole words search and replace in ASCII files of arbitrary size
- Support UTF-8 code points from U+0000 to U+00FF ([UTF-8 table](https://www.utf8-chartable.de/unicode-utf8-table.pl))
- Parallel search against a corpus of up to 2,500 words of 36 characters
- Remote or local execution facility
- Easy to use Python API

## Limitations

- Each word must appear only once in the corpus
- Inputs and outputs can't be larger than 30GB.
- See also limitations from API

## Parameters

This section describes accelerator inputs and outputs.

### Configuration parameters
**Generic parameters:**
* `datafile`: Path to the corpus of words to replace.
Needs to be a text file with one line per replacement with format: `WordToReplace, ReplacementWord`.

### Processing parameters
**Generic parameters:**
* `file_in`: Path to an existing text file to process.
* `file_out`: Path to processing result text file (Overwritten if exists).

### Processing output
Processing output is file defined by `file_out` parameter.

## Getting started

The Apyfal Python library is required.

Apyfal is installed using PIP. 

You can install the full package with all options using:

```bash
pip install apyfal[all]
```

### Using Accelerator with Apyfal

#### Running example

For this example, we will process the complete shakespeare work (`samples/shakespeare.txt`) with a corpus of 2500 words
(`samples/corpus.csv`).

You can clone a repository to get examples files, then move to the cloned
directory:

```bash
git clone https://github.com/Accelize/HyperFiRe --depth 1
cd HyperFiRe
```

You need to create and configure an `accelerator.conf` file to run the example.
See "Configuration" in Apyfal documentation for more information.

You can run the example with Apyfal :
```bash
./run_example.py
```
>The result is the `"results/shakespeare_out.txt"` file.

You can run [sed](https://www.gnu.org/software/sed) command benchmark to compare time used with classic CPU
```bash
./run_sed_benchmark.py
```
>The result will be the `results/shakespeare_sed_out.txt` file.

You can compare results from accelerator with result from sed (or with reference replaced file
`results/ref_out_shakespeare.txt`):

```bash
diff results/shakespeare_out.txt results/ref_out_shakespeare.txt
```

#### Using Apyfal step by step

This section explains how to run this particular accelerator.
For explanation on Apyfal and host configuration,
See "Getting Started" in Apyfal documentation.

```python
import apyfal

# 1- Create Accelerator
with apyfal.Accelerator(accelerator='axonerve_hyperfire') as myaccel:
    
    # 2- Configure Accelerator and its host
    #    Note: This step can take some minutes depending the configured host
    #    The corpus of words to replace if passed to the accelerator at this step.
    myaccel.start(datafile="samples/corpus.csv")
    
    # 3- Process file
    #    Words are replaced using the previously passed corpus.
    myaccel.process(file_in="samples/shakespeare.txt", file_out="results/shakespeare_out.txt")
```
>The result is the `"results/shakespeare_out.txt"` file.


### Local execution on cloud instance

This section shows how to run the above example directly on host.

This example requires an host running the accelerator.

#### Creating cloud instance host using Apyfal CLI

You can easily generate a cloud instance host with Apyfal CLI

```bash
apyfal create --accelerator axonerve_hyperfire

apyfal start
```

And then connect to it with SSH (``key_pair`` and ``ip_address`` values are
printed by Apyfal CLI on start):

```bash
ssh -Yt -i ~/.ssh/${key_pair}.pem centos@${ip_address}
```

It is now possible to continue using Apyfal as Python library or as CLI, 
The example next steps will use the CLI.

#### Accelerator configuration

First, initialize the Apyfal CLI.
```bash
apyfal create
```

Like previously, start the accelerator:

The corpus of words to replace if passed to the accelerator at this step.
```bash
apyfal start --datafile samples/corpus.csv
```

#### Process with accelerator

Then, process with accelerator.

Words are replaced using the previously passed corpus.
```bash
apyfal process --file_in samples/shakespeare.txt --file_out results/shakespeare_out.txt
```
>The result is the `"results/shakespeare_out.txt"` file.


#### Terminate cloud instance with Apyfal CLI

From client computer, don't forget to terminate instance you have created with
Apyfal once you have finished with it:

```bash
apyfal stop
```
