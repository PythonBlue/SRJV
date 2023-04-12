import os

offset = 0
bits = []
bitResult = []
isSysex = False

def parseBits(bitNum):
    global offset
    global bits
    global out_file
    global bitResult
    for k in range(8):
        if k < bitNum:
            bitResult.append(bits[offset])
        offset += 1

def run(in_string):
    global offset
    global bits
    global out_file
    global bitResult
    in_file = open(in_string + ".syx", "rb")
    out_file = open(in_string + ".patches", "wb")
    if in_file.read(1) == b'\xf0':
        isSysex = True
    startOffset = 0
    if isSysex == True:
        in_file.seek(9)
        firstMessage = int.from_bytes(in_file.read(1),"big")
        if (firstMessage < 32):
            startOffset = 12
    in_file.seek(0,2)
    patchCount = int((in_file.tell() - startOffset) / 645)

    in_file.seek(startOffset)
        
    for i in range(patchCount):
        scan = in_file.tell()
        result = out_file.tell()
        bits.clear()
        bitResult.clear()
        if isSysex == True:
            in_file.seek(scan + 9)
            for j in range(74):
                byte = int.from_bytes(in_file.read(1), "big")
                bits.append(byte & 1)
                bits.append((byte & 2) >> 1)
                bits.append((byte & 4) >> 2)
                bits.append((byte & 8) >> 3)
                bits.append((byte & 16) >> 4)
                bits.append((byte & 32) >> 5)
                bits.append((byte & 64) >> 6)
                bits.append((byte & 128) >> 7)
            for k in range(4):
                in_file.seek(11,1)
                for j in range(129):
                    byte = int.from_bytes(in_file.read(1), "big")
                    bits.append(byte & 1)
                    bits.append((byte & 2) >> 1)
                    bits.append((byte & 4) >> 2)
                    bits.append((byte & 8) >> 3)
                    bits.append((byte & 16) >> 4)
                    bits.append((byte & 32) >> 5)
                    bits.append((byte & 64) >> 6)
                    bits.append((byte & 128) >> 7)
        else:
            for j in range(590):
                byte = int.from_bytes(in_file.read(1), "big")
                bits.append(byte & 1)
                bits.append((byte & 2) >> 1)
                bits.append((byte & 4) >> 2)
                bits.append((byte & 8) >> 3)
                bits.append((byte & 16) >> 4)
                bits.append((byte & 32) >> 5)
                bits.append((byte & 64) >> 6)
                bits.append((byte & 128) >> 7)
        offset = 0
        for j in range(12):
            parseBits(7)
        #MFX
        parseBits(6)
        for j in range(12):
            parseBits(7)
        parseBits(2)
        for j in range(3):
            parseBits(7)
        parseBits(4)
        parseBits(7)
        parseBits(4)
        parseBits(7)
        #Chorus
        for j in range(5):
            parseBits(7)
        parseBits(2)
        #Reverb
        parseBits(3)
        for j in range(2):
            parseBits(7)
        parseBits(5)
        parseBits(7)
        #Misc Common
        offset += 8
        parseBits(4)
        offset -= 16
        parseBits(4)
        offset += 8
        for j in range(3):
            parseBits(7)
        parseBits(4)
        parseBits(6)
        for j in range(6):
            parseBits(1)
        parseBits(7)
        for j in range(2):
            parseBits(4)
        for j in range(4):
            parseBits(2)
        parseBits(1)
        parseBits(3)
        parseBits(2)
        parseBits(1)
        #Tone Structure
        parseBits(4)
        parseBits(2)
        parseBits(4)
        parseBits(2)
        #JV-2080 and Up: Clock Source and Category
        parseBits(1)
        parseBits(7)
        for b in range(12):
            bitResult.append(0)
        #Tones
        for t in range(4):
            parseBits(1)
            parseBits(2)
            parseBits(7)
            offset += 8
            parseBits(4)
            offset -= 16
            parseBits(4)
            offset += 8
            parseBits(2)
            parseBits(1)
            parseBits(2)
            parseBits(4)
            parseBits(3)
            parseBits(7)
            #Mods
            for j in range(5):
                parseBits(7)
            for j in range(4):
                parseBits(1)
            parseBits(2)
            for j in range(12):
                parseBits(5)
                parseBits(7)
            #LFO's
            for j in range(2):
                parseBits(3)
                parseBits(1)
                parseBits(7)
                parseBits(3)
                parseBits(7)
                parseBits(2)
                parseBits(7)
                parseBits(2)
            #Pitch
            parseBits(7)
            parseBits(7)
            parseBits(5)
            parseBits(4)
            parseBits(5)
            parseBits(7)
            parseBits(4)
            parseBits(4)
            parseBits(4)
            for j in range(10):
                parseBits(7)
            #Filter
            parseBits(3)
            parseBits(7)
            parseBits(4)
            parseBits(7)
            parseBits(7)
            parseBits(7)
            parseBits(3)
            parseBits(7)
            parseBits(4)
            parseBits(4)
            parseBits(4)
            for j in range(10):
                parseBits(7)
            #Amp
            parseBits(7)
            parseBits(2)
            parseBits(7)
            parseBits(4)
            parseBits(3)
            parseBits(7)
            parseBits(4)
            parseBits(4)
            parseBits(4)
            for j in range(10):
                parseBits(7)
            parseBits(4)
            parseBits(6)
            parseBits(7)
            parseBits(7)
            parseBits(7)
            #Output
            parseBits(2)
            parseBits(7)
            parseBits(7)
            parseBits(7)
            for b in range(8):
                bitResult.append(0)
                
        offset = 0
        for i in range(401):
            theSum = bitResult[offset]
            theSum += bitResult[offset + 1] << 1
            theSum += bitResult[offset + 2] << 2
            theSum += bitResult[offset + 3] << 3
            theSum += bitResult[offset + 4] << 4
            theSum += bitResult[offset + 5] << 5
            theSum += bitResult[offset + 6] << 6
            theSum += bitResult[offset + 7] << 7
            offset += 8
            out_file.write(theSum.to_bytes(1,"big"))
        in_file.seek(scan + 590)
        if isSysex == True:
            in_file.seek(scan + 645)
    in_file.close()
    out_file.close()

