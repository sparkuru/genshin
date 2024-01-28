#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

// gcc -g -o heap -fstack-protector heap.c
int main()
{

    init();

    int round, chunksize;

    puts("1. input round");
    scanf("%d", &round);

    for (int i = 0; i < round; i++)
    {
        puts("input chunksize");
        scanf("%d", &chunksize);

        printf("start malloc for %d bytes\n", chunksize);
        char *ptr1 = malloc(chunksize);
        char *ptr2 = malloc(chunksize);
        char *ptr3 = malloc(chunksize);

        puts("start memset 'A' to *ptr1");
        memset(ptr2, 'A', chunksize);

        puts("start free");
        free(ptr1);
        free(ptr2);
        free(ptr3);
    }

    return 0;
}