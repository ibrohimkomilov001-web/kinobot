import Foundation

/// Vaqt va sonlarni o'zbekcha formatlash
enum Formatters {
    /// 7260 → "2 soat 1 daq", 2700 → "45 daq"
    static func duration(_ seconds: Int?) -> String? {
        guard let seconds = seconds, seconds > 0 else { return nil }
        let hours = seconds / 3600
        let minutes = (seconds % 3600) / 60
        if hours > 0 && minutes > 0 {
            return "\(hours) soat \(minutes) daq"
        }
        if hours > 0 {
            return "\(hours) soat"
        }
        return "\(max(minutes, 1)) daq"
    }

    /// Pozitsiya: "05:30" yoki "1:05:30"
    static func clock(_ seconds: Int) -> String {
        let total = max(0, seconds)
        let hours = total / 3600
        let minutes = (total % 3600) / 60
        let secs = total % 60
        if hours > 0 {
            return String(format: "%ld:%02ld:%02ld", hours, minutes, secs)
        }
        return String(format: "%02ld:%02ld", minutes, secs)
    }

    /// "45 daq qoldi"
    static func remaining(position: Int, duration: Int) -> String? {
        let left = duration - position
        guard left > 30, let text = self.duration(left) else { return nil }
        return "\(text) qoldi"
    }

    /// 15230 → "15,2 ming"
    static func views(_ count: Int) -> String {
        if count >= 1_000_000 {
            return compact(Double(count) / 1_000_000) + " mln"
        }
        if count >= 1_000 {
            return compact(Double(count) / 1_000) + " ming"
        }
        return String(count)
    }

    private static func compact(_ value: Double) -> String {
        let rounded = (value * 10).rounded() / 10
        if rounded == rounded.rounded() {
            return String(Int(rounded))
        }
        return String(format: "%.1f", rounded).replacingOccurrences(of: ".", with: ",")
    }

    /// Ism bosh harflari: "Samarqand sirlari" → "SS"
    static func initials(_ title: String) -> String {
        let words = title.split(whereSeparator: { char in char == " " || char == ":" || char == "-" })
        var letters: [Character] = []
        for word in words.prefix(2) {
            if let letter = word.first(where: { char in char.isLetter || char.isNumber }) {
                letters.append(letter)
            }
        }
        return String(letters).uppercased()
    }
}
