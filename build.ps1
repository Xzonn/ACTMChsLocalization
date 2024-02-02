# Download the original files
if (-not(Test-Path -Path "original_files/arm9.bin" -PathType "Leaf")) {
  Invoke-WebRequest $env:ORIGINAL_FILES_URL -OutFile "original_files.zip"
  Expand-Archive -Path "original_files.zip" -DestinationPath "original_files/"
}

# Download the Source Han Serif SC
if (-not(Test-Path -Path "original_files/SourceHanSerifSC-SemiBold.otf" -PathType "Leaf")) {
  Invoke-WebRequest "https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-SemiBold.otf" -OutFile "original_files/SourceHanSerifSC-SemiBold.otf"
}

# Import texts and create font
python "scripts/import_texts.py"

# Import images
python "scripts/import_images.py"

# Create xdelta
dotnet-script scripts/create_xdelta.csx

# Edit banner
dotnet-script scripts/edit_banner.csx

# Create patch.zip
Copy-Item -Path "files/md5.txt" -Destination "out/patch/md5.txt" -Force
Compress-Archive -Path "out/patch/*" -DestinationPath "out/patch.zip" -Force
Move-Item -Path "out/patch.zip" -Destination "out/patch.xzp" -Force