#!/usr/bin/env dotnet-script
#r "nuget: NitroHelper, 0.12.0"

var newTitle = "Another Code\n两种记忆\nNintendo";
var banner = new NitroHelper.Banner($"original_files/banner.bin");
banner.japaneseTitle = newTitle;
banner.englishTitle = newTitle;
banner.frenchTitle = newTitle;
banner.germanTitle = newTitle;
banner.italianTitle = newTitle;
banner.spanishTitle = newTitle;
banner.WriteTo($"out/patch/banner.bin");