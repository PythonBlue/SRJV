import sys, math, platform, os

def run(fname):
    wav = open(fname, "rb")
    print(fname)
    #print(fname)
    audioFile = wav.read()

    wav.seek(0)
    bitRate = audioFile[34]
    if bitRate != 16 and bitRate != 24 and bitRate != 32:
        print("Error: unsupported bitrate of input!")
        return
    dataChk = audioFile.find(b'data')
    dataPrefix = wav.read(dataChk + 4)
    wav.seek(dataChk + 4)
    sampleCount = int(int.from_bytes(wav.read(4), "little") / (bitRate / 8))

    smplLoop = sampleCount - 2
    smplEnd = sampleCount - 1
    smplChk = audioFile.find(b'smpl')
    dataOff = dataChk + 8
    if dataChk < smplChk and smplChk < dataChk + sampleCount * bitRate / 8 and dataChk > -1:
        smplChk = audioFile.find(b'smpl', 0, dataOff)
        if smplChk == -1:
            smplChk = audioFile.find(b'smpl', dataOff + dataSz)
    if smplChk >= 0 and smplChk + 64 < len(audioFile):
        wav.seek(smplChk + 52)
        smplLoop = int.from_bytes(wav.read(4), "little")
        smplEnd = int.from_bytes(wav.read(4), "little")
        
    wav.seek(dataOff)
    wavSamplesPrep = []
    wavSamples = []
    wavSamplesFinal = []
    for i in range(sampleCount):
        End1 = int.from_bytes(wav.read(1), "big")
        End2 = int.from_bytes(wav.read(1), "big")
        End3 = 0
        End4 = 0
        Endian = (End2 << 8) + End1
        if bitRate > 16:
            End3 = int.from_bytes(wav.read(1), "big")
            Endian = (End3 << 16) + (End2 << 8) + End1
            if bitRate > 24:
                End4 = int.from_bytes(wav.read(1), "big")
                Endian = (End4 << 16) + (End3 << 16) + (End2 << 8) + End1
        if Endian >= 1 << (bitRate - 1):
            Endian -= 1 << bitRate
        if bitRate == 16:
            Endian = Endian << 8
        wavSamplesPrep.append(Endian)
    dataSuffix = wav.read()
    for i in range(16):
        wavSamplesPrep.append(wavSamplesPrep[smplEnd - sampleCount + smplLoop + i])
    sampleCountB = len(wavSamplesPrep)
    prevDelta = 0
    newBitRate = max(bitRate, 24)
    wavSamples = []
    prevDelta = 0
    prevEndian = 0
    for i in range(sampleCountB):
        Endian = wavSamplesPrep[i] * 15 / 16
        if i > 0:
            Endian -= wavSamplesPrep[i - 1] * 15 / 64
        if i < len(wavSamplesPrep) - 1:
            Endian -= wavSamplesPrep[i + 1] * 15 / 64
        wavSamples.append(round(Endian))
    for i in range(sampleCount):
        wavSamplesFinal.append(wavSamples[i])
    if not os.path.exists("Brighter"):
        os.mkdir("Brighter")
    newWav = open("Brighter" + os.path.sep + fname, "wb")
    newWav.write(dataPrefix[:4])
    if bitRate == 16:
        newSize = int.from_bytes(dataPrefix[4:8], "little") + sampleCount
        if sampleCount % 2 == 1:
            newSize += 3
        newWav.write(newSize.to_bytes(4,"little"))
    else:
        newWav.write(dataPrefix[4:8])
    newWav.write(dataPrefix[8:28])
    if bitRate == 16:
        newSize = int(int.from_bytes(dataPrefix[28:32], "little") * 1.5)
        if sampleCount % 2 == 1:
            newSize += 3
        newWav.write(newSize.to_bytes(4,"little"))
    else:
        newWav.write(dataPrefix[28:32])
    newWav.write(int(newBitRate / 8).to_bytes(1,"little"))
    newWav.write(dataPrefix[33].to_bytes(1,"little"))
    newWav.write(newBitRate.to_bytes(1,"little"))
    newWav.write(dataPrefix[35].to_bytes(1,"little"))
        
    newWav.write(dataPrefix[36:])
    if bitRate == 16:
        if sampleCount % 2 == 1:
            newWav.write(int(sampleCount * 3 + 3).to_bytes(4,"little"))
        else:
            newWav.write(int(sampleCount * 3).to_bytes(4,"little"))
    else:
        newWav.write(int(sampleCount * bitRate / 8).to_bytes(4,"little"))
    for i in range(len(wavSamplesFinal)):
        newWav.write((wavSamplesFinal[i] % (1 << newBitRate)).to_bytes(int(newBitRate / 8), "little"))
    if bitRate == 16 and sampleCount % 2 == 1:
        newWav.write((0).to_bytes(int(newBitRate / 8), "little"))
    newWav.write(dataSuffix)
    
    wav.close()
    newWav.close()

    return
    
folder = input("Enter a relative folder for samples to brighten: ")
for file in os.listdir(folder):
    if file.endswith(".wav"):
        os.chdir(folder)
        run(file)
        os.chdir("..")
