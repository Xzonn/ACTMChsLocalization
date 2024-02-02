import os
import struct
from typing import Any, Generator
from PIL import Image

import decompressor

os.makedirs("temp_files/pack/", exist_ok=True)

head_inf_reader = open("original_files/data/data/pack/head.inf", "rb")
head_bin_reader = open("original_files/data/data/pack/head.bin", "rb")
head_bin_writer = open("temp_files/pack/head.bin", "wb")
head_bin_writer.write(head_bin_reader.read())

def get_xy_objh_1234(width: int, height: int) -> Generator[tuple[int, int], Any, None]:
  for y_1 in range(0, height, 8):
    for x_1 in range(0, width, 8):
      for y_2 in range(8):
        for x_2 in range(8):
          yield x_1 + x_2, y_1 + y_2

def get_xy_tile(width: int, height: int) -> Generator[tuple[int, int], Any, None]:
  for y in range(height):
    for x in range(width):
      yield x, height - y - 1

while True:
  file_name = head_inf_reader.read(0x10).decode("utf8").rstrip("\0")
  if file_name == "END":
    break
  start_pos, length, unk1, unk2 = struct.unpack("<4I", head_inf_reader.read(0x10))
  if not os.path.exists(f"files/images/{file_name}"):
    continue

  file_reader = open(f"original_files/data/data/pack/{file_name}.bin", "rb")
  file_writer = open(f"temp_files/pack/{file_name}.bin", "wb")
  file_writer.seek(0)

  head_bin_reader.seek(start_pos)
  while True:
    sub_name = head_bin_reader.read(0x10).decode("utf8").rstrip("\0")
    if sub_name == "END":
      break
    sub_start_pos, sub_length, unk1, unk2 = struct.unpack("<4I", head_bin_reader.read(0x10))

    file_reader.seek(sub_start_pos)
    new_start_pos = file_writer.tell()
    head_bin_writer.seek(head_bin_reader.tell() - 0x10)
    head_bin_writer.write(struct.pack("<I", new_start_pos))
    if not os.path.exists(f"files/images/{file_name}/{sub_name}.png"):
      file_writer.write(file_reader.read(sub_length))
    else:
      original_data = file_reader.read(sub_length)
      has_header = True
      if original_data.startswith(b"\x12\x3d\xda\x01"):
        decompressed = decompressor.decompress(original_data)
      elif original_data.startswith(b"\x12\x3d\xda\x01"):
        decompressed = bytearray(original_data[0x10:])
      else:
        decompressed = bytearray(original_data)
        has_header = False

      image_length, unk, palette_length = struct.unpack("<3H", decompressed[0x08:0x0e])
      half_byte = palette_length == 0x20
      palette = []
      palette_index = 0
      for i in range(palette_length // 2):
        color = struct.unpack("<H", decompressed[0x10 + i * 2 : 0x12 + i * 2])[0] & 0x7fff
        if color != 0 and palette_index == 0:
          palette_index = i
        palette.append(color)
      image = Image.open(f"files/images/{file_name}/{sub_name}.png").convert("RGB")
      width, height = image.size
      new_binary = bytearray(width * height // (2 if half_byte else 1))
      xy_generator = get_xy_objh_1234(width, height)
      if width == 32 and height == 32:
        xy_generator = get_xy_tile(width, height)
      pos = 0
      for x, y in xy_generator:
        pixel = image.getpixel((x, y))
        r = pixel[0] >> 3
        g = pixel[1] >> 3
        b = pixel[2] >> 3
        color = (b << 10) | (g << 5) | r
        if color not in palette:
          if palette_index > 0:
            palette_index -= 1
            palette[palette_index] = color
            color_index = palette_index
          else:
            print(f"Invalid color {color:04x} (#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}) in {file_name}/{sub_name}.png")
        else:
          color_index = palette.index(color)
        if half_byte:
          if x % 2 == 0:
            new_binary[pos] = (new_binary[pos] & 0xf0) + color_index
          else:
            new_binary[pos] = (new_binary[pos] & 0x0f) + (color_index << 4)
            pos += 1
        else:
          new_binary[pos] = color_index
          pos += 1
      decompressed[0x10 + palette_length:0x10 + palette_length + image_length] = new_binary
      for i in range(palette_length // 2):
        decompressed[0x10 + i * 2 : 0x12 + i * 2] = struct.pack("<H", palette[i] | 0x8000)

      if has_header:
        file_writer.write(b"\x12\x3d\xda\x00" + struct.pack("<I", len(decompressed)) + b"\xff\xff\xff\xff\x00\x00\x00\x00")
      file_writer.write(decompressed)
      head_bin_writer.write(struct.pack("<I", len(decompressed) + 0x10))

    while file_writer.tell() % 0x20 != 0:
      file_writer.write(b"\xff")
