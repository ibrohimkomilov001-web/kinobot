import Foundation
import Observation

/// GET /v1/titles — cursor bo'yicha cheksiz ro'yxat
@MainActor
@Observable
final class TitleGridViewModel {
    let query: CatalogQuery

    private(set) var items: [TitleCard] = []
    private(set) var isLoading = false
    private(set) var isLoadingMore = false
    private(set) var errorMessage: String? = nil
    private(set) var hasLoaded = false

    private let service: any KinoService
    private let pageSize = 24
    @ObservationIgnored private var nextCursor: String? = nil
    @ObservationIgnored private var seenIDs: Set<Int> = []

    init(query: CatalogQuery, service: any KinoService) {
        self.query = query
        self.service = service
    }

    var canLoadMore: Bool { nextCursor != nil }

    func loadIfNeeded() async {
        guard !hasLoaded, !isLoading else { return }
        await reload()
    }

    func reload() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let page = try await service.titles(
                kind: query.kind,
                genre: query.genre,
                sort: query.sort,
                cursor: nil,
                limit: pageSize
            )
            var seen: Set<Int> = []
            var fresh: [TitleCard] = []
            for card in page.items where !seen.contains(card.id) {
                seen.insert(card.id)
                fresh.append(card)
            }
            seenIDs = seen
            items = fresh
            nextCursor = page.nextCursor
            errorMessage = nil
            hasLoaded = true
        } catch is CancellationError {
        } catch {
            errorMessage = ErrorText.message(for: error)
        }
    }

    /// Ro'yxat oxiriga yaqin element ko'ringanda keyingi sahifani yuklaydi
    func itemAppeared(_ card: TitleCard) {
        guard nextCursor != nil, !isLoadingMore, !isLoading else { return }
        guard let index = items.firstIndex(where: { $0.id == card.id }), index >= items.count - 6 else { return }
        Task { await loadMore() }
    }

    func loadMore() async {
        guard let cursor = nextCursor, !isLoadingMore, !isLoading else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        do {
            let page = try await service.titles(
                kind: query.kind,
                genre: query.genre,
                sort: query.sort,
                cursor: cursor,
                limit: pageSize
            )
            var fresh: [TitleCard] = []
            for card in page.items where !seenIDs.contains(card.id) {
                seenIDs.insert(card.id)
                fresh.append(card)
            }
            items.append(contentsOf: fresh)
            nextCursor = page.nextCursor
        } catch {
            // Keyingi safar qayta urinib ko'riladi
        }
    }
}
