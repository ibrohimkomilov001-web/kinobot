import Foundation

// Bitta buzilgan element butun ro'yxatni yiqitmasligi uchun o'ram
struct FailableDecodable<Value: Decodable>: Decodable {
    let value: Value?

    init(from decoder: Decoder) throws {
        value = try? Value(from: decoder)
    }
}

extension KeyedDecodingContainer {
    /// Ro'yxatni "yumshoq" o'qiydi: buzilgan elementlar tashlab yuboriladi.
    func lossyArray<T: Decodable>(_ type: T.Type, forKey key: Key) -> [T] {
        guard let wrapped = try? decodeIfPresent([FailableDecodable<T>].self, forKey: key) else {
            return []
        }
        return wrapped.compactMap { $0.value }
    }

    /// Butun son: Int, Double (1200.0) yoki "1200" satr ko'rinishida kelishi mumkin.
    func flexibleInt(_ key: Key) -> Int? {
        if let value = try? decodeIfPresent(Int.self, forKey: key) {
            return value
        }
        if let value = try? decodeIfPresent(Double.self, forKey: key),
           value.isFinite, abs(value) < 1e15 {
            return Int(value.rounded())
        }
        if let text = try? decodeIfPresent(String.self, forKey: key),
           let value = Int(text) {
            return value
        }
        return nil
    }

    func flexibleBool(_ key: Key, fallback: Bool) -> Bool {
        if let value = try? decodeIfPresent(Bool.self, forKey: key) {
            return value
        }
        if let value = try? decodeIfPresent(Int.self, forKey: key) {
            return value != 0
        }
        return fallback
    }

    func optionalString(_ key: Key) -> String? {
        guard let value = try? decodeIfPresent(String.self, forKey: key) else { return nil }
        return value
    }
}

/// ISO-8601 sanalarni o'qiydi: kasr soniyali/soniyasiz, "Z" yoki "+05:00",
/// hatto vaqt zonasisiz (UTC deb olinadi) ko'rinishlarni ham qabul qiladi.
enum ISODateParser {
    static func parse(_ raw: String) -> Date? {
        var text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return nil }

        // Faqat sana: "2026-09-28"
        if !text.contains("T") && !text.contains(" ") {
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withFullDate]
            return formatter.date(from: text)
        }

        text = text.replacingOccurrences(of: " ", with: "T")

        // Kasr soniyalarni ajratib olamiz (".123" yoki ".123456")
        var fraction: Double = 0
        if let dot = text.firstIndex(of: ".") {
            var end = text.index(after: dot)
            while end < text.endIndex, text[end].isASCII, text[end].isNumber {
                end = text.index(after: end)
            }
            let digits = String(text[text.index(after: dot)..<end])
            if !digits.isEmpty {
                fraction = Double("0." + digits) ?? 0
            }
            text.removeSubrange(dot..<end)
        }

        if !hasTimeZone(text) {
            text += "Z"
        }

        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        guard let base = formatter.date(from: text) else { return nil }
        return base.addingTimeInterval(fraction)
    }

    private static func hasTimeZone(_ text: String) -> Bool {
        guard let tIndex = text.firstIndex(of: "T") else { return true }
        let timePart = text[text.index(after: tIndex)...]
        return timePart.contains("Z") || timePart.contains("+") || timePart.contains("-")
    }
}

extension JSONDecoder {
    /// API uchun sozlangan dekoder: snake_case → camelCase, moslashuvchan sanalar.
    static func kino() -> JSONDecoder {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { dateDecoder in
            let container = try dateDecoder.singleValueContainer()
            let raw = try container.decode(String.self)
            if let date = ISODateParser.parse(raw) {
                return date
            }
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "Sana formati noto'g'ri: \(raw)"
            )
        }
        return decoder
    }
}

enum URLSanitizer {
    /// Bo'sh yoki sxemasiz satrlarni nil qiladi.
    static func url(_ raw: String?) -> URL? {
        guard let trimmed = raw?.trimmingCharacters(in: .whitespacesAndNewlines),
              !trimmed.isEmpty,
              let url = URL(string: trimmed),
              url.scheme != nil else {
            return nil
        }
        return url
    }
}
