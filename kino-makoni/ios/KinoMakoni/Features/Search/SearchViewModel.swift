import Foundation
import Observation

@MainActor
@Observable
final class SearchViewModel {
    var query = ""

    private(set) var results: [TitleCard] = []
    private(set) var isSearching = false
    private(set) var hasSearched = false
    private(set) var searchError: String? = nil
    private(set) var genres: [Genre] = []
    private(set) var isLoadingGenres = false
    private(set) var genresError: String? = nil
    private let service: any KinoService

    init(service: any KinoService) {
        self.service = service
    }

    var trimmedQuery: String {
        query.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Qidiruv (debounce ~350ms; .task(id:) oldingi vazifani bekor qiladi)

    func search() async {
        let text = trimmedQuery
        guard !text.isEmpty else {
            results = []
            isSearching = false
            hasSearched = false
            searchError = nil
            return
        }
        isSearching = true
        do {
            try await Task.sleep(nanoseconds: 350_000_000)
        } catch {
            return
        }
        await performSearch(text)
    }

    func retrySearch() async {
        await performSearch(trimmedQuery)
    }

    private func performSearch(_ text: String) async {
        guard !text.isEmpty else { return }
        isSearching = true
        searchError = nil
        do {
            let items = try await service.search(query: text, limit: 30)
            guard text == trimmedQuery else { return }
            results = items
            hasSearched = true
            isSearching = false
        } catch is CancellationError {
            // yangi so'rov boshlandi
        } catch {
            guard text == trimmedQuery else { return }
            results = []
            searchError = ErrorText.message(for: error)
            hasSearched = true
            isSearching = false
        }
    }

    // MARK: - Janrlar

    func loadGenresIfNeeded() async {
        guard genres.isEmpty, !isLoadingGenres else { return }
        await loadGenres()
    }

    func loadGenres() async {
        isLoadingGenres = true
        defer { isLoadingGenres = false }
        do {
            genres = try await service.genres()
            genresError = nil
        } catch is CancellationError {
        } catch {
            genresError = ErrorText.message(for: error)
        }
    }
}
