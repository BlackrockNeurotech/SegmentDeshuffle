from helper import *
from tkinter import Tk
import os
import sys
from tkinter.filedialog import asksaveasfile
import numpy as np

# establish input file
Tk().withdraw()
print('Select original file')
readFile = openfilecheck("rb")
path, file = os.path.split(readFile.name)


# establish header information from readFile needed for script
basicHeader = processheaders(readFile, nsx_header_dict["basic"])
channels = basicHeader["ChannelCount"]
headerBytes = basicHeader["BytesInHeader"]
fileType = basicHeader["FileType"].decode('utf-8')
oneHeaderBytes = 1      # byte, always 1
timestampBytes = 8      # uint64
sampHeaderBytes = 4     # uint32
dataBytes = channels*2  # int16 * #channels
segmentBytes = oneHeaderBytes + timestampBytes + sampHeaderBytes + dataBytes

if fileType != 'BRSMPGRP':
    sys.exit('Segment Shuffle bug only occurs on filetype BRSMPGRP. This file is ' + fileType +
             '. Closing application...')
else:
    print('Confirmed BRSMPGRP...')

# establish number of segments in readFile
eof = readFile.seek(0, 2)   # finds size of file in bytes
nSegments = int((eof-headerBytes)/segmentBytes)

# extract all segment timestamps and perform health checks
prec = [("reserved", "uint8", (1,)),
        ("timestamps", "uint64", (1,)),
        ("num_data_points", "uint32", (1,)),
        ("samples", "int16", (channels,))]
struct_arr = np.memmap(readFile.name, dtype=prec, shape=(nSegments, 1), offset=int(headerBytes), mode="r")
allTS = struct_arr['timestamps']
allOneSegment = struct_arr['num_data_points']

# see if file is vulnerable, i.e. has one sample per segment
if np.sum(allOneSegment) != nSegments:
    sys.exit('This file does not have 1 sample per segment. Closing application...')
else:
    print('Confirmed 1 sample per segment...')

# check if the timestamps are ordered
sortedInds = np.argsort(allTS, axis=None)
jumps = np.array(np.where(np.diff(sortedInds) != 1))
if np.size(jumps) == 0:
    sys.exit('This file has timestamps that are properly ordered. Closing application...')
else:
    print('Confirmed out-of-order timestamps...')

# checks passed, create output file
print('Select output file')
saveFile = asksaveasfile(
    title="Select output file",
    initialfile=file,
    initialdir=path,
    filetypes=[("NSx Files", ("*.ns1", "*.ns2", "*.ns3", "*.ns4", "*.ns5", "*.ns6"))])
writeFile = open(saveFile.name, 'wb')

# write identical header information from readFile in writeFile
readFile.seek(0, 0)
allHeader = readFile.read(headerBytes)
writeFile.write(allHeader)

# bug presents itself as shifting 1-5 samples out of order occasionally in groups. These shifts can be captured
# according to the pseudoplot below, where the input data is modeled as a linear increase of voltage:
#
#    ---------------------------------------------X----------
#    -----------------------------------------X--------------
#    ---------------------X----------------------------------
#    -----------------X--------------------------------------
#    -------------------------------------X------------------
#  V ---------------------------------X----------------------
#    -----------------------------X--------------------------
#    -------------------------X------------------------------
#    -------------X------------------------------------------
#    ---------X----------------------------------------------
#    -----X--------------------------------------------------
#         1   2   3   4   5   6   7   8   9   10  11            index
#    <--__normal__|   |bad|   |__shifted__|   |__normal__-->    epochs
#                 |_indShift__|____nShift_____|                 shuffle points

# bug always has jumps between normal:bad, bad:shifted, and shifted:normal, so timestamp indices will jump 3x
# per occurence.
# order bug epochs in 3s and find number of epochs
try:
    jumps = np.reshape(jumps, (-1, 3))
except ValueError:
    sys.exit('Timestamps are not predictably ordered. Please contact Blackrock Support.')

nJumps = np.shape(jumps)[0]

# loop through identified epochs and reorder data
lastJump = 0
newStart = headerBytes
print('Reordering...')
for k in range(0, nJumps):
    # find epochs of interest
    indShift = jumps[k, 1] - jumps[k, 0]
    nShift = jumps[k, 2] - jumps[k, 1]

    # jump to start of normal epoch
    readFile.seek(newStart)

    # read/write normal epoch
    chunk = readFile.read((jumps[k, 0]+1-lastJump)*segmentBytes)
    writeFile.write(chunk)
    locus = readFile.tell()     # define ptr where the bad epoch starts

    # jump to shifted data
    readFile.seek(nShift*segmentBytes, 1)

    # read/write shifted data
    chunk = readFile.read(indShift * segmentBytes)
    writeFile.write(chunk)
    newStart = readFile.tell()  # define ptr where the next normal epoch starts

    # jump to bad epoch
    readFile.seek(locus, 0)

    # read/write bad epoch
    chunk = readFile.read(nShift*segmentBytes)
    writeFile.write(chunk)
    lastJump = jumps[k, 2]+1

    # readout
    print(str(k+1) + ' of ' + str(nJumps) + ' index errors addressed...')

print('Cleaning up...')
# write the remaining data in readFile to writeFile
readFile.seek(newStart)
lastChunk = readFile.read(-1)
writeFile.write(lastChunk)

# close files
readFile.close()
writeFile.close()

# readout
print(writeFile.name + ' is a copy of ' + readFile.name + ' with deshuffled segments')
sys.exit(0)
