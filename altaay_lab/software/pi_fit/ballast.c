/* Lock a block of anonymous pages, then wait.
 * The size is the cited Bookworm Lite "used" figure, passed in bytes.
 * This is a stand-in for that OS footprint, not a boot of Raspberry Pi OS.
 */
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(int argc, char **argv) {
    long long bytes;
    unsigned char *block;
    size_t i;
    if (argc != 2) {
        fprintf(stderr, "usage: ballast BYTES\n");
        return 2;
    }
    bytes = atoll(argv[1]);
    if (bytes < 4096) {
        fprintf(stderr, "size too small\n");
        return 2;
    }
    block = mmap(NULL, (size_t)bytes, PROT_READ | PROT_WRITE,
                 MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (block == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    for (i = 0; i < (size_t)bytes; i += 4096) {
        block[i] = 1;
    }
    if (mlock(block, (size_t)bytes) != 0) {
        perror("mlock");
        return 1;
    }
    printf("locked %lld\n", bytes);
    fflush(stdout);
    for (;;) {
        pause();
    }
    return 0;
}
