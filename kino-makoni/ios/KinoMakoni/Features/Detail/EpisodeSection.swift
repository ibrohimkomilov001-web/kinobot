import SwiftUI

/// Serial: fasl tanlash chiplari + qismlar ro'yxati
struct EpisodeSection: View {
    let detail: TitleDetail
    @Binding var selectedSeasonID: Int?

    @Environment(AppState.self) private var app

    private var orderedSeasons: [Season] {
        detail.seasons.sorted { $0.number < $1.number }
    }

    private var currentSeason: Season? {
        if let id = selectedSeasonID, let season = detail.seasons.first(where: { $0.id == id }) {
            return season
        }
        return detail.resumeEpisode?.season ?? orderedSeasons.first
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Qismlar")
                .font(.title3.weight(.bold))
                .foregroundStyle(Theme.textPrimary)

            if orderedSeasons.count > 1 {
                seasonPicker
            }

            if let season = currentSeason {
                LazyVStack(spacing: 10) {
                    ForEach(season.episodes.sorted { $0.number < $1.number }) { episode in
                        EpisodeRow(
                            season: season,
                            episode: episode,
                            isResume: episode.id == detail.progress?.episodeId,
                            isPreparing: app.isPreparing(detail.id),
                            onPlay: {
                                app.play(
                                    detail.card,
                                    episodeID: episode.id,
                                    episodeLabel: EpisodeRef(season: season, episode: episode).label,
                                    durationHint: episode.durationSec
                                )
                            }
                        )
                    }
                }
            }
        }
    }

    private var seasonPicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            GlassEffectContainer(spacing: 8) {
                HStack(spacing: 8) {
                    ForEach(orderedSeasons) { season in
                        Button {
                            withAnimation(.snappy) {
                                selectedSeasonID = season.id
                            }
                        } label: {
                            GlassChip(title: season.displayTitle, isSelected: season.id == currentSeason?.id)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .scrollClipDisabled()
    }
}

/// Bitta qism qatori
struct EpisodeRow: View {
    let season: Season
    let episode: Episode
    let isResume: Bool
    let isPreparing: Bool
    let onPlay: () -> Void

    var body: some View {
        Button(action: onPlay) {
            HStack(spacing: 14) {
                Text(String(episode.number))
                    .font(.headline.weight(.bold))
                    .foregroundStyle(isResume ? Theme.onAccent : Theme.textPrimary)
                    .frame(width: 44, height: 44)
                    .glassEffect(numberGlass, in: .circle)

                VStack(alignment: .leading, spacing: 5) {
                    Text(episode.displayTitle)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(Theme.textPrimary)
                        .lineLimit(1)
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(Theme.textSecondary)
                        .lineLimit(1)
                    if episode.progressFraction > 0 {
                        ProgressBar(value: episode.progressFraction, height: 3)
                    }
                }

                Spacer(minLength: 0)

                Image(systemName: episode.isAvailable ? "play.fill" : "clock")
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(episode.isAvailable ? Theme.accent : Theme.textSecondary)
            }
            .padding(12)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .strokeBorder(isResume ? Theme.accent.opacity(0.55) : Theme.stroke, lineWidth: 1)
            }
            .contentShape(Rectangle())
            .opacity(episode.isAvailable ? 1 : 0.55)
        }
        .buttonStyle(.plain)
        .disabled(!episode.isAvailable || isPreparing)
    }

    private var numberGlass: Glass {
        if isResume {
            return Glass.regular.tint(Theme.accent)
        }
        return Glass.regular
    }

    private var subtitle: String {
        if !episode.isAvailable {
            return "Tez orada"
        }
        var parts: [String] = []
        if let duration = Formatters.duration(episode.durationSec) {
            parts.append(duration)
        }
        if episode.progressSec > 0 {
            parts.append("\(Formatters.clock(episode.progressSec)) ko'rilgan")
        }
        if parts.isEmpty {
            parts.append("\(season.number)-fasl")
        }
        return parts.joined(separator: " · ")
    }
}
