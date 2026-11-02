/* Test-only LD_PRELOAD shim: lets serial libraries open a pseudo terminal.
 *
 * serialport 4.7.0 (used by rustypot 0.1.0) sets DTR with ioctl(TIOCMBIS) right after open
 * (src/posix/tty.rs, dtr_on_open defaults to Some(true) in src/lib.rs) and fails with ENOTTY on
 * a pty, which has no modem lines. This shim turns that one failure into success for the four
 * modem-line requests only. Every other ioctl, and every ioctl on a real serial device, goes
 * straight to libc unchanged. Build: gcc -shared -fPIC -O2 -o pty_shim.so pty_shim.c -ldl
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdarg.h>
#include <sys/ioctl.h>
#include <termios.h>

typedef int (*ioctl_fn)(int, unsigned long, ...);

int ioctl(int fd, unsigned long req, ...) {
    static ioctl_fn real_ioctl = 0;
    va_list ap;
    va_start(ap, req);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    if (!real_ioctl) real_ioctl = (ioctl_fn)dlsym(RTLD_NEXT, "ioctl");
    int r = real_ioctl(fd, req, arg);
    if (r == -1 && errno == ENOTTY &&
        (req == TIOCMBIS || req == TIOCMBIC || req == TIOCMSET || req == TIOCMGET)) {
        if (req == TIOCMGET && arg) *(int *)arg = TIOCM_DTR | TIOCM_RTS | TIOCM_CTS | TIOCM_DSR | TIOCM_CD;
        errno = 0;
        return 0;
    }
    return r;
}
