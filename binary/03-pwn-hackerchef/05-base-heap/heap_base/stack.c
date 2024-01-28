# include <stdio.h>
# include <stdlib.h>
# include <string.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

void backdoor() {
    system("/bin/sh");
}

// gcc -o stack -m32 -g -fstack-protector -no-pie ./heap_base/stack.c 
int main() {
    init();

    char buf[0x20];
    char *ptr = buf;

    printf("input your overflow chain: \n");
    gets(ptr);

    return 0;
}