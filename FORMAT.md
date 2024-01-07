# SRJV Format Information
 
## General

The SR-JV80 ROM format consists of a scrambled collection of 8 1MB blocks, big endian format, merged into one ROM image file. Each block contains the following:

* 1 KB of header information
* 31 KB of exponents for the compressed sample data
* 992KB of everything else, mostly delta samples

> * The first block contains compatible data for one series of models, usually the JV-80, in the header section
>
> * If there are specific patches and drumkits for another model (i.e. JV-1080+ or the JD-990), the compatible data for that model is located in the second block's header section
>
> * The sample, multisample, patch, and drumkit tables are all stored in what's otherwise reserved for ADPCM delta samples. Theoretically, these tables can be positioned anywhere in that section, but in the standard cards, these are reserved for the end of the last block.

## Header

* 0x0000000 - 32 bytes - encrypted information about the card (perversely, the scrambling program will make these bytes readable to the average human being, whereas unscrambling is needed for the rest of the block)
* 0x0000020 - 16 bytes - ASCII name of the card
* 0x0000030 - 10 bytes - ROM date
* 0x000003a - 6 bytes - unknown purpose, usually "0xffffffffffff"
* 0x0000040 - 4 byte - unknown purpose, usually "0x01400000"
* 0x0000044 - 1 byte - block number to point to with more model data (i.e. "0x10" in the first block to the second, "0x20" in the second to third, etc.) Last block with important data has this set to "0x08"
* 0x0000050 - 2 bytes - unknown purpose, seemingly always "0x0201" in the first block
* 0x0000053 - 1 byte - supported model ID. Known values: 0x02 (JV-80), 0x03 (JD-990), 0x05 (JV-1080)
* 0x0000054 - 1 byte - number of drumkits per bank?
* 0x000005f - 1 byte - unknown purpose, "0x03" or "0x00"
* 0x0000060 - 2 bytes - number of raw samples (first block only)
* 0x0000062 - 2 bytes - number of multisamples (first block only)
* 0x0000066 - 2 bytes - number of patches (max 256)
* 0x0000068 - 2 bytes - number of drumkits (max 8, possibly?)
* 0x000007f - 1 byte - unknown purpose
* 0x0000080 - 4 bytes - pointer to start of sample table (first table if not first block)
* 0x0000084 - 4 bytes - pointer to start of multisample table (first table if not first block)
* 0x000008c - 4 bytes - pointer to start of patch table
* 0x0000090 - 4 bytes - pointer to start of drumkit table
* 0x00000bc - 4 bytes - unknown table pointer
* 0x00000fd - 3 bytes - first and last bytes are the block number

## Sample Table

(per entry, 18 bytes each)
* 0x000000 - 1 byte - volume byte (max is 0x7f)
* 0x000001 - 3 bytes - pointer to sample start
* 0x000004 - 3 bytes - pointer to sample loop start
* 0x000007 - 3 bytes - pointer to sample end
* 0x00000a - 2 bytes - unknown purpose
* 0x00000c - 1 byte - loop type. Known values: 0x00 (forward loop), 0x01 (ping-pong loop), 0x02 (no loop), 0x04 (reverse), 0x06 (reverse, non-JD only)
* 0x00000d - 1 byte - root key
* 0x00000e - 2 bytes - fine tune, 1/1024ths of a semitone
* 0x000010 - 2 bytes - loop fine tune, 1/1024ths of a semitone

## Multisample Table

(per entry, 60 bytes each):
* 0x000000 - 12 bytes - ASCII name of multisample
* 0x00000c - 16 bytes - high key of sample, 1 byte for each of 16 samples
* 0x00001c - 32 bytes - sample ID in order of sample table, 2 bytes for each of 16 samples

## Patch Table Information

Obviously the patch data format varies depending on model. The JV-80 and JD-990 formats are stored in a fairly straightforward manner, with slight arrangement variations from their SysEx equivalents (and without the SysEx headers, obviously). Unfortunately, with the JV-1080, to save space, the patch data is compressed by number of bits each parameter is supposed to use. Add to the complications that when a parameter spans multiple bytes, the least significant bits are transferred to the most significant bits of the next byte in line. A Python module has already been created to handle most parameters from the JV-2080 (importance being the JV-2080 introduced patch categories, also stored in this table), but if you wish to look into specific parameters for yourself, quick advice is to read the SysEx manual, note how many bytes all parameters use total, and determine the bit, not byte, offset from that.