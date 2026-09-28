import SwiftUI

/// Dizayn tokenlari — barcha ranglar shu yerda (logo: oltin kinotasma belgisi).
enum Theme {
    // Fon: ko'mir-qora
    static let background = Color(hex: 0x0B0B0F)
    // Fon ustidagi iliq-neytral nur
    static let glow = Color(hex: 0x1C1B21)

    // Asosiy urg'u rangi — oltin (glass tint, prominent tugma, progress, tanlangan chip)
    static let accent = Color(hex: 0xE8C166)
    // Gradient uchlari: och oltin → to'q oltin
    static let accentLight = Color(hex: 0xF8E4A9)
    static let accentDeep = Color(hex: 0xB7842A)
    // Oltin fon ustidagi matn rangi
    static let onAccent = Color(hex: 0x141417)

    static let surface = Color.white.opacity(0.06)
    static let stroke = Color.white.opacity(0.08)
    static let textPrimary = Color.white
    static let textSecondary = Color.white.opacity(0.62)

    /// Sarlavha va urg'ular uchun oltin gradient
    static var accentGradient: LinearGradient {
        LinearGradient(colors: [accentLight, accentDeep], startPoint: .topLeading, endPoint: .bottomTrailing)
    }

    // Rasm yo'q bo'lganda poster o'rniga chiqadigan to'q, iliq gradientlar
    private static let placeholderPalettes: [[Color]] = [
        [Color(hex: 0x2A2418), Color(hex: 0x0F0E12)],
        [Color(hex: 0x23262E), Color(hex: 0x0D0E12)],
        [Color(hex: 0x2E2320), Color(hex: 0x100D0E)],
        [Color(hex: 0x1F2A28), Color(hex: 0x0C1011)],
        [Color(hex: 0x2B2530), Color(hex: 0x0F0D12)],
        [Color(hex: 0x302A1C), Color(hex: 0x121010)],
        [Color(hex: 0x24282A), Color(hex: 0x0E0F10)],
        [Color(hex: 0x2C2226), Color(hex: 0x110D0F)]
    ]

    static func placeholderGradient(seed: Int) -> LinearGradient {
        let count = placeholderPalettes.count
        let index = ((seed % count) + count) % count
        return LinearGradient(
            colors: placeholderPalettes[index],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
    }
}

extension Color {
    /// 0xRRGGBB ko'rinishidagi rang
    init(hex: UInt32, opacity: Double = 1) {
        let red = Double((hex >> 16) & 0xFF) / 255
        let green = Double((hex >> 8) & 0xFF) / 255
        let blue = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: red, green: green, blue: blue, opacity: opacity)
    }
}

/// Ilova foni: ko'mir-qora + yuqoridan tushuvchi yumshoq iliq nur
struct AppBackground: View {
    var body: some View {
        ZStack {
            Theme.background
            RadialGradient(
                colors: [Theme.glow, Theme.background.opacity(0)],
                center: UnitPoint(x: 0.5, y: 0.0),
                startRadius: 10,
                endRadius: 560
            )
            RadialGradient(
                colors: [Theme.accent.opacity(0.05), Theme.background.opacity(0)],
                center: UnitPoint(x: 0.5, y: 1.1),
                startRadius: 10,
                endRadius: 480
            )
        }
        .ignoresSafeArea()
    }
}

/// Bosh sahifa navigatsiya panelidagi brend belgisi
struct BrandTitle: View {
    var body: some View {
        HStack(spacing: 8) {
            Image("Logo")
                .resizable()
                .scaledToFit()
                .frame(width: 26, height: 26)
            Text("Kino Makoni")
                .font(.headline.weight(.heavy))
                .foregroundStyle(Theme.accentGradient)
        }
        .accessibilityElement(children: .combine)
    }
}
