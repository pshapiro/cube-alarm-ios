# Cube Alarm iOS App

This directory contains a standalone SwiftUI alarm clock that schedules local notifications. No backend server or Raspberry Pi is required.

To run the app:

1. Open `CubeAlarmApp.swift` in Xcode 15 or later.
2. Build and run the app in the iOS Simulator or on a device.
3. Grant notification permission when prompted.

> SwiftUI and UserNotifications are only available on Apple platforms. The Linux container used for development cannot build this target, so no automated tests are provided.
