#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

// gcc -o blog2 -no-pie -fstack-protector-all blog2.c
void main()
{
    init();
    char buf[0x100];
    memset(&buf, 0, 0x100ull);
    puts("input sth: ");
    read(0, &buf, 0x100ull);
    printf(&buf);
    puts("bye~");
    exit(0);
}
