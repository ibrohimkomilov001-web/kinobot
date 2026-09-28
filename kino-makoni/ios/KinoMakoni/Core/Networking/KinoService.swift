import Foundation

/// Backend bilan ishlash shartnomasi (docs/API.md). Jonli va demo (mock) amalga oshirishlari bor.
protocol KinoService: Sendable {
    /// GET /v1/home
    func home() async throws -> HomeResponse
    /// GET /v1/titles
    func titles(kind: TitleKind?, genre: String?, sort: TitleSort?, cursor: String?, limit: Int) async throws -> TitlePage
    /// GET /v1/titles/{id}
    func titleDetail(id: Int) async throws -> TitleDetail
    /// GET /v1/genres
    func genres() async throws -> [Genre]
    /// GET /v1/search?q=
    func search(query: String, limit: Int) async throws -> [TitleCard]
    /// POST /v1/playback
    func playback(titleID: Int, episodeID: Int?) async throws -> PlaybackInfo
    /// GET /v1/me
    func me() async throws -> UserInfo
    /// GET /v1/me/favorites
    func favorites() async throws -> [TitleCard]
    /// PUT / DELETE /v1/me/favorites/{title_id}
    func setFavorite(titleID: Int, isFavorite: Bool) async throws
    /// GET /v1/me/continue
    func continueWatching() async throws -> [ContinueItem]
    /// PUT /v1/me/progress
    func reportProgress(_ report: ProgressReport) async throws
}
