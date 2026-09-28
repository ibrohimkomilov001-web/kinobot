import Foundation

/// Qurilmaning doimiy anonim identifikatori (birinchi ishga tushishda yaratiladi, Keychain'da saqlanadi)
enum DeviceIdentity {
    private static let account = "device_id"
    private static let fallbackKey = "km.device_id"

    static var current: String {
        if let existing = KeychainStore.string(for: account), !existing.isEmpty {
            return existing
        }
        // Keychain ishlamagan holatlar uchun zaxira
        if let fallback = UserDefaults.standard.string(forKey: fallbackKey), !fallback.isEmpty {
            KeychainStore.set(fallback, for: account)
            return fallback
        }
        let fresh = UUID().uuidString
        if !KeychainStore.set(fresh, for: account) {
            UserDefaults.standard.set(fresh, forKey: fallbackKey)
        }
        return fresh
    }
}

/// Access token saqlovchi (Keychain)
enum TokenStore {
    private static let account = "access_token"

    static func load() -> String? {
        guard let token = KeychainStore.string(for: account), !token.isEmpty else {
            return nil
        }
        return token
    }

    static func save(_ token: String) {
        KeychainStore.set(token, for: account)
    }

    static func clear() {
        KeychainStore.remove(account)
    }
}
