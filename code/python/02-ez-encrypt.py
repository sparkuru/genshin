# -*- coding: utf-8 -*-

import argparse
import os
import sys
import subprocess
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from getpass import getpass


def color(text: str = '', color: int = 1) -> str:
    '''
    Returns the corresponding console ANSI color
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


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=10000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())


def pad_salt(salt: bytes, desired_length: int = 16) -> bytes:
    if len(salt) < desired_length:
        salt += b'\x00' * (desired_length - len(salt))
    elif len(salt) > desired_length:
        salt = salt[:desired_length]
    return salt


def encrypt_file(input_path: str, output_path: str, password: str, salt: bytes):
    salt = pad_salt(salt)
    key = derive_key(password, salt)
    initialization_vector = salt[:16]
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(initialization_vector),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()

    with open(input_path, 'rb') as f:
        data = f.read()

    # AES byte padding
    padding_length = 16 - len(data) % 16
    data += bytes([padding_length] * padding_length)

    cipher_text = encryptor.update(data) + encryptor.finalize()

    with open(output_path, 'wb') as f:
        f.write(salt + cipher_text)


def decrypt_file(input_path: str, output_path: str, password: str):
    file_size = os.path.getsize(input_path)
    if file_size < 16:
        raise ValueError(f"{color('File size abnormal, might not be a valid encrypted file', 1)}")

    with open(input_path, 'rb') as f:
        try:
            salt_read = f.read(16)
            cipher_text = f.read()

            if not salt_read or not cipher_text:
                raise ValueError(f"{color('Invalid file format, might not be a valid encrypted file', 1)}")

            salt_read = pad_salt(salt_read)
            key = derive_key(password, salt_read)
            initialization_vector = salt_read[:16]
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(initialization_vector),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            data = decryptor.update(cipher_text) + decryptor.finalize()

            padding_length = data[-1]
            if padding_length > 16 or padding_length < 1:
                raise ValueError(f"{color('Decryption failed: invalid padding', 1)}")

            data = data[:-padding_length]

            with open(output_path, 'wb') as f:
                f.write(data)
        except (ValueError, Exception) as e:
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e


def process_directory(directory: str, func, output_dir: str, password: str, recursive: bool, salt: bytes = None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for root, dirs, files in os.walk(directory):
        for file in files:
            input_path = os.path.join(root, file)
            rel_path = os.path.relpath(input_path, directory)
            output_path = os.path.join(output_dir, rel_path)
            if func == encrypt_file:
                func(input_path, output_path, password, salt)
            else:  # decrypt_file
                func(input_path, output_path, password)
        if not recursive:
            break


def get_system_uuid() -> str:
    try:
        if sys.platform == "win32":
            cmd = 'wmic csproduct get UUID'
            uuid = subprocess.check_output(cmd).decode().split('\n')[1].strip()
        elif sys.platform == "linux":
            cmd = 'cat /proc/sys/kernel/random/uuid'
            uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        elif sys.platform == "Darwin":
            cmd = "system_profiler SPHardwareDataType | awk '/UUID/ { print $3; }'"
            uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        else:
            raise Exception("Unsupported OS")
        return uuid
    except Exception as e:
        print(f"Error obtaining system UUID: {e}")
        exit()


def get_salt(key: str, salt_file='salt', is_use_salt=False) -> str:
    if os.path.exists(salt_file) and is_use_salt:
        with open(salt_file, 'rb') as file:
            salt = file.read()
            if salt != b'':
                return salt

    uuid = get_system_uuid() if is_use_salt else key
    salt_sha256_obj = hashes.Hash(hashes.SHA256(), backend=default_backend())
    salt_sha256_obj.update(uuid.encode())
    salt_sha256_obj.update(key.encode())
    salt = salt_sha256_obj.finalize()

    if is_use_salt:
        with open(salt_file, 'wb') as file:
            file.write(salt[:16])
    return salt


def get_banner():
    script_name = os.path.basename(sys.argv[0])
    description = f'{color("Simple Encrypt/Decrypt Tool", 2)}'
    epilog = f'''
{color("Examples:", 3)}
  Encrypt a file:
    {color(f"python {script_name} enc -i secret.txt", 6)}
  Decrypt a file:
    {color(f"python {script_name} dec -i secret.txt.enc", 6)}
  Encrypt a directory recursively:
    {color(f"python {script_name} enc -i secret_folder -r", 6)}
  Encrypt with custom salt file:
    {color(f"python {script_name} enc -i secret.txt -s my_salt", 6)}
'''
    return description, epilog


def main():
    description, epilog = get_banner()
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )

    # Create argument groups for better organization
    mode_group = parser.add_argument_group(f'{color("Mode", 2)}')
    mode_group.add_argument(
        'mode',
        choices=['enc', 'dec'],
        metavar='MODE',
        help='Choose operation mode: enc(encrypt) or dec(decrypt)'
    )

    required_group = parser.add_argument_group(f'{color("Required arguments", 2)}')
    required_group.add_argument(
        '-i', '--input',
        required=True,
        help='Specify input file or directory path'
    )

    optional_group = parser.add_argument_group(f'{color("Optional arguments", 2)}')
    optional_group.add_argument(
        '-o', '--output',
        help='Specify output file or directory path'
    )
    optional_group.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process directory recursively'
    )
    optional_group.add_argument(
        '-d', '--delete',
        action='store_true',
        help='Delete source file after processing'
    )

    security_group = parser.add_argument_group(f'{color("Security options", 2)}')
    security_group.add_argument(
        '-s', '--salt',
        help='Specify a salt file. If file is empty, generate salt from key and uuid'
    )
    security_group.add_argument(
        '-k', '--key',
        help='Specify a key file or string (not recommended in command line)'
    )

    args = vars(parser.parse_args())
    args['mode'] = args.pop('mode')
    
    # assert
    assert os.path.exists(args['input']), f'{color("Invalid input file or directory", 3)}'

    # Check if key is specified and get its value
    if args['key'] is None:
        password = getpass(color('Please enter key: ', 3))
    else:
        if os.path.exists(args['key']):
            with open(args['key'], 'r') as f:
                password = f.read().strip()
        else:
            password = args['key']

    if args['salt'] is not None:
        salt = get_salt(password, args['salt'], is_use_salt=True)
    else:
        salt = get_salt(password, is_use_salt=False)

    if os.path.isdir(args['input']):
        if args['output'] is None:
            if args['mode'] == 'enc':
                args['output'] = args['input'] + \
                    ('_enc' if not args['input'].endswith('_enc') else '')
            elif args['mode'] == 'dec':
                if args['output'].endswith('_enc'):
                    temp_dir = args['output'][:-4]
                    if os.path.exists(temp_dir):
                        args['output'] = temp_dir + '_dec'
        process_directory(
            args['input'],
            encrypt_file if args['mode'] == 'enc' else decrypt_file,
            args['output'],
            password,
            args['recursive'],
            salt
        )
    else:
        if args['output'] is None:
            args['output'] = args['input'] + \
                '.enc' if args['mode'] == 'enc' else args['input'].rstrip(
                    '.enc')
        if args['mode'] == 'enc':
            encrypt_file(args['input'], args['output'], password, salt)
        else:
            decrypt_file(args['input'], args['output'], password)

    if args['delete']:
        if args['mode'] == 'enc':
            assert input('Delete source file? (y/n)') == 'y', '{}'.format(color('Deletion cancelled', 3))
            if os.path.isdir(args['input']):
                for root, dirs, files in os.walk(args['input'], topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            else:
                os.remove(args['input'])
        elif args['mode'] == 'dec':  # Add deletion for decryption
            assert input('Delete source file? (y/n)') == 'y', '{}'.format(color('Deletion cancelled', 3))
            if os.path.isdir(args['input']):
                for root, dirs, files in os.walk(args['input'], topdown=False):
                    for name in files:
                        os.remove(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
            else:
                os.remove(args['input'])


if __name__ == '__main__':
    main()
