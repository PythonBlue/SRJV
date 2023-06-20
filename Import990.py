import os
import math

offset = 0
bits = []
bitResult = []
chkSum = 0
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
    patchCount = int((in_file.tell()) / 519)
    in_file.seek(0)
    offset = 0

    for i in range(patchCount):
        scan = in_file.tell()
        result = out_file.tell()
        bits = []
        bitCount = 0
        in_file.seek(scan + 9)
        for j in range(118):
            byte = int.from_bytes(in_file.read(1), "big")
            if bitCount == 117 and byte & 3 == 0:
                byte += 3
            elif bitCount == 117:
                byte -= 1
            bits.append(byte & 1)
            bits.append((byte & 2) >> 1)
            bits.append((byte & 4) >> 2)
            bits.append((byte & 8) >> 3)
            bits.append((byte & 16) >> 4)
            bits.append((byte & 32) >> 5)
            bits.append((byte & 64) >> 6)
            bits.append((byte & 128) >> 7)
            bitCount += 1
        in_file.seek(11,1)
        bitCount = 0
        for k in range(4):
            for j in range(92):
                byte = int.from_bytes(in_file.read(1), "big")
                if bitCount == (k * 92) and byte > 1:
                    byte = 1
                bits.append(byte & 1)
                bits.append((byte & 2) >> 1)
                bits.append((byte & 4) >> 2)
                bits.append((byte & 8) >> 3)
                bits.append((byte & 16) >> 4)
                bits.append((byte & 32) >> 5)
                bits.append((byte & 64) >> 6)
                bits.append((byte & 128) >> 7)
                bitCount += 1
                if k == 2 and bitCount == 256:
                    in_file.seek(11,1)
                
        offset = 25 * 8
        parseBits(4)
        offset = 24 * 8
        parseBits(4)
        offset = 0
        for j in range(16):
            parseBits(8)
        parseBits(7)
        offset = 27 * 8
        parseBits(1)
        offset = 17 * 8
        parseBits(7)
        offset = 28 * 8
        parseBits(1)
        offset = 18 * 8
        parseBits(8)
        offset = 20 * 8
        parseBits(6)
        offset = 30 * 8
        parseBits(1)
        parseBits(1)
        offset = 21 * 8
        parseBits(4)
        offset = 32 * 8
        parseBits(3)
        offset = 19 * 8
        parseBits(1)
        offset = 22 * 8
        parseBits(3)
        offset = 23 * 8
        parseBits(3)
        offset = 117 * 8
        parseBits(2)
        
        offset = 29 * 8
        parseBits(7)
        offset = 26 * 8
        parseBits(1)
        offset = 40 * 8
        parseBits(3)
        offset = 34 * 8
        parseBits(5)
        offset = 41 * 8
        parseBits(3)
        offset = 35 * 8
        parseBits(5)
        offset = 42 * 8
        for j in range(8):
            parseBits(8)
        parseBits(2)
        parseBits(2)
        parseBits(2)
        parseBits(2)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        parseBits(8)
        offset = 37 * 8
        parseBits(5)
        offset = 36 * 8
        parseBits(3)
        offset = 39 * 8
        parseBits(5)
        offset = 33 * 8
        parseBits(1)
        offset = 38 * 8
        parseBits(2)

        #Effects
        offset = 62 * 8
        parseBits(8)
        parseBits(3)
        offset = 66 * 8
        parseBits(3)
        offset = 100 * 8
        parseBits(2)
        offset = 64 * 8
        parseBits(4)
        offset = 67 * 8
        parseBits(4)
        offset = 65 * 8
        parseBits(8)
        offset = 68 * 8
        parseBits(8)

        parseBits(5)
        offset = 91 * 8
        parseBits(3)
        offset = 70 * 8
        parseBits(1)
        parseBits(1)
        parseBits(1)
        parseBits(1)
        offset = 92 * 8
        parseBits(1)
        parseBits(1)
        parseBits(2)
        offset = 74 * 8
        for j in range(17):
            parseBits(8)
        offset = 95 * 8
        for j in range(5):
            parseBits(8)
        offset = 102 * 8
        parseBits(7)
        offset = 101 * 8
        parseBits(1)
        offset = 103 * 8
        parseBits(8)
        offset = 105 * 8
        parseBits(7)
        offset = 104 * 8
        parseBits(1)
        offset = 106 * 8
        parseBits(8)
        offset = 108 * 8
        parseBits(7)
        offset = 107 * 8
        parseBits(1)
        offset = 109 * 8
        parseBits(8)
        offset = 110 * 8
        parseBits(8)
        offset = 111 * 8
        for j in range(6):
            parseBits(8)
            
        offset = 944
        for tone in range(4):
            scanT = offset
            resultT = out_file.tell()

            #Pitch
            for k in range(2):
                bitResult.append(0)
            offset = scanT + 1
            parseBits(1)
            offset = scanT + 12 * 8
            parseBits(5)
            offset = scanT + 2 * 8
            parseBits(7)
            offset = scanT + 8
            parseBits(1)
            offset = scanT + 4 * 8
            parseBits(7)
            offset = scanT + 5 * 8
            parseBits(1)
            for k in range(2):
                bitResult.append(0)
            offset = scanT + 11 * 8
            parseBits(5)
            offset = scanT + 13 * 8
            parseBits(1)
            offset = scanT + 7 * 8
            parseBits(8)
            parseBits(8)
            parseBits(8)
            parseBits(8)
            offset = scanT + 64 * 8
            parseBits(8)
            offset = scanT + 73 * 8
            parseBits(8)
            offset = scanT + 17 * 8
            for k in range(7):
                parseBits(8)
            offset = scanT + 14 * 8
            parseBits(8)
            parseBits(8)
            parseBits(5)
            offset = scanT + 3 * 8
            parseBits(3)

            #TVF
            offset = scanT + 24 * 8
            parseBits(2)
            offset = scanT + 27 * 8
            parseBits(6)
            offset = scanT + 25 * 8
            parseBits(8)
            parseBits(8)
            offset = scanT + 28 * 8
            parseBits(8)
            offset = scanT + 65 * 8
            parseBits(8)
            offset = scanT + 74 * 8
            parseBits(8)
            offset = scanT + 32 * 8
            for k in range(8):
                parseBits(8)
            offset = scanT + 29 * 8
            parseBits(8)
            parseBits(8)
            parseBits(5)
            offset = scanT + 58 * 8
            parseBits(3)

            #TVA
            offset = scanT + 40 * 8
            parseBits(8)
            parseBits(2)
            offset = scanT + 43 * 8
            parseBits(6)
            offset = scanT + 42 * 8
            parseBits(8)
            offset = scanT + 44 * 8
            parseBits(8)
            parseBits(4)
            offset = scanT + 62 * 8
            parseBits(2)
            offset = scanT + 71 * 8
            parseBits(2)
            offset = scanT + 66 * 8
            parseBits(8)
            offset = scanT + 75 * 8
            parseBits(8)
            offset = scanT + 49 * 8
            for k in range(7):
                parseBits(8)
            offset = scanT + 46 * 8
            parseBits(8)
            parseBits(8)
            parseBits(5)
            offset = scanT + 67 * 8
            parseBits(3)

            #LFO's
            offset = scanT + 59 * 8
            parseBits(7)
            offset = scanT + 63 * 8
            parseBits(1)
            offset = scanT + 60 * 8
            parseBits(8)
            parseBits(8)
            
            offset = scanT + 68 * 8
            parseBits(7)
            offset = scanT + 72 * 8
            parseBits(1)
            offset = scanT + 69 * 8
            parseBits(7)
            offset = scanT + 57 * 8
            parseBits(1)
            offset = scanT + 70 * 8
            parseBits(8)

            #Control
            
            offset = scanT + 56 * 8
            parseBits(4)
            offset = scanT + 6 * 8
            parseBits(4)

            #Mods
            offset = scanT + 76 * 8
            parseBits(4)
            offset = scanT + 78 * 8
            parseBits(4)
            offset = scanT + 80 * 8
            parseBits(4)
            offset = scanT + 82 * 8
            parseBits(4)
            offset = scanT + 84 * 8
            parseBits(4)
            offset = scanT + 86 * 8
            parseBits(4)
            offset = scanT + 88 * 8
            parseBits(4)
            offset = scanT + 90 * 8
            parseBits(4)
            offset = scanT + 77 * 8
            parseBits(8)
            offset = scanT + 79 * 8
            parseBits(8)
            offset = scanT + 81 * 8
            parseBits(8)
            offset = scanT + 83 * 8
            parseBits(8)
            offset = scanT + 85 * 8
            parseBits(8)
            offset = scanT + 87 * 8
            parseBits(8)
            offset = scanT + 89 * 8
            parseBits(8)
            offset = scanT + 91 * 8
            parseBits(8)
            
        resultOff = 379 * 8 * i
        for j in range(379):
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
        in_file.seek(scan + 519)
    in_file.close()
    out_file.close()
