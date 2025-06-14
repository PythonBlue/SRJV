import math
import os.path
import struct
import sys
import wave
import re
import json
import descramble_internal_rom as descramble
import argparse
import platform

BLOCK_SIZE = 1024 * 1024
used_samples = set()


def loop_type_to_str(loop_type_value):
    if loop_type_value == 0x00:
        return "forward"
    if loop_type_value == 0x01:
        return "pingpong"
    if loop_type_value == 0x02:
        return "noloop"
    if loop_type_value == 0x04:
        return "reverse"
    if loop_type_value == 0x06:
        return "reverse"

    return "unknown"


def loop_type_to_sfz_loop_type(loop_type_value):
    if loop_type_value == 0x00:
        return "forward"
    if loop_type_value == 0x01:
        return "alternate"
    if loop_type_value == 0x06:
        return "backward"

    return None


def loop_type_to_wav_type(loop_type_value):
    if loop_type_value == 0x00:
        return 0
    if loop_type_value == 0x01:
        return 1
    if loop_type_value == 0x06:
        return 2

    return None


def modelid_to_str(model_id):
    if model_id == 0x02:
        return "JV80"
    elif model_id == 0x03:
        return "JD990"
    elif model_id == 0x05:
        return "JV1080"
    else:
        return "unknown: " + hex(model_id)


def number_to_note(note_number):
    # Define the note names
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Determine the note and octave
    note = note_names[(note_number - 36) % 12]
    octave = (note_number // 12) - 1

    return note + str(octave)


def read_header(block_num, file):
    offset = block_num * BLOCK_SIZE
    header = {}

    file.seek(offset + 0x20)
    card_name_bytes = file.read(16)
    header["card_name"] = card_name_bytes.decode(
        'ascii').strip().replace("\x00", "")  # Strip to remove any potential padding or trailing spaces

    #file.seek(offset + 0x53)
    header["supported_model_id"] = struct.unpack(">B", file.read(1))[0]
    header["supported_model_id_str"] = "JV80"

    #file.seek(offset + 0x40)
    header["sample_rate"] = 32000
    
    #file.seek(offset + 0x60)
    
    header["number_of_samples"] = 577
    header["number_of_multisamples"] = 129
    header["number_of_drumkits"] = 0
    header["number_of_patches"] = 0

    #file.seek(offset + 0x80)
    
    header["sample_table_position"] = 4202048
    header["multisample_table_position"] = 4194308
    header["drumkit_table_position"] = 0
    header["patch_table_position"] = 0

    return header


def read_multisamples_table(file, multisamples_table_pos, header):
    multisamples = []

    file.seek(multisamples_table_pos)

    for i in range(header["number_of_multisamples"]):
        multisample = {}
        name_bytes = file.read(12)
        multisample["multisample_id"] = i
        multisample["multisample_name"] = name_bytes.decode(
            'ascii').strip()  # Strip to remove any potential padding or trailing spaces
        multisample["high_key"] = []
        for _ in range(16):
            high_key = struct.unpack(">B", file.read(1))[0]
#            print(str(high_key) + "/" + number_to_note(high_key))
            multisample["high_key"].append(high_key)

#        print("---------")

        # sample id: 65535 is probably unused
        multisample["sample_id"] = []
        for _ in range(16):
            sample_id = struct.unpack(">H", file.read(2))[0]
#            print(sample_id)
            multisample["sample_id"].append(sample_id)

#        print("=========")

        multisamples.append(multisample)

    return multisamples


def read_sample_table(file, sample_table_pos, header):
    samples = []
    file.seek(sample_table_pos)
    for i in range(header["number_of_samples"]):
        sample = {}
        sample["id"] = i
        sample["volume"] = struct.unpack(">B", file.read(1))[0]
        sample["sample_start"] = struct.unpack(">I", b'\x00' + file.read(3))[0]
        sample["loop_start"] = struct.unpack(">I", b'\x00' + file.read(3))[0]
        sample["sample_end"] = struct.unpack(">I", b'\x00' + file.read(3))[0]
        sample["unknown"] = struct.unpack(">H", file.read(2))[0]
        sample["loop_type"] = struct.unpack(">B", file.read(1))[0]
        sample["loop_type_str"] = loop_type_to_str(sample["loop_type"])
        sample["root_key"] = struct.unpack(">B", file.read(1))[0]
        sample["root_key_str"] = number_to_note(sample["root_key"])
        sample["fine_tune"] = struct.unpack(">H", file.read(2))[0]
        sample["loop_fine_tune"] = struct.unpack(">H", file.read(2))[0]
        sample["sample_offset"] = 0
        sample["sample_delay"] = (sample["sample_start"] % 16)
        for j in range(len(samples)):
            if sample["sample_end"] == samples[j]["sample_end"]:
                if sample["sample_start"] < samples[j]["sample_start"]:
                    sample["sample_offset"] = 0
                    samples[j]["sample_offset"] = samples[j]["sample_start"] - sample["sample_start"]
                    samples[j]["sample_start"] -= samples[j]["sample_offset"]
                    sample["sample_delay"] = sample["sample_start"] % 16
                elif sample["sample_start"] > samples[j]["sample_start"]:
                    sample["sample_offset"] = sample["sample_start"] - samples[j]["sample_start"]
                    sample["sample_start"] -= sample["sample_offset"]
                    sample["sample_delay"] = samples[j]["sample_start"] % 16
        sample["sample_trim"] = 0
        samples.append(sample)
    return samples


def read_all_exponents(block_count, block_size, file):
    # For each block, extract exponents
    all_exponents = []

    for block_number in range(block_count):
        block_start_offset = block_number * block_size
        exponent_start_offset = block_start_offset + 1024

        file.seek(exponent_start_offset)
        exponents_in_block = file.read(31*1024)
        all_exponents.append(exponents_in_block)

    return all_exponents

def read_all_samples(block_count, block_size, file):
    # For each block, extract exponents
    all_samples  = []

    for block_number in range(block_count):
        block_start_offset = block_number * block_size
        samples_start_offset = block_start_offset + 1024 * 32

        file.seek(samples_start_offset)
        samples = file.read(block_size - 32*1024)
        all_samples.append(samples)

    return all_samples

def decode_block(coefs: bytes, deltas: bytes) -> list[int]:
    result = [0] * (len(coefs) * 2 * 16)
    value = 62000

    for frame in range(2 * len(coefs)):
        coef = coefs[frame // 2]
        exp = coef & 0x0F if (frame & 1) == 0 else (coef >> 4) & 0x0F

        for i in range(16):
            offset = frame * 16 + i
            sample = deltas[offset]

            if sample >= 128:
                sample -= 256

            delta = sample << exp
            value += delta
            result[offset] = value << 14

    return result

def decode_all_blocks(all_coefs: list[bytes], all_deltas: list[bytes]) -> list[int]:
    all_samples_pcm = []
    for block_index, (coefs, deltas) in enumerate(zip(all_coefs, all_deltas)):
        samples = decode_block(coefs, deltas)
        all_samples_pcm.extend(samples)
    return all_samples_pcm

import wave
import struct

def write_wav(filename: str, samples: list[int], sample_rate: int = 32000):
    with wave.open(filename, 'wb') as wav_file:
        n_channels = 1
        sampwidth = 4  # 4 bytes = 32 bits
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(sampwidth)
        wav_file.setframerate(sample_rate)
        wav_file.setnframes(len(samples))

        # Empaquetar samples como enteros de 32 bits con signo en little endian
        for sample in samples:
            wav_file.writeframes(struct.pack('<i', sample))



def get_block_number(sample_start, block_size):
    block_start = sample_start // block_size

    return block_start


def create_sampler_chunk(loop_start, loop_end, loop_type, framerate, root_note):
    smpl_chunk = (
        b'smpl' +  # Chunk ID
        (36 + 24).to_bytes(4, byteorder='little') +  # Chunk size (36 bytes for header + 24 bytes per loop)
        (0).to_bytes(4, byteorder='little') +  # Manufacturer
        (0).to_bytes(4, byteorder='little') +  # Product
        (int(1e9 / framerate)).to_bytes(4, byteorder='little') +  # Sample period in ns
#        (0).to_bytes(4, byteorder='little') +   # Sample period in ns
        root_note.to_bytes(4, byteorder='little') +  # MIDI unity note
        (0).to_bytes(4, byteorder='little') +   # MIDI pitch fraction
        (0).to_bytes(4, byteorder='little') +   # SMPTE format
        (0).to_bytes(4, byteorder='little') +   # SMPTE offset
        (1).to_bytes(4, byteorder='little') +   # Number of sample loops
        (0).to_bytes(4, byteorder='little') +   # Sampler data
        (0).to_bytes(4, byteorder='little') +   # Cue point ID
        loop_type.to_bytes(4, byteorder='little') +   # Loop type (0 = forward loop)
        loop_start.to_bytes(4, byteorder='little') +  # Loop start
        loop_end.to_bytes(4, byteorder='little') +    # Loop end
        (0).to_bytes(4, byteorder='little') +   # Fraction
        (0).to_bytes(4, byteorder='little')     # Play count (0 = infinite)
    )

    return smpl_chunk


def create_instrument_chunk(root_note, fine_tuning, gain, low_note, high_note, low_velocity, high_velocity):
    inst_chunk = (
        b'inst' +  # Chunk ID
        (7).to_bytes(4, byteorder='little') +    # Chunk size (7 bytes)
        root_note.to_bytes(1, byteorder='little') +    # unshifted note / root note (1 byte)
        (0).to_bytes(1, byteorder='little') +    # fine tuning (1 byte)
        (0).to_bytes(1, byteorder='little') +    # gain (1 byte)
        low_note.to_bytes(1, byteorder='little') +     # low note (1 byte)
        high_note.to_bytes(1, byteorder='little') +    # high note (1 byte)
        (0).to_bytes(1, byteorder='little') +    # low velocity (1 byte)
        (127).to_bytes(1, byteorder='little') +  # high velocity (1 byte)
        (0).to_bytes(1, byteorder='little')      # padding for even number of bytes in the chunk
    )

    return inst_chunk



def decode_dpcm(deltas, exponents, sample_start, block_of_sample):
    decoded_samples_24bit = []
    decoded_sample = 0

    num_frames = math.ceil(len(deltas) / 16)

    if num_frames == 0:
        num_frames = 1

    sample_start_offset_in_block = (sample_start - 31 * 1024 - 1024) - (block_of_sample * BLOCK_SIZE)
    for frame in range(num_frames):
        exp_byte = exponents[(sample_start_offset_in_block // (16*2)) + frame//2]
        if frame & 1 == 0:
            exp = exp_byte & 0x0F
        else:
            exp = (exp_byte >> 4) & 0x0F

        for i in range(16):
            index = frame * 16 + i

            if index >= len(deltas):
                break

            delta_byte = deltas[index]
            if delta_byte >= 128:
                delta_byte -= 256

            original_delta = delta_byte << exp
            decoded_sample += original_delta
            clipped_sample = decoded_sample << 7

            # 24-bit clipping
            if clipped_sample < -8388608:
                clipped_sample = -8388608
            if clipped_sample > 8388607:
                clipped_sample = 8388607

            decoded_samples_24bit.append(clipped_sample)

    return decoded_samples_24bit


def loop_unroll_pingpong(pcm_data, loop_start, end_sample):
    loop_data = pcm_data[loop_start:end_sample]
    reversed_inverted_loop_data = [-x if x != -8388608 else 8388607 for x in loop_data][::-1]

    unrolled_pcm_data = pcm_data + reversed_inverted_loop_data
    new_sample_end = end_sample + len(reversed_inverted_loop_data)

    return new_sample_end, unrolled_pcm_data


def loop_unroll_reverse(sample, pcm_data, loop_start, end_sample):
    # It turns out that Roland means with loop invese that always the whole sample is inversed.
    # The loop points seem to be irrelevant.
    reversed_loop_data = [x for x in pcm_data][::-1]

#    unrolled_pcm_data = pcm_data[:loop_start-1] + reversed_loop_data
    unrolled_pcm_data = reversed_loop_data
    new_sample_end = sample["sample_end"]

    return new_sample_end, unrolled_pcm_data


def write_samples_to_pcm(file, multisamples, samples, all_exponents, loop_unroll_flag, header):
    name_whitelisted_characters = r'[^a-zA-Z0-9_]'

    print("=[multisample samples]==================")
    # step 1: write multisamples
    fine_tune_low = None
    fine_tune_high = None
    start_list = []
    end_list = []
    for idx_multisample, multisample in enumerate(multisamples):
        sample_ids = multisample["sample_id"]
        multisample_name_compact = re.sub(r'[<>:"\|?*]', '_', multisample["multisample_name"])#.replace(" ", "_").lower()
        #multisample_name_compact = re.sub(name_whitelisted_characters, '', multisample_name_compact)

        multisample_id = str(multisample['multisample_id'] + 1).zfill(3)

        sfz_content = ""
        #sfz_content_la = ""
# group opcode unsupported by falcon, thus removed and inlined
#        sfz_content = "<group>\n"
#        sfz_content += "  lovel=0 hivel=127\n"
        for idx_sample_prep, sample_id_prep in enumerate(sample_ids):
            if sample_id_prep == 65535:
                continue
            
            startMin = samples[sample_id_prep]["sample_start"]
            endMax = samples[sample_id_prep]["sample_end"]
            finalID = sample_id_prep
            for sample_id_search in range(header["number_of_samples"]):
                if samples[sample_id_prep]["sample_end"] == samples[sample_id_search]["sample_end"]:
                    finalID = min(finalID,sample_id_search)
                    startMin = min(samples[sample_id_prep]["sample_start"], samples[sample_id_search]["sample_start"])
            
            sample_id = finalID
            idx_sample = idx_sample_prep

            sample = samples[sample_id]
            used_samples.add(sample_id)

            #if samples[sample_id_prep]["sample_offset"] > 0:
                #print(multisample_name_compact)
                #print(samples[sample_id_prep]["sample_offset"])

            block_of_sample = get_block_number(startMin, BLOCK_SIZE)
            data_offset_in_block = (block_of_sample * BLOCK_SIZE + 1024 + (31 * 1024))

            length = endMax - startMin + 1 + (startMin % 16)
            if length % 16 > 0:
                while length % 16 > 0:
                    length += 1

            if length <= 0:
                print("sample start before end. skipping.")
                continue
            

            file.seek(startMin-(startMin % 16))
            deltas = file.read(length)

            exponents_block = all_exponents[block_of_sample]
            pcm_data_24bit = decode_dpcm(deltas, exponents_block, startMin - (startMin % 16), block_of_sample)

            start_sample_offset = startMin - 1024 - 31*1024 - block_of_sample*BLOCK_SIZE
            
            loop_start = samples[sample_id_prep]["loop_start"] - 1024 - 31*1024 - block_of_sample*BLOCK_SIZE - start_sample_offset
            end_sample = samples[sample_id_prep]["sample_end"] - 1024 - 31*1024 - block_of_sample*BLOCK_SIZE - start_sample_offset

            #if loop_unroll_flag and sample['loop_type_str'] == "pingpong":
                #end_sample, pcm_data_24bit = loop_unroll_pingpong(pcm_data_24bit, loop_start, end_sample)

            #if loop_unroll_flag and sample['loop_type_str'] == "reverse":
                #end_sample, pcm_data_24bit = loop_unroll_reverse(sample, pcm_data_24bit, loop_start, end_sample)

            bytes_list = [(sample % 16777216).to_bytes(3, "little") for sample in pcm_data_24bit]
            pcm_data_bytearray = b''.join(bytes_list)

            multisample_sample_id = str(idx_sample+1).zfill(2)

            high_key = multisample["high_key"][idx_sample]
            high_key_str = number_to_note(high_key)

            low_key = 0
            if idx_sample > 0:
                low_key = multisample["high_key"][idx_sample-1]+1
            low_key_str = number_to_note(low_key)

            filename = f"{sample_id}".zfill(5) + ".wav"

            inst_chunk = None
            if sample["root_key"] is not None:
                inst_chunk = create_instrument_chunk(sample['root_key'], 0, 0, low_key, high_key, 0, 127)

            wav_loop_type = loop_type_to_wav_type(sample['loop_type'])
            framerate = header["sample_rate"]
            smpl_chunk = None

            #if loop_unroll_flag and (samples[sample_id_prep]'loop_type_str'] == "pingpong" or samples[sample_id_prep]'loop_type_str'] == "reverse"):
                #wav_loop_type = 0

            if wav_loop_type is not None and (loop_start >= 0) and (loop_start <= end_sample):
                smpl_chunk = create_sampler_chunk(loop_start, end_sample, wav_loop_type, framerate, sample['root_key'])

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(3)  # 2=16bit, 3=24bit, 4=32bit
                wf.setframerate(framerate)
                wf.writeframes(pcm_data_bytearray)

            add_chunk(filename, smpl_chunk)
            if inst_chunk is not None:
                add_chunk(filename, inst_chunk)

            fine_tune = sample["fine_tune"]

            if fine_tune_low is None:
                fine_tune_low = fine_tune
            if fine_tune_high is None:
                fine_tune_high = fine_tune

            if fine_tune < fine_tune_low:
                fine_tune_low = fine_tune

            if fine_tune > fine_tune_high:
                fine_tune_high = fine_tune

            fine_tune -= 1024
            loop_fine_tune = sample["loop_fine_tune"] - 1024

            region_content = ("<region>\nsample=" + str(filename) +
                            "\nregion_label=" + str(sample_id_prep).zfill(5) + ".wav" + 
                            "\namplitude=" + str(round(sample["volume"] / 1.27, 3)) + 
                            "\nlokey=" + str(low_key) + "\nhikey=" + str(high_key) +
                            "\npitch_keycenter=" + str(sample["root_key"]) +
                            "\ntune=" + str(round((fine_tune*100 / 1024), 3)) +
                            "\ndelay_samples=" + str(samples[sample_id_prep]["sample_delay"]) +
                            "\noffset=" + str(samples[sample_id_prep]["sample_offset"]))
            sfz_content += region_content
            #sfz_content_la += region_content

            sfz_loop_type = loop_type_to_sfz_loop_type(samples[sample_id_prep]["loop_type"])

            if loop_unroll_flag:
                sfz_loop_type = "forward"

            if (samples[sample_id_prep]['loop_type_str'] == "reverse"):
                sfz_content += ("\ndirection=reverse")
                #sfz_content_la += ("\ndirection=reverse")

            if ((0 <= loop_start <= end_sample and sfz_loop_type is not None) and
                    not (samples[sample_id_prep]['loop_type_str'] == "reverse")):
                sfz_content += ("\nloop_start=" + str(loop_start + samples[sample_id_prep]["sample_delay"]) +
                                "\nloop_end=" + str(end_sample + samples[sample_id_prep]["sample_delay"]) +
                                "\nloop_type=" + str(sfz_loop_type) +
                                "\nlooptune=" + str(round((loop_fine_tune*100 / 1024), 3)) +
                                "\nloop_mode=loop_continuous")
                #sfz_content_la += ("\nloop_start=" + str(loop_start) +
                                #"\nloop_end=" + str(end_sample+1) +
                                #"\nloop_type=" + str(sfz_loop_type) +
                                #"\nloop_mode=loop_continuous"
                                #)
            else:
                loop_content = "\nloop_mode=no_loop" + "\nlooptune=" + str(round((loop_fine_tune*100 / 1024), 3))
                sfz_content += loop_content
                #sfz_content_la += loop_content

            sfz_content += "\n\n"
            #sfz_content_la += "\n"

        sfz_filename = f"{multisample_id}-{multisample_name_compact}.sfz"
        if platform.system() != "Windows":
            sfz_filename = sfz_filename.replace("/",":")
        #sfz_filename_la = f"{multisample_id}-{multisample_name_compact}_la.sfz"
        with open(sfz_filename, 'w') as sfz_file:
            sfz_file.write(sfz_content)
        #with open(sfz_filename_la, 'w') as sfz_file:
            #sfz_file.write(sfz_content_la)

#    print("fine_tune_high: " + str(fine_tune_high))
#    print("fine_tune_low: " + str(fine_tune_low))

    print("done.")


def add_chunk(filename, chunk):
    if chunk is not None:
        with open(filename, 'rb') as original_wav:
            original_wav_data = original_wav.read()

        with open(filename, 'wb') as updated_wav:
            updated_wav.write(original_wav_data)
            updated_wav.write(chunk)
            updated_wav.seek(0, 2)
            final_size = updated_wav.tell()
            final_size -= 8
            updated_wav.seek(4)
            updated_wav.write(final_size.to_bytes(4, byteorder='little'))


def main(scrambled_rom1_file, scrambled_rom2_file, rom_file):

    output_filename = "int_descrambled.bin"
    if not os.path.exists(output_filename):
        descrambled_rom1 = descramble.descramble(scrambled_rom1_file)
        descrambled_rom2 = descramble.descramble(scrambled_rom2_file)
        
        with open(rom_file, "rb") as f1:
            rom = f1.read()
        
        with open(output_filename, 'wb') as file:
            file.write(descrambled_rom1)
            file.write(descrambled_rom2)
            file.write(rom)

        print(f'Descrambled ROM has been written to {output_filename}')

    with open(output_filename, "rb") as file:
        
        print("-[Header Block 0]--------------------------")
        header = read_header(0, file)
        print(json.dumps(header, indent=4, sort_keys=True))
        #header = read_header(0, file)

        print("---------------------------")

        all_exponents = read_all_exponents(4, BLOCK_SIZE, file)
                
        samples = read_sample_table(file, header["sample_table_position"], header)
        multisamples = read_multisamples_table(file, header["multisample_table_position"], header)
        write_samples_to_pcm(file, multisamples, samples, all_exponents, False, header)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract waveforms and SFZ files from an JV80/JV880 card ROM images")
    parser.add_argument("waverom1", type=str, help="Internal waverom #1 file")
    parser.add_argument("waverom2", type=str, help="Internal waverom #2 file")
    parser.add_argument("rom2", type=str, help="Internal main rom #2 file")
    
    args = parser.parse_args()

    main(args.waverom1, args.waverom2, args.rom2)
