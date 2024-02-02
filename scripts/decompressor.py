import struct

def Hibit(n: int):
  n |= (n >> 1)
  n |= (n >> 2)
  n |= (n >> 4)
  n |= (n >> 8)
  n |= (n >> 16)
  return n - (n >> 1)

# Thanks to: Jason Harley
# Reference: https://github.com/Jas2o/KyleHyde/blob/main/KyleHyde/Formats/HotelDusk/Decompress.cs
def decompress(compressed: bytearray | bytes) -> bytearray:
  header, sizeun, sizeco, zero = struct.unpack("<4I", compressed[:0x10])
  if header == 0x00da3d12:
    return bytearray(compressed[0x10:])
  elif header != 0x01da3d12:
    return bytearray(compressed)

  uncompressed = bytearray(sizeun)
  uncompressed_pos = 0
  compressed_pos = 0x10
  while compressed_pos < sizeco + 0x10:
    input = compressed[compressed_pos]
    compressed_pos += 1
    for i in range(8):
      if compressed_pos >= sizeco + 0x10:
        break
      bits_i = input & 1
      input >>= 1
      if bits_i:
        uncompressed[uncompressed_pos] = compressed[compressed_pos]
        compressed_pos += 1
        uncompressed_pos += 1
      else:
        offset, = struct.unpack("<H", compressed[compressed_pos : compressed_pos + 2])
        len = 4 + compressed[compressed_pos + 2]
        compressed_pos += 3

        posHi = Hibit(uncompressed_pos - 0xff - 4)
        offHi = Hibit(offset)
        if uncompressed_pos < 0x10000:
          signed = offset & 0xffff
          if signed >= 0x8000:
            signed -= 0x10000
          if signed < 0 and signed + 0xff + 4 >= 0:
            offset = signed
        elif posHi >= 0x20000 and offHi < posHi:
          if offset + posHi < uncompressed_pos:
            offset += posHi
          elif offset + 0x10000 < uncompressed_pos:
            offset += 0x10000
        elif posHi >= 0x10000 and offHi < posHi and offset + posHi < uncompressed_pos:
          offset += posHi
        offset += 0xff + 4

        if offset < 0 or offset + len >= sizeun:
          for x in range(len):
            uncompressed[uncompressed_pos + x] = 0
        else:
          for x in range(len):
            uncompressed[uncompressed_pos + x] = uncompressed[offset + x]

        uncompressed_pos += len

  return uncompressed
