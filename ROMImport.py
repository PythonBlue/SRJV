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

    sampleRate = []
    bitRate = 0
    smplStart = []
    smplLoop = []
    smplEnd = []
    rootKey = []
    fineTune = []
    sampleCount = -1
    sampleIDs = []
    multiCount = -1
    newBlock = 0
    sourceDir = tmpDir

    currentRegion = -1
    RegName = []
    RegRoot = []
    RegLoop = []
    RegEnd = []
    RegIndex = []
    RegEna = []
    smplCount = []
    
    SetName = False
    SetHi = False
    SetRoot = False
    SetLoop = False
    SetEnd = False
    SetIndex = False
    SetEna = False
    
    for sfzName in sorted(os.listdir(sourceDir)):
            if sfzName.endswith(".sfz"):
                sfzTemp = open(sourceDir + foldersplit + sfzName, "r")
                sfzTemp2 = open(sourceDir + foldersplit + "tmp", "w")
                for line in sfzTemp.readlines():
                    if line.startswith("<region>"):
                        if currentRegion >= 0:
                            if SetName == False:
                                RegName.append("")
                            if SetHi == False:
                                line = "hikey=127\n" + line
                            if SetRoot == False:
                                RegRoot.append(60)
                            if SetEna == False:
                                RegEna.append(0)
                            if SetLoop == False:
                                RegLoop.append(-1)
                            if SetEnd == False:
                                RegEnd.append(-1)
                        currentRegion += 1
                        RegIndex.append(currentRegion)
                        SetName = False
                        SetHi = False
                        SetRoot = False
                        SetLoop = False
                        SetEnd = False
                        SetIndex = False
                        SetEna = False
                    else:
                        if line.startswith("sample=") and SetName == False:
                            RegName.append(line.split("=")[1].rstrip("\n"))
                            SetName = True
                            line = line + "ID=" + str(currentRegion) + "\n"
                        if line.startswith("hikey=") and SetHi == False:
                            SetHi = True
                        if line.startswith("pitch_keycenter=") and SetRoot == False:
                            RegRoot.append(int(line.split("=")[1].rstrip("\n")))
                            SetRoot = True
                        if line.startswith("loop_mode=") and SetEna == False:
                            check = line.split("=")[1].rstrip("\n")
                            if check == "loop_sustain" or check == "loop_continuous":
                                RegEna.append(1)
                            else:
                                RegEna.append(0)
                            SetEna = True
                        if line.startswith("loop_start=") and SetLoop == False:
                            RegLoop.append(int(line.split("=")[1].rstrip("\n")))
                            SetLoop = True
                        if line.startswith("loop_end=") and SetEnd == False:
                            RegEnd.append(int(line.split("=")[1].rstrip("\n")))
                            SetEnd = True
                    sfzTemp2.write(line)
                sfzTemp.close()
                sfzTemp2.close()
                os.remove(sourceDir + foldersplit + sfzName)
                os.rename(sourceDir + foldersplit + "tmp", sourceDir + foldersplit + sfzName)

    smplCountPrep = list(zip(RegName, RegRoot, RegLoop, RegEnd))
    for item in smplCountPrep:
        if item not in smplCount:
            smplCount.append(item)
    RegName, RegRoot, RegLoop, RegEnd = zip(*smplCount)

    for i in range(len(RegName)):
        if RegName[i] == "":
            continue
        try:
            audioFile = open(sourceDir + foldersplit + RegName[i], "rb")
        except:
            print(RegName[i] + " not found! Cannot proceed!")
            return
        sampleCount += 1
        sampleIDs.append(i)
        print(RegName[i])
        
        audioRead = audioFile.read()
        audioFile.seek(24)
        sampleRate.append(int.from_bytes(audioFile.read(4), "little"))
        audioFile.seek(34)
        bitRate = int.from_bytes(audioFile.read(2), "little") / 8
        dataOff = audioRead.find(b'data')
        audioFile.seek(dataOff + 4)
        dataSz = int(int.from_bytes(audioFile.read(4), "little") / bitRate)

        if RegEna[i] == 1 and RegLoop[i] > -1 and RegEnd[i] > -1:
            smplLoop.append(RegLoop[i])
            smplEnd.append(RegEnd[i])
        else:
            smplLoop.append(dataSz - 2)
            smplEnd.append(dataSz - 1)
            
        if smplEnd[i] == -1:
            smplEnd[i] = dataSz
        
        rootKey.append(RegRoot[i])
            
        fineTune.append(1024)
        
        if sampleRate[sampleCount] != 32000:
            pitchFix = 12 * math.log(sampleRate[sampleCount] / 32000, 2)
            pitchFixStep = math.floor(pitchFix)
            pitchFixDecim = pitchFix - pitchFixStep
            rootKey[sampleCount] -= pitchFixStep
            fineTune[sampleCount] += int(pitchFixDecim * 1024)

        audioFile.close()
        DPCM.Encode(sourceDir + foldersplit + RegName[i],i,smplLoop[i],smplEnd[i],VerboseMode,False)

        coefIn = open(sourceDir + foldersplit + str(i) + "_exp.bin", "rb")
        deltaIn = open(sourceDir + foldersplit + str(i) + "_delt.bin", "rb")
        deltaIn.seek(0,2)
        fullSize = deltaIn.tell()
        deltaIn.seek(0)
        
        if template.tell() + fullSize > 1048576 * (newBlock + 1):
            newBlock += 1
            template.seek(1048576 * newBlock + 32768)
            templateCoef.seek(1048576 * newBlock + 1024)

        template.seek(math.ceil(template.tell() / 32) * 32)
        smplStart.append(template.tell())
        templateCoef.write(coefIn.read())
        template.write(deltaIn.read())
        coefIn.close()
        deltaIn.close()

    template.seek(96)
    template.write((sampleCount + 1).to_bytes(2,"big"))
    for i in range(sampleCount + 1):
        sampleTable.write(b'\x7f')
        sampleTable.write(smplStart[i].to_bytes(3, "big"))
        sampleTable.write((smplStart[i] + smplLoop[i]).to_bytes(3, "big"))
        sampleTable.write((smplStart[i] + smplEnd[i]).to_bytes(3, "big"))
        sampleTable.write(b'\x00\x00')
        if smplLoop[i] == 0 or (smplEnd[i] - smplLoop[i] < 4):
            sampleTable.write(b'\x02')
        else:
            sampleTable.write(b'\x00')
        sampleTable.write(rootKey[i].to_bytes(1, "big"))
        sampleTable.write(fineTune[i].to_bytes(2, "big"))
        sampleTable.write(b'\x04\x00')

    waveOffset = 8388608 - sampleTable.tell()
    sampleTable.close()
    sampleTable = open("SampleTable.bin", "rb+")
    sampleTable.seek(0)
    template.seek(128)
    template.write(waveOffset.to_bytes(4,"big"))
    template.seek(waveOffset)
    template.write(sampleTable.read())
    sampleTable.close()
    templateCoef.close()

    multiTable = open("MultiTable.bin", "wb")

    sampleIDCount = 0
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
            sfzText = sfzFile.read()
            sfzFile.close()
        
            sampleID = re.findall("ID=.+",sfzText)
            sampleNum = [65535,65535,65535,65535,65535,65535,65535,65535,
                     65535,65535,65535,65535,65535,65535,65535,65535]
            sampleHiInt = [127,127,127,127,127,127,127,127,
                       127,127,127,127,127,127,127,127]
        
            for i in range(min(16,len(sampleID))):
                sampleID[i] = (sampleID[i].split("="))[1]
                for j in range(len(sampleIDs)):
                    if sampleID[i] == sampleIDs[j]:
                        sampleNum[i] = j
        
            sampleHi = re.findall("hikey=.+",sfzText)
            for i in range(min(16,len(sampleHi))):
                sampleHiInt[i] = int((sampleHi[i].split("="))[1])
            

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

    template.seek(83)
    template.write(b'\x02')
    template.seek(140)
    patch80Offset = multiOffset
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx"):
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
        template.write(patch80Offset.to_bytes(4,"big"))
        template.write(patch80Offset.to_bytes(4,"big"))
        template.seek(102)
        template.write(b'\x00\x00')

    template.seek(83 + 1048576)
    template.write(b'\x03')
    template.seek(128 + 1048576)
    template.write(patch80Offset.to_bytes(4,"big"))
    template.write(patch80Offset.to_bytes(4,"big"))
    template.seek(140 + 1048576)
    patch990Offset = patch80Offset
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "990.syx"):
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
        template.write(patch990Offset.to_bytes(4,"big"))
        template.write(patch990Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576)
        template.write(b'\x00\x00')

    template.seek(83 + 1048576 * 2)
    template.write(b'\x05')
    template.seek(128 + 1048576 * 2)
    template.write(patch990Offset.to_bytes(4,"big"))
    template.write(patch990Offset.to_bytes(4,"big"))
    template.seek(140 + 1048576 * 2)
    patch2080Offset = patch990Offset
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
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576 * 2)
        template.write(b'\x00\x00')    
    

    template.close()

    #os.remove("SampleTable.bin")
    #os.remove("MultiTable.bin")

