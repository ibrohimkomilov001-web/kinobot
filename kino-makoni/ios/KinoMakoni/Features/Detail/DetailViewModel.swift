import Foundation
import Observation

@MainActor
@Observable
final class DetailViewModel {
    let initialCard: TitleCard

    private(set) var detail: TitleDetail? = nil
    private(set) var isLoading = false
    private(set) var errorMessage: String? = nil
    var selectedSeasonID: Int? = nil
    private let service: any KinoService

    init(card: TitleCard, service: any KinoService) {
        self.initialCard = card
        self.service = service
    }

    /// Yuklangan ma'lumot bo'lsa undan, bo'lmasa ro'yxatdagi kartadan
    var card: TitleCard {
        detail?.card ?? initialCard
    }

    /// Birinchi yuklash. Yangi ma'lumot kelgan bo'lsa uni qaytaradi.
    @discardableResult
    func loadIfNeeded() async -> TitleDetail? {
        guard detail == nil, !isLoading else { return nil }
        return await reload()
    }

    @discardableResult
    func reload() async -> TitleDetail? {
        isLoading = true
        defer { isLoading = false }
        do {
            let fresh = try await service.titleDetail(id: initialCard.id)
            detail = fresh
            errorMessage = nil
            if selectedSeasonID == nil || !fresh.seasons.contains(where: { $0.id == selectedSeasonID }) {
                selectedSeasonID = fresh.resumeEpisode?.season.id ?? fresh.seasons.first?.id
            }
            return fresh
        } catch is CancellationError {
            return nil
        } catch {
            if detail == nil {
                errorMessage = ErrorText.message(for: error)
            }
            return nil
        }
    }
}
