#include <stdio.h>
#include <stdlib.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

void vuln()
{
    char buf[0xb];
    puts("input sth:");
    gets(&buf);
    puts(&buf);
}


// gcc -o blog4 blog4.c
int main()
{
    init();
    vuln();
    return 0;
}