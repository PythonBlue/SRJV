import os, platform

foldersplit = "/"
if platform.system() == "Windows":
    foldersplit = "\\"

directory = input("Directory of files to fix: ")
for wavName in sorted(os.listdir(directory)):
    if wavName.endswith(".wav"):
        audioFile = open(directory + foldersplit + wavName, "rb")
        audioRead = audioFile.read()
        dataOff = audioRead.find(b'data')
        audioFile.seek(dataOff + 4)
        dataSz = int.from_bytes(audioFile.read(4), "little")
        chnkOff = audioRead.find(b'smpl')
        if dataOff < chnkOff and chnkOff < dataOff + dataSz:
            chnkOff = audioRead.find(b'smpl', 0, dataOff)
            if chnkOff == -1:
                chnkOff = audioRead.find(b'smpl', dataOff + dataSz)
        if chnkOff >= 0 and chnkOff + 64 < len(audioRead):
            audioFile.seek(chnkOff + 20)
            rootKey = int.from_bytes(audioFile.read(4), "little")
            audioFile.seek(chnkOff + 52)
            sampleLoop = int.from_bytes(audioFile.read(4), "little")
            sampleEnd = int.from_bytes(audioFile.read(4), "little")
            
            for sfzName in sorted(os.listdir(directory)):
                if sfzName.endswith(".sfz"):
                    sfzFile1 = open(directory + foldersplit + sfzName, "r")
                    sfzFile2 = open(directory + foldersplit + "tmp", "w")
                    for line in sfzFile1.readlines():
                        if line == "sample=" + wavName + "\n":
                            line = "sample=" + wavName + "\npitch_keycenter=" + str(rootKey) + "\nloop_mode=loop_continuous\nloop_start=" + str(sampleLoop) + "\nloop_end=" + str(sampleEnd) + "\n"
                        elif line == "sample=" + wavName:
                            line = "sample=" + wavName + "\npitch_keycenter=" + str(rootKey) + "\nloop_mode=loop_continuous\nloop_start=" + str(sampleLoop) + "\nloop_end=" + str(sampleEnd)
                        sfzFile2.write(line)
                    sfzFile1.close()
                    sfzFile2.close()
                    os.remove(directory + foldersplit + sfzName)
                    os.rename(directory + foldersplit + "tmp", directory + foldersplit + sfzName)
        print(wavName)
