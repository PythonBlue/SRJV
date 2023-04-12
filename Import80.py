import os
import math

offset = 0
bits = []
bitResult = []
isSysex = False

def parseBits(bitNum):
    global offset
    global bits
    global bitResult
    for k in range(8):
        if k < bitNum:
            bitResult.append(bits[offset])
        offset += 1

def run(in_string):
    global offset
    global bits
    global bitResult
    isSysex = False
    in_file = open(in_string + ".syx", "rb")
    out_file = open(in_string + ".patches", "wb")
    if in_file.read(1) == b'\xf0':
        isSysex = True
    in_file.seek(0,2)
    patchCount = int((in_file.tell()) / 549)
    in_file.seek(0)
    offset = 0

    for i in range(patchCount):
        scan = 549 * i
        result = out_file.tell()
        bits = []
        bitCount = 0
        in_file.seek(scan + 9)
        for j in range(34):
            byte = int.from_bytes(in_file.read(1), "big")
            if bitCount == 26:
                byte = (byte - 64) % 256
            bits.append(byte & 1)
            bits.append((byte & 2) >> 1)
            bits.append((byte & 4) >> 2)
            bits.append((byte & 8) >> 3)
            bits.append((byte & 16) >> 4)
            bits.append((byte & 32) >> 5)
            bits.append((byte & 64) >> 6)
            bits.append((byte & 128) >> 7)
            bitCount += 1
        for k in range(4):
            in_file.seek(11,1)
            for j in range(115):
                byte = int.from_bytes(in_file.read(1), "big")
                if bitCount == 34 + (k * 115) and byte > 1:
                    byte = 1
                #if bitCount == 42 + (k * 115):
                    #byte = byte ^ 1
                #if bitCount == 43 + (k * 115):
                    #byte = byte ^ 1
                if bitCount == 45 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 47 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 49 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 51 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 53 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 55 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 57 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 59 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 61 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 63 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 65 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 67 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 76 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 77 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 78 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 87 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 88 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 89 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 90 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 91 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 94 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 98 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 100 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 102 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 104 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 106 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 113 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 117 + (k * 115):
                    byte = (byte - 64) % 256
                if bitCount == 135 + (k * 115):
                    byte = (byte - 64) % 256
                bits.append(byte & 1)
                bits.append((byte & 2) >> 1)
                bits.append((byte & 4) >> 2)
                bits.append((byte & 8) >> 3)
                bits.append((byte & 16) >> 4)
                bits.append((byte & 32) >> 5)
                bits.append((byte & 64) >> 6)
                bits.append((byte & 128) >> 7)
                bitCount += 1

        for j in range(12):
            parseBits(8)
        #Reverb
        offset = 104
        parseBits(3)
        offset = 136
        parseBits(2)
        for j in range(2):
            bitResult.append(0)
        offset = 96
        parseBits(1)
        offset = 112
        parseBits(8)
        parseBits(8)
        parseBits(8)
        offset = 136
        #Chorus
        offset = 144
        parseBits(8)
        parseBits(8)
        offset = 160
        parseBits(7)
        offset = 176
        parseBits(1)
        offset = 168
        parseBits(8)
        offset = 184
        #Misc
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(4)
        offset = 248
        parseBits(1)
        offset = 240
        parseBits(1)
        offset = 232
        parseBits(1)
        offset = 224
        parseBits(1)
        offset = 264
        parseBits(7)
        offset = 256
        parseBits(1)
        
        offset = 272
        for tone in range(4):
            scanT = offset
            resultT = out_file.tell()

            offset = scanT
            parseBits(2)
            offset = scanT + 40
            parseBits(4)
            offset = scanT + 32
            parseBits(1)
            offset = scanT + 24
            parseBits(1)
            offset = scanT + 16
            parseBits(4)
            offset = scanT + 8
            parseBits(4)
            for j in range(8):
                bitResult.append(0)
            offset = scanT + 48
            parseBits(8)
            #offset = scanT + 64
            #parseBits(1)
            offset = scanT + 56
            parseBits(8)
            #offset = scanT + 72
            #parseBits(1)
            
            offset = scanT + 80
            #Mods A
            ModStart = offset
            offset = ModStart
            parseBits(4)
            offset = ModStart + 16
            parseBits(4)
            offset = ModStart + 32
            parseBits(4)
            offset = ModStart + 48
            parseBits(4)
            offset = ModStart + 8
            parseBits(8)
            offset = ModStart + 24
            parseBits(8)
            offset = ModStart + 40
            parseBits(8)
            offset = ModStart + 56
            parseBits(8)
            #Mods B
            ModStart = offset
            offset = ModStart
            parseBits(4)
            offset = ModStart + 16
            parseBits(4)
            offset = ModStart + 32
            parseBits(4)
            offset = ModStart + 48
            parseBits(4)
            offset = ModStart + 8
            parseBits(8)
            offset = ModStart + 24
            parseBits(8)
            offset = ModStart + 40
            parseBits(8)
            offset = ModStart + 56
            parseBits(8)
            #Mods C
            ModStart = offset
            offset = ModStart
            parseBits(4)
            offset = ModStart + 16
            parseBits(4)
            offset = ModStart + 32
            parseBits(4)
            offset = ModStart + 48
            parseBits(4)
            offset = ModStart + 8
            parseBits(8)
            offset = ModStart + 24
            parseBits(8)
            offset = ModStart + 40
            parseBits(8)
            offset = ModStart + 56
            parseBits(8)
            #LFO1
            LFOStart = offset
            offset = LFOStart
            parseBits(3)
            parseBits(3)
            parseBits(1)
            bitResult.append(0)
            parseBits(7)
            bitResult.append(0)
            offset = LFOStart + 40
            parseBits(4)
            offset = LFOStart + 32
            parseBits(4)
            offset = LFOStart + 56
            parseBits(7)
            offset = LFOStart + 48
            parseBits(1)
            offset = LFOStart + 88
            #LFO2
            parseBits(3)
            parseBits(3)
            parseBits(1)
            bitResult.append(0)
            parseBits(7)
            bitResult.append(0)
            offset = LFOStart + 128
            parseBits(4)
            offset = LFOStart + 120
            parseBits(4)
            offset = LFOStart + 144
            parseBits(7)
            offset = LFOStart + 136
            parseBits(1)
            #LFOMix
            offset = LFOStart + 64
            parseBits(8)
            parseBits(8)
            parseBits(8)
            offset = LFOStart + 152
            parseBits(8)
            parseBits(8)
            parseBits(8)
            offset = LFOStart + 176
            #Pitch
            PitchStart = offset
            parseBits(8)
            parseBits(8)
            parseBits(4)
            offset = PitchStart + 320
            parseBits(4)
            
            offset = PitchStart + 24
            parseBits(4)
            offset = PitchStart + 56
            parseBits(4)
            offset = PitchStart + 32
            parseBits(8)
            parseBits(4)
            parseBits(4)
            offset = PitchStart + 64
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            offset = PitchStart + 136
            #Filter
            FilStart = offset
            offset = FilStart + 8
            parseBits(8)
            parseBits(7)
            parseBits(1)
            parseBits(4)
            offset = FilStart + 72
            parseBits(4)
            offset = FilStart + 40
            parseBits(3)
            offset = FilStart
            parseBits(2)
            for j in range(3):
                bitResult.append(0)
            offset = FilStart + 48
            parseBits(8)
            parseBits(4)
            parseBits(4)
            offset = FilStart + 80
            parseBits(7)
            bitResult.append(0)
            
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            offset = FilStart + 152

            #Level
            LevStart = offset
            parseBits(8)
            offset = LevStart + 24
            parseBits(4)
            offset = LevStart + 16
            parseBits(4)
            offset = LevStart + 48
            parseBits(4)
            parseBits(4)
            offset = LevStart + 8
            parseBits(4)
            offset = LevStart + 96
            parseBits(4)
            offset = LevStart + 64
            parseBits(3)
            offset = LevStart + 40
            parseBits(2)
            for j in range(1):
                bitResult.append(0)
            offset = scanT + 64
            parseBits(1)
            offset = scanT + 72
            parseBits(1)
            offset = LevStart + 72
            parseBits(8)
            parseBits(4)
            parseBits(4)
            offset = LevStart + 104
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)

            #Sends
            parseBits(8)
            parseBits(8)
            parseBits(8)
            
        resultOff = 362 * 8 * i
        for j in range(362):
            theSum = bitResult[resultOff]
            theSum += bitResult[resultOff + 1] << 1
            theSum += bitResult[resultOff + 2] << 2
            theSum += bitResult[resultOff + 3] << 3
            theSum += bitResult[resultOff + 4] << 4
            theSum += bitResult[resultOff + 5] << 5
            theSum += bitResult[resultOff + 6] << 6
            theSum += bitResult[resultOff + 7] << 7
            resultOff += 8
            out_file.write(theSum.to_bytes(1,"big"))
        offset = 0
        in_file.seek(scan + 549)
    in_file.close()
    out_file.close()
