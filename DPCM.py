import sys, math, platform

def logo(x):
    if x < 128:
        return 0
    elif x < 256:
        return 1
    elif x < 512:
        return 2
    elif x < 1024:
        return 3
    elif x < 2048:
        return 4
    elif x < 4096:
        return 5
    elif x < 8192:
        return 6
    elif x < 16384:
        return 7
    elif x < 32768:
        return 8
    elif x < 65536:
        return 9
    elif x < 131072:
        return 10
    elif x < 262144:
        return 11
    elif x < 524288:
        return 12
    elif x < 1048576:
        return 13
    elif x < 2097152:
        return 14
    else:
        return 15
    
def DPCMEncode(coefs, deltas, samples, offset, sampleStart, loopType, sampleLoop, smplEnd, VerboseMode):
    value = 0
    loopValue = 0
    loopCoef = 0
    invalue = 0
    offsetCheck = 0
    maxexp = 0

    loopDC = 0
    if loopType == 0:
        loopDC = (samples[smplEnd] - samples[sampleLoop - 1])
    loopLength = smplEnd - sampleLoop + 1
    loopAdjust = loopDC / loopLength
    if loopLength < 4:
        loopAdjust = 0
    if VerboseMode: print("sample loop DC offset: " + str(loopDC) + " (adj=" + str(loopAdjust) + ")")
    frameCount = math.ceil(smplEnd / 16)
    if smplEnd % 16 == 0 or int(smplEnd / 16) == int(sampleLoop / 16):
        frameCount += 1
    
    #encode all frames except the last one
    for frame in range(frameCount - 1):
        maxdelta = 0
        eval1 = []
        eval2 = []
        eval3 = []
        for i in range(16):
            off = frame * 16 + i
            if off > smplEnd:
                sample = 0
            else:
                sample = samples[off]
            if off == sampleLoop:
                loopFrame = frame
            if (off >= sampleLoop):
                adj = int(loopAdjust * (off - sampleLoop))
                sample -= adj
            delta = (sample - invalue)
            eval1.append(delta)
            #if delta < 0:
                #delta += 1
            maxdelta = max(maxdelta, abs(delta))
            invalue = sample
            
        #decide on coefficient
        exp = int(logo(maxdelta))
        if (exp < 0):
            exp = 0
        elif (exp > 15):
            exp = 15

        for i in range(16):
            eval2.append((eval1[i] >> exp) % 2)
            eval3.append((eval1[i] >> (exp + 1)) % 2)
        if 1 not in eval2 and exp > 0:
            exp += 1
            if 1 not in eval3 and exp > 0:
                exp += 1
            
        if maxexp < exp:
            maxexp = exp

        #store exponent
        if ((frame & 1) == 0):
            coefs[int(frame / 2)] = ((int.from_bytes(coefs[int(frame / 2)],"big") & 0xf0) | exp).to_bytes(1,"big")
        else:
            coefs[int(frame / 2)] = ((int.from_bytes(coefs[int(frame / 2)],"big") & 0x0f) | (exp << 4)).to_bytes(1,"big")

        #compute coefficient only once
        coef = 1 << exp

        #compute compressed sample values
        for i in range(16):
            off = frame * 16 + i
            if off > smplEnd:
                break
            sample = samples[off]
            if (off >= sampleLoop):
                adj = int(loopAdjust * (off - sampleLoop))
                sample -= adj
            delta = (sample - value)
            if delta > (127 << exp):
                delta = (127 << exp)
            elif delta < (-128 << exp):
                delta = (-128 << exp)
            #quantize delta
            deltas[off] = (int((delta) >> exp) & 0xff).to_bytes(1,"big")

            #predict
            qsample = int.from_bytes(deltas[off], "little")
            if qsample >= 128:
                qsample -= 256
            preddelta = qsample << exp

            if (off == sampleLoop) and loopLength >= 4:
                loopValue = value
                loopCoef = exp

            value += preddelta
    #second pass: find smallest exponent in the loop
    minexp = 15
    for i in range(sampleLoop, (frameCount - 1) * 16, 16):
        sampleId = i - sampleStart
        if sampleId > smplEnd:
            break
        frame = int(sampleId / 16)
        coef = int.from_bytes(coefs[int(frame / 2)], "big")

        if (frame & 1) == 0:
            exp = coef & 15
        else:
            exp = (coef >> 4) & 15
        if (exp < minexp):
            minexp = exp

    #third pass: count frames with minimal exponent in the loop
    minexpcnt = 0
    for i in range(sampleLoop, (frameCount - 1) * 16, 16):
        sampleId = i - sampleStart
        if sampleId > smplEnd:
            break
        frame = int(sampleId / 16)
        coef = int.from_bytes(coefs[int(frame / 2)], "big")

        if (frame & 1) == 0:
            exp = coef & 15
        else:
            exp = (coef >> 4) & 15
        if(exp == minexp):
            minexpcnt += 1

    if VerboseMode: print("minimal exponent = " + str(minexp) + " (" + str(minexpcnt) + "x)")

    #fourth pass: compute current DC offset and print it for debugging
    decodeValue = loopValue
    for i in range(sampleLoop, (frameCount - 1) * 16):
        sampleId = i - sampleStart
        if sampleId > smplEnd:
            break
        frame = int(sampleId / 16)
        coef = int.from_bytes(coefs[int(frame / 2)], "big")

        if (frame & 1) == 0:
            exp = coef & 15
        else:
            exp = (coef >> 4) & 15
            
        sample = int.from_bytes(deltas[i], "big")
        if sample >= 128:
            sample -= 256
        delta = sample << exp
        decodeValue += delta
    if VerboseMode: print("value=" + str(value) + ", decodeValue=" + str(decodeValue))


    if int(smplEnd / 16) == int(sampleLoop / 16):
        print("Caution: loop in same frame")
        print("")
        return
    
    frame = frameCount - 1
    end = smplEnd & 0x0f

    #find minimum/maximum of delta in the current frame
    maxdelta = 0
    eval1 = []
    eval2 = []
    eval3 = []
    for i in range(min(16,end + 2)):
        off = frame * 16 + i
        if off > smplEnd:
            sample = samples[sampleLoop + off - smplEnd]
        sample = samples[off]
        if (off >= sampleLoop):
            adj = int(loopAdjust * (off - sampleLoop))
            sample -= adj
        delta = (sample - invalue)
        #if delta < 0:
            #delta += 1
        eval1.append(delta)
        maxdelta = max(maxdelta, abs(delta))
        invalue = sample
        
    lastSample = samples[smplEnd]
    lastSample -= int(loopAdjust * loopLength)
    loopDelta = (loopValue - lastSample)
    if loopLength < 4 or loopType != 0:
        loopDelta = 0
        
    adjust = int(loopDelta / (end + 1))
    
    if VerboseMode: print("loop delta: " + str(loopDelta) + " (" + str((samples[sampleLoop - 1] - samples[smplEnd])) + ")")
    if (end != 0):
        if int(abs(loopDelta / (end + 1))) > maxdelta:
            maxdelta = int(abs(loopDelta / (end + 1)))
    elif int(abs(loopDelta) > maxdelta):
        maxdelta = abs(loopDelta)
    if VerboseMode: print("loop adjust: " + str(adjust) + " over " + str(end + 1) + " samples")


    #decide on coefficient
    exp = int(logo(maxdelta))
    if (exp < 0):
        exp = 0
    if (exp > 15):
        exp = 15

    for i in range(min(16,end + 2)):
        eval2.append((eval1[i] >> exp) % 2)
        eval3.append((eval1[i] >> (exp + 1)) % 2)
    if 1 not in eval2 and exp > 0:
        exp += 1
        if 1 not in eval3 and exp > 0:
            exp += 1

    if maxexp < exp:
        maxexp = exp
        
    coef = 1 << exp
    quant = int(adjust / coef * (end + 1))
    quant *= coef
    if (quant != loopDelta):
        if VerboseMode: print("inherent DC offset: " + str(quant - loopDelta))
    #store exponent
    if ((frame & 1) == 0):
        coefs[int(frame / 2)] = ((int.from_bytes(coefs[int(frame / 2)],"big") & 0xf0) | exp).to_bytes(1,"big")
    else:
        coefs[int(frame / 2)] = ((int.from_bytes(coefs[int(frame / 2)],"big") & 0x0f) | (exp << 4)).to_bytes(1,"big")

    for i in range(end + 1):
        off = frame * 16 + i
        sample = samples[off]
        adj = int(loopAdjust * (off - sampleLoop))
        sample -= adj
        delta = sample - value + adjust
        if delta > (127 << exp):
            delta = (127 << exp)
        elif delta < (-128 << exp):
            delta = (-128 << exp)

        #quantize delta
        deltas[off] = (int((delta) >> exp) & 0xff).to_bytes(1,"big")

        #predict
        qsample = int.from_bytes(deltas[off], "big")
        if qsample >= 128:
            qsample -= 256
        preddelta = qsample << exp
        value += preddelta
    

    #Last passes: adjust using minimum
    residualDC = 0
    if loopType == 0:
        residualDC = (loopValue - value)
    if abs(residualDC) >> minexp == 0:
        residualDC = 0
    for expa in range(maxexp - minexp,-1,-1):
        adjSign = 0
        if math.floor(residualDC >> (minexp + expa)) < 0:
            adjSign = -1
        elif residualDC >> (minexp + expa) > 0:
            adjSign = 1
        if (residualDC % (1 << (minexp + expa + 8)) >= 0) and residualDC != 0:
            adjustment = residualDC >> (minexp + expa)
            if VerboseMode: print("correcting error exactly: " + str(adjustment) + " (" + str(residualDC) + ")")
            #adjusting once per sample
            for i in range(sampleLoop, (frameCount - 1) * 16):
                sampleId = i - sampleStart
                frame = int(sampleId / 16)
                coef = int.from_bytes(coefs[int(frame / 2)], "big")
                if ((frame & 1) == 0):
                    exp = coef & 0x0f
                else:
                    exp = (coef >> 4) & 0x0f
                    
                if (exp == (minexp + expa) and adjustment != 0):
                    #perform adjustment
                    if (0 < int.from_bytes(deltas[i], "big") < 127) or (255 > int.from_bytes(deltas[i], "big") > 128):
                        byteConv = (int.from_bytes(deltas[i],"big") + adjSign) % 256
                        deltas[i] = byteConv.to_bytes(1,"big")
                        adjustment -= adjSign
                        residualDC -= (adjSign << (minexp + expa))

            if VerboseMode: print("adjustment: " + str(adjustment))

    decodeValue = 0
    for i in range(sampleLoop, smplEnd + 1):
        sampleId = i - sampleStart
        frame = int(sampleId / 16)
        coef = int.from_bytes(coefs[int(frame / 2)], "big")

        if ((frame & 1) == 0):
            exp = coef & 0x0f
        else:
            exp = (coef >> 4) & 0x0f
        sample = int.from_bytes(deltas[i],"big")
        if sample >= 128:
            sample -= 256
        delta = sample << exp
        if delta >= 128 << exp:
            delta = exp % (128 << exp)
        elif delta < -128 << exp:
            delta = delta % (128 << exp) - (128 << exp)
        decodeValue += delta
    if abs(decodeValue) >> minexp == 0:
        decodeValue = 0
    #check if there is some DC offset
    if (decodeValue != 0 and smplEnd - sampleLoop > 1) and loopType == 0:
        print("DC offset: " + str(decodeValue))
    elif VerboseMode:
        print("no DC offset")
    print("")

def Encode(fname, loopType, smplLoop, smplEnd, VerboseMode):
    wav = open(fname, "rb")
    #print(fname)
    audioFile = wav.read()
    wav.seek(0)
    bitRate = audioFile[34]
    if bitRate != 24 and bitRate != 32:
        print("Error: unsupported bitrate of input!")
        return
    dataChk = audioFile.find(b'data')
    wav.seek(dataChk + 4)
    sampleCount = int(int.from_bytes(wav.read(4), "little") / (bitRate / 8))
    wav.seek(dataChk + 4)
    sampleStart = 0
    smplLoop = int(smplLoop)
    smplEnd = int(smplEnd)
    if smplLoop == 0 and smplEnd == 0:
        smplLoop = sampleCount - 1
        smplEnd = sampleCount
    #smplLoop += 1
    #smplEnd += 1
    
    coefLen = math.ceil((smplEnd + 1) / 32)
	
    coefs = []
    for i in range(coefLen):
        coefs.append(b'\x00')
    deltas = []
    for i in range(coefLen * 32):
        deltas.append(b'\x00')
    print("sample loop: " + str(smplLoop) + " to " + str(smplEnd))

    wav.seek(dataChk + 8)
    wavSamplesPrep = []
    wavSamples = []
    for i in range(smplEnd):
        End1 = int.from_bytes(wav.read(1), "big")
        End2 = int.from_bytes(wav.read(1), "big")
        End3 = int.from_bytes(wav.read(1), "big")
        Endian = (End3 << 16) + (End2 << 8) + End1
        End4 = 0
        if bitRate > 16:
            if bitRate > 24:
                End4 = int.from_bytes(wav.read(1), "big")
                Endian = (End4 << 16) + (End3 << 16) + (End2 << 8) + End1
        if Endian >= 1 << (bitRate - 1):
            Endian -= 1 << bitRate
        #if i == 0 and Endian != 0:
            #wavSamplesPrep.append(0)
        wavSamplesPrep.append(Endian)
        if loopType == 1 and i >= smplEnd - 1:
            continue
    for i in range(16):
        if loopType == 1:
            wavSamplesPrep.append(0)
        else:
            wavSamplesPrep.append(wavSamplesPrep[smplLoop + i - 1])
    sampleCount = len(wavSamplesPrep)
    prevDelta = 0
    for i in range(sampleCount):
        wavSamples.append((wavSamplesPrep[i] << 1) >> (bitRate - 16))

    DPCMEncode(coefs, deltas, wavSamples, 0, sampleStart, loopType, smplLoop, smplEnd, VerboseMode)
    foldersplit = "/"
    if platform.system() == "Windows":
        foldersplit = "\\"
        
    try:
        output1 = open(fname + "_exp.bin", "wb")
        for i in range(coefLen):
            output1.write(coefs[i])
        output1.close()
    except:
        print("Error: cannot open exponent file!")
        return
    try:
        output2 = open(fname + "_delt.bin",  "wb")
        for i in range(coefLen * 32):
            output2.write(deltas[i])
        output2.close()
    except:
        print("Error: cannot open delta file!")
        return
