import SwiftUI

/// "Davom ettirish" gorizontal qatori
struct ContinueRow: View {
    let title: String
    let items: [ContinueItem]

    var body: some View {
        if !items.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeader(title: title)
                    .padding(.horizontal, 16)
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(alignment: .top, spacing: 14) {
                        ForEach(items) { item in
                            ContinueCard(item: item)
                        }
                    }
                    .scrollTargetLayout()
                }
                .contentMargins(.horizontal, 16, for: .scrollContent)
                .scrollTargetBehavior(.viewAligned)
            }
        }
    }
}

/// 16:9 karta + progress; bosilganda to'g'ridan-to'g'ri ijro
struct ContinueCard: View {
    let item: ContinueItem
    var width: CGFloat = 250

    @Environment(AppState.self) private var app

    var body: some View {
        Button {
            app.play(
                item.title,
                episodeID: item.episodeId,
                episodeLabel: item.episodeLabel,
                durationHint: item.durationSec
            )
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                ArtworkView(
                    url: item.title.backdropImageURL ?? item.title.posterImageURL,
                    title: item.title.title,
                    seed: item.title.id
                )
                .frame(width: width, height: width * 9 / 16)
                .overlay {
                    LinearGradient(
                        colors: [Color.black.opacity(0), Color.black.opacity(0.55)],
                        startPoint: .center,
                        endPoint: .bottom
                    )
                }
                .overlay {
                    ContinuePlayBadge(isLoading: app.isPreparing(item.title.id))
                }
                .overlay(alignment: .bottom) {
                    ProgressBar(value: item.fraction)
                        .padding(.horizontal, 12)
                        .padding(.bottom, 10)
                }
                .clipShape(.rect(cornerRadius: 16))

                Text(item.title.title)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(Theme.textPrimary)
                    .lineLimit(1)
                Text(ContinueText.subtitle(for: item))
                    .font(.caption)
                    .foregroundStyle(Theme.textSecondary)
                    .lineLimit(1)
            }
            .frame(width: width, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(app.preparingTitleID != nil)
    }
}

/// Ro'yxat ko'rinishidagi "davom ettirish" qatori (Saqlanganlar sahifasi)
struct ContinueListRow: View {
    let item: ContinueItem

    @Environment(AppState.self) private var app

    var body: some View {
        Button {
            app.play(
                item.title,
                episodeID: item.episodeId,
                episodeLabel: item.episodeLabel,
                durationHint: item.durationSec
            )
        } label: {
            HStack(spacing: 14) {
                ArtworkView(
                    url: item.title.backdropImageURL ?? item.title.posterImageURL,
                    title: item.title.title,
                    seed: item.title.id,
                    showsInitials: false
                )
                .frame(width: 132, height: 74)
                .overlay {
                    ContinuePlayBadge(isLoading: app.isPreparing(item.title.id), size: 34)
                }
                .clipShape(.rect(cornerRadius: 12))

                VStack(alignment: .leading, spacing: 6) {
                    Text(item.title.title)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Theme.textPrimary)
                        .lineLimit(1)
                    Text(ContinueText.subtitle(for: item))
                        .font(.caption)
                        .foregroundStyle(Theme.textSecondary)
                        .lineLimit(1)
                    ProgressBar(value: item.fraction)
                }
                Spacer(minLength: 0)
            }
            .padding(10)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .disabled(app.preparingTitleID != nil)
    }
}

/// O'rtadagi shisha "play" belgisi
struct ContinuePlayBadge: View {
    let isLoading: Bool
    var size: CGFloat = 46

    var body: some View {
        ZStack {
            if isLoading {
                ProgressView()
                    .tint(Theme.textPrimary)
            } else {
                Image(systemName: "play.fill")
                    .font(.system(size: size * 0.36, weight: .bold))
                    .foregroundStyle(Theme.textPrimary)
            }
        }
        .frame(width: size, height: size)
        .glassEffect(.regular.interactive(), in: .circle)
    }
}

enum ContinueText {
    static func subtitle(for item: ContinueItem) -> String {
        var parts: [String] = []
        if let label = item.episodeLabel, !label.isEmpty {
            parts.append(label)
        }
        if let left = Formatters.remaining(position: item.positionSec, duration: item.durationSec) {
            parts.append(left)
        } else {
            parts.append(Formatters.clock(item.positionSec))
        }
        return parts.joined(separator: " · ")
    }
}
