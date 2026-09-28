import SwiftUI
import AVFoundation

@main
struct KinoMakoniApp: App {
    @State private var appState: AppState

    init() {
        Self.configureAudioSession()
        Self.configureURLCache()
        _appState = State(initialValue: AppState.makeDefault())
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appState)
                .preferredColorScheme(.dark)
                .tint(Theme.accent)
        }
    }

    // Audio sessiya: PiP va fon rejimida ovoz davom etishi uchun .playback
    private static func configureAudioSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .moviePlayback, options: [])
        } catch {
            print("[KinoMakoni] AVAudioSession sozlanmadi: \(error)")
        }
    }

    // Poster/backdrop rasmlari uchun kattaroq URL kesh
    private static func configureURLCache() {
        URLCache.shared = URLCache(
            memoryCapacity: 64 * 1024 * 1024,
            diskCapacity: 512 * 1024 * 1024,
            directory: nil
        )
    }
}
