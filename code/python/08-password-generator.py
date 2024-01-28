# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import base64
import argparse
import subprocess
from time import time

OUTPUT_PASSWORD_COLOR = 3
OUTPUT_LENGTH_COLOR = 4
OUTPUT_KEY_COLOR = 5
OUTPUT_SALT_COLOR = 6

BANNER = '''Generated password with:
| password: {}
| length: {}
| key: {}
| salt_file: {}'''

def color(text: str = '', color: int = 1) -> str:
    '''
    返回对应的控制台 ANSI 颜色
    '''
    color_table = {
        0: '\033[1;30m{}\033[0m',   # 黑色加粗
        1: '\033[1;31m{}\033[0m',   # 红色加粗
        2: '\033[1;32m{}\033[0m',   # 绿色加粗
        3: '\033[1;33m{}\033[0m',   # 黄色加粗
        4: '\033[1;34m{}\033[0m',   # 蓝色加粗
        5: '\033[1;35m{}\033[0m',   # 紫色加粗
        6: '\033[1;36m{}\033[0m',   # 青色加粗
        7: '\033[1;37m{}\033[0m',   # 白色加粗
    }
    return color_table[color].format(text)


def get_system_uuid() -> str:
    try:
        if sys.platform == "win32":
            cmd = 'wmic csproduct get UUID'
            uuid = subprocess.check_output(cmd).decode().split('\n')[1].strip()
        elif sys.platform == "linux":
            cmd = 'cat /proc/sys/kernel/random/uuid'
            uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        else:
            raise Exception("Unsupported OS")
        return uuid
    except Exception as e:
        print(f"Error obtaining system UUID: {e}")
        exit()

def get_salt(uuid: str, key: str, salt_file: str ='salt') -> str:
    if os.path.exists(salt_file):
        with open(salt_file, 'r') as file:
            salt = file.read()
            if salt != '':
                return salt

    salt_sha256_obj = hashlib.sha256(uuid.encode())
    salt_sha256_obj.update(key.encode())
    salt = salt_sha256_obj.hexdigest()[:16]

    with open(salt_file, 'w') as file:
        file.write(salt)
    return salt

def get_file_full_path(file_path: str) -> str:
    return os.path.abspath(file_path).replace('\\', '/')

def check_length(src_length: int, generated_password: str) -> int:
    this_length = len(generated_password)
    return src_length - this_length if this_length < src_length else 0

def generate_password(seed: str, length: int, salt_file: str, char_set: str = None, is_recursive: bool = False) -> str:
    if salt_file is not None:
        system_uuid = get_system_uuid()
        salt = get_salt(system_uuid, seed, salt_file)
        salt = base64.b64encode(salt.encode()).decode('utf-8')
    else:
        salt = seed

    password = ''
    current_seed = seed
    
    while len(password) < length:
        hash_bytes = hashlib.sha256(current_seed.encode()).digest()
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            hash_bytes,
            salt.encode(),
            10000
        )
        base64_str = base64.b64encode(hash_bytes).decode()
        
        # 过滤字符
        if char_set:
            password += ''.join(c for c in base64_str if c in char_set)
        else:
            password += ''.join(c for c in base64_str if c.isalnum() or c in '-#.')
            
        current_seed = base64_str  # 使用新的base64字符串作为下一次迭代的种子
    
    return password[:length]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-k', '--key', type=str,
                    help='Seed for password generation')
    ap.add_argument('-l', '--length', default=15,
                    type=int, help='Password length')
    ap.add_argument('-s', '--salt', type=str, default=None,
                    help='指定一个含有 salt 的文件路径, 没有则自动创建并写入随机字符')
    ap.add_argument('--char', type=str, default=None,
                    help='指定密码生成的字符集, 例如 --char "abcdefg123"')
    args = vars(ap.parse_args())

    if args['key'] is None:
        key_seed = str(time())
    else:
        key_seed = args['key']

    password = generate_password(key_seed, args['length'], args['salt'], args['char'])
    print(BANNER.format(
        color(password, OUTPUT_PASSWORD_COLOR),
        color(str(len(password)), OUTPUT_LENGTH_COLOR),
        color(key_seed + ' (base on time.time())' if (args['key'] is None) else key_seed, OUTPUT_KEY_COLOR),
        color(get_file_full_path(args['salt']) if args['salt'] else 'None', OUTPUT_SALT_COLOR)
    ))


if __name__ == "__main__":
    main()
