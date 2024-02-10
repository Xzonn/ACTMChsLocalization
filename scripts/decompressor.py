import struct

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
        offset, len = struct.unpack("<HB", compressed[compressed_pos : compressed_pos + 3])
        offset = (offset + 0xff + 4) & 0xffff
        len += 4
        compressed_pos += 3

        while offset < uncompressed_pos - 0x10000:
          offset += 0x10000

        if offset < 0 or offset + len >= sizeun:
          for x in range(len):
            uncompressed[uncompressed_pos + x] = 0
        else:
          for x in range(len):
            uncompressed[uncompressed_pos + x] = uncompressed[offset + x]

        uncompressed_pos += len

  return uncompressed
