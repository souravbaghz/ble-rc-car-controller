# ble-rc-car-controller

A realtime keyboard controller for the `YC_CAR_DEMO` BLE toy car, talking
directly to it over Bluetooth Low Energy — no companion app required.

## Background

This car ships with unconfigured demo firmware (it advertises as
`YC_CAR_DEMO` and exposes TI's stock `SimpleBLEPeripheral` GATT profile),
so its actual companion app (Wonder Toys / `LCW_RCcar`) never recognizes
it — the app filters for a different device name it'll never see. The
drive-command protocol here was reverse-engineered directly from that
app's APK (a uni-app bundle; the BLE logic lives in plain JS in
`app-service.js`) and confirmed on the physical car.

### Protocol summary

- GATT service `0000fff0`
  - `0000fff1` — notify (status, unused so far)
  - `0000fff2` — write (drive commands)
- 10-byte command frame: `aa000200000000 <n> <speed> <flag>`
  - `n` — bit-packed state byte: bit0=forward, bit1=backward,
    bit2=steer-left, bit3=steer-right (bits confirmed empirically on-device)
  - `speed` — throttle byte, 0–100; confirmed to have **no effect** on this
    unit (its motor driver is on/off only, no PWM), always sent as `0x64`
  - `flag` — vehicle-family tag (`0x01` for this model)

## Product / app links

- Vendor site: [wondertoys.in](https://wondertoys.in)
- App download page: [wondertoys.in/app-download](https://wondertoys.in/app-download)
- Companion app: **LCW_RCcar** (published by Shenzhen LCW Microelectronics)
  - Android APK (direct download, outside Play Store): [wonder-toys-remote.apk](https://wondertoys.in/uploads/app/wonder-toys-remote.apk)
  - iOS: [LCW_RCcar on the App Store](https://apps.apple.com/us/app/lcw-rccar/id6745876302)
- Per the vendor's own app-download page, the app expects the car to appear
  in Bluetooth settings as **`HY_2504`** — the unit this project targets
  shipped instead advertising as `YC_CAR_DEMO` (unconfigured demo firmware),
  which is why the app never finds it and why this project exists.

## Requirements

- Linux with BlueZ (or macOS; Bluetooth adapter with BLE support)
- Python 3.8+

## Setup

```bash
git clone https://github.com/souravbaghz/ble-rc-car-controller.git
cd ble-rc-car-controller
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

Find your car's BLE MAC address (e.g. with a BLE scanner app, or
`bleak`'s own scanner), then run:

```bash
python3 car_rc.py --addr AA:BB:CC:DD:EE:FF
```

If you don't pass `--addr`, it defaults to the MAC address baked into the
script (`D6:C5:29:60:85:FC` — the specific car this was built for; change
`DEFAULT_ADDR` in `car_rc.py` or always pass `--addr` for a different unit).

### Controls

| Key | Action |
|---|---|
| `w` / `s` | forward / backward |
| `a` / `d` | steer left / right (in place) |
| `q` / `e` | forward-left / forward-right |
| `z` / `c` | backward-left / backward-right |
| `space` | stop |
| `x` or `Ctrl+C` | quit |

Hold a key down to keep moving — the script leans on terminal key-repeat
plus a short release timeout (~0.2s) to approximate "hold to drive"; a
single tap only nudges the car briefly.

Run it in a real terminal with a live keyboard — it needs raw stdin input,
so it won't work piped or in a non-interactive shell.
