/* SPDX-FileCopyrightText: 2026 maninblack
 * SPDX-License-Identifier: MIT
 * Fixed-path reversible diagnostic, never a shipped component or policy grant.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv) {
    const char *path;
    if (getuid()!=0 || geteuid()!=0 || argc!=2) return 2;
    if (!strcmp(argv[1],"load"))
        path="/run/vision-camera-store-proof/policy-proof/etc/selinux/aos/policy/policy.33";
    else if (!strcmp(argv[1],"restore"))
        path="/run/vision-camera-store-proof/stock-policy.bin";
    else return 2;
    int input=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
    struct stat s;
    if (input<0 || fstat(input,&s) || !S_ISREG(s.st_mode) || s.st_uid ||
        s.st_gid || s.st_nlink!=1 || (s.st_mode&0022) || s.st_size<1024 ||
        s.st_size>64*1024*1024) return 3;
    size_t size=(size_t)s.st_size, at=0;
    char *bytes=malloc(size);
    if (!bytes) return 4;
    while (at<size) {
        ssize_t count=read(input,bytes+at,size-at);
        if (count<0 && errno==EINTR) continue;
        if (count<=0) { free(bytes);return 5; }
        at+=(size_t)count;
    }
    close(input);
    int output=open("/sys/fs/selinux/load",O_WRONLY|O_CLOEXEC|O_NOFOLLOW);
    if (output<0) {free(bytes);return 6;}
    ssize_t written=write(output,bytes,size); /* One exact kernel transaction. */
    free(bytes);close(output);
    if (written!=(ssize_t)size) return 7;
    puts("POLICY_LOAD_COMPLETE");return 0;
}
