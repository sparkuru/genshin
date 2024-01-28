#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

void banner()
{
    puts("\
=========== shellcode test ===========\n\
1. 熟悉 shellcraft.sh() z\n\
2. 栈上空间不够，使用更短的 shellcode z\n\
=========== shellcode test ===========\n\
choose: ");
}

void shellcode1()
{
    char buf[0x50];
    memset(&buf, 0, sizeof(buf));
    printf("your return address should be: %p\n", &buf);
    read(0, &buf, 0x6c);
}

void shellcode2()
{
    char buf[0x19];
    memset(&buf, 0, sizeof(buf));
    printf("return to stack: %p\n", &buf);
    read(0, &buf, 0x30);
}

// gcc -z execstack -o blog3 blog3.c
int main()
{
    int select = 0;
    init();
    banner();
    scanf("%d", &select);
    switch (select)
    {
    case 1:
        shellcode1();
        break;
    case 2:
        shellcode2();
        break;
    default:
        puts("wrong choice");
        break;
    }
    return 0;
}