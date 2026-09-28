import Foundation

// MARK: - Genre

struct Genre: Decodable, Hashable, Identifiable, Sendable {
    let slug: String
    let name: String
    let count: Int

    var id: String { slug }

    enum CodingKeys: String, CodingKey {
        case slug, name, count
    }
}

extension Genre {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        slug = try c.decode(String.self, forKey: .slug)
        name = c.optionalString(.name) ?? slug
        count = c.flexibleInt(.count) ?? 0
    }
}

// MARK: - ContinueItem

struct ContinueItem: Decodable, Hashable, Identifiable, Sendable {
    let title: TitleCard
    let episodeId: Int?
    let episodeLabel: String?
    let positionSec: Int
    let durationSec: Int
    let updatedAt: Date?

    var id: String { "\(title.id)-\(episodeId ?? 0)" }

    var fraction: Double {
        guard durationSec > 0 else { return 0 }
        return min(1, max(0, Double(positionSec) / Double(durationSec)))
    }

    enum CodingKeys: String, CodingKey {
        case title, episodeId, episodeLabel, positionSec, durationSec, updatedAt
    }
}

extension ContinueItem {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        title = try c.decode(TitleCard.self, forKey: .title)
        episodeId = c.flexibleInt(.episodeId)
        episodeLabel = c.optionalString(.episodeLabel)
        positionSec = c.flexibleInt(.positionSec) ?? 0
        durationSec = c.flexibleInt(.durationSec) ?? 0
        updatedAt = try? c.decodeIfPresent(Date.self, forKey: .updatedAt)
    }
}

// MARK: - Home

enum SectionStyle: String, Hashable, Sendable {
    case hero
    case row
    case continueWatching = "continue"
    case unknown
}

extension SectionStyle: Decodable {
    init(from decoder: Decoder) throws {
        let raw = try decoder.singleValueContainer().decode(String.self)
        self = SectionStyle(rawValue: raw) ?? .unknown
    }
}

struct HomeSection: Decodable, Hashable, Identifiable, Sendable {
    let id: String
    let title: String
    let style: SectionStyle
    let items: [TitleCard]
    let continueItems: [ContinueItem]?

    enum CodingKeys: String, CodingKey {
        case id, title, style, items, continueItems
    }
}

extension HomeSection {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        title = c.optionalString(.title) ?? ""
        style = (try? c.decodeIfPresent(SectionStyle.self, forKey: .style)) ?? .row
        items = c.lossyArray(TitleCard.self, forKey: .items)
        if c.contains(.continueItems) {
            continueItems = c.lossyArray(ContinueItem.self, forKey: .continueItems)
        } else {
            continueItems = nil
        }
    }
}

struct HomeResponse: Decodable, Sendable {
    let sections: [HomeSection]

    enum CodingKeys: String, CodingKey {
        case sections
    }
}

extension HomeResponse {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        sections = c.lossyArray(HomeSection.self, forKey: .sections)
    }
}

// MARK: - Ro'yxatlar

enum TitleSort: String, Hashable, Sendable {
    case new
    case popular
    case year
}

struct TitlePage: Decodable, Sendable {
    let items: [TitleCard]
    let nextCursor: String?

    enum CodingKeys: String, CodingKey {
        case items, nextCursor
    }
}

extension TitlePage {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        items = c.lossyArray(TitleCard.self, forKey: .items)
        let cursor = c.optionalString(.nextCursor)
        nextCursor = (cursor?.isEmpty ?? true) ? nil : cursor
    }
}

/// `{ "items": [...] }` ko'rinishidagi javoblar uchun
struct ItemsResponse<Item: Decodable>: Decodable {
    let items: [Item]

    enum CodingKeys: String, CodingKey {
        case items
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        items = c.lossyArray(Item.self, forKey: .items)
    }
}
