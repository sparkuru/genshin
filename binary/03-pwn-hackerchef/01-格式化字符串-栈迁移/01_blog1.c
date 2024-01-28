#include <stdio.h>
#include <stdlib.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

void banner()
{
    puts("1. leak_stack");
    puts("2. leak_libc");
    puts("3. rop");
    puts("4. exit");
    puts("Your choice:");
}

void stack()
{
    char buf[0x40];
    puts("try to leak stack");
    read(0, &buf, sizeof(buf));
    printf(&buf);
    return;
}

void libc()
{
    char buf[0x60];
    puts("input sth");
    read(0, &buf, sizeof(buf) + 0x20);
    return;
}

int rop()
{
    char buf[0x60];
    puts("pwn me");
    read(0, &buf, sizeof(buf) + 0x40);
    return 0;
}

// gcc -o blog1 -fstack-protector blog1.c
int main()
{
    init();
    int select;
    while (1)
    {
        banner();
        scanf("%d", &select);
        switch (select)
        {
        case 1:
            stack();
            break;
        case 2:
            libc();
            break;
        case 3:
            rop();
            break;
        case 4:
            exit(0);
        default:
            break;
        }
    }
    return 0;
}
