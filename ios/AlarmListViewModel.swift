import Foundation
import UserNotifications

@MainActor
class AlarmListViewModel: ObservableObject {
    @Published var alarms: [Alarm] = []
    private let storageKey = "alarms"

    init() {
        loadAlarms()
        requestPermissions()
    }

    func addAlarm(at date: Date) {
        let alarm = Alarm(id: UUID(), date: date)
        alarms.append(alarm)
        scheduleNotification(for: alarm)
        saveAlarms()
    }

    func removeAlarms(at offsets: IndexSet) {
        let removed = offsets.map { alarms[$0] }
        alarms.remove(atOffsets: offsets)
        for alarm in removed {
            UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [alarm.id.uuidString])
        }
        saveAlarms()
    }

    private func requestPermissions() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if let error = error {
                print("Notification permission error: \(error)")
            }
            if !granted {
                print("Notification permission not granted")
            }
        }
    }

    private func scheduleNotification(for alarm: Alarm) {
        let content = UNMutableNotificationContent()
        content.title = "Cube Alarm"
        content.body = "Solve the cube to dismiss"
        content.sound = UNNotificationSound.default

        let triggerDate = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: alarm.date)
        let trigger = UNCalendarNotificationTrigger(dateMatching: triggerDate, repeats: false)

        let request = UNNotificationRequest(identifier: alarm.id.uuidString, content: content, trigger: trigger)
        UNUserNotificationCenter.current().add(request) { error in
            if let error = error {
                print("Failed to schedule notification: \(error)")
            }
        }
    }

    private func loadAlarms() {
        guard let data = UserDefaults.standard.data(forKey: storageKey) else { return }
        if let decoded = try? JSONDecoder().decode([Alarm].self, from: data) {
            alarms = decoded
        }
    }

    private func saveAlarms() {
        if let data = try? JSONEncoder().encode(alarms) {
            UserDefaults.standard.set(data, forKey: storageKey)
        }
    }
}
