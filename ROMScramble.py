import sys

def scramble_data8(word):
    return ((word & 1) << 2) + ((word & 2) >> 1) + ((word & 4) << 2) + ((word & 8) << 2) + ((word & 16) << 3) + ((word & 32) << 1) + ((word & 64) >> 3) + ((word & 128) >> 6)

def scramble_addr8(addr):
    sumUp = ((addr & 1) << 2) + ((addr & 2) >> 1) + ((addr & 4) << 1) + ((addr & 8) << 1)
    sumUp += ((addr & 16) >> 3) + ((addr & 32) << 4) + ((addr & 64) << 7) + ((addr & 128) << 3)
    sumUp += ((addr & 256) << 10) + ((addr & 512) << 8) + ((addr & 1024) >> 4) + ((addr & 2048) << 4)
    sumUp += ((addr & 4096) >> 1) + ((addr & 8192) << 3) + ((addr & 16384) >> 6) + ((addr & 32768) >> 10)
    sumUp += ((addr & 65536) >> 4) + ((addr & 131072) >> 10) + ((addr & 262144) >> 4) + (addr & 4294443008)
    return sumUp

def run(filename_in, filename_out):
    #if len(arguments) < 3:
        #print("Usage: scramble.py descrambled.bin scrambled.bin")
        #return
    #filename_in = arguments[1]
    #filename_out = arguments[2]

    try:
        f = open(filename_in, "rb")
    except:
        print("Error: cannot open input file!")
        return
    f.seek(0,2)
    fsize = f.tell()
    f.seek(0)
    buf = bytearray(f.read())
    outbuf = bytearray(fsize)
    f.close()

    #figure out ROM type: scramble first 32 bytes
    for i in range(32):
        addr = scramble_addr8(i)
        tmp = scramble_data8(buf[i])
        #print(tmp)
        outbuf[addr] = tmp

    if outbuf[0:12].decode('UTF-8') != 'Roland JV80 ':
        print("Error: not an SR-JV80 ROM!")
        return
    print("ROM ID:   " + (buf[32:38].decode('UTF-8')))
    print("Date:   " + (buf[48:58].decode('UTF-8')))
    for i in range(fsize):
        addr = scramble_addr8(i)
        tmp = scramble_data8(buf[i])
        outbuf[addr] = tmp

    try:
        out = open(filename_out, "wb")
    except:
        print("Error: cannot open output file!")
        return

    for i in range(fsize):
        out.write(outbuf[i].to_bytes(1,"big"))
    out.close()
