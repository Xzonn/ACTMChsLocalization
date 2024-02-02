#!/usr/bin/env dotnet-script
#r "nuget: xdelta3.net, 1.0.1"

using xdelta3.net;

Directory.CreateDirectory("out/patch/xdelta/data/data/pack/");
foreach(var fileName in Directory.GetFiles("temp_files/pack/"))
{
  var fileNameWithoutPath = Path.GetFileName(fileName);
  CreatePatch($"original_files/data/data/pack/{fileNameWithoutPath}", $"temp_files/pack/{fileNameWithoutPath}", $"out/patch/xdelta/data/data/pack/{fileNameWithoutPath}");
}

void CreatePatch(string source, string target, string output)
{
  var sourceBytes = File.ReadAllBytes(source);
  var targetBytes = File.ReadAllBytes(target);
  var delta = Xdelta3Lib.Encode(sourceBytes, targetBytes);
  File.WriteAllBytes(output, delta.ToArray());
}