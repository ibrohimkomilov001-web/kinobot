import SwiftUI

/// To'liq kenglikdagi sahifalanuvchi hero karusel
struct HeroCarousel: View {
    let items: [TitleCard]
    let height: CGFloat
    let zoom: Namespace.ID

    @State private var currentID: Int? = nil

    var body: some View {
        VStack(spacing: 14) {
            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(spacing: 0) {
                    ForEach(items) { card in
                        HeroCard(card: card, height: height, zoom: zoom)
                            .containerRelativeFrame(.horizontal)
                    }
                }
                .scrollTargetLayout()
            }
            .scrollTargetBehavior(.viewAligned)
            .scrollPosition(id: $currentID)
            .frame(height: height)

            if items.count > 1 {
                pageDots
            }
        }
        .onAppear {
            if currentID == nil {
                currentID = items.first?.id
            }
        }
    }

    private var pageDots: some View {
        HStack(spacing: 6) {
            ForEach(items) { card in
                let isCurrent = card.id == (currentID ?? items.first?.id)
                Capsule()
                    .fill(isCurrent ? Theme.accent : Color.white.opacity(0.3))
                    .frame(width: isCurrent ? 18 : 6, height: 6)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 7)
        .glassEffect(.regular, in: .capsule)
        .animation(.snappy, value: currentID)
        .accessibilityHidden(true)
    }
}

/// Bitta hero kartasi: katta fon rasmi, sarlavha va shisha tugmalar
struct HeroCard: View {
    let card: TitleCard
    let height: CGFloat
    let zoom: Namespace.ID

    @Environment(AppState.self) private var app

    private var sourceID: String { "hero-\(card.id)" }

    var body: some View {
        ZStack(alignment: .bottomLeading) {
            NavigationLink(value: TitleRoute(card: card, sourceID: sourceID)) {
                ZStack(alignment: .bottomLeading) {
                    ArtworkView(
                        url: card.backdropImageURL ?? card.posterImageURL,
                        title: card.title,
                        seed: card.id
                    )
                    .frame(height: height)
                    .matchedTransitionSource(id: sourceID, in: zoom)

                    // Pastki va yuqori qoraytirish (matn o'qilishi uchun)
                    LinearGradient(
                        colors: [Theme.background.opacity(0), Theme.background.opacity(0.6), Theme.background],
                        startPoint: UnitPoint(x: 0.5, y: 0.35),
                        endPoint: .bottom
                    )
                    LinearGradient(
                        colors: [Theme.background.opacity(0.65), Theme.background.opacity(0)],
                        startPoint: .top,
                        endPoint: UnitPoint(x: 0.5, y: 0.22)
                    )

                    info
                        .padding(.horizontal, 20)
                        .padding(.bottom, 88)
                }
                .frame(height: height)
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)

            actions
                .padding(.horizontal, 20)
                .padding(.bottom, 24)
        }
        .frame(height: height)
    }

    private var info: some View {
        VStack(alignment: .leading, spacing: 8) {
            if card.isPremium {
                PremiumBadge()
            }
            Text(card.title)
                .font(.system(size: 34, weight: .heavy))
                .foregroundStyle(Theme.textPrimary)
                .lineLimit(2)
                .minimumScaleFactor(0.7)
                .shadow(color: .black.opacity(0.5), radius: 8, y: 2)
            Text(metaLine)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Theme.textSecondary)
                .lineLimit(1)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var metaLine: String {
        var parts: [String] = []
        if let year = card.year {
            parts.append(String(year))
        }
        parts.append(contentsOf: card.genres.prefix(2))
        if card.kind == .serial {
            parts.append("Serial")
        } else if let duration = Formatters.duration(card.durationSec) {
            parts.append(duration)
        }
        return parts.joined(separator: " · ")
    }

    private var favoriteAccessibilityLabel: String {
        app.isFavorite(card.id) ? "Saqlanganlardan olib tashlash" : "Saqlash"
    }

    private var actions: some View {
        GlassEffectContainer(spacing: 12) {
            HStack(spacing: 12) {
                Button {
                    app.play(card)
                } label: {
                    HStack(spacing: 8) {
                        if app.isPreparing(card.id) {
                            ProgressView()
                                .tint(Theme.onAccent)
                        } else {
                            Image(systemName: app.isLocked(card.id) ? "lock.fill" : "play.fill")
                        }
                        Text("Ko'rish")
                            .fontWeight(.bold)
                    }
                    .foregroundStyle(Theme.onAccent)
                    .padding(.horizontal, 10)
                }
                .buttonStyle(.glassProminent)
                .tint(Theme.accent)
                .controlSize(.large)
                .disabled(app.preparingTitleID != nil)

                Button {
                    app.toggleFavorite(card)
                } label: {
                    Image(systemName: app.isFavorite(card.id) ? "bookmark.fill" : "bookmark")
                        .font(.headline)
                        .foregroundStyle(app.isFavorite(card.id) ? Theme.accent : Theme.textPrimary)
                        .frame(width: 22, height: 22)
                }
                .buttonStyle(.glass)
                .controlSize(.large)
                .accessibilityLabel(favoriteAccessibilityLabel)
            }
        }
    }
}
