/* SPDX-FileCopyrightText: 2026 maninblack
 * SPDX-License-Identifier: MIT
 * Native-Aos diagnostic consumer, not Perception or a production IPC SDK.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <openssl/sha.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/statvfs.h>
#include <sys/time.h>
#include <sys/un.h>
#include <unistd.h>

static const char *reader="/run/aosedge/platform/camera/camera.sock";

static int exact(int fd, void *buffer, size_t count, int write_mode) {
    unsigned char *p=buffer;
    while(count) {
        ssize_t n=write_mode?send(fd,p,count,MSG_NOSIGNAL):recv(fd,p,count,0);
        if(n<=0)return 0;
        p+=n;count-=(size_t)n;
    }
    return 1;
}

static int connection(const char *path) {
    int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);
    if(fd<0)return -1;
    struct timeval timeout={2,0};
    setsockopt(fd,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));
    setsockopt(fd,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
    struct sockaddr_un address={.sun_family=AF_UNIX};
    if(strlen(path)>=sizeof(address.sun_path)){close(fd);return -1;}
    strcpy(address.sun_path,path);
    if(connect(fd,(struct sockaddr*)&address,sizeof(address))){close(fd);return -1;}
    return fd;
}

static int query(int fd,const char *operation,char header[4097]) {
    char body[100];
    int length=snprintf(body,sizeof(body),"{\"schemaVersion\":1,\"operation\":\"%s\"}",operation);
    uint32_t size=htonl((uint32_t)length);
    if(!exact(fd,&size,4,1)||!exact(fd,body,(size_t)length,1)||!exact(fd,&size,4,0))return 0;
    size=ntohl(size);
    if(size==0||size>4096||!exact(fd,header,size,0))return 0;
    header[size]=0;
    return 1;
}

static int verified_pair(int fd,const char *header) {
    /* The peer is the signed Camera daemon's closed serializer. This fixture
       extracts only its two length/hash fields; no general JSON API is implied. */
    size_t sizes[2];char expected[2][65];unsigned long long frames[2],times[2];
    const char *cursor=strstr(header,"\"frames\":[");
    if(!cursor)return 0;
    for(int i=0;i<2;i++) {
        cursor=strstr(cursor,"\"frame\":");if(!cursor)return 0;
        cursor+=8;char *number_end=NULL;
        frames[i]=strtoull(cursor,&number_end,10);if(number_end==cursor)return 0;
        cursor=strstr(number_end,"\"simulationTimeNs\":");if(!cursor)return 0;
        cursor+=19;times[i]=strtoull(cursor,&number_end,10);if(number_end==cursor)return 0;
        cursor=strstr(cursor,"\"payloadBytes\":");if(!cursor)return 0;
        cursor+=15;char *end=NULL;
        unsigned long size=strtoul(cursor,&end,10);
        if(end==cursor||size==0||size>4194304)return 0;
        sizes[i]=(size_t)size;
        cursor=strstr(end,"\"sha256\":\"");if(!cursor)return 0;
        cursor+=10;
        if(strlen(cursor)<65||cursor[64]!='"')return 0;
        for(int k=0;k<64;k++)if(!((cursor[k]>='0'&&cursor[k]<='9')||(cursor[k]>='a'&&cursor[k]<='f')))return 0;
        memcpy(expected[i],cursor,64);expected[i][64]=0;cursor+=65;
    }
    if(strstr(cursor,"\"payloadBytes\":"))return 0;
    if(frames[1]<=frames[0] || times[1]<times[0] || times[1]-times[0]<80000000 || times[1]-times[0]>120000000)return 0;
    for(int i=0;i<2;i++) {
        unsigned char *body=malloc(sizes[i]),hash[SHA256_DIGEST_LENGTH];char actual[65];
        if(!body)return 0;
        if(!exact(fd,body,sizes[i],0)){free(body);return 0;}
        SHA256(body,sizes[i],hash);free(body);
        for(int k=0;k<SHA256_DIGEST_LENGTH;k++)sprintf(actual+k*2,"%02x",hash[k]);
        if(strcmp(actual,expected[i]))return 0;
    }
    printf("{\"probe\":\"LIVE_PAIR\",\"frames\":[%llu,%llu],\"sha256\":[\"%s\",\"%s\"],\"bytesVerified\":true}\n",
        frames[0],frames[1],expected[0],expected[1]);
    return 1;
}

int main(void) {
    setvbuf(stdout,NULL,_IOLBF,0);
    if(getuid()==0||geteuid()==0){puts("{\"probe\":\"ROOT_IDENTITY_REJECTED\"}");return 2;}
    int oem=connection("/run/aos-camera-access/oem/producer.sock");
    if(oem>=0){close(oem);puts("{\"probe\":\"OEM_SOCKET_VISIBLE\"}");return 3;}
    gid_t groups[128];int group_count=getgroups(128,groups);
    struct statvfs mount;
    printf("{\"probe\":\"IDENTITY\",\"uid\":%lu,\"gid\":%lu,\"groups\":[",(unsigned long)getuid(),(unsigned long)getgid());
    for(int i=0;i<group_count;i++)printf("%s%lu",i?",":"",(unsigned long)groups[i]);
    printf("],\"oemSocketDenied\":true,\"readMountReadonly\":%s}\n",
        statvfs("/run/aosedge/platform/camera",&mount)==0&&(mount.f_flag&ST_RDONLY)?"true":"false");
    for(;;) {
        int fd=connection(reader);
        if(fd<0) {puts("{\"probe\":\"NO_RESOURCE\"}");sleep(1);continue;}
        char header[4097];
        if(!query(fd,"pair",header)) {close(fd);puts("{\"probe\":\"IPC_FAILED\"}");sleep(1);continue;}
        int pair=strstr(header,"\"state\":\"PAIR\"")!=NULL;
        int good=pair?verified_pair(fd,header):1;
        close(fd);
        printf("{\"probe\":\"READ\",\"pair\":%s,\"bytesVerified\":%s}\n",pair?"true":"false",good?"true":"false");
        if(!good)return 4;
        fd=connection(reader);
        if(fd>=0) {
            int denied=!query(fd,"select",header);
            close(fd);
            if(!denied){puts("{\"probe\":\"MUTATION_NOT_DENIED\"}");return 5;}
            puts("{\"probe\":\"READER_MUTATION_DENIED\"}");
        }
        sleep(1);
    }
}
