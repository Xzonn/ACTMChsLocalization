import struct

def compress(uncompressed: bytearray | bytes) -> bytearray:
  def find_largest(uncompressed: bytearray | bytes, uncompressed_pos: int) -> tuple[int, int, int]:
    start = max(0, uncompressed_pos - 0x10000)
    before = uncompressed[start :]
    after = uncompressed[uncompressed_pos : uncompressed_pos + 4]
    
    max_len = 0
    max_len_offset = -1
    offset = before.find(after)
    while offset > -1 and start + offset < uncompressed_pos:
      this_len = 4
      while offset + this_len < len(before) and uncompressed_pos + this_len < len(uncompressed) and this_len < 0x103 and before[offset + this_len] == uncompressed[uncompressed_pos + this_len]:
        this_len += 1

      if this_len > max_len:
        max_len = this_len
        max_len_offset = start + offset
      offset = before.find(after, offset + max_len)

    if max_len_offset != -1:
      return 0, max_len_offset, max_len

    if uncompressed[uncompressed_pos:uncompressed_pos + 4] == b"\0\0\0\0":
      zero_pos = uncompressed_pos + 4
      while zero_pos < len(uncompressed) and zero_pos < uncompressed_pos + 0x103 and uncompressed[zero_pos] == 0:
        zero_pos += 1
      if zero_pos < 0xffff:
        zero_len = zero_pos - uncompressed_pos
        return 0, 0x10000 - zero_len, zero_len

    return 1, 0, 0

  compressed = bytearray()
  compressed.extend(struct.pack("<4I", 0x01da3d12, len(uncompressed), 0, 0))

  uncompressed_pos = 0
  bits = 0
  while uncompressed_pos < len(uncompressed):
    bits_pos = len(compressed)
    compressed.append(0)
    bits = 0
    for i in range(8):
      if uncompressed_pos >= len(uncompressed):
        break

      bits_i, max_len_offset, max_len = find_largest(uncompressed, uncompressed_pos)

      if bits_i == 0:
        real_offset = (max_len_offset + 0x10000 - 0xff - 4) & 0xffff
        real_len = max_len - 4
        compressed.extend(struct.pack("<HB", real_offset, real_len))
        uncompressed_pos += max_len
      else:
        compressed.append(uncompressed[uncompressed_pos])
        uncompressed_pos += 1

      bits |= (bits_i << i)
    compressed[bits_pos] = bits

  if len(compressed) - 0x10 > len(uncompressed):
    compressed = bytearray()
    compressed.extend(struct.pack("<4I", 0x00da3d12, len(uncompressed), 0xffffffff, 0))
    compressed.extend(uncompressed)
  else:
    compressed[0x08:0x0c] = struct.pack("<I", len(compressed) - 0x10)
  return compressed
