import Foundation

// MARK: - TitleKind

enum TitleKind: String, Hashable, Sendable {
    case movie
    case serial
}

extension TitleKind: Decodable {
    init(from decoder: Decoder) throws {
        let raw = try decoder.singleValueContainer().decode(String.self)
        self = TitleKind(rawValue: raw) ?? .movie
    }
}

// MARK: - TitleCard (API: TitleCard)

struct TitleCard: Decodable, Hashable, Identifiable, Sendable {
    let id: Int
    let kind: TitleKind
    let title: String
    let year: Int?
    let genres: [String]
    let posterUrl: String?
    let backdropUrl: String?
    let isPremium: Bool
    let quality: String?
    let durationSec: Int?

    enum CodingKeys: String, CodingKey {
        case id, kind, title, year, genres, posterUrl, backdropUrl, isPremium, quality, durationSec
    }
}

extension TitleCard {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        kind = (try? c.decodeIfPresent(TitleKind.self, forKey: .kind)) ?? .movie
        title = c.optionalString(.title) ?? ""
        year = c.flexibleInt(.year)
        genres = (try? c.decodeIfPresent([String].self, forKey: .genres)) ?? []
        posterUrl = c.optionalString(.posterUrl)
        backdropUrl = c.optionalString(.backdropUrl)
        isPremium = c.flexibleBool(.isPremium, fallback: false)
        quality = c.optionalString(.quality)
        durationSec = c.flexibleInt(.durationSec)
    }

    var posterImageURL: URL? { URLSanitizer.url(posterUrl) }
    var backdropImageURL: URL? { URLSanitizer.url(backdropUrl) }

    /// Poster ostidagi qisqa satr: "2024 · Jangari" yoki "2025 · Serial"
    var subtitleLine: String {
        var parts: [String] = []
        if let year = year {
            parts.append(String(year))
        }
        if kind == .serial {
            parts.append("Serial")
        } else if let genre = genres.first {
            parts.append(genre)
        }
        return parts.joined(separator: " · ")
    }
}

// MARK: - TitleDetail (API: TitleCard + qo'shimcha maydonlar)

struct WatchProgress: Decodable, Hashable, Sendable {
    let episodeId: Int?
    let positionSec: Int
    let durationSec: Int?

    enum CodingKeys: String, CodingKey {
        case episodeId, positionSec, durationSec
    }
}

extension WatchProgress {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        episodeId = c.flexibleInt(.episodeId)
        positionSec = c.flexibleInt(.positionSec) ?? 0
        durationSec = c.flexibleInt(.durationSec)
    }
}

struct Episode: Decodable, Hashable, Identifiable, Sendable {
    let id: Int
    let number: Int
    let title: String?
    let durationSec: Int?
    let isAvailable: Bool
    let progressSec: Int

    enum CodingKeys: String, CodingKey {
        case id, number, title, durationSec, isAvailable, progressSec
    }
}

extension Episode {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        number = c.flexibleInt(.number) ?? 0
        title = c.optionalString(.title)
        durationSec = c.flexibleInt(.durationSec)
        isAvailable = c.flexibleBool(.isAvailable, fallback: true)
        progressSec = c.flexibleInt(.progressSec) ?? 0
    }

    var displayTitle: String {
        if let title = title, !title.isEmpty {
            return title
        }
        return "\(number)-qism"
    }

    var progressFraction: Double {
        guard let duration = durationSec, duration > 0, progressSec > 0 else { return 0 }
        return min(1, max(0, Double(progressSec) / Double(duration)))
    }
}

struct Season: Decodable, Hashable, Identifiable, Sendable {
    let id: Int
    let number: Int
    let title: String?
    let episodes: [Episode]

    enum CodingKeys: String, CodingKey {
        case id, number, title, episodes
    }
}

extension Season {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        number = c.flexibleInt(.number) ?? 0
        title = c.optionalString(.title)
        episodes = c.lossyArray(Episode.self, forKey: .episodes)
    }

    var displayTitle: String {
        if let title = title, !title.isEmpty {
            return title
        }
        return "\(number)-fasl"
    }
}

struct TitleDetail: Decodable, Hashable, Identifiable, Sendable {
    let id: Int
    let kind: TitleKind
    let title: String
    let year: Int?
    let genres: [String]
    let posterUrl: String?
    let backdropUrl: String?
    let isPremium: Bool
    let quality: String?
    let durationSec: Int?
    let code: Int?
    let overview: String?
    let language: String?
    let views: Int
    let isFavorite: Bool
    let isAvailable: Bool
    let progress: WatchProgress?
    let seasons: [Season]

    enum CodingKeys: String, CodingKey {
        case id, kind, title, year, genres, posterUrl, backdropUrl, isPremium, quality, durationSec
        case code
        case overview = "description"
        case language, views, isFavorite, isAvailable, progress, seasons
    }
}

extension TitleDetail {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        kind = (try? c.decodeIfPresent(TitleKind.self, forKey: .kind)) ?? .movie
        title = c.optionalString(.title) ?? ""
        year = c.flexibleInt(.year)
        genres = (try? c.decodeIfPresent([String].self, forKey: .genres)) ?? []
        posterUrl = c.optionalString(.posterUrl)
        backdropUrl = c.optionalString(.backdropUrl)
        isPremium = c.flexibleBool(.isPremium, fallback: false)
        quality = c.optionalString(.quality)
        durationSec = c.flexibleInt(.durationSec)
        code = c.flexibleInt(.code)
        overview = c.optionalString(.overview)
        language = c.optionalString(.language)
        views = c.flexibleInt(.views) ?? 0
        isFavorite = c.flexibleBool(.isFavorite, fallback: false)
        isAvailable = c.flexibleBool(.isAvailable, fallback: true)
        progress = try? c.decodeIfPresent(WatchProgress.self, forKey: .progress)
        seasons = c.lossyArray(Season.self, forKey: .seasons)
    }

    var card: TitleCard {
        TitleCard(
            id: id,
            kind: kind,
            title: title,
            year: year,
            genres: genres,
            posterUrl: posterUrl,
            backdropUrl: backdropUrl,
            isPremium: isPremium,
            quality: quality,
            durationSec: durationSec
        )
    }

    func episodeRef(id episodeID: Int) -> EpisodeRef? {
        for season in seasons {
            if let episode = season.episodes.first(where: { $0.id == episodeID }) {
                return EpisodeRef(season: season, episode: episode)
            }
        }
        return nil
    }

    var firstAvailableEpisode: EpisodeRef? {
        let orderedSeasons = seasons.sorted { $0.number < $1.number }
        for season in orderedSeasons {
            let orderedEpisodes = season.episodes.sorted { $0.number < $1.number }
            if let episode = orderedEpisodes.first(where: { $0.isAvailable }) {
                return EpisodeRef(season: season, episode: episode)
            }
        }
        return nil
    }

    /// Serialda "Ko'rish" bosilganda qaysi qism ochiladi
    var resumeEpisode: EpisodeRef? {
        if let episodeID = progress?.episodeId, let ref = episodeRef(id: episodeID) {
            return ref
        }
        return firstAvailableEpisode
    }
}

struct EpisodeRef: Hashable, Sendable {
    let season: Season
    let episode: Episode

    var label: String { "\(season.number)-fasl, \(episode.number)-qism" }
}
