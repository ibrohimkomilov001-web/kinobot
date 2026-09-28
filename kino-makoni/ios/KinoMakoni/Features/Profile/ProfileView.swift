import SwiftUI

/// Profil: logo, versiya, API rejimi, kesh, ilova haqida
struct ProfileView: View {
    @Environment(AppState.self) private var app
    @State private var userID: Int? = nil
    @State private var cacheSize = ""

    private let service: any KinoService

    init(service: any KinoService) {
        self.service = service
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 18) {
                    headerCard
                    settingsCard
                    aboutCard
                    Text("© 2026 Kino Makoni")
                        .font(.caption2)
                        .foregroundStyle(Theme.textSecondary)
                        .padding(.top, 4)
                }
                .padding(16)
                .padding(.bottom, 24)
            }
            .background { AppBackground() }
            .navigationTitle("Profil")
            .task {
                await load()
            }
        }
    }

    // MARK: - Kartalar

    private var headerCard: some View {
        VStack(spacing: 12) {
            Image("Logo")
                .resizable()
                .scaledToFit()
                .frame(width: 84, height: 84)
                .padding(16)
                .glassEffect(.regular.tint(Theme.accent.opacity(0.15)), in: .circle)

            Text("Kino Makoni")
                .font(.title.weight(.heavy))
                .foregroundStyle(Theme.accentGradient)

            Text(versionText)
                .font(.footnote)
                .foregroundStyle(Theme.textSecondary)

            modeBadge

            if let userID = userID {
                Text(guestText(userID))
                    .font(.footnote.weight(.medium))
                    .foregroundStyle(Theme.textSecondary)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
        .padding(.horizontal, 16)
        .glassEffect(.regular, in: .rect(cornerRadius: 28))
    }

    private var modeBadge: some View {
        HStack(spacing: 6) {
            Image(systemName: app.isDemo ? "play.tv" : "checkmark.seal.fill")
            Text(modeTitle)
        }
        .font(.caption.weight(.bold))
        .foregroundStyle(app.isDemo ? Theme.accent : Color.green)
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .glassEffect(.regular.tint(badgeTint), in: .capsule)
    }

    private var settingsCard: some View {
        VStack(spacing: 0) {
            Button {
                clearCache()
            } label: {
                SettingsRow(icon: "trash", title: "Keshni tozalash", value: cacheSize)
            }

            rowDivider

            Link(destination: AppConfig.telegramChannelURL) {
                SettingsRow(
                    icon: "paperplane.fill",
                    title: "Telegram kanalimiz",
                    value: AppConfig.telegramChannelHandle,
                    showsChevron: true
                )
            }

            rowDivider

            SettingsRow(icon: "server.rack", title: "API", value: serverText)
        }
        .buttonStyle(.plain)
        .glassEffect(.regular, in: .rect(cornerRadius: 24))
    }

    private var aboutCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Ilova haqida", systemImage: "info.circle")
                .font(.headline)
                .foregroundStyle(Theme.textPrimary)
            Text("Kino Makoni — o'zbek tilidagi kinolar va seriallarni bir joyda qulay tomosha qilish uchun ilova. Katalog Kino Makoni Telegram kanali bilan bog'langan: yangi kinolar avtomatik qo'shiladi, ko'rishni istalgan joydan davom ettirishingiz mumkin.")
                .font(.subheadline)
                .foregroundStyle(Theme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
            Text("Ro'yxatdan o'tish shart emas — qurilmangiz uchun mehmon hisob avtomatik yaratiladi.")
                .font(.footnote)
                .foregroundStyle(Theme.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(18)
        .glassEffect(.regular, in: .rect(cornerRadius: 24))
    }

    private var rowDivider: some View {
        Rectangle()
            .fill(Theme.stroke)
            .frame(height: 1)
            .padding(.leading, 58)
    }

    // MARK: - Matnlar

    private var versionText: String {
        "Versiya \(AppConfig.appVersion) (\(AppConfig.buildNumber))"
    }

    private var modeTitle: String {
        app.isDemo ? "Demo rejim" : "Server"
    }

    private var badgeTint: Color {
        app.isDemo ? Theme.accent.opacity(0.18) : Color.green.opacity(0.18)
    }

    private var serverText: String {
        if let host = AppConfig.apiBaseURL?.host() {
            return host
        }
        return "Demo katalog"
    }

    private func guestText(_ id: Int) -> String {
        "Mehmon #\(id)"
    }

    // MARK: - Amallar

    private func load() async {
        refreshCacheSize()
        guard userID == nil else { return }
        let me = try? await service.me()
        if let me = me {
            userID = me.id
        }
    }

    private func refreshCacheSize() {
        let bytes = Int64(URLCache.shared.currentDiskUsage + URLCache.shared.currentMemoryUsage)
        cacheSize = ByteCountFormatter.string(fromByteCount: bytes, countStyle: .file)
    }

    private func clearCache() {
        URLCache.shared.removeAllCachedResponses()
        refreshCacheSize()
        app.showToast("Kesh tozalandi")
    }
}

/// Sozlamalar qatori
struct SettingsRow: View {
    let icon: String
    let title: String
    var value: String = ""
    var showsChevron: Bool = false

    var body: some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 15, weight: .semibold))
                .foregroundStyle(Theme.onAccent)
                .frame(width: 30, height: 30)
                .background(Theme.accentGradient, in: RoundedRectangle(cornerRadius: 8, style: .continuous))
            Text(title)
                .font(.body)
                .foregroundStyle(Theme.textPrimary)
            Spacer(minLength: 8)
            if !value.isEmpty {
                Text(value)
                    .font(.subheadline)
                    .foregroundStyle(Theme.textSecondary)
                    .lineLimit(1)
            }
            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.caption.weight(.bold))
                    .foregroundStyle(Theme.textSecondary)
            }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 13)
        .contentShape(Rectangle())
    }
}

#Preview {
    ProfileView(service: MockKinoService(latency: 0))
        .environment(AppState.preview)
        .preferredColorScheme(.dark)
}
