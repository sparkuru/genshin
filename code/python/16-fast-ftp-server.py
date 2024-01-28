# -*- coding: utf-8 -*-
# need pip install wsgidav gevent netifaces

def exec(cmd):
    assert type(cmd) == str, 'wrong cmd'
    import subprocess
    try:
        output = subprocess.check_output(cmd, shell=True)
        print(output)
    except KeyboardInterrupt:
        print("Process interrupted")
        return

def color(text) -> str:
    return '\033[1;33m{}\033[0m'.format(text)

def fgx(text = False, _fgx = '='):
    _fgx = _fgx * 10
    print('\033[1;34m{}\033[0m {} \033[1;34m{}\033[0m'.format(_fgx, text if text else '分割线', _fgx))


import argparse
ap = argparse.ArgumentParser(description = '用于在当前文件夹下创建一个 webdav 项目; e.g.: {}'.format(color('webdav --port 1024')))
ap.add_argument('-p', '--port', type = int, default = 1024, help = '指定创建 dav 的端口, 默认 1024')
args = vars(ap.parse_args())

import netifaces as ni
for interface in ni.interfaces():
    try:
        ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
        print('Access: {}'.format(color('http://{}:{}'.format(ip, args['port']))))
    except KeyError:
        pass
    except KeyboardInterrupt:
        print("Process interrupted")
        break
    finally:
        continue

try:
    exec('wsgidav --host 0.0.0.0 --port {} --auth anonymous --server gevent --root .'.format(args['port']))
except KeyboardInterrupt:
    print("Server stopped by user")