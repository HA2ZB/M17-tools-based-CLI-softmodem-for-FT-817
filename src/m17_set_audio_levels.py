import yaml
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

PROFILE = "m17_config.yaml"

def get_endpoint_volume(dev_id):
    enumerator = AudioUtilities.GetDeviceEnumerator()
    endpoint = enumerator.GetDevice(dev_id)
    interface = endpoint.Activate(
        IAudioEndpointVolume._iid_,
        CLSCTX_ALL,
        None
    )
    return interface.QueryInterface(IAudioEndpointVolume)

with open(PROFILE, "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

devices = AudioUtilities.GetAllDevices()

print("M17 audio level restore")
print("=" * 50)

for key, item in cfg["audio"].items():

    if "device_contains" not in item:
        continue

    wanted = item["device_contains"]
    target = float(item["level_percent"])
    mute = bool(item.get("mute", False))

    found = None
    for dev in devices:
        name = getattr(dev, "FriendlyName", "")
        state = str(getattr(dev, "state", ""))
        if "Active" in state and wanted in name:
            found = dev
            break

    if not found:
        print(f"{key}: NOT FOUND / not active ({wanted})")
        continue

    vol = get_endpoint_volume(found.id)
    old = vol.GetMasterVolumeLevelScalar() * 100

    vol.SetMasterVolumeLevelScalar(target / 100.0, None)
    vol.SetMute(1 if mute else 0, None)

    new = vol.GetMasterVolumeLevelScalar() * 100

    print(f"{key}: {found.FriendlyName}")
    print(f"  {old:.1f}% -> {new:.1f}%")
    print()
    
radio = cfg.get("radio", {})
model = radio.get("model", "Radio")
menu = radio.get("pkt_mic_menu", "?")
value = radio.get("pkt_mic_value", "?")

print("=" * 50)
print(f"WARNING: check: {model} MENU {menu} PKT MIC = {value}")
