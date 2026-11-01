/* SPDX-FileCopyrightText: 2026 maninblack
 * SPDX-License-Identifier: MIT */
#define main native_probe_entry
#include "vision-camera-probe.c"
#undef main
#include <assert.h>

static int sample(const char *header,const char *body) {
    int sockets[2];assert(socketpair(AF_UNIX,SOCK_STREAM,0,sockets)==0);
    assert(send(sockets[0],body,6,0)==6);
    int result=verified_pair(sockets[1],header);
    close(sockets[0]);close(sockets[1]);return result;
}
int main(void) {
    const char *sha="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad";
    char header[1024];
    snprintf(header,sizeof(header),"{\"frames\":[{\"frame\":10,\"simulationTimeNs\":100000000,\"payloadBytes\":3,\"sha256\":\"%s\"},{\"frame\":12,\"simulationTimeNs\":200000000,\"payloadBytes\":3,\"sha256\":\"%s\"}]}",sha,sha);
    assert(sample(header,"abcabc"));assert(!sample(header,"abcabd"));
    snprintf(header,sizeof(header),"{\"frames\":[{\"frame\":10,\"simulationTimeNs\":100000000,\"payloadBytes\":3,\"sha256\":\"%s\"},{\"frame\":12,\"simulationTimeNs\":250000000,\"payloadBytes\":3,\"sha256\":\"%s\"}]}",sha,sha);
    assert(!sample(header,"abcabc"));assert(!sample("{\"frames\":[]}","abcabc"));
    puts("NATIVE_CAMERA_PROBE_PARSER_PASS");return 0;
}
