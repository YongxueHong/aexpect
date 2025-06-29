# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.

"""Some shared functions"""

import os
import fcntl
import termios
import time

BASE_DIR = os.environ.get("TMPDIR", "/tmp")


def get_lock_fd(filename, timeout=-1):
    """Lock a file"""
    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8"):
            pass

    lock_fd = os.open(filename, os.O_RDWR)
    lock_flags = fcntl.LOCK_EX
    if timeout > 0:
        lock_flags |= fcntl.LOCK_NB
    end_time = time.monotonic() + timeout if timeout > 0 else -1
    while True:
        try:
            fcntl.flock(lock_fd, lock_flags)
            break
        except IOError:
            if time.monotonic() > end_time:
                os.close(lock_fd)
                raise
    return lock_fd


def unlock_fd(lock_fd):
    """Unlock a file"""
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)


def is_file_locked(filename):
    """Check whether file is currently locked"""
    try:
        lock_fd = os.open(filename, os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        os.close(lock_fd)
        return True
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    return False


def wait_for_lock(filename, timeout=-1):
    """
    Wait until lock can be acquired, then release it

    :return: True on success, False on failure/timeout
    """
    try:
        lock_fd = get_lock_fd(filename, timeout)
    except (IOError, FileNotFoundError):
        return False
    unlock_fd(lock_fd)
    return True


def makeraw(shell_fd):
    """Turn console into 'raw' format"""
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~(
        termios.IGNBRK
        | termios.BRKINT
        | termios.PARMRK
        | termios.ISTRIP
        | termios.INLCR
        | termios.IGNCR
        | termios.ICRNL
        | termios.IXON
    )
    attr[1] &= ~termios.OPOST
    attr[2] &= ~(termios.CSIZE | termios.PARENB)
    attr[2] |= termios.CS8
    attr[3] &= ~(
        termios.ECHO
        | termios.ECHONL
        | termios.ICANON
        | termios.ISIG
        | termios.IEXTEN
    )
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def makestandard(shell_fd, echo):
    """Turn console into 'normal' mode"""
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~termios.INLCR
    attr[0] &= ~termios.ICRNL
    attr[0] &= ~termios.IGNCR
    attr[1] &= ~termios.OPOST
    if echo:
        attr[3] |= termios.ECHO
    else:
        attr[3] &= ~termios.ECHO
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def get_filenames(base_dir):
    """Get paths to files produced by aexpect in it's working dir"""
    files = (
        "shell-pid",
        "status",
        "output",
        "inpipe",
        "ctrlpipe",
        "lock-server-running",
        "lock-client-starting",
        "server-log",
    )
    return [os.path.join(base_dir, s) for s in files]


def get_reader_filename(base_dir, reader):
    """Return path to pipe of the associated reader"""
    return os.path.join(base_dir, f"outpipe-{reader}")
