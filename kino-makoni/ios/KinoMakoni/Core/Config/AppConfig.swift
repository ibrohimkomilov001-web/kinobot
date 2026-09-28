import Foundation

/// Ilova sozlamalari: Info.plist'dagi `KMApiBaseURL` (build sozlamasi `API_BASE_URL`).
/// Qiymat bo'sh yoki noto'g'ri bo'lsa ilova demo rejimda ishlaydi.
enum AppConfig {
    static let apiBaseURL: URL? = {
        guard let raw = Bundle.main.object(forInfoDictionaryKey: "KMApiBaseURL") as? String else {
            return nil
        }
        var value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        while value.hasSuffix("/") {
            value.removeLast()
        }
        // "$(API_BASE_URL)" o'zgarmay qolgan bo'lsa ham demo rejim
        guard !value.isEmpty, !value.contains("$(") else { return nil }
        guard let url = URL(string: value),
              let scheme = url.scheme?.lowercased(),
              scheme == "https" || scheme == "http",
              url.host() != nil else {
            return nil
        }
        return url
    }()

    static var isDemoMode: Bool { apiBaseURL == nil }

    static let appVersion: String =
        (Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String) ?? "1.0.0"

    static let buildNumber: String =
        (Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String) ?? "1"

    // Telegram kanal havolasi (vaqtinchalik — haqiqiy kanal manzili bilan almashtiring)
    static let telegramChannelURL = URL(string: "https://t.me/kinomakoni")!
    static let telegramChannelHandle = "@kinomakoni"
}
