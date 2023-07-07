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
    smplLoopType = []
    smplEnd = []
    rootKey = []
    fineTune = []
    sampleCount = -1
    sampleIDs = []
    multiCount = -1
    newBlock = 0
    sourceDir = tmpDir
    for filename in sorted(os.listdir(sourceDir)):
        if filename.endswith(".wav"):
            print(filename)
            sampleCount += 1
            sampleIDs.append(filename)
            audioFile = open(sourceDir + foldersplit + filename, "rb")
            audioRead = audioFile.read()
            audioFile.seek(24)
            sampleRate.append(int.from_bytes(audioFile.read(4), "little"))
            audioFile.seek(34)
            bitRate = int.from_bytes(audioFile.read(2), "little") / 8
            
            dataOff = audioRead.find(b'data')
            audioFile.seek(dataOff + 4)
            dataSz = int.from_bytes(audioFile.read(4), "little")
        
            audioFile.seek(0,2)
            audioFile.seek(-108,1)

            
            chnkOff = audioRead.find(b'smpl')
            if dataOff < chnkOff and chnkOff < dataOff + dataSz:
                chnkOff = audioRead.find(b'smpl', 0, dataOff)
                if chnkOff == -1:
                    chnkOff = audioRead.find(b'smpl', dataOff + dataSz)
            if chnkOff >= 0:
                audioFile.seek(chnkOff + 20)
                rootKey.append(int.from_bytes(audioFile.read(1), "little"))
                if chnkOff + 64 < len(audioRead):
                    audioFile.seek(chnkOff + 48)
                    smplLoopType.append(int.from_bytes(audioFile.read(4), "little"))
                    smplLoop.append(int.from_bytes(audioFile.read(4), "little"))
                    smplEnd.append(int.from_bytes(audioFile.read(4), "little"))
                else:
                    smplLoopType.append(0)
                    buff = int(dataSz / bitRate)
                    smplLoop.append(buff - 2)
                    smplEnd.append(buff - 1)
            else:
                smplLoopType.append(0)
                rootKey.append(60)
                buff = int(dataSz / bitRate)
                smplLoop.append(buff - 2)
                smplEnd.append(buff - 1)
            
            fineTune.append(1024)
        
            if sampleRate[sampleCount] != 32000:
                pitchFix = 12 * math.log(sampleRate[sampleCount] / 32000, 2)
                pitchFixStep = math.floor(pitchFix)
                pitchFixDecim = pitchFix - pitchFixStep
                rootKey[sampleCount] -= pitchFixStep
                fineTune[sampleCount] += int(pitchFixDecim * 1024)
        
            audioFile.close()
            DPCM.Encode(sourceDir + foldersplit + filename,sampleCount,smplLoop[sampleCount],smplEnd[sampleCount],VerboseMode,False)
            

            coefIn = open(sourceDir + foldersplit + filename + "_exp.bin", "rb")
            deltaIn = open(sourceDir + foldersplit + filename + "_delt.bin", "rb")
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
    template.write(((sampleCount + 1) * 2).to_bytes(2,"big"))
    for i in range(sampleCount + 1):
        for j in range(2):
            sampleTable.write(b'\x7f')
            sampleTable.write(smplStart[i].to_bytes(3, "big"))
            sampleTable.write((smplStart[i] + smplLoop[i]).to_bytes(3, "big"))
            sampleTable.write((smplStart[i] + smplEnd[i]).to_bytes(3, "big"))
            sampleTable.write(b'\x00\x00')
            if j == 1:
                sampleTable.write(b'\x06')
            elif (smplLoop[i] == 0 or (smplEnd[i] - smplLoop[i] < 4)):
                sampleTable.write(b'\x02')
            elif smplLoopType[i] == 1:
                sampleTable.write(b'\x01')
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
        
            sampleID = re.findall("sample=.+",sfzText)
            sampleNum = [65535,65535,65535,65535,65535,65535,65535,65535,
                     65535,65535,65535,65535,65535,65535,65535,65535]
            sampleHiInt = [127,127,127,127,127,127,127,127,
                       127,127,127,127,127,127,127,127]
        
            for i in range(min(16,len(sampleID))):
                sampleID[i] = (sampleID[i].split("="))[1]
                for j in range(len(sampleIDs)):
                    if sampleID[i] == sampleIDs[j]:
                        sampleNum[i] = j * 2
                        if multiName.find("REV") > -1:
                            sampleNum[i] += 1
        
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
    patch80Offset = multiOffset
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx"):
        template.seek(83)
        template.write(b'\x02')
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
    elif PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "990.syx"):
        template.seek(83)
        template.write(b'\x03')
        template.seek(140)
        patch990Offset = patch80Offset
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
    elif PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "2080.syx"):
        template.seek(83)
        template.write(b'\x05')
        template.seek(140)
        patch2080Offset = patch80Offset
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
        template.seek(140)
        template.write(patch80Offset.to_bytes(4,"big"))
        template.write(patch80Offset.to_bytes(4,"big"))
        template.seek(102)
        template.write(b'\x00\x00')
    template.seek(128 + 1048576)
    template.write(patch80Offset.to_bytes(4,"big"))
    template.write(patch80Offset.to_bytes(4,"big"))
    patch990Offset = patch80Offset
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "990.syx") and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx"):
        if os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "2080.syx"):
            template.seek(68 + 1048576)
            template.write(b'\x10')
        template.seek(83 + 1048576)
        template.write(b'\x03')
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
    elif PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "2080.syx") and not os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx"):
        template.seek(83 + 1048576)
        template.write(b'\x05')
        template.seek(140 + 1048576)
        patch2080Offset = patch990Offset
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
        template.seek(140 + 1048576)
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
    if PatchImport == True and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "80.syx") and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "990.syx") and os.path.exists(sourceDir + foldersplit + "Patches" + foldersplit + "2080.syx"):
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
        template.seek(140 + 1048576)
        template.write(patch2080Offset.to_bytes(4,"big"))
        template.seek(102 + 1048576 * 2)
        template.write(b'\x00\x00')
    

    template.close()

    #os.remove("SampleTable.bin")
    #os.remove("MultiTable.bin")

