#!/usr/bin/env python3
"""
car_rc.py — Realtime keyboard controller for the YC_CAR_DEMO BLE toy car.

Controls:
  w/s       forward / backward
  a/d       steer left / right (in place)
  q/e       forward-left / forward-right
  z/c       backward-left / backward-right
  space     stop
  x or Ctrl+C   quit

Usage:
  python3 car_rc.py [--addr MAC]

Author: @souravbaghz (https://github.com/souravbaghz)
"""
import argparse
import asyncio
import sys
import termios
import time
import tty

from bleak import BleakClient

DEFAULT_ADDR = "D6:C5:29:60:85:FC"
FFF2 = "0000fff2-0000-1000-8000-00805f9b34fb"
HEADER = "aa000200000000"

BANNER = r"""
================================================
        D E M O L I T I O N   D E R B Y
              rogue BLE remote
                  @souravbaghz
================================================
"""

RELEASE_TIMEOUT = 0.2   # no repeat seen for this long -> treat key as released
SEND_INTERVAL = 0.06    # how often we refresh the command while a key is held

# key -> (A=forward, B=backward, C=steer-left, D=steer-right)
DIR_KEYS = {
    "w": (1, 0, 0, 0),
    "s": (0, 1, 0, 0),
    "a": (0, 0, 1, 0),
    "d": (0, 0, 0, 1),
    "q": (1, 0, 1, 0),
    "e": (1, 0, 0, 1),
    "z": (0, 1, 1, 0),
    "c": (0, 1, 0, 1),
}


def n_byte(A, B, C, D, play="10"):
    bits = f"0{play}0{D}{C}{B}{A}"
    return int(bits, 2)


SPEED = 0x64  # full speed - this car's motor driver has no PWM, so this is fixed


def build_frame(A, B, C, D):
    n = n_byte(A, B, C, D)
    return bytes.fromhex(HEADER) + bytes([n, SPEED, 0x01])


class KeyState:
    def __init__(self):
        self.active = None       # current direction key char
        self.last_seen = 0.0
        self.quit = False

    def on_key(self, ch):
        now = time.monotonic()
        if ch in DIR_KEYS:
            self.active = ch
            self.last_seen = now
        elif ch == " ":
            self.active = None
        elif ch in ("x", "\x03"):
            self.quit = True

    def current_bits(self):
        now = time.monotonic()
        if self.active and (now - self.last_seen) > RELEASE_TIMEOUT:
            self.active = None
        A, B, C, D = DIR_KEYS.get(self.active, (0, 0, 0, 0))
        return A, B, C, D


async def sender_loop(client, state: KeyState):
    while not state.quit:
        A, B, C, D = state.current_bits()
        frame = build_frame(A, B, C, D)
        try:
            await client.write_gatt_char(FFF2, frame, response=True)
        except Exception as e:
            sys.stdout.write(f"\r[write error: {e}]                    \n")
        label = state.active or "idle"
        sys.stdout.write(f"\r[{label:6s}] frame={frame.hex()}   ")
        sys.stdout.flush()
        await asyncio.sleep(SEND_INTERVAL)


async def run(addr):
    loop = asyncio.get_event_loop()
    state = KeyState()

    def on_stdin():
        ch = sys.stdin.read(1)
        if ch:
            state.on_key(ch)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    loop.add_reader(fd, on_stdin)

    print(BANNER)
    print(f"[*] Connecting to {addr} ...")
    try:
        async with BleakClient(addr, timeout=15.0) as client:
            print("[+] Connected. w/a/s/d/q/e/z/c to drive, space=stop, "
                  "x=quit.\n")
            await sender_loop(client, state)
    finally:
        loop.remove_reader(fd)
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\n[*] Disconnected.")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--addr", default=DEFAULT_ADDR, help="Car's BLE MAC address")
    args = p.parse_args()
    try:
        asyncio.run(run(args.addr))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
