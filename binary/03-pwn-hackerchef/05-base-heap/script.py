# -*- coding: utf-8 -*-

import os
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('-g', '--gcc', default=False, action='store_true', help='gcc 编译')

ap.add_argument('-c', '--changeVersion', default=False, action='store_true', help = 'change glibc version')
ap.add_argument('-v', '--version', default='2.23', type=str, help = 'select glibc version, default is 2.23')

ap.add_argument('fileName', help = 'need fileName')

args = vars(ap.parse_args())

BASEDIR = os.getcwd()
LIBSDIR = os.path.join(BASEDIR, 'libs')

GLIBCPATH = {
    '2.23': os.path.join(LIBSDIR, '2.23'),
    '2.31': os.path.join(LIBSDIR, '2.31')
}

WORKDIR = 'heap_base'

def exec(cmd):
    os.system(cmd)

def changeVersion(fileName, version):

    # set-interpreter ld.so
    ldPath = os.path.join(GLIBCPATH.get(version), 'ld-{}.so'.format(version))
    ldStr = 'patchelf --set-interpreter {} {}'.format(ldPath, fileName)
    exec(ldStr)

    # replace-needer
    libcPath = os.path.join(GLIBCPATH.get(version), 'libc.so.6')
    libcStr = 'patchelf --replace-needed libc.so.6 {} {}'.format(libcPath, fileName)
    exec(libcStr)

    # show ldd
    exec('ldd {}'.format(fileName))

def gcc(fileName):
    gccStr = 'gcc -g -o {} {}'.format(fileName[:-2], fileName)
    exec(gccStr)

if not args['fileName']:
    print('You must specify the fileName')
    exit(1)

if args['gcc']:
    gcc(args['fileName'])

elif args['changeVersion']:
    if not args['version']:
        print('You must specify the version with -v 2.23 (example)')
        exit(0)
    changeVersion(args['fileName'], args['version'])

else:
    print('bad args')
    exit(0)