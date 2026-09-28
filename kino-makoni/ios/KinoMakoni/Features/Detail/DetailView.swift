import SwiftUI

/// Kino / serial sahifasi
struct DetailView: View {
    @Environment(AppState.self) private var app
    @State private var model: DetailViewModel
    @State private var isOverviewExpanded = false

    private let headerHeight: CGFloat = 430

    init(card: TitleCard, service: any KinoService) {
        _model = State(initialValue: DetailViewModel(card: card, service: service))
    }

    private var card: TitleCard { model.card }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                header
                VStack(alignment: .leading, spacing: 22) {
                    titleBlock
                    actionBar
                    if !card.genres.isEmpty {
                        genreChips
                    }
                    detailContent
                }
                .padding(.horizontal, 20)
                .padding(.top, -92)
                .padding(.bottom, 48)
            }
        }
        .ignoresSafeArea(edges: .top)
        .background { AppBackground() }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                ShareLink(item: shareText) {
                    Image(systemName: "square.and.arrow.up")
                }
            }
        }
        .task {
            if let fresh = await model.loadIfNeeded() {
                app.syncFavorite(id: fresh.id, isFavorite: fresh.isFavorite)
            }
        }
        .onChange(of: app.playbackEndedTick) { _, _ in
            Task { await model.reload() }
        }
    }

    // MARK: - Sarlavha rasmi (cho'ziluvchan)

    private var header: some View {
        GeometryReader { proxy in
            let minY = proxy.frame(in: .global).minY
            let stretch = max(0, minY)
            ArtworkView(
                url: card.backdropImageURL ?? card.posterImageURL,
                title: card.title,
                seed: card.id,
                showsInitials: false
            )
            .frame(width: proxy.size.width, height: headerHeight + stretch)
            .backgroundExtensionEffect()
            .overlay {
                LinearGradient(
                    colors: [
                        Theme.background.opacity(0.45),
                        Theme.background.opacity(0),
                        Theme.background.opacity(0.75),
                        Theme.background
                    ],
                    startPoint: .top,
                    endPoint: .bottom
                )
            }
            .offset(y: -stretch)
        }
        .frame(height: headerHeight)
    }

    // MARK: - Nomi va meta

    private var titleBlock: some View {
        HStack(alignment: .bottom, spacing: 16) {
            PosterView(card: card, cornerRadius: 12)
                .frame(width: 112, height: 168)
                .shadow(color: .black.opacity(0.55), radius: 18, y: 10)

            VStack(alignment: .leading, spacing: 8) {
                if card.isPremium {
                    PremiumBadge()
                }
                Text(card.title)
                    .font(.title2.weight(.heavy))
                    .foregroundStyle(Theme.textPrimary)
                    .lineLimit(3)
                    .minimumScaleFactor(0.8)
                if !metaLine.isEmpty {
                    Text(metaLine)
                        .font(.footnote.weight(.medium))
                        .foregroundStyle(Theme.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            Spacer(minLength: 0)
        }
    }

    private var metaLine: String {
        var parts: [String] = []
        if let year = card.year {
            parts.append(String(year))
        }
        if let quality = card.quality, !quality.isEmpty {
            parts.append(quality)
        }
        if card.kind == .serial {
            if let count = model.detail?.seasons.count, count > 0 {
                parts.append("\(count) fasl")
            } else {
                parts.append("Serial")
            }
        } else if let duration = Formatters.duration(card.durationSec) {
            parts.append(duration)
        }
        if let language = model.detail?.language, !language.isEmpty {
            parts.append(language)
        }
        return parts.joined(separator: " · ")
    }

    // MARK: - Tugmalar

    private var isFavorite: Bool { app.isFavorite(card.id) }

    private var isAvailable: Bool { model.detail?.isAvailable ?? true }

    private var actionBar: some View {
        VStack(alignment: .leading, spacing: 10) {
            GlassEffectContainer(spacing: 12) {
                HStack(spacing: 12) {
                    playButton

                    Button {
                        app.toggleFavorite(card)
                    } label: {
                        Image(systemName: isFavorite ? "bookmark.fill" : "bookmark")
                            .font(.title3.weight(.semibold))
                            .foregroundStyle(isFavorite ? Theme.accent : Theme.textPrimary)
                            .frame(width: 26, height: 26)
                    }
                    .buttonStyle(.glass)
                    .controlSize(.large)
                    .accessibilityLabel(favoriteAccessibilityLabel)
                }
            }
            if let caption = playCaption {
                Text(caption)
                    .font(.caption.weight(.medium))
                    .foregroundStyle(Theme.textSecondary)
            }
        }
    }

    @ViewBuilder
    private var playButton: some View {
        if !isAvailable {
            Button {} label: {
                Label("Tez orada", systemImage: "clock")
                    .fontWeight(.bold)
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.glass)
            .controlSize(.large)
            .disabled(true)
        } else {
            Button {
                startPlayback()
            } label: {
                HStack(spacing: 8) {
                    if app.isPreparing(card.id) {
                        ProgressView()
                            .tint(Theme.onAccent)
                    } else {
                        Image(systemName: app.isLocked(card.id) ? "lock.fill" : "play.fill")
                    }
                    Text(playTitle)
                        .fontWeight(.bold)
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                }
                .foregroundStyle(Theme.onAccent)
                .frame(maxWidth: .infinity)
            }
            .buttonStyle(.glassProminent)
            .tint(Theme.accent)
            .controlSize(.large)
            .disabled(app.preparingTitleID != nil || (card.kind == .serial && model.detail == nil))
        }
    }

    private var favoriteAccessibilityLabel: String {
        isFavorite ? "Saqlanganlardan olib tashlash" : "Saqlash"
    }

    /// "Ko'rish" yoki "Davom ettirish (mm:ss)"
    private var playTitle: String {
        guard let progress = model.detail?.progress, progress.positionSec > 5 else {
            return "Ko'rish"
        }
        return "Davom ettirish (\(Formatters.clock(progress.positionSec)))"
    }

    private var playCaption: String? {
        guard let detail = model.detail, detail.kind == .serial, detail.isAvailable,
              let ref = detail.resumeEpisode else {
            return nil
        }
        return ref.label
    }

    private func startPlayback() {
        guard let detail = model.detail else {
            app.play(card)
            return
        }
        if detail.kind == .serial {
            guard let ref = detail.resumeEpisode else {
                app.showToast("Qismlar hali mavjud emas")
                return
            }
            app.play(detail.card, episodeID: ref.episode.id, episodeLabel: ref.label, durationHint: ref.episode.durationSec)
        } else {
            app.play(detail.card, durationHint: detail.durationSec)
        }
    }

    // MARK: - Janrlar

    private var genreChips: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            GlassEffectContainer(spacing: 8) {
                HStack(spacing: 8) {
                    ForEach(card.genres, id: \.self) { genre in
                        GlassChip(title: genre)
                    }
                }
                .padding(.vertical, 2)
            }
        }
        .scrollClipDisabled()
    }

    // MARK: - Tavsif, kod, qismlar

    @ViewBuilder
    private var detailContent: some View {
        if let detail = model.detail {
            if let overview = detail.overview, !overview.isEmpty {
                overviewBlock(overview)
            }
            infoRow(detail)
            if detail.kind == .serial && !detail.seasons.isEmpty {
                EpisodeSection(detail: detail, selectedSeasonID: $model.selectedSeasonID)
            }
        } else if let message = model.errorMessage {
            ErrorStateView(message: message) {
                Task { await model.reload() }
            }
        } else {
            VStack(alignment: .leading, spacing: 10) {
                SkeletonBlock(cornerRadius: 6).frame(height: 14)
                SkeletonBlock(cornerRadius: 6).frame(height: 14)
                SkeletonBlock(cornerRadius: 6).frame(width: 220, height: 14)
            }
        }
    }

    private func overviewBlock(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(text)
                .font(.callout)
                .foregroundStyle(Theme.textPrimary.opacity(0.86))
                .lineLimit(isOverviewExpanded ? nil : 4)
                .fixedSize(horizontal: false, vertical: true)
            if text.count > 160 {
                Button {
                    withAnimation(.snappy) {
                        isOverviewExpanded.toggle()
                    }
                } label: {
                    Text(overviewToggleTitle)
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Theme.accent)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private var overviewToggleTitle: String {
        isOverviewExpanded ? "Kamroq" : "Ko'proq"
    }

    private func infoRow(_ detail: TitleDetail) -> some View {
        HStack(spacing: 18) {
            if let code = detail.code {
                Label(codeText(code), systemImage: "number")
            }
            if detail.views > 0 {
                Label(Formatters.views(detail.views), systemImage: "eye")
            }
            Spacer(minLength: 0)
        }
        .font(.footnote.weight(.semibold))
        .foregroundStyle(Theme.textSecondary)
    }

    private func codeText(_ code: Int) -> String {
        "Kod: \(code)"
    }

    private var shareText: String {
        var text = "\(card.title) — Kino Makoni ilovasida tomosha qiling."
        if let code = model.detail?.code {
            text += " Kod: \(code)"
        }
        return text
    }
}

#Preview {
    NavigationStack {
        DetailView(card: MockCatalog.previewCard, service: MockKinoService(latency: 0))
    }
    .environment(AppState.preview)
    .preferredColorScheme(.dark)
}
