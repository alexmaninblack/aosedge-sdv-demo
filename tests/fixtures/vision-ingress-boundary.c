/* SPDX-FileCopyrightText: 2026 maninblack
 * SPDX-License-Identifier: MIT
 * Ephemeral acceptance probe: no credentials, listener or successful traffic.
 */
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <unistd.h>
static int fail(const char *stage) {
    printf("{\"fixtureError\":\"%s\",\"errno\":%d,\"uid\":%u,\"gid\":%u}\n",stage,errno,(unsigned)getuid(),(unsigned)getgid());return 2;
}

int main(int argc,char **argv) {
    if(argc!=3 && argc!=4)return fail("ARGUMENT_COUNT");
    int identity_only=argc==4;
    if(identity_only && strcmp(argv[3],"--identity-only"))return fail("ARGUMENT_VALUE");
    unsigned long uid=strtoul(argv[1],NULL,10),gid=strtoul(argv[2],NULL,10);
    if(!uid||!gid||getuid()!=uid||geteuid()!=uid||getgid()!=gid||getegid()!=gid)return fail("PROCESS_IDENTITY");
    if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return fail("NO_NEW_PRIVILEGES");
    char context[200]={0};FILE *file=fopen("/proc/self/attr/current","r");
    if(!file)return fail("CONTEXT_OPEN");
    if(!fgets(context,sizeof(context),file))return fail("CONTEXT_READ");
    fclose(file);if(!strstr(context,":camera_ingress_t:"))return fail("CONTEXT_DOMAIN");
    if(identity_only){puts("{\"fixtureIdentityVerified\":true,\"ingressDomainVerified\":true}");return 0;}
    int fd=socket(AF_INET,SOCK_STREAM,0);if(fd<0)return fail("BIND_SOCKET_CREATE");
    struct sockaddr_in address={.sin_family=AF_INET,.sin_port=0,.sin_addr.s_addr=INADDR_ANY};
    int code=bind(fd,(struct sockaddr*)&address,sizeof(address)),failure=errno;close(fd);
    int bind_denied=code<0&&(failure==EACCES||failure==EPERM);
    fd=socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK,0);if(fd<0)return fail("CONNECT_SOCKET_CREATE");
    address.sin_port=htons(6443);if(inet_pton(AF_INET,"203.0.113.1",&address.sin_addr)!=1)return 2;
    code=connect(fd,(struct sockaddr*)&address,sizeof(address));failure=errno;
    struct pollfd poller={.fd=fd,.events=POLLOUT};
    int drop_denied=code<0&&(failure==EACCES||failure==EPERM||
        (failure==EINPROGRESS&&poll(&poller,1,250)==0));close(fd);
    printf("{\"ingressBoundary\":true,\"nonrootDomainVerified\":true,\"bindDenied\":%s,\"outsidePeerDenied\":%s}\n",
        bind_denied?"true":"false",drop_denied?"true":"false");
    return bind_denied&&drop_denied?0:3;
}
