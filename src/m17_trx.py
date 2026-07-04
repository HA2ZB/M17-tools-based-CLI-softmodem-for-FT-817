import os
import sys
import time
import msvcrt
import subprocess
import yaml
import serial

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "m17_config.yaml")


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_endpoint_volume(dev_id):
    enumerator = AudioUtilities.GetDeviceEnumerator()
    endpoint = enumerator.GetDevice(dev_id)
    interface = endpoint.Activate(
        IAudioEndpointVolume._iid_,
        CLSCTX_ALL,
        None
    )
    return interface.QueryInterface(IAudioEndpointVolume)


def restore_audio_levels(cfg):
    devices = AudioUtilities.GetAllDevices()
    items = [
        ("TX microphone", cfg["audio"]["tx_microphone"]),
        ("TX output", cfg["audio"]["tx_output"]),
        ("RX input", cfg["audio"]["rx_input"]),
    ]

    print("M17 station check")
    print("=" * 50)

    for label, item in items:
        wanted = item["device_contains"]
        target = float(item["level_percent"])

        found = None
        for dev in devices:
            name = getattr(dev, "FriendlyName", "")
            state = str(getattr(dev, "state", ""))
            if "Active" in state and wanted in name:
                found = dev
                break

        if not found:
            print(f"[WARN] {label}: not found / not active: {wanted}")
            continue

        vol = get_endpoint_volume(found.id)
        old = vol.GetMasterVolumeLevelScalar() * 100
        vol.SetMasterVolumeLevelScalar(target / 100.0, None)
        vol.SetMute(0, None)
        new = vol.GetMasterVolumeLevelScalar() * 100

        print(f"[OK] {label}: {found.FriendlyName}")
        print(f"     {old:.1f}% -> {new:.1f}%")

    radio = cfg["radio"]
    print()
    print(
        f"[CHECK] {radio['model']} MENU {radio['pkt_mic_menu']} "
        f"PKT MIC = {radio['pkt_mic_value']}"
    )
    print("=" * 50)
    print()


class M17TRX:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mode = "RX"
        self.proc = None
        self.ptt = None

        self.call = cfg["callsign"]
        self.dest = cfg["destination"]
        self.ptt_com = cfg["ptt"]["com_port"]

        self.rx_audio = cfg["audio"]["rx_input"]["device_contains"]
        self.rx_out = cfg["audio"]["rx_output"]["waveaudio_device"]
        self.tx_audio = cfg["audio"]["tx_microphone"]["device_contains"]
        self.tx_out = cfg["audio"]["tx_output"]["waveaudio_device"]
        
        self.m17_tools = cfg["paths"]["m17_tools"]
        self.sox = cfg["paths"]["sox"]
        self.ffplay = cfg["paths"].get("ffplay", "ffplay.exe")

        self.m17_mod = os.path.join(self.m17_tools, "m17-mod.exe")
        self.m17_demod = os.path.join(self.m17_tools, "m17-demod.exe")

    def rx_cmd(self):
        return (
            f'"{self.sox}" -q -t waveaudio "{self.rx_audio}" '
            f'-r 48000 -e signed-integer -b 16 -c 1 -t raw - vol -1 '
            f'| "{self.m17_demod}" -l '
            f'| "{self.sox}" -q -t raw -r 8000 -e signed-integer -b 16 -c 1 - '
            f'-t waveaudio {self.rx_out}'
        )
    
    def tx_cmd(self):
        return (
            f'"{self.sox}" -q -t waveaudio "{self.tx_audio}" '
            f'-r 8000 -e signed-integer -b 16 -c 1 -t raw - '
            f'| "{self.m17_mod}" -S {self.call} -i -C 0 '
            f'| "{self.sox}" -q -t raw -r 48000 -e signed-integer -b 16 -c 1 - '
            f'-t waveaudio {self.tx_out}'
        )

    def screen(self):
        os.system("cls")
        print("========================================")
        print("          M17 CLI TRANSCEIVER")
        print("========================================")
        print(f"Call : {self.call}")
        print(f"Dest : {self.dest}")
        print(f"Mode : {self.mode}")
        print(f"PTT  : {'ON' if self.ptt else 'OFF'}")
        print("----------------------------------------")
        print("SPACE  RX/TX switch")
        print("ESC    Exit")
        print("========================================")
        print()

    def start_process(self, cmd):
        return subprocess.Popen(
            cmd,
            shell=True,
            stdin=subprocess.DEVNULL,
        )

    def stop_process(self):
        if self.proc and self.proc.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(self.proc.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.3)
        self.proc = None

    def ptt_on(self):
        if self.ptt:
            return
        self.ptt = serial.Serial(self.ptt_com, 9600, rtscts=False)
        self.ptt.rts = True
        time.sleep(0.15)

    def ptt_off(self):
        if self.ptt:
            try:
                self.ptt.rts = False
                self.ptt.close()
            except Exception:
                pass
        self.ptt = None
        time.sleep(0.15)

    def start_rx(self):
        self.stop_process()
        self.ptt_off()
        self.mode = "RX"
        self.screen()
        self.proc = self.start_process(self.rx_cmd())

    def start_tx(self):
        self.stop_process()
        self.mode = "TX"
        self.screen()
        self.ptt_on()
        self.screen()
        self.proc = self.start_process(self.tx_cmd())

    def toggle(self):
        if self.mode == "RX":
            self.start_tx()
        else:
            self.start_rx()

    def shutdown(self):
        self.stop_process()
        self.ptt_off()
        print("Stopped.")
        sys.exit(0)

    def run(self):
        self.start_rx()

        while True:
            if self.proc and self.proc.poll() is not None:
                self.start_rx()

            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b" ":
                    self.toggle()

                elif key == b"\x1b":
                    self.shutdown()

            time.sleep(0.05)


if __name__ == "__main__":
    cfg = load_config()
    restore_audio_levels(cfg)

    trx = M17TRX(cfg)

    try:
        trx.run()
    except KeyboardInterrupt:
        trx.shutdown()
    except Exception as e:
        try:
            trx.shutdown()
        finally:
            print(e)