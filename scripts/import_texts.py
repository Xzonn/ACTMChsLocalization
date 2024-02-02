import json
import os
import struct
from PIL import Image, ImageDraw, ImageFont

FONT_CONFIG = [
  {
    "postfix": "_lc",
    "font_path": "C:/Windows/Fonts/SimSun.ttc",
    "font_size": 12,
    "x": 0,
    "y": -1,
  },
  {
    "postfix": "",
    "font_path": "original_files/SourceHanSerifSC-SemiBold.otf",
    "font_size": 12,
    "x": 0,
    "y": -3,
  },
]
OVERLAY_RAM_ADDR = 0x02164a60

def import_texts() -> list[str]:
  cp932_chars = []
  with open("files/cp932.txt", "r", -1, "utf8") as reader:
    lines = reader.read().splitlines()
  for line in lines:
    if line.startswith("#"):
      continue
    no, char_code, char = line.split("\t")
    cp932_chars.append(char)

  chinese_to_cp932 = {}
  texts = []
  for file_name in os.listdir("offsets"):
    with open(f"texts/zh_Hans/{file_name}", "r", -1, "utf8") as reader:
      texts_data: dict[str, str] = json.load(reader)
    texts += texts_data.values()
  for char in sorted(set("".join(texts))):
    if char not in chinese_to_cp932 and 0x4e00 <= ord(char) <= 0x9fff:
      chinese_to_cp932[char] = cp932_chars.pop(0)

  all_texts = {}
  for file_name in os.listdir("offsets"):
    with open(f"offsets/{file_name}", "r", -1, "utf8") as reader:
      offsets_data: list[dict[str, str | int]] = json.load(reader)

    with open(f"texts/zh_Hans/{file_name}", "r", -1, "utf8") as reader:
      texts_data: dict[str, str] = json.load(reader)
    all_texts.update(texts_data)

    binary_path = file_name
    if file_name.startswith("overlay_"):
      binary_path = f"overlay/{file_name}"
    binary_path = binary_path.replace(".json", ".bin")

    with open(f"original_files/{binary_path}", "rb") as reader:
      binary_data = bytearray(reader.read())

    for offsets in offsets_data:
      id: str = offsets["id"]
      pos: int = offsets["pos"]
      length: int = offsets.get("new_length", offsets["length"])

      if "new_pos" in offsets:
        pos = offsets["new_pos"]
        overlay_pos_list = offsets["overlay_pos"]
        if type(overlay_pos_list) == int:
          overlay_pos_list: list[int] = [overlay_pos_list]
        for overlay_pos in overlay_pos_list:
          assert binary_data[overlay_pos:overlay_pos + 4] == struct.pack("<I", OVERLAY_RAM_ADDR + offsets["pos"])
          binary_data[overlay_pos:overlay_pos + 4] = struct.pack("<I", OVERLAY_RAM_ADDR + pos)

      text: str = ""
      if "equals" in offsets and offsets["equals"] in all_texts:
        text = all_texts[offsets["equals"]]
        all_texts[id] = text
      elif "parts" in offsets:
        parts = []
        for part in offsets["parts"]:
          if "id" in part:
            parts.append(all_texts[part["id"]])
          elif "text" in part:
            parts.append(part["text"])
        text = "".join(parts)
        all_texts[id] = text
      else:
        text = all_texts.get(id, "")
      
      if not text:
        print(f"Text not found: {id}")
        continue

      new_text = list(text.replace("\n", "").replace("·", "・"))
      for i, char in enumerate(new_text):
        if char not in chinese_to_cp932 and 0x4e00 <= ord(char) <= 0x9fff:
          print(f"Unknown char: {id} {char}")
        elif char in chinese_to_cp932:
          new_text[i] = chinese_to_cp932[char]
      bytes_data = "".join(new_text).encode("cp932")
      if len(bytes_data) > length:
        print(f"Text too long: {id} ({len(bytes_data)} > {length})")
        continue
      elif len(bytes_data) < length:
        bytes_data += b"\0" * (length - len(bytes_data))
      binary_data[pos : pos + length] = bytes_data

    with open(f"out/patch/{binary_path}", "wb") as writer:
      writer.write(binary_data)

  return list(chinese_to_cp932.keys())

def create_font(char_list: list[str]):
  for config in FONT_CONFIG:
    postfix = config["postfix"]
    font_path = config["font_path"]
    font_size = config["font_size"]
    x = config["x"]
    y = config["y"]

    font = ImageFont.truetype(font_path, font_size)
    with open(f"original_files/data/data/font{postfix}.bin", "rb") as reader:
      font_data = bytearray(reader.read())

    OFFSET = 1410

    for i in range(OFFSET):
      # Move the original font data to 1px down
      original_byte_data = font_data[i * 0x40 : (i + 1) * 0x40]
      new_byte_data = original_byte_data[0x2E : 0x30] + original_byte_data[0x00 : 0x0E] + original_byte_data[0x3E : 0x40] + original_byte_data[0x10 : 0x1E] + original_byte_data[0x0E : 0x10] + original_byte_data[0x20 : 0x2E] + original_byte_data[0x1E : 0x20] + original_byte_data[0x30 : 0x3E]
      font_data[i * 0x40 : (i + 1) * 0x40] = new_byte_data

    for i, char in enumerate(char_list):
      image = Image.new("L", (16, 16))
      draw = ImageDraw.Draw(image)
      draw.text((x, y), char, font=font, fill=255)
      byte_data = []
      for y_1 in range(0, 16, 8):
        for x_1 in range(0, 16, 8):
          for y_2 in range(8):
            for x_2 in range(0, 8, 4):
              value = 0
              for j in range(4):
                bit = image.getpixel((x_1 + x_2 + j, y_1 + y_2)) // 64
                value |= bit << (6 - j * 2)
              byte_data.append(value)
      font_data[(OFFSET + i) * 0x40 : (OFFSET + i + 1) * 0x40] = bytes(byte_data)

    with open(f"out/patch/data/data/font{postfix}.bin", "wb") as writer:
      writer.write(font_data)

if __name__ == "__main__":
  os.makedirs("out/patch/data/data", exist_ok=True)
  os.makedirs("out/patch/overlay", exist_ok=True)

  char_list = import_texts()
  create_font(char_list)