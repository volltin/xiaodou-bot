# -*- coding: utf-8 -*-
# Adapted from: https://stackoverflow.com/questions/57099246/set-output-device-for-pygame-mixer

try:
    import pygame
    import pygame._sdl2.audio as sdl2_audio
except ImportError:
    raise ImportError("pygame module is required for this script")


def get_devices(capture_devices: bool):
    init_by_me = not pygame.mixer.get_init()
    if init_by_me:
        pygame.mixer.init()
    devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
    if init_by_me:
        pygame.mixer.quit()
    return devices


if __name__ == "__main__":
    print("Audio devices:")
    print("===== Input =====")
    for idx, device in enumerate(get_devices(True)):
        print(f"{idx}: {device}")
    print("===== Output =====")
    for idx, device in enumerate(get_devices(False)):
        print(f"{idx}: {device}")
