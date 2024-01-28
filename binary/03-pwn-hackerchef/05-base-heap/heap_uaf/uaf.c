#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct
{
    char name[8];
    int privilege;
    char *msg;
} Info;

void init()
{
    setvbuf(stdin, 0ull, 2, 0ull);
    setvbuf(stdout, 0ull, 2, 0ull);
    setvbuf(stderr, 0ull, 2, 0ull);
}

int main()
{
    init();

    char *buf[0x10];
    char *input[0x10];

    Info *ptr1 = malloc(sizeof(Info));
    Info *ptr2 = malloc(sizeof(Info));
    Info *ptr3 = malloc(sizeof(Info));

    free(ptr1);
    free(ptr2);
    free(ptr3);

    memcpy(buf, ptr1, sizeof(buf));
    printf("ptr1.fd = %#llx\n", *(unsigned long long *)buf);

    ptr2 = NULL;
    printf("ptr2.fd = %#llx\n", ptr2);

    puts("input sth");
    read(0, ptr3->name, 0x8);
    puts(ptr3->name);

    return 0;
}

// gcc -o ./heap_uaf/uaf -g ./heap_uaf/uaf.c