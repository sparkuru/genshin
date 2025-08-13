import base64

VARIANT_BASE64_TABLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
VARIANT_BASE64_DICT = {i: val for i, val in enumerate(VARIANT_BASE64_TABLE)}
VARIANT_BASE64_REVERSE_DICT = {val: i for i, val in enumerate(VARIANT_BASE64_TABLE)}

class LicenseType:
    Professional = 1
    Educational = 3
    Personal = 4

def variant_base64_encode(bs):
    result = []
    blocks_count = len(bs) // 3
    left_bytes = len(bs) % 3

    for i in range(blocks_count):
        coding_int = int.from_bytes(bs[3 * i: 3 * i + 3], 'little')
        block = VARIANT_BASE64_DICT[coding_int & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 12) & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 18) & 0x3f]
        result.extend(block.encode())

    if left_bytes == 1:
        coding_int = int.from_bytes(bs[3 * blocks_count:], 'little')
        block = VARIANT_BASE64_DICT[coding_int & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3f]
        result.extend(block.encode())
    elif left_bytes == 2:
        coding_int = int.from_bytes(bs[3 * blocks_count:], 'little')
        block = VARIANT_BASE64_DICT[coding_int & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 6) & 0x3f]
        block += VARIANT_BASE64_DICT[(coding_int >> 12) & 0x3f]
        result.extend(block.encode())

    return bytes(result)

def encrypt_bytes(key, bs):
    result = []
    for val in bs:
        result.append(val ^ ((key >> 8) & 0xff))
        key = result[-1] & key | 0x482D
    return bytes(result)

def decrypt_bytes(key, bs):
    result = []
    for val in bs:
        result.append(val ^ ((key >> 8) & 0xff))
        key = val & key | 0x482D
    return bytes(result)

def generate_license(type, user_name, count, major_version, minor_version):
    license_source_str = f"{type}#{user_name}|{major_version}{minor_version}#{count}#{major_version}3{minor_version}6{minor_version}#0#0#0#"
    encrypted_bytes = encrypt_bytes(0x787, license_source_str.encode())
    encoded_bytes = variant_base64_encode(encrypted_bytes)
    return encoded_bytes.decode()