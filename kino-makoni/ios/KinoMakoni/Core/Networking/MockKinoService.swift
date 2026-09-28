import Foundation

/// Demo rejim servisi: ichki katalog, sevimlilar va progress xotirada saqlanadi.
actor MockKinoService: KinoService {
    private struct ProgressEntry {
        let titleID: Int
        let episodeID: Int?
        var position: Int
        var duration: Int
        var updatedAt: Date

        var isFinished: Bool { duration > 0 && Double(position) >= 0.92 * Double(duration) }
    }

    private let catalog: [MockTitle]
    private var favoriteOrder: [Int]
    private var progress: [String: ProgressEntry]
    private let latency: UInt64

    init(latency: UInt64 = 350_000_000) {
        self.latency = latency
        self.catalog = MockCatalog.makeTitles()
        self.favoriteOrder = MockCatalog.initialFavorites

        // Namoyish uchun boshlang'ich "davom ettirish" yozuvlari
        var seeded: [String: ProgressEntry] = [:]
        let now = Date()
        let first = ProgressEntry(titleID: 2, episodeID: nil, position: 2_460, duration: 6_480, updatedAt: now.addingTimeInterval(-3_600))
        let second = ProgressEntry(titleID: 18, episodeID: 18_103, position: 1_130, duration: 2_700, updatedAt: now.addingTimeInterval(-600))
        seeded[MockKinoService.key(first.titleID, first.episodeID)] = first
        seeded[MockKinoService.key(second.titleID, second.episodeID)] = second
        self.progress = seeded
    }

    // MARK: - Katalog

    func home() async throws -> HomeResponse {
        try await pause()
        let cards = catalog.map { $0.card }
        var sections: [HomeSection] = []

        let hero = MockCatalog.heroIDs.compactMap { id in cards.first(where: { $0.id == id }) }
        sections.append(HomeSection(id: "hero", title: "Tavsiya", style: .hero, items: hero, continueItems: nil))

        let continueList = makeContinueItems()
        if !continueList.isEmpty {
            sections.append(HomeSection(id: "continue", title: "Davom ettirish", style: .continueWatching, items: [], continueItems: continueList))
        }

        let newest = catalog.sorted { $0.addedOrder > $1.addedOrder }.prefix(12).map { $0.card }
        sections.append(HomeSection(id: "new", title: "Yangi qo'shilganlar", style: .row, items: Array(newest), continueItems: nil))

        let popular = catalog.sorted { $0.views > $1.views }.prefix(12).map { $0.card }
        sections.append(HomeSection(id: "popular", title: "Ko'p ko'rilganlar", style: .row, items: Array(popular), continueItems: nil))

        let serials = cards.filter { $0.kind == .serial }
        sections.append(HomeSection(id: "serials", title: "Seriallar", style: .row, items: serials, continueItems: nil))

        let action = cards.filter { $0.genres.contains("Jangari") || $0.genres.contains("Sarguzasht") }
        sections.append(HomeSection(id: "genre:jangari", title: "Jangari", style: .row, items: action, continueItems: nil))

        let comedy = cards.filter { $0.genres.contains("Komediya") || $0.genres.contains("Oilaviy") }
        sections.append(HomeSection(id: "genre:komediya", title: "Komediya", style: .row, items: comedy, continueItems: nil))

        return HomeResponse(sections: sections)
    }

    func titles(kind: TitleKind?, genre: String?, sort: TitleSort?, cursor: String?, limit: Int) async throws -> TitlePage {
        try await pause()
        var list = catalog
        if let kind = kind {
            list = list.filter { $0.card.kind == kind }
        }
        if let slug = genre, let name = MockCatalog.genreName(for: slug) {
            list = list.filter { $0.card.genres.contains(name) }
        }
        switch sort ?? .new {
        case .new:
            list.sort { $0.addedOrder > $1.addedOrder }
        case .popular:
            list.sort { $0.views > $1.views }
        case .year:
            list.sort { ($0.card.year ?? 0) > ($1.card.year ?? 0) }
        }

        let pageSize = min(max(limit, 1), 50)
        let offset = max(0, Int(cursor ?? "") ?? 0)
        guard offset < list.count else {
            return TitlePage(items: [], nextCursor: nil)
        }
        let end = min(offset + pageSize, list.count)
        let page = list[offset..<end].map { $0.card }
        let next: String? = end < list.count ? String(end) : nil
        return TitlePage(items: page, nextCursor: next)
    }

    func titleDetail(id: Int) async throws -> TitleDetail {
        try await pause()
        guard let mock = catalog.first(where: { $0.card.id == id }) else {
            throw APIError(code: .notFound, message: "Kino topilmadi", status: 404)
        }
        return makeDetail(mock)
    }

    func genres() async throws -> [Genre] {
        try await pause()
        return MockCatalog.genres.map { entry in
            let count = catalog.filter { $0.card.genres.contains(entry.name) }.count
            return Genre(slug: entry.slug, name: entry.name, count: count)
        }
    }

    func search(query: String, limit: Int) async throws -> [TitleCard] {
        try await pause()
        let needle = MockKinoService.normalize(query)
        guard !needle.isEmpty else {
            throw APIError(code: .validationError, message: "Qidiruv so'zi bo'sh", status: 422)
        }
        let isNumber = Int(needle) != nil
        let matches = catalog.filter { mock in
            if isNumber && String(mock.code).hasPrefix(needle) {
                return true
            }
            if MockKinoService.normalize(mock.card.title).contains(needle) {
                return true
            }
            return mock.card.genres.contains { MockKinoService.normalize($0).contains(needle) }
        }
        return Array(matches.prefix(max(limit, 1)).map { $0.card })
    }

    // MARK: - Ijro

    func playback(titleID: Int, episodeID: Int?) async throws -> PlaybackInfo {
        try await pause()
        guard let mock = catalog.first(where: { $0.card.id == titleID }) else {
            throw APIError(code: .notFound, message: "Kino topilmadi", status: 404)
        }
        if mock.card.isPremium {
            throw APIError(code: .premiumRequired, message: "Bu kino Premium obunachilar uchun", status: 403)
        }
        if !mock.isAvailable {
            throw APIError(code: .unavailable, message: "Bu video hozircha mavjud emas", status: 409)
        }
        if mock.card.kind == .serial {
            guard let episodeID = episodeID else {
                throw APIError(code: .validationError, message: "Qism tanlanmagan", status: 422)
            }
            let episode = mock.seasons.flatMap { $0.episodes }.first(where: { $0.id == episodeID })
            guard let found = episode, found.isAvailable else {
                throw APIError(code: .unavailable, message: "Bu qism hali mavjud emas", status: 409)
            }
        }
        var resume = 0
        if let entry = progress[MockKinoService.key(titleID, episodeID)], !entry.isFinished {
            resume = entry.position
        }
        return PlaybackInfo(
            streamUrl: MockCatalog.streamURL,
            expiresAt: Date().addingTimeInterval(6 * 3_600),
            resumePositionSec: resume
        )
    }

    // MARK: - Foydalanuvchi

    func me() async throws -> UserInfo {
        try await pause()
        return UserInfo(id: 1, createdAt: Date())
    }

    func favorites() async throws -> [TitleCard] {
        try await pause()
        return favoriteOrder.compactMap { id in catalog.first(where: { $0.card.id == id })?.card }
    }

    func setFavorite(titleID: Int, isFavorite: Bool) async throws {
        try await pause()
        favoriteOrder.removeAll { $0 == titleID }
        if isFavorite {
            favoriteOrder.insert(titleID, at: 0)
        }
    }

    func continueWatching() async throws -> [ContinueItem] {
        try await pause()
        return makeContinueItems()
    }

    func reportProgress(_ report: ProgressReport) async throws {
        let entry = ProgressEntry(
            titleID: report.titleId,
            episodeID: report.episodeId,
            position: max(0, report.positionSec),
            duration: max(0, report.durationSec),
            updatedAt: Date()
        )
        progress[MockKinoService.key(report.titleId, report.episodeId)] = entry
    }

    // MARK: - Ichki yordamchilar

    private func pause() async throws {
        guard latency > 0 else { return }
        try await Task.sleep(nanoseconds: latency)
    }

    private static func key(_ titleID: Int, _ episodeID: Int?) -> String {
        "\(titleID)-\(episodeID ?? 0)"
    }

    private static func normalize(_ text: String) -> String {
        let folded = text.folding(options: [.caseInsensitive, .diacriticInsensitive], locale: nil)
        let removed = folded.filter { !"'`ʻʼ‘’".contains($0) }
        return removed.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func makeContinueItems() -> [ContinueItem] {
        let active = progress.values
            .filter { !$0.isFinished && $0.position > 0 }
            .sorted { $0.updatedAt > $1.updatedAt }
        var items: [ContinueItem] = []
        for entry in active.prefix(20) {
            guard let mock = catalog.first(where: { $0.card.id == entry.titleID }) else { continue }
            var label: String?
            if let episodeID = entry.episodeID {
                for season in mock.seasons {
                    if let episode = season.episodes.first(where: { $0.id == episodeID }) {
                        label = "\(season.number)-fasl, \(episode.number)-qism"
                    }
                }
            }
            items.append(
                ContinueItem(
                    title: mock.card,
                    episodeId: entry.episodeID,
                    episodeLabel: label,
                    positionSec: entry.position,
                    durationSec: entry.duration,
                    updatedAt: entry.updatedAt
                )
            )
        }
        return items
    }

    private func makeDetail(_ mock: MockTitle) -> TitleDetail {
        let entries = progress.values
            .filter { $0.titleID == mock.card.id }
            .sorted { $0.updatedAt > $1.updatedAt }

        var watch: WatchProgress?
        if let latest = entries.first(where: { !$0.isFinished && $0.position > 0 }) {
            watch = WatchProgress(episodeId: latest.episodeID, positionSec: latest.position, durationSec: latest.duration)
        }

        let seasons = mock.seasons.map { season -> Season in
            let episodes = season.episodes.map { episode -> Episode in
                let saved = progress[MockKinoService.key(mock.card.id, episode.id)]?.position ?? 0
                return Episode(
                    id: episode.id,
                    number: episode.number,
                    title: episode.title,
                    durationSec: episode.durationSec,
                    isAvailable: episode.isAvailable,
                    progressSec: saved
                )
            }
            return Season(id: season.id, number: season.number, title: season.title, episodes: episodes)
        }

        let card = mock.card
        return TitleDetail(
            id: card.id,
            kind: card.kind,
            title: card.title,
            year: card.year,
            genres: card.genres,
            posterUrl: card.posterUrl,
            backdropUrl: card.backdropUrl,
            isPremium: card.isPremium,
            quality: card.quality,
            durationSec: card.durationSec,
            code: mock.code,
            overview: mock.overview,
            language: mock.language,
            views: mock.views,
            isFavorite: favoriteOrder.contains(card.id),
            isAvailable: mock.isAvailable,
            progress: watch,
            seasons: seasons
        )
    }
}
