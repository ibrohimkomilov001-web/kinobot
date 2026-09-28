import Foundation
import Observation

@MainActor
@Observable
final class LibraryViewModel {
    private(set) var favorites: [TitleCard] = []
    private(set) var continueItems: [ContinueItem] = []
    private(set) var isLoadingFavorites = false
    private(set) var isLoadingContinue = false
    private(set) var favoritesError: String? = nil
    private(set) var continueError: String? = nil
    private(set) var hasLoadedFavorites = false
    private(set) var hasLoadedContinue = false

    private let service: any KinoService

    init(service: any KinoService) {
        self.service = service
    }

    func loadIfNeeded() async {
        if !hasLoadedFavorites && !isLoadingFavorites {
            await reloadFavorites()
        }
        if !hasLoadedContinue && !isLoadingContinue {
            await reloadContinue()
        }
    }

    func reloadAll() async {
        await reloadFavorites()
        await reloadContinue()
    }

    func reloadFavorites() async {
        isLoadingFavorites = true
        defer { isLoadingFavorites = false }
        do {
            favorites = try await service.favorites()
            favoritesError = nil
            hasLoadedFavorites = true
        } catch is CancellationError {
        } catch {
            favoritesError = ErrorText.message(for: error)
        }
    }

    func reloadContinue() async {
        isLoadingContinue = true
        defer { isLoadingContinue = false }
        do {
            continueItems = try await service.continueWatching()
            continueError = nil
            hasLoadedContinue = true
        } catch is CancellationError {
        } catch {
            continueError = ErrorText.message(for: error)
        }
    }

    /// Optimistik: ro'yxatdan darhol olib tashlash
    func removeFavoriteLocally(_ id: Int) {
        favorites.removeAll { $0.id == id }
    }
}
