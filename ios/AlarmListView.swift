import SwiftUI

struct AlarmListView: View {
    @StateObject private var viewModel = AlarmListViewModel()
    @State private var newDate = Date()

    var body: some View {
        NavigationView {
            VStack {
                List {
                    ForEach(viewModel.alarms) { alarm in
                        Text(alarm.date, style: .time)
                    }
                    .onDelete(perform: viewModel.removeAlarms)
                }

                HStack {
                    DatePicker("", selection: $newDate, displayedComponents: .hourAndMinute)
                        .labelsHidden()
                    Button("Add") {
                        viewModel.addAlarm(at: newDate)
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding()
            }
            .navigationTitle("Alarms")
        }
    }
}

#Preview {
    AlarmListView()
}
