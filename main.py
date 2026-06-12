LANE_BITS = 128
LANE_MASK = (1 << LANE_BITS) - 1
ROUNDS = 32

RHO_OFFSETS = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]

def rotl(x: int, n: int, bits: int = LANE_BITS) -> int:
    n %= bits
    return ((x << n) | (x >> (bits - n))) & ((1 << bits) - 1)

def avalanche_mix_lane(v: int) -> int:
    v ^= (v >> 37)
    v = (v * 0x9E3779B185EBCA87) & LANE_MASK
    v ^= (v >> 41)
    v = (v * 0xC2B2AE3D27D4EB4F) & LANE_MASK
    v ^= (v >> 47)
    return v & LANE_MASK

def crush_lane(v: int) -> int:
    # Intentionally non-invertible:
    # 1) fold high 64 bits into low 64
    low = v & ((1 << 64) - 1)
    high = v >> 64
    w = (low ^ high) & ((1 << 64) - 1)

    # 2) nonlinear 64-bit mixing
    w ^= (w >> 33)
    w = (w * 0xff51afd7ed558ccd) & ((1 << 64) - 1)
    w ^= (w >> 29)
    w = (w * 0xc4ceb9fe1a85ec53) & ((1 << 64) - 1)
    w ^= (w >> 32)

    # 3) re-expand to 128 bits in a structured but irreversible way
    v128 = (w << 64) | (w ^ 0xA5A5A5A5A5A5A5A5)
    return v128 & LANE_MASK

def keccak_like_permute(state):
    for rnd in range(ROUNDS):
        # θ
        C = [0] * 5
        for x in range(5):
            C[x] = state[x][0] ^ state[x][1] ^ state[x][2] ^ state[x][3] ^ state[x][4]
        D = [0] * 5
        for x in range(5):
            D[x] = rotl(C[(x - 1) % 5], 7) ^ C[(x + 1) % 5]
        for x in range(5):
            for y in range(5):
                state[x][y] ^= D[x]

        # ρ + π
        B = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                nx = y
                ny = (2 * x + 3 * y) % 5
                B[nx][ny] = rotl(state[x][y], RHO_OFFSETS[x][y], LANE_BITS)

        # χ + avalanche + crush (non-invertible)
        for x in range(5):
            for y in range(5):
                v = B[x][y] ^ ((~B[(x + 1) % 5][y]) & B[(x + 2) % 5][y])
                v &= LANE_MASK
                v = avalanche_mix_lane(v)
                state[x][y] = crush_lane(v)

        # ι
        rc = ROUND_CONSTANTS[rnd % len(ROUND_CONSTANTS)]
        state[0][0] ^= rc

    return state

def pad10star1(message: bytes, rate_bytes: int) -> bytes:
    m = bytearray(message)
    m.append(0x06)
    while (len(m) % rate_bytes) != (rate_bytes - 1):
        m.append(0x00)
    m.append(0x80)
    return bytes(m)

def sponge_hash(data: bytes, out_bits: int = 512) -> str:
    state = [[0 for _ in range(5)] for _ in range(5)]

    rate_bits = 1024
    rate_bytes = rate_bits // 8
    out_bytes = out_bits // 8

    padded = pad10star1(data, rate_bytes)

    # Absorb
    for offset in range(0, len(padded), rate_bytes):
        block = padded[offset:offset + rate_bytes]
        lanes_in_rate = rate_bytes // 16  # 16 bytes per 128-bit lane

        for i in range(lanes_in_rate):
            chunk = block[i * 16:(i + 1) * 16]
            val = int.from_bytes(chunk, "little")
            x = i % 5
            y = i // 5
            state[x][y] ^= val & LANE_MASK

        state = keccak_like_permute(state)

    # Squeeze
    output = bytearray()
    while len(output) < out_bytes:
        lanes_in_rate = rate_bytes // 16
        for i in range(lanes_in_rate):
            x = i % 5
            y = i // 5
            lane = crush_lane(avalanche_mix_lane(state[x][y]))
            lane_bytes = lane.to_bytes(16, "little")
            output.extend(lane_bytes)
            if len(output) >= out_bytes:
                break
        if len(output) >= out_bytes:
            break
        state = keccak_like_permute(state)

    return output[:out_bytes].hex()

if __name__ == "__main__":
    print("H('hello') =", sponge_hash(b"hello", 512))
    print("H('hellp') =", sponge_hash(b"hellp", 512))
