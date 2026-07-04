from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

enumerator = AudioUtilities.GetDeviceEnumerator()
devices = AudioUtilities.GetAllDevices()

for dev in devices:
    name = getattr(dev, "FriendlyName", "?")
    state = str(getattr(dev, "state", "?"))
    dev_id = getattr(dev, "id", "?")

    if "Active" not in state:
        continue

    print("=" * 60)
    print(f"Name  : {name}")
    print(f"State : {state}")
    print(f"ID    : {dev_id}")

    try:
        endpoint = enumerator.GetDevice(dev_id)
        interface = endpoint.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = interface.QueryInterface(IAudioEndpointVolume)

        level = volume.GetMasterVolumeLevelScalar() * 100
        mute = volume.GetMute()

        print(f"Level : {level:.1f}%")
        print(f"Muted : {bool(mute)}")

    except Exception as e:
        print(f"Volume read failed: {e}")

    print()