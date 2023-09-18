// Adopted from:
// https://learn.microsoft.com/en-us/azure/ai-services/speech-service/how-to-select-audio-input-devices#audio-device-ids-on-macos
// compile with: clang -framework Foundation -framework CoreAudio
// list_audio_devices.m -o build/list_audio_devices
#import <CoreAudio/CoreAudio.h>
#import <Foundation/Foundation.h>

CFArrayRef CreateDeviceArray(bool input_devices) {
  AudioObjectPropertyAddress propertyAddress = {
      kAudioHardwarePropertyDevices, kAudioObjectPropertyScopeGlobal,
      kAudioObjectPropertyElementMain};

  UInt32 dataSize = 0;
  OSStatus status = AudioObjectGetPropertyDataSize(
      kAudioObjectSystemObject, &propertyAddress, 0, NULL, &dataSize);
  if (kAudioHardwareNoError != status) {
    fprintf(stderr,
            "AudioObjectGetPropertyDataSize (kAudioHardwarePropertyDevices) "
            "failed: %i\n",
            status);
    return NULL;
  }

  UInt32 deviceCount = (uint32)(dataSize / sizeof(AudioDeviceID));

  AudioDeviceID *audioDevices = (AudioDeviceID *)(malloc(dataSize));
  if (NULL == audioDevices) {
    fputs("Unable to allocate memory", stderr);
    return NULL;
  }

  status =
      AudioObjectGetPropertyData(kAudioObjectSystemObject, &propertyAddress, 0,
                                 NULL, &dataSize, audioDevices);
  if (kAudioHardwareNoError != status) {
    fprintf(stderr,
            "AudioObjectGetPropertyData (kAudioHardwarePropertyDevices) "
            "failed: %i\n",
            status);
    free(audioDevices);
    audioDevices = NULL;
    return NULL;
  }

  CFMutableArrayRef inputDeviceArray = CFArrayCreateMutable(
      kCFAllocatorDefault, deviceCount, &kCFTypeArrayCallBacks);
  if (NULL == inputDeviceArray) {
    fputs("CFArrayCreateMutable failed", stderr);
    free(audioDevices);
    audioDevices = NULL;
    return NULL;
  }

  // Iterate through all the devices and determine which are input-capable
  if (input_devices) {
    propertyAddress.mScope = kAudioDevicePropertyScopeInput;
  } else {
    propertyAddress.mScope = kAudioDevicePropertyScopeOutput;
  }
  for (UInt32 i = 0; i < deviceCount; ++i) {
    // Query device UID
    CFStringRef deviceUID = NULL;
    dataSize = sizeof(deviceUID);
    propertyAddress.mSelector = kAudioDevicePropertyDeviceUID;
    status = AudioObjectGetPropertyData(audioDevices[i], &propertyAddress, 0,
                                        NULL, &dataSize, &deviceUID);
    if (kAudioHardwareNoError != status) {
      fprintf(stderr,
              "AudioObjectGetPropertyData (kAudioDevicePropertyDeviceUID) "
              "failed: %i\n",
              status);
      continue;
    }

    // Query device name
    CFStringRef deviceName = NULL;
    dataSize = sizeof(deviceName);
    propertyAddress.mSelector = kAudioDevicePropertyDeviceNameCFString;
    status = AudioObjectGetPropertyData(audioDevices[i], &propertyAddress, 0,
                                        NULL, &dataSize, &deviceName);
    if (kAudioHardwareNoError != status) {
      fprintf(stderr,
              "AudioObjectGetPropertyData "
              "(kAudioDevicePropertyDeviceNameCFString) failed: %i\n",
              status);
      continue;
    }

    // Determine if the device is an input device (it is an input device if it
    // has input channels)
    dataSize = 0;
    propertyAddress.mSelector = kAudioDevicePropertyStreamConfiguration;
    status = AudioObjectGetPropertyDataSize(audioDevices[i], &propertyAddress,
                                            0, NULL, &dataSize);
    if (kAudioHardwareNoError != status) {
      fprintf(stderr,
              "AudioObjectGetPropertyDataSize "
              "(kAudioDevicePropertyStreamConfiguration) failed: %i\n",
              status);
      continue;
    }

    AudioBufferList *bufferList = (AudioBufferList *)(malloc(dataSize));
    if (NULL == bufferList) {
      fputs("Unable to allocate memory", stderr);
      break;
    }

    status = AudioObjectGetPropertyData(audioDevices[i], &propertyAddress, 0,
                                        NULL, &dataSize, bufferList);
    if (kAudioHardwareNoError != status || 0 == bufferList->mNumberBuffers) {
      if (kAudioHardwareNoError != status)
        fprintf(stderr,
                "AudioObjectGetPropertyData "
                "(kAudioDevicePropertyStreamConfiguration) failed: %i\n",
                status);
      free(bufferList);
      bufferList = NULL;
      continue;
    }

    free(bufferList);
    bufferList = NULL;

    // Add a dictionary for this device to the array of input devices
    CFStringRef keys[] = {CFSTR("deviceUID"), CFSTR("deviceName")};
    CFStringRef values[] = {deviceUID, deviceName};

    CFDictionaryRef deviceDictionary = CFDictionaryCreate(
        kCFAllocatorDefault, (const void **)(keys), (const void **)(values), 2,
        &kCFTypeDictionaryKeyCallBacks, &kCFTypeDictionaryValueCallBacks);

    CFArrayAppendValue(inputDeviceArray, deviceDictionary);

    CFRelease(deviceDictionary);
    deviceDictionary = NULL;
  }

  free(audioDevices);
  audioDevices = NULL;

  // Return a non-mutable copy of the array
  CFArrayRef immutableInputDeviceArray =
      CFArrayCreateCopy(kCFAllocatorDefault, inputDeviceArray);
  CFRelease(inputDeviceArray);
  inputDeviceArray = NULL;

  return immutableInputDeviceArray;
}

// create main function and print the list of audio devices
int main(int argc, const char *argv[]) {
  @autoreleasepool {
    CFArrayRef inputDeviceArray = CreateDeviceArray(true);
    CFArrayRef outputDeviceArray = CreateDeviceArray(false);

    if (NULL == inputDeviceArray || NULL == outputDeviceArray) {
      fputs("Unable to create device array", stderr);
      return -1;
    }

    CFIndex inputDeviceCount = CFArrayGetCount(inputDeviceArray);
    CFIndex outputDeviceCount = CFArrayGetCount(outputDeviceArray);

    printf("Input devices:\n");
    for (CFIndex i = 0; i < inputDeviceCount; ++i) {
      CFDictionaryRef deviceDictionary =
          (CFDictionaryRef)(CFArrayGetValueAtIndex(inputDeviceArray, i));
      CFStringRef deviceUID = (CFStringRef)(CFDictionaryGetValue(
          deviceDictionary, CFSTR("deviceUID")));
      CFStringRef deviceName = (CFStringRef)(CFDictionaryGetValue(
          deviceDictionary, CFSTR("deviceName")));
      printf("    %3i: %s (%s)\n", (int)(i + 1),
             CFStringGetCStringPtr(deviceName, kCFStringEncodingUTF8),
             CFStringGetCStringPtr(deviceUID, kCFStringEncodingUTF8));
    }

    printf("Output devices:\n");
    for (CFIndex i = 0; i < outputDeviceCount; ++i) {
      CFDictionaryRef deviceDictionary =
          (CFDictionaryRef)(CFArrayGetValueAtIndex(outputDeviceArray, i));
      CFStringRef deviceUID = (CFStringRef)(CFDictionaryGetValue(
          deviceDictionary, CFSTR("deviceUID")));
      CFStringRef deviceName = (CFStringRef)(CFDictionaryGetValue(
          deviceDictionary, CFSTR("deviceName")));
      printf("    %3i: %s (%s)\n", (int)(i + 1),
             CFStringGetCStringPtr(deviceName, kCFStringEncodingUTF8),
             CFStringGetCStringPtr(deviceUID, kCFStringEncodingUTF8));
    }

    CFRelease(inputDeviceArray);
    inputDeviceArray = NULL;
    CFRelease(outputDeviceArray);
    outputDeviceArray = NULL;
  }

  return 0;
}
