import Foundation

// MARK: - Playback

struct PlaybackInfo: Decodable, Hashable, Sendable {
    let streamUrl: String
    let expiresAt: Date?
    let resumePositionSec: Int

    var streamURL: URL? { URLSanitizer.url(streamUrl) }

    enum CodingKeys: String, CodingKey {
        case streamUrl, expiresAt, resumePositionSec
    }
}

extension PlaybackInfo {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        streamUrl = try c.decode(String.self, forKey: .streamUrl)
        expiresAt = try? c.decodeIfPresent(Date.self, forKey: .expiresAt)
        resumePositionSec = c.flexibleInt(.resumePositionSec) ?? 0
    }
}

/// POST /v1/playback tanasi. `episode_id` har doim yuboriladi (kino uchun null).
struct PlaybackRequest: Encodable, Sendable {
    let titleId: Int
    let episodeId: Int?

    enum CodingKeys: String, CodingKey {
        case titleId = "title_id"
        case episodeId = "episode_id"
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(titleId, forKey: .titleId)
        if let episodeId = episodeId {
            try c.encode(episodeId, forKey: .episodeId)
        } else {
            try c.encodeNil(forKey: .episodeId)
        }
    }
}

/// PUT /v1/me/progress tanasi
struct ProgressReport: Encodable, Hashable, Sendable {
    let titleId: Int
    let episodeId: Int?
    let positionSec: Int
    let durationSec: Int

    enum CodingKeys: String, CodingKey {
        case titleId = "title_id"
        case episodeId = "episode_id"
        case positionSec = "position_sec"
        case durationSec = "duration_sec"
    }

    func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(titleId, forKey: .titleId)
        if let episodeId = episodeId {
            try c.encode(episodeId, forKey: .episodeId)
        } else {
            try c.encodeNil(forKey: .episodeId)
        }
        try c.encode(positionSec, forKey: .positionSec)
        try c.encode(durationSec, forKey: .durationSec)
    }
}

// MARK: - Auth / foydalanuvchi

struct DeviceAuthRequest: Encodable, Sendable {
    let deviceId: String
    let platform: String
    let appVersion: String

    enum CodingKeys: String, CodingKey {
        case deviceId = "device_id"
        case platform
        case appVersion = "app_version"
    }
}

struct UserInfo: Decodable, Hashable, Sendable {
    let id: Int
    let createdAt: Date?

    enum CodingKeys: String, CodingKey {
        case id, createdAt
    }
}

extension UserInfo {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(Int.self, forKey: .id)
        createdAt = try? c.decodeIfPresent(Date.self, forKey: .createdAt)
    }
}

struct AuthResponse: Decodable, Sendable {
    let accessToken: String
    let tokenType: String?
    let expiresIn: Int?
    let user: UserInfo?

    enum CodingKeys: String, CodingKey {
        case accessToken, tokenType, expiresIn, user
    }
}

extension AuthResponse {
    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        accessToken = try c.decode(String.self, forKey: .accessToken)
        tokenType = c.optionalString(.tokenType)
        expiresIn = c.flexibleInt(.expiresIn)
        user = try? c.decodeIfPresent(UserInfo.self, forKey: .user)
    }
}
