#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

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
    Info *info;
    char *msg;
    int msgSize;

    init();

    printf("try to overflow me\n");
    printf("input your msg size: \n");
    scanf("%d", &msgSize);

    msg = malloc(0x40);
    info = malloc(sizeof(Info));

    strcpy(info->name, "User");
    info->privilege = 1;
    info->msg = msg;

    read(0, msg, msgSize);

    printf("checking your privilege\n");
    if (info->privilege == 2)
    {
        printf("welcome Admin, your privilege is %d\n", info->privilege);
        free(msg);
        free(info);
        system("/bin/sh");
    }
    else
    {
        printf("nonono, your privilege is %d\n", info->privilege);
    }

    return 0;
}