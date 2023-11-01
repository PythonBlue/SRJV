import os
import sys
import shutil
import argparse

import DPCM
import ROMImport
import ROMScramble

os.chdir(os.path.dirname(os.path.abspath(__file__)))

Folder = ""
FinalFile = ""
VerboseMode = False
PatchImport = False
if len(sys.argv) > 1:
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='input', help='Input folder')
    parser.add_argument('-o', '--output', type=str, default='Final', help='Output filename')
    parser.add_argument('-p', '--patches', action='store_true', help='Import patches')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    args = parser.parse_args()
    Folder = args.input
    if args.output.split('.')[0] == "Result":
        FinalFile = "Final.bin"
    else:
        FinalFile = args.output.split('.')[0] + ".bin"
    PatchImport = args.patches
    VerboseMode = args.verbose
else:
    Folder = input("Enter the name of the relative folder to import into a ROM image: ")
    FinalFile = input("Enter the name of the resulting filename: ")
    if FinalFile.split('.')[0] == "Result":
        FinalFile = "Final.bin"
    else:
        FinalFile = FinalFile.split('.')[0] + ".bin"
    PatchImportStr = input("Import Patches? (Y if yes) ")
    if PatchImportStr == "y" or PatchImportStr == "Y":
        PatchImport = True
    VerboseModeStr = input("Verbose Mode? (Y if yes) ")
    if VerboseModeStr == "y" or VerboseModeStr == "Y":
        VerboseMode = True


pathDiv = "/"
if sys.platform == "win32":
    pathDiv = "\\"

tmpDir = "tmp"
if os.path.exists(tmpDir):
    shutil.rmtree(tmpDir)
shutil.copytree(Folder, tmpDir)
for path, dirc, files in os.walk(tmpDir):
    for name in sorted(files):
        if name.endswith(".wav"):
            shutil.copy(Folder + pathDiv + name, tmpDir + pathDiv + name)
        
ROMImport.run(tmpDir, PatchImport, VerboseMode)
ROMScramble.run("Result.bin", FinalFile)

#os.remove("sampleList.txt")
os.remove("SampleTable.bin")
os.remove("MultiTable.bin")
shutil.rmtree(tmpDir)
print("Done!")
