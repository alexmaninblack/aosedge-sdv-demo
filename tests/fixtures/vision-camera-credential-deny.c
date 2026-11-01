/* SPDX-FileCopyrightText: 2026 maninblack
 * SPDX-License-Identifier: MIT
 * Exact same-UID/core-domain denial probe. Opens, never reads a credential.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <unistd.h>
int main(int argc,char **argv) {
    /* Resolve account names with the target's native libc in the outer probe.
       A static cross-distro fixture must never dlopen foreign NSS modules. */
    if(argc!=3)return 2;
    char *end=NULL;unsigned long uid=strtoul(argv[1],&end,10);
    if(!uid || !end || *end || uid>65535)return 2;
    unsigned long gid=strtoul(argv[2],&end,10);
    if(!gid || !end || *end || gid>65535 || getuid()!=uid || geteuid()!=uid ||
        getgid()!=gid || prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return 2;
    char context[200]={0};FILE *label=fopen("/proc/self/attr/current","r");
    if(!label || !fgets(context,sizeof(context),label))return 2;
    fclose(label);
    if(!strstr(context,":camera_access_t:"))return 2;
    int fd=open("/run/credentials/aos-camera-ingress.service/camera-private-key",O_RDONLY|O_CLOEXEC);
    int result=errno;
    int denied=fd<0 && (result==EACCES || result==EPERM || result==ENOENT);
    if(fd>=0)close(fd);
    printf("{\"coreCredentialDenied\":%s,\"nonroot\":true,\"coreDomainVerified\":true,\"errno\":%d}\n",denied?"true":"false",fd<0?result:0);
    return denied?0:3;
}
