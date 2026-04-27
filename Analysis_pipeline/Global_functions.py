import gc
import time
import os
import re

import numpy as np
import tqdm
import matplotlib.pyplot as plt

# import spikeinterface.full as si
from DemoReadSGLXData.readSGLX import readMeta, SampRate, makeMemMapRaw, GainCorrectIM, GainCorrectNI


class TtlStampConsts:
    N_BITS = 14
    ZERO_TIME_MS = 1
    BIT_SIZE_MS = 5
    ONSET_TTL_LENGTH_MS = 10


def read_ttl_from_stream(data, t_vec):
    sr = 1 / (t_vec[1] - t_vec[0])

    nBits = TtlStampConsts.N_BITS
    rampSizeMs = 0
    zeroTimeMs = TtlStampConsts.ZERO_TIME_MS
    bitSizeMs = TtlStampConsts.BIT_SIZE_MS
    onsetTtlSizeMs = TtlStampConsts.ONSET_TTL_LENGTH_MS
    entireStampTimeLengthMs = TtlStampConsts.ONSET_TTL_LENGTH_MS + TtlStampConsts.BIT_SIZE_MS * TtlStampConsts.N_BITS

    nSamplesZero = max(round(sr * zeroTimeMs / 1000), 1)
    nSamplesRamp = round(sr * rampSizeMs / 1000)
    nPeriBitSamples = nSamplesZero + nSamplesRamp
    proportionOfBitIgnoredAtEachEdge = 0.2
    nPeriBitSamples = round(nPeriBitSamples + bitSizeMs / 1000 * sr * proportionOfBitIgnoredAtEachEdge)
    nPeriBitSamples = min(nPeriBitSamples, round(bitSizeMs / 1000 * sr / 2) - 1)

    ttlThreshold = 0.5 * (max(data) + min(data))

    isAboveThreshold = data > ttlThreshold

    # plt.figure(figsize=(20, 10))
    # plt.plot(t_vec, data)
    # plt.axhline(ttlThreshold, color='k', linestyle='--')
    # plt.plot(t_vec, isAboveThreshold)
    # plt.show(block=False)

    aboveThresholdIndices = np.where(isAboveThreshold)[0]
    interOnesInterval = np.insert(np.diff(aboveThresholdIndices), 0, len(data) + 1)

    minZeroSamplesBetweenStamps = entireStampTimeLengthMs / 1000 * sr
    isFirstStampBitOne = interOnesInterval > minZeroSamplesBetweenStamps
    firstStampBitIndices = aboveThresholdIndices[isFirstStampBitOne]

    nStamps = len(firstStampBitIndices)
    stampValues = np.full(nStamps, np.nan)
    stampIndices = np.full(nStamps, np.nan)

    for stampInd in range(nStamps):
        currentStampFirstInd = firstStampBitIndices[stampInd]
        bitsForCurrentStamp = np.full(nBits, np.nan)

        for bitInd in range(nBits):
            currentBitFirstIndex = currentStampFirstInd + int(
                np.ceil((onsetTtlSizeMs + (bitInd) * bitSizeMs) / 1000 * sr)) + nPeriBitSamples
            currentBitLastIndex = currentStampFirstInd + int(
                np.floor((onsetTtlSizeMs + (bitInd + 1) * bitSizeMs) / 1000 * sr)) - nPeriBitSamples

            currentBitFractionAboveThreshold = np.mean(isAboveThreshold[currentBitFirstIndex:currentBitLastIndex])

            bitsForCurrentStamp[bitInd] = currentBitFractionAboveThreshold > 0.5

        stampIndices[stampInd] = currentStampFirstInd
        bitsForCurrentStamp = bitsForCurrentStamp[::-1]
        stampValues[stampInd] = int("".join(map(str, bitsForCurrentStamp.astype(int))), 2)

    stampTimesSec = stampIndices / sr

    return stampValues, stampIndices, stampTimesSec


def read_sync_times_from_stream(data_stream, t_vec):
    trigger_val = 0.5 * (max(data_stream) + min(data_stream))

    # Rising edges
    edges_times_mask = np.argwhere((data_stream[:-1] < trigger_val) & (data_stream[1:] > trigger_val))
    # Falling edges
    # edges_times = (data_stream[:-1] > trigger_val) & (data_stream[1:] < trigger_val)

    return t_vec[edges_times_mask.flatten()]


def read_meta_file(binFullPath, tStart, tEnd, chanList):
    meta = readMeta(binFullPath)
    sRate = SampRate(meta)

    firstSamp = int(sRate*tStart)
    lastSamp = int(sRate*tEnd)
    rawData = makeMemMapRaw(binFullPath, meta)
    selectData = rawData[chanList, firstSamp:lastSamp+1]

    if meta['typeThis'] == 'imec':
        # apply gain correction and convert to uV
        convData = 1e6*GainCorrectIM(selectData, chanList, meta)
    else:
        # apply gain correction and convert to mV
        convData = 1e3*GainCorrectNI(selectData, chanList, meta)

    return convData, sRate


def read_file_by_time_steps(file_path, t_vec, tstep,  chanList):
    read_data = []
    # tstep = t_vec[1] - t_vec[0]

    for tStart in tqdm.tqdm(t_vec):
        tEnd = tStart + tstep
        cur_data, sr = read_meta_file(file_path, tStart, tEnd, chanList)
        read_data.append(cur_data)
        del cur_data
        gc.collect()

    # read_data = np.concatenate(read_data, axis=1)
    return read_data, sr


def find_files(root_folder, pattern):
    # Compile the regex pattern for matching
    regex = re.compile(pattern)

    matching_files = []
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            if regex.match(filename):
                file_path = os.path.join(dirpath, filename)
                matching_files.append(file_path)
                print(f"File found: {file_path}")
    return matching_files