# M17 CLI Softmodem for FT-817 / FT-818

A lightweight command-line framework for operating **M17** with **Yaesu
FT-817 / FT-818** transceivers under **Windows 11**, using the official
**M17-tools** project as the modem engine.

## Background

The original goal was to use the graphical application included with
M17-tools. Although the underlying **modulator** (`m17-mod`) and
**demodulator** (`m17-demod`) worked reliably, I could not achieve
stable on-air operation with the GUI.

This project therefore wraps the official command-line tools in a simple
transceiver framework, providing reliable RX/TX switching, PTT control
and audio management for the FT-817/FT-818.

The project does **not** replace M17-tools. It builds on top of it.

## Tested Configuration

-   Windows 11
-   Yaesu FT-817 (also intended for FT-818)
-   DigiRig Mobile
-   Official M17-tools
-   SoX
-   Python 3.13
-   RTL-SDR (recommended for initial TX deviation calibration)

## Features

-   Native CLI-based M17 operation
-   RX/TX switching from a single console application
-   External RTS-based PTT control
-   Automatic Windows audio level restoration from YAML
-   YAML-based configuration
-   Simple deployment without the original GUI

## Installation

### 1. Install M17-tools

Clone and build the official project:

https://github.com/M17-Project/m17-tools

Make sure `m17-mod.exe` and `m17-demod.exe` are available.

### 2. Install SoX

Install SoX and verify that it supports the Windows `waveaudio` driver.

### 3. Install Python packages

``` text
pip install pyserial pycaw comtypes pyyaml
```

## DigiRig Requirements

The DigiRig Mobile **must** use its built-in **20 dB attenuator**.

Verify with an ohmmeter that approximately **100 kΩ** is present across
the ATT jumper pads.

If your interface does not contain the resistor, add an external **100
kΩ series resistor** in the **RIG AF OUT** path.

Use the **9600 bps DATA cable** connected to the FT-817 DATA connector.

The 1200 bps cable is **not suitable**.

## Radio Configuration

Verify at least:

-   PKT mode: 9600
-   MENU 39 (PKT MIC): calibrated value (for the reference station this
    is **50**)

The helper application reminds you to verify the radio setting because
it cannot be changed from software.

## TX Deviation Calibration

Correct 4FSK deviation is critical.

A recommended workflow is:

1.  Connect an RTL-SDR.
2.  Start SDR++.
3.  Enable the M17 demodulator/plugin.
4.  Transmit a test signal.
5.  Adjust Windows microphone gain and DigiRig playback level until the
    constellation/4FSK monitor matches the expected reference.

After calibration, store the Windows audio levels in `m17_config.yaml`.

The helper utility restores these levels automatically before the
transceiver starts.

## Configuration

All user settings are stored in:

``` text
m17_config.yaml
```

The configuration contains:

-   Callsign
-   Destination
-   COM port for PTT
-   Windows audio devices
-   Audio levels
-   WaveAudio routing
-   Paths to required applications:
    -   M17-tools
    -   SoX
    -   FFplay (optional)

The application can therefore be started from any directory.

## Transceiver Controls

When running `m17_trx.py`:

  Key     Function
  ------- ------------------
  Space   Toggle RX / TX
  Esc     Exit application

Operation sequence:

``` text
Program start
    ↓
Restore Windows audio levels
    ↓
Reminder: Verify FT-817 MENU 39
    ↓
Receive mode

SPACE
    ↓

PTT ON
Transmit

SPACE
    ↓

PTT OFF
Receive

ESC
    ↓

Stop RX/TX
Release PTT
Exit
```

## Repository Structure

``` text
src/
    m17_trx.py
    m17_set_audio_levels.py
    m17_config.yaml
```

## Acknowledgements

This project is built on the excellent **M17-tools** project.

All modulation and demodulation functions are provided by the official
M17 implementation.

This repository only adds a lightweight operating framework around those
tools.

## Known Limitations

Current validation status:

-   Tested only on **Windows 11**.
-   Validated with **Yaesu FT-817** (expected to work with FT-818, but
    not yet fully verified).
-   Tested with **DigiRig Mobile** using the **9600 bps DATA** cable.
- 	**Important:** The FT-817 9600 bps DATA OUT produces an **inverted
	discriminator signal**. The official `m17-demod` expects the opposite
	polarity, therefore the received baseband must be inverted (e.g. using
	`SoX vol -1`) before demodulation. This was experimentally verified
	during over-the-air testing and appears to be largely undocumented in
	existing FT-817/M17 integration guides.
-   The **20 dB DigiRig attenuator** (or equivalent external 100 kΩ
    attenuation) is required for reliable RX operation.
-   Windows audio device names may differ between systems and must be
    updated in `m17_config.yaml`.
-   The application cannot read or configure FT-817 menu settings;
    **MENU 39 (PKT MIC)** must be checked manually before operation.
-   Initial transmit deviation should be calibrated with an independent
    receiver (for example, an RTL-SDR with SDR++ and the M17 monitoring
    plugin).
-   The project currently focuses on **voice operation** using the
    official `m17-mod` and `m17-demod` applications. Data operation and
    networking features are outside the current scope.
-   This framework relies on the external M17-tools executables and does
    not replace or modify the modem implementation itself.

## License

This project is licensed under the **GNU Affero General Public License v3.0
(AGPL-3.0)**, the same license used by the M17-tools project.

See the LICENSE file for details.

This project is an independent command-line framework built around the
official M17-tools applications and is not affiliated with the M17 Project.

This project was developed by the author with iterative assistance from
AI-based coding tools.