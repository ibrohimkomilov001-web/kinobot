import Foundation
import Observation

@MainActor
@Observable
final class HomeViewModel {
    private(set) var sections: [HomeSection] = []
    private(set) var isLoading = false
    private(set) var errorMessage: String? = nil
    private let service: any KinoService
    @ObservationIgnored private var hasLoaded = false

    init(service: any KinoService) {
        self.service = service
    }

    func loadIfNeeded() async {
        guard !hasLoaded, !isLoading else { return }
        await reload()
    }

    func reload() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await service.home()
            sections = response.sections
            errorMessage = nil
            hasLoaded = true
        } catch is CancellationError {
            // ko'rinish yopildi — keyingi safar qayta yuklanadi
        } catch {
            errorMessage = ErrorText.message(for: error)
        }
    }
}
