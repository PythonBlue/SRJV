def descramble_data8(word):
    return ((word & 0x02) << 6) | ((word & 0x08) << 3) | ((word & 0x40) >> 1) | \
        ((word & 0x80) >> 3) | ((word & 0x20) >> 2) | ((word & 0x10) >> 2) | \
        ((word & 0x01) << 1) | ((word & 0x04) >> 2)


def descramble_data16(word):
    return ((word & 0x0002) << 6) | ((word & 0x0008) << 3) | ((word & 0x0040) >> 1) | \
        ((word & 0x0080) >> 3) | ((word & 0x0020) >> 2) | ((word & 0x0010) >> 2) | \
        ((word & 0x0001) << 1) | ((word & 0x0004) >> 2) | ((word & 0x0200) << 6) | \
        ((word & 0x0800) << 3) | ((word & 0x4000) >> 1) | ((word & 0x8000) >> 3) | \
        ((word & 0x2000) >> 2) | ((word & 0x1000) >> 2) | ((word & 0x0100) << 1) | \
        ((word & 0x0400) >> 2)


def descramble_addr(addr, width):
    if width == 8:
        return ((addr & 0x01) << 1) | ((addr & 0x02) << 3) | ((addr & 0x04) >> 2) | \
            ((addr & 0x08) >> 1) | ((addr & 0x10) >> 1) | ((addr & 0x20) << 10) | \
            ((addr & 0x40) << 4) | ((addr & 0x80) << 10) | ((addr & 0x100) << 6) | \
            ((addr & 0x200) >> 4) | ((addr & 0x400) >> 3) | ((addr & 0x800) << 1) | \
            ((addr & 0x1000) << 4) | ((addr & 0x2000) >> 7) | ((addr & 0x4000) << 4) | \
            ((addr & 0x8000) >> 4) | ((addr & 0x10000) >> 3) | ((addr & 0x20000) >> 8) | \
            ((addr & 0x40000) >> 10) | (addr & 0xFFF80000)
    else:
        return ((addr & 0x02) << 3) | ((addr & 0x10) >> 3) | ((addr & 0x20) << 3) | \
            ((addr & 0x40) << 6) | ((addr & 0x80) >> 1) | ((addr & 0x100) << 5) | \
            ((addr & 0x200) << 2) | ((addr & 0x400) >> 1) | ((addr & 0x800) << 5) | \
            ((addr & 0x1000) >> 5) | ((addr & 0x2000) >> 8) | ((addr & 0x8000) << 2) | \
            ((addr & 0x10000) >> 6) | ((addr & 0x20000) >> 2) | (addr & 0xFFFC400D)


def determine_rom_type(buf):
    if buf.startswith(b'JP-800'):
        return 8, "JP-800"
    elif buf.startswith(b'Roland'):
        if buf[0xC:0xF] == b'O\xB0S':
            return 8, "SR-JV80"
        elif buf[0xC:0xF] == b'O\xB0X':
            return 16, "SRX"
        else:
            raise ValueError(f"Unknown ROM type: {buf[0xC:0xF]}")
    else:
        raise ValueError(f"Invalid ROM: {buf[:6]}")


def descramble(filename):
    try:
        with open(filename, 'rb') as f:
            buf = f.read()
    except:
        print(f"Error: Cannot open {filename}")
        return

    outbuf = bytearray(len(buf))

    width, rom_type = determine_rom_type(buf)

    print(rom_type + " ROM detected.")

    if width == 16:
        for i in range(0, len(buf), 2):
            addr = descramble_addr(i, width)
            tmp = descramble_data16(int.from_bytes(buf[i:i + 2], 'little'))
            outbuf[addr:addr + 2] = tmp.to_bytes(2, 'little')
    else:
        for i in range(len(buf)):
            addr = descramble_addr(i, width)
            tmp = descramble_data8(buf[i])
            outbuf[addr] = tmp

    return outbuf
