import platform
import sys
import os
import shutil
import math
import re
from datetime import datetime

import DPCM
import Import80
import Import990
import Import2080

def run(tmpDir, PatchImport, VerboseMode):
    shutil.copyfile("Template.bin", "Result.bin")
    template = open("Result.bin", "rb+")
    templateCoef = open("Result.bin", "rb+")
    template.seek(48)
    today = datetime.now()
    template.write('{0:04d}'.format(today.year).encode('utf-8'))
    template.seek(53)
    template.write('{0:02d}'.format(today.month).encode('utf-8'))
    template.seek(56)
    template.write('{0:02d}'.format(today.day).encode('utf-8'))
    
    template.seek(32768)
    templateCoef.seek(1024)
    sampleTable = open("SampleTable.bin", "wb")

    foldersplit = "/"
    if platform.system() == "Windows":
        foldersplit = "\\"


    endCheck = []
    dupPreCheck = []

    sampleRate = []
    bitRate = 0
    smplVol = []
    smplDelay = []
    smplStart = []
    smplStartN = []
    smplLoop = []
    smplLoopType = []
    smplEnd = []
    rootKey = []
    fineTune = []
    loopTune = []
    
    sampleCount = -1
    sampleIDs = []
    multiCount = -1
    newBlock = 0
    sourceDir = tmpDir
    orDir = os.getcwd()
    os.chdir(sourceDir)
    counter = 0
    dupCheck = []
    dataChunkList = []
    
    for newBlock in range(8):
        for filename in sorted(os.listdir(os.getcwd()), key=os.path.getsize, reverse=True):
            if filename.endswith(".wav"):
                if ("=" + filename) in dupPreCheck:
                    continue
                fineTuneResult = 1024
                loopTuneResult = 1024
    
                dataChunkValid = False
                audioFile = open(filename, "rb")
                audioRead = audioFile.read()
                audioFile.seek(34)
                bitRate = int.from_bytes(audioFile.read(2), "little") / 8
            
                dataOff = audioRead.find(b'data')
                audioFile.seek(dataOff + 4)
                dataSz = int.from_bytes(audioFile.read(4), "little")

                finalSample = 0
                chnkOff = audioRead.find(b'smpl')
                if dataOff < chnkOff and chnkOff < dataOff + dataSz:
                    chnkOff = audioRead.find(b'smpl', 0, dataOff)
                    if chnkOff == -1:
                        chnkOff = audioRead.find(b'smpl', dataOff + dataSz)
                if chnkOff >= 0 and chnkOff + 64 < len(audioRead):
                    audioFile.seek(chnkOff + 56)
                    finalSample = int.from_bytes(audioFile.read(4), "little")
                else:
                    finalSample = (dataSz / bitRate)
                
                if template.tell() + finalSample + 33 >= 1048576 * (newBlock + 1):
                    audioFile.close()
                    continue
                
                print(filename)
                dupPreCheck.append("=" + filename)

                smplLoopMax = 0
                smplEndMax = 0
                template.seek(math.ceil(template.tell() / 32) * 32)
                
                if chnkOff >= 0:
                    dataChunkValid = True
                    sampleCount += 1
                    sampleIDs.append("=" + filename)
                    dataChunkList.append(dataChunkValid)
                    audioFile.seek(24)
                    sampleRate.append(int.from_bytes(audioFile.read(4), "little"))
                    audioFile.seek(chnkOff + 20)
                    rootKey.append(int.from_bytes(audioFile.read(4), "little"))
                    fineTuneResult = 1024 + round(float(int.from_bytes(audioFile.read(4), "little")) * 1024 / 100)
                    smplVol.append(127)
                    if chnkOff + 64 < len(audioRead):
                        audioFile.seek(chnkOff + 48)
                        smplStart.append(template.tell())
                        smplDelay.append(0)
                        smplStartN.append(0)
                        smplLoopType.append(int.from_bytes(audioFile.read(4), "little"))
                        smplLoop.append(int.from_bytes(audioFile.read(4), "little"))
                        smplEnd.append(int.from_bytes(audioFile.read(4), "little"))
                        loopTuneResult = 1024 + round(float(int.from_bytes(audioFile.read(4), "little")) * 1024 / 100)
                    else:
                        smplLoopType.append(0)
                        buff = int(dataSz / bitRate)
                        smplStart.append(template.tell())
                        smplDelay.append(0)
                        smplStartN.append(0)
                        smplLoop.append(buff - 2)
                        smplEnd.append(buff - 1)
                        loopTuneResult = 1024
                    fineTune.append(fineTuneResult)
                    loopTune.append(loopTuneResult)
        
                    if sampleRate[sampleCount] != 32000:
                        pitchFix = 12 * math.log(sampleRate[sampleCount] / 32000, 2)
                        pitchFixStep = math.floor(pitchFix)
                        pitchFixDecim = pitchFix - pitchFixStep
                        rootKey[sampleCount] -= pitchFixStep
                        fineTune[sampleCount] += int(pitchFixDecim * 1024)
                    if fineTune[sampleCount] < 0:
                        rootKey[sampleCount] += 1
                        fineTune[sampleCount] += 1024
                    elif fineTune[sampleCount] >= 2048:
                        rootKey[sampleCount] -= 1
                        fineTune[sampleCount] -= 1024
                
                for multiname in sorted(os.listdir(os.getcwd())):
                    if multiCount == 254 : continue
                    if multiname.endswith(".sfz"):
                        sfzFile = open(os.getcwd() + foldersplit + multiname, "r")
                        sfzText = "   \n" + sfzFile.read()
                        sfzFile.close()
                        RegionList = sfzText.split("<region>")
                        if len(RegionList) > 1:
                            for i in range(min(16, len(RegionList) - 1)):
                                if "=" + filename in RegionList[i + 1] and dataChunkValid == False:
                                    buff = int(dataSz / bitRate)
                                    
                                    audioFile.seek(24)
                                    sampleRatePrep = (int.from_bytes(audioFile.read(4), "little"))
                                    if "loop_mode=loop_sustain" in RegionList[i + 1] or "loop_mode=loop_continuous" in RegionList[i + 1]:
                                        if "loop_type=alternate" in RegionList[i + 1]:
                                            smplLoopTypePrep = (1)
                                        else:
                                            reverseFind = re.findall('direction=reverse', RegionList[i + 1])
                                            if len(reverseFind) > 0:
                                                smplLoopTypePrep = (6)
                                            else:
                                                smplLoopTypePrep = (0)
                                    else:
                                        reverseFind = re.findall('direction=reverse', RegionList[i + 1])
                                        if len(reverseFind) > 0:
                                            smplLoopTypePrep = (6)
                                        else:
                                            smplLoopTypePrep = (2)
                                    rootKeyFind = re.findall('pitch_keycenter=(\d+)', RegionList[i + 1])
                                    rootKeyPrep = 60
                                    if len(rootKeyFind) > 0:
                                        rootKeyPrep = (int(rootKeyFind[0]))

                                    smplDelayFind = re.findall('delay_samples=(\d+)', RegionList[i + 1])
                                    smplDelayPrep = 0
                                    if len(smplDelayFind) > 0:
                                        smplDelayPrep = (int(smplDelayFind[0]))

                                    smplStartFind = re.findall('offset=(\d+)', RegionList[i + 1])
                                    smplStartPrep = 0
                                    if len(smplStartFind) > 0:
                                        smplStartPrep = (int(smplStartFind[0]))
                                        
                                    smplLoopFind = re.findall('loop_start=(\d+)', RegionList[i + 1])
                                    smplLoopPrep = (buff - 2)
                                    if len(smplLoopFind) > 0 and ("loop_mode=loop_sustain" in RegionList[i + 1] or "loop_mode=loop_continuous" in RegionList[i + 1]):
                                        smplLoopPrep = (int(smplLoopFind[0]))
                                        
                                    smplEndFind = re.findall('loop_end=(\d+)', RegionList[i + 1])
                                    smplEndPrep = (buff - 1)
                                    if len(smplEndFind) > 0 and ("loop_mode=loop_sustain" in RegionList[i + 1] or "loop_mode=loop_continuous" in RegionList[i + 1]):
                                        smplEndPrep = (int(smplEndFind[0]))
                                        
                                    smplVolFind = re.findall('amplitude=(\d+.?\d*)', RegionList[i + 1])
                                    smplVolPrep = 127
                                    if len(smplVolFind) > 0:
                                        smplVolPrep = (round(float(max(0,min(100,float(smplVolFind[0])))) * 1.27))
                        
                                    smplTuneFind = re.findall('\ntune=(-?\d+.?\d*)', RegionList[i + 1])
                                    if len(smplTuneFind) > 0:
                                        fineTuneResult = 1024 + round(float(smplTuneFind[0]) * 1024 / 100)
                                    loopTuneFind = re.findall('looptune=(-?\d+.?\d*)', RegionList[i + 1])
                                    if len(loopTuneFind) > 0:
                                        loopTuneResult = 1024 + round(float(loopTuneFind[0]) * 1024 / 100)

                                    duped = False

                                    compare1 = [template.tell(), smplStartPrep, smplLoopTypePrep, rootKeyPrep, smplLoopPrep, smplEndPrep, smplVolPrep, fineTuneResult, loopTuneResult]

                                    for k in range(sampleCount + 1):
                                        compare2 = [smplStart[k], smplStartN[k], smplLoopType[k], rootKey[k], smplLoop[k], smplEnd[k], smplVol[k], fineTune[k], loopTune[k]]
                                        if compare1 == compare2:
                                            duped = True

                                    if duped == True:
                                        continue
                                    
                                    sampleCount += 1
                                    dataChunkList.append(dataChunkValid)
                                    sampleIDs.append("=" + filename)
                                    
                                    sampleRate.append(sampleRatePrep)
                                    smplLoopType.append(smplLoopTypePrep)
                                    rootKey.append(rootKeyPrep)
                                    smplStart.append(template.tell())
                                    smplStartN.append(smplStartPrep)
                                    smplDelay.append(smplDelayPrep)
                                    smplLoop.append(smplLoopPrep)
                                    smplEnd.append(smplEndPrep)
                                    smplVol.append(smplVolPrep)
                                    
                                    fineTune.append(fineTuneResult)
                                    loopTune.append(loopTuneResult)
        
                                    if sampleRate[sampleCount] != 32000:
                                        pitchFix = 12 * math.log(sampleRate[sampleCount] / 32000, 2)
                                        pitchFixStep = math.floor(pitchFix)
                                        pitchFixDecim = pitchFix - pitchFixStep
                                        rootKey[sampleCount] -= pitchFixStep
                                        fineTune[sampleCount] += int(pitchFixDecim * 1024)
                                    if fineTune[sampleCount] < 0:
                                        rootKey[sampleCount] += 1
                                        fineTune[sampleCount] += 1024
                                    elif fineTune[sampleCount] >= 2048:
                                        rootKey[sampleCount] -= 1
                                        fineTune[sampleCount] -= 1024
        
                audioFile.close()
                #if smplLoopType[sampleCount] == 1:
                    #print("WARNING: ping-pong looping not fully supported!")
                if filename not in endCheck:
                    DPCM.Encode(filename,smplLoopType[sampleCount],smplLoop[sampleCount],smplEnd[sampleCount],VerboseMode)
                endCheck.append(filename)

                coefIn = open(filename + "_exp.bin", "rb")
                deltaIn = open(filename + "_delt.bin", "rb")
                deltaIn.seek(0,2)
                fullSize = deltaIn.tell()
                deltaIn.seek(0)

                if fullSize >= 1015806:
                    print("Error: at least one sample is compressed larger than 992KB!")
                    return

                template.seek(math.ceil(template.tell() / 32) * 32)
                
                templateCoef.write(coefIn.read())
                template.write(deltaIn.read())
                coefIn.close()
                deltaIn.close()
                counter += 1
        template.seek(1048576 * (newBlock + 1) + 32768)
        templateCoef.seek(1048576 * (newBlock + 1) + 1024)
    os.chdir(orDir)

    template.seek(96)
    template.write(((sampleCount + 1)).to_bytes(2,"big"))
    for i in range(sampleCount + 1):
        for j in range(1):
            #if (smplVol[i] * 1000000 + smplStart[i] / 16 + smplLoopType[i] * 20000000 + rootKey[i] * 40000000) in dupCheck:
                #continue
            sampleTable.write((smplVol[i]).to_bytes(1,"big"))
            sampleTable.write((smplStart[i] + smplStartN[i] + smplDelay[i]).to_bytes(3, "big"))
            sampleTable.write((smplStart[i] + smplLoop[i]).to_bytes(3, "big"))
            sampleTable.write((smplStart[i] + smplEnd[i]).to_bytes(3, "big"))
            sampleTable.write(b'\x00\x00')
            if smplLoopType[i] == 6:
                sampleTable.write(b'\x06')
            elif (smplEnd[i] == 0 or (smplEnd[i] - smplLoop[i] < 4) or smplLoopType[i] == 2):
                sampleTable.write(b'\x02')
            elif smplLoopType[i] == 1:
                sampleTable.write(b'\x01')
            else:
                sampleTable.write(b'\x00')
            sampleTable.write(rootKey[i].to_bytes(1, "big"))
            sampleTable.write(fineTune[i].to_bytes(2, "big"))
            sampleTable.write(loopTune[i].to_bytes(2, "big"))

    sampleTable.close()
    sampleTable = open("SampleTable.bin", "rb+")
    sampleTable.seek(0,2)
    waveOffset = 8388608 - sampleTable.tell()
    sampleTable.seek(0)
    template.seek(128)
    template.write(waveOffset.to_bytes(4,"big"))
    template.seek(waveOffset)
    template.write(sampleTable.read())
    sampleTable.close()
    templateCoef.close()

    multiTable = open("MultiTable.bin", "wb")

    for filename in sorted(os.listdir(sourceDir)):
        if multiCount == 254 : continue
        if filename.endswith(".sfz"):
            multiName = filename.replace(".sfz","")[4:]
            if len(multiName) > 12:
                multiName = multiName[:12]
            elif len(multiName) < 12:
                for i in range(12 - len(multiName)):
                    multiName = multiName + " "
            print(multiName)
            
            multiCount += 1
            sfzFile = open(sourceDir + foldersplit + filename, "r")
            sfzText = "   \n" + sfzFile.read()
            sfzFile.close()
            
            sampleNum = [65535,65535,65535,65535,65535,65535,65535,65535,
                     65535,65535,65535,65535,65535,65535,65535,65535]
            sampleHiInt = [127,127,127,127,127,127,127,127,
                       127,127,127,127,127,127,127,127]
            
            RegionList = sfzText.split("<region>")
            if len(RegionList) > 1:
                for i in range(min(16, len(RegionList) - 1)):
                    sampleIDList = re.findall("sample=.+\.wav",RegionList[i + 1])
                    if len(sampleIDList) > 0:
                        sampleIDList[0] = "=" + (sampleIDList[0].split("="))[1]
                        for j in range(sampleCount + 1):
                            if sampleIDList[0] == sampleIDs[j]:
                                if dataChunkList[j] == False:
                                    volumeCheck = 127
                                    if len(re.findall("amplitude=(\d+.?\d*)",RegionList[i + 1])) > 0:
                                        volumeCheck = round(float(max(0,min(100,float(re.findall("amplitude=(\d+.?\d*)",RegionList[i + 1])[0])))) * 1.27)
                                    startCheck = 0
                                    if len(re.findall("offset=(\d+)",RegionList[i + 1])) > 0:
                                        startCheck = int(re.findall("offset=(\d+)",RegionList[i + 1])[0])
                                    loopTypeCheck = 0
                                    if "loop_type=alternate" in RegionList[i + 1]:
                                        loopTypeCheck = 1
                                    elif "direction=reverse" in RegionList[i + 1]:
                                        loopTypeCheck = 6
                                    elif "loop_mode=loop_continuous" not in RegionList[i + 1] and "loop_mode=loop_sustain" not in RegionList[i + 1]:
                                        loopTypeCheck = 2
                                    if volumeCheck == smplVol[j]:
                                        if startCheck == smplStartN[j]:
                                            if loopTypeCheck == smplLoopType[j]:
                                                print("Match!")
                                                sampleNum[i] = j
                                else:
                                    sampleNum[i] = j
                                    
        
                    sampleHi = re.findall("hikey=[0-9]+",RegionList[i + 1])
                    if len(sampleHi) > 0:
                        sampleHiInt[i] = int(((sampleHi[0]).split("="))[1])
            

            multiTable.write(multiName.encode("ascii"))
            for i in range(16):
                multiTable.write(sampleHiInt[i].to_bytes(1,"big"))
            for i in range(16):
                multiTable.write(sampleNum[i].to_bytes(2,"big"))
    multiOffset = waveOffset - multiTable.tell()
    multiTable.close()
    multiTable = open("MultiTable.bin", "rb")
    template.seek(98)
    template.write((multiCount + 1).to_bytes(2,"big"))
    template.seek(132)
    template.write(multiOffset.to_bytes(4,"big"))
    template.seek(multiOffset)
    template.write(multiTable.read())

    multiTable.close()
    patch80Offset = multiOffset
    patch990Offset = multiOffset
    patch2080Offset = multiOffset
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx"):
        template.seek(140)
        Import80.run(sourceDir + foldersplit + "Patches" + foldersplit + "80")
        patch80Table = open(sourceDir + foldersplit + "Patches" + foldersplit + "80.patches", "rb")
        patch80Table.seek(0,2)
        patch80Offset -= patch80Table.tell()
        patch80Count = int(patch80Table.tell() / 362)
        patch80Table.seek(0)
        template.write(patch80Offset.to_bytes(4,"big"))
        template.write(patch80Offset.to_bytes(4,"big"))
        template.seek(188)
        template.write(patch80Offset.to_bytes(4,"big"))
        template.seek(102)
        template.write(patch80Count.to_bytes(2,"big"))
        template.seek(patch80Offset)
        template.write(patch80Table.read())
        patch80Table.close()
    else:
        template.seek(140)
        template.write(patch80Offset.to_bytes(4,"big"))
        template.write(patch80Offset.to_bytes(4,"big"))
        template.seek(102)
        template.write(b'\x00\x00')
    patch990Offset = patch80Offset
    template.seek(128 + 1048576)
    template.write(patch80Offset.to_bytes(4,"big"))
    template.write(patch80Offset.to_bytes(4,"big"))
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "990.syx"):
        template.seek(140 + 1048576)
        Import990.run(sourceDir + foldersplit + "Patches" + foldersplit + "990")
        patch990Table = open(sourceDir + foldersplit + "Patches" + foldersplit + "990.patches", "rb")
        patch990Table.seek(0,2)
        patch990Offset -= patch990Table.tell()
        patch990Count = int(patch990Table.tell() / 379)
        patch990Table.seek(0)
        template.write(patch990Offset.to_bytes(4,"big"))
        template.write(patch990Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576)
        template.write(patch990Count.to_bytes(2,"big"))
        template.seek(patch990Offset)
        template.write(patch990Table.read())
        patch990Table.close()
    else:
        template.seek(96 + 1048576)
        template.write(patch990Offset.to_bytes(4,"big"))
        template.write(patch990Offset.to_bytes(4,"big"))
        template.seek(140 + 1048576)
        template.write(patch990Offset.to_bytes(4,"big"))
        template.write(patch990Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576)
        template.write(b'\x00\x00')
    patch2080Offset = patch990Offset
    
    template.seek(128 + 1048576 * 2)
    template.write(patch990Offset.to_bytes(4,"big"))
    template.write(patch990Offset.to_bytes(4,"big"))
    template.seek(140 + 1048576 * 2)
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "2080.syx"):
        Import2080.run(sourceDir + foldersplit + "Patches" + foldersplit + "2080")
        patch2080Table = open(sourceDir + foldersplit + "Patches" + foldersplit + "2080.patches", "rb")
        patch2080Table.seek(0,2)
        patch2080Offset -= patch2080Table.tell()
        patch2080Count = int(patch2080Table.tell() / 401)
        patch2080Table.seek(0)
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576 * 2)
        template.write(patch2080Count.to_bytes(2,"big"))
        template.seek(patch2080Offset)
        template.write(patch2080Table.read())
        patch2080Table.close()
    else:
        template.seek(96 + 1048576 * 2)
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.seek(140 + 1048576 * 2)
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576 * 2)
        template.write(b'\x00\x00')
    

    template.close()

    #os.remove("SampleTable.bin")
    #os.remove("MultiTable.bin")

