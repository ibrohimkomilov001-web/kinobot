import SwiftUI
import Observation

/// Pleyerga uzatiladigan tayyor ijro sessiyasi
struct PlaybackSession: Identifiable {
    let id = UUID()
    let title: TitleCard
    let episodeID: Int?
    let episodeLabel: String?
    let durationHint: Int?
    let info: PlaybackInfo
}

/// "Premium kerak" oynasi uchun
struct PremiumPrompt: Identifiable {
    let id = UUID()
    let titleName: String
}

/// Ilova bo'ylab umumiy holat: servis, sevimlilar, ijro oqimi, toast xabarlar.
@MainActor
@Observable
final class AppState {
    let service: any KinoService
    let isDemo: Bool

    var favoriteIDs: Set<Int> = []
    /// Sevimlilar serverda o'zgargach oshiriladi (Saqlanganlar ro'yxati yangilanadi)
    private(set) var favoritesVersion = 0
    /// Pleyer yopilib progress yuborilgach oshiriladi (davom ettirish ro'yxatlari yangilanadi)
    private(set) var playbackEndedTick = 0
    /// Qaysi kino uchun ijro tayyorlanmoqda (tugmada spinner)
    private(set) var preparingTitleID: Int? = nil
    /// Premium talab qilgan kinolar (tugmada qulf belgisi)
    private(set) var lockedTitleIDs: Set<Int> = []

    var activePlayback: PlaybackSession? = nil
    var premiumPrompt: PremiumPrompt? = nil
    var playbackErrorMessage: String? = nil
    var toastMessage: String? = nil
    @ObservationIgnored private var didBootstrap = false
    @ObservationIgnored private var pendingFavoriteOps = 0

    init(service: any KinoService, isDemo: Bool) {
        self.service = service
        self.isDemo = isDemo
    }

    static func makeDefault() -> AppState {
        if let baseURL = AppConfig.apiBaseURL {
            return AppState(service: LiveKinoService(baseURL: baseURL), isDemo: false)
        }
        return AppState(service: MockKinoService(), isDemo: true)
    }

    static var preview: AppState {
        AppState(service: MockKinoService(latency: 0), isDemo: true)
    }

    // MARK: - Ishga tushish

    func bootstrap() async {
        guard !didBootstrap else { return }
        didBootstrap = true
        let items = try? await service.favorites()
        if let items = items {
            adoptServerFavorites(items.map { $0.id })
        }
    }

    // MARK: - Sevimlilar

    func isFavorite(_ id: Int) -> Bool {
        favoriteIDs.contains(id)
    }

    func syncFavorite(id: Int, isFavorite: Bool) {
        guard pendingFavoriteOps == 0 else { return }
        setLocalFavorite(id: id, isFavorite: isFavorite)
    }

    /// Server ro'yxatini haqiqat deb qabul qiladi (o'zgartirish jarayonda bo'lmasa)
    func adoptServerFavorites(_ ids: [Int]) {
        guard pendingFavoriteOps == 0 else { return }
        favoriteIDs = Set(ids)
    }

    /// Optimistik almashtirish: UI darhol yangilanadi, xato bo'lsa qaytariladi
    func toggleFavorite(_ card: TitleCard) {
        setFavorite(card, isFavorite: !favoriteIDs.contains(card.id))
    }

    /// PUT/DELETE /v1/me/favorites/{id} — optimistik
    func setFavorite(_ card: TitleCard, isFavorite newValue: Bool) {
        let previousValue = favoriteIDs.contains(card.id)
        setLocalFavorite(id: card.id, isFavorite: newValue)
        pendingFavoriteOps += 1
        let service = self.service
        Task {
            do {
                try await service.setFavorite(titleID: card.id, isFavorite: newValue)
                pendingFavoriteOps -= 1
                favoritesVersion += 1
                showToast(newValue ? "Saqlanganlarga qo'shildi" : "Saqlanganlardan olib tashlandi")
            } catch {
                pendingFavoriteOps -= 1
                setLocalFavorite(id: card.id, isFavorite: previousValue)
                if !(error is CancellationError) {
                    showToast(ErrorText.message(for: error))
                }
            }
        }
    }

    private func setLocalFavorite(id: Int, isFavorite: Bool) {
        if isFavorite {
            favoriteIDs.insert(id)
        } else {
            favoriteIDs.remove(id)
        }
    }

    // MARK: - Ijro

    func isPreparing(_ titleID: Int) -> Bool {
        preparingTitleID == titleID
    }

    func isLocked(_ titleID: Int) -> Bool {
        lockedTitleIDs.contains(titleID)
    }

    /// POST /v1/playback → muvaffaqiyatli bo'lsa pleyer ochiladi.
    /// Serial uchun qism berilmasa — davom ettirish yoki birinchi mavjud qism tanlanadi.
    func play(_ card: TitleCard, episodeID: Int? = nil, episodeLabel: String? = nil, durationHint: Int? = nil) {
        guard preparingTitleID == nil, activePlayback == nil else { return }
        preparingTitleID = card.id
        let service = self.service
        Task {
            defer { preparingTitleID = nil }
            do {
                var chosenEpisode = episodeID
                var chosenLabel = episodeLabel
                var chosenDuration = durationHint ?? card.durationSec

                if card.kind == .serial && chosenEpisode == nil {
                    let detail = try await service.titleDetail(id: card.id)
                    guard let ref = detail.resumeEpisode else {
                        throw APIError(code: .unavailable, message: "Bu serialning qismlari hali mavjud emas.")
                    }
                    chosenEpisode = ref.episode.id
                    chosenLabel = ref.label
                    chosenDuration = ref.episode.durationSec
                }

                let info = try await service.playback(titleID: card.id, episodeID: chosenEpisode)
                activePlayback = PlaybackSession(
                    title: card,
                    episodeID: chosenEpisode,
                    episodeLabel: chosenLabel,
                    durationHint: chosenDuration,
                    info: info
                )
            } catch let apiError as APIError where apiError.code == .premiumRequired {
                lockedTitleIDs.insert(card.id)
                premiumPrompt = PremiumPrompt(titleName: card.title)
            } catch is CancellationError {
                // bekor qilindi — hech narsa qilmaymiz
            } catch {
                playbackErrorMessage = ErrorText.message(for: error)
            }
        }
    }

    /// Pleyer yopilganda: yakuniy progressni yuboradi (UI'ni bloklamaydi), keyin ro'yxatlarni yangilaydi
    func finishPlayback(report: ProgressReport?) {
        let service = self.service
        Task {
            if let report = report {
                try? await service.reportProgress(report)
            }
            playbackEndedTick += 1
        }
    }

    // MARK: - Toast

    func showToast(_ message: String) {
        toastMessage = message
    }

    func clearToast(ifMatches message: String?) {
        if toastMessage == message {
            toastMessage = nil
        }
    }
}
