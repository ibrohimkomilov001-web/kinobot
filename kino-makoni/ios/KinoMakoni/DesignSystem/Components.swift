import SwiftUI

/// Bo'lim sarlavhasi + ixtiyoriy "Hammasi" havolasi
struct SectionHeader: View {
    let title: String
    var query: CatalogQuery? = nil

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title)
                .font(.title3.weight(.bold))
                .foregroundStyle(Theme.textPrimary)
            Spacer(minLength: 8)
            if let query = query {
                NavigationLink(value: query) {
                    HStack(spacing: 3) {
                        Text("Hammasi")
                        Image(systemName: "chevron.right")
                            .font(.caption.weight(.bold))
                    }
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Theme.accent)
                }
                .buttonStyle(.plain)
            }
        }
    }
}

/// Ko'rish progressi chizig'i (oltin)
struct ProgressBar: View {
    let value: Double
    var height: CGFloat = 4

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Capsule()
                    .fill(Color.white.opacity(0.2))
                Capsule()
                    .fill(Theme.accent)
                    .frame(width: proxy.size.width * CGFloat(min(max(value, 0), 1)))
            }
        }
        .frame(height: height)
        .accessibilityElement()
        .accessibilityLabel("Ko'rilgan")
        .accessibilityValue("\(Int((min(max(value, 0), 1) * 100).rounded())) foiz")
    }
}

/// Premium belgisi (toj)
struct PremiumBadge: View {
    var compact: Bool = false

    var body: some View {
        if compact {
            Image(systemName: "crown.fill")
                .font(.system(size: 10, weight: .bold))
                .foregroundStyle(Theme.onAccent)
                .padding(5)
                .background(Theme.accentGradient, in: Circle())
                .accessibilityLabel("Premium")
        } else {
            HStack(spacing: 4) {
                Image(systemName: "crown.fill")
                Text("Premium")
            }
            .font(.caption.weight(.bold))
            .foregroundStyle(Theme.onAccent)
            .padding(.horizontal, 10)
            .padding(.vertical, 4)
            .background(Theme.accentGradient, in: Capsule())
        }
    }
}

/// Qisqa xabar (toast) — ekran tepasida shisha kapsula
struct ToastOverlay: View {
    let message: String?

    var body: some View {
        if let message = message {
            Text(message)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Theme.textPrimary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 18)
                .padding(.vertical, 12)
                .glassEffect(.regular, in: .capsule)
                .padding(.top, 8)
                .padding(.horizontal, 24)
                .transition(.move(edge: .top).combined(with: .opacity))
        }
    }
}
