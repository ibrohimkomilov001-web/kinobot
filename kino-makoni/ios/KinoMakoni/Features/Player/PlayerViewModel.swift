import Foundation
import AVFoundation
import Observation

/// AVPlayer hayot sikli, davom ettirish va progress yuborish (har ~15 soniyada)
@MainActor
@Observable
final class PlayerViewModel {
    let session: PlaybackSession

    private(set) var player: AVPlayer? = nil
    private(set) var errorMessage: String? = nil
    private(set) var isBuffering = true

    private let service: any KinoService
    @ObservationIgnored private var info: PlaybackInfo
    @ObservationIgnored private var timeObserver: Any? = nil
    @ObservationIgnored private var statusObservation: NSKeyValueObservation? = nil
    @ObservationIgnored private var didStartPlayback = false
    @ObservationIgnored private var lastReportDate = Date.distantPast
    @ObservationIgnored private var isStopped = false

    init(session: PlaybackSession, service: any KinoService) {
        self.session = session
        self.service = service
        self.info = session.info
    }

    var titleText: String {
        if let label = session.episodeLabel, !label.isEmpty {
            return "\(session.title.title) · \(label)"
        }
        return session.title.title
    }

    // MARK: - Hayot sikli

    func start() {
        guard player == nil, !isStopped else { return }
        guard let url = info.streamURL else {
            isBuffering = false
            errorMessage = "Video manzili noto'g'ri."
            return
        }
        try? AVAudioSession.sharedInstance().setActive(true)

        let item = AVPlayerItem(url: url)
        let newPlayer = AVPlayer(playerItem: item)
        newPlayer.allowsExternalPlayback = true
        observeStatus(of: item)
        addTimeObserver(to: newPlayer)
        didStartPlayback = false
        player = newPlayer
    }

    /// Pleyerni to'xtatadi va yakuniy progress hisobotini qaytaradi (yuborish — chaqiruvchida)
    func stop() -> ProgressReport? {
        guard !isStopped else { return nil }
        isStopped = true
        var report: ProgressReport? = nil
        if let current = player {
            report = makeReport(position: current.currentTime().seconds)
        }
        tearDownPlayer()
        return report
    }

    func retry() async {
        guard !isStopped else { return }
        tearDownPlayer()
        errorMessage = nil
        isBuffering = true
        do {
            info = try await service.playback(titleID: session.title.id, episodeID: session.episodeID)
            start()
        } catch is CancellationError {
        } catch {
            isBuffering = false
            errorMessage = ErrorText.message(for: error)
        }
    }

    // MARK: - Kuzatuvchilar

    private func observeStatus(of item: AVPlayerItem) {
        statusObservation = item.observe(\.status, options: [.initial, .new]) { [weak self] observedItem, _ in
            let status = observedItem.status
            let errorText = observedItem.error?.localizedDescription
            guard let owner = self else { return }
            Task { @MainActor in
                owner.handle(status: status, errorText: errorText)
            }
        }
    }

    private func handle(status: AVPlayerItem.Status, errorText: String?) {
        switch status {
        case .readyToPlay:
            isBuffering = false
            guard !didStartPlayback, let current = player else { return }
            didStartPlayback = true
            let resume = info.resumePositionSec
            if resume > 5 {
                current.seek(to: CMTime(seconds: Double(resume), preferredTimescale: 600))
            }
            current.play()
        case .failed:
            isBuffering = false
            errorMessage = errorText ?? "Videoni yuklab bo'lmadi."
        case .unknown:
            break
        @unknown default:
            break
        }
    }

    private func addTimeObserver(to player: AVPlayer) {
        let interval = CMTime(seconds: 15, preferredTimescale: 1)
        timeObserver = player.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            let seconds = time.seconds
            guard let owner = self else { return }
            Task { @MainActor in
                owner.periodicTick(position: seconds)
            }
        }
    }

    private func periodicTick(position: Double) {
        guard !isStopped else { return }
        // Seek/pauza paytida kuzatuvchi tez-tez chaqirilishi mumkin — 10 soniyada bir martadan ko'p emas
        guard Date().timeIntervalSince(lastReportDate) >= 10 else { return }
        guard let report = makeReport(position: position) else { return }
        lastReportDate = Date()
        let service = self.service
        Task {
            try? await service.reportProgress(report)
        }
    }

    private func makeReport(position: Double) -> ProgressReport? {
        guard position.isFinite, position >= 1 else { return nil }
        var duration: Double = 0
        if let itemDuration = player?.currentItem?.duration.seconds, itemDuration.isFinite, itemDuration > 0 {
            duration = itemDuration
        } else if let hint = session.durationHint, hint > 0 {
            duration = Double(hint)
        }
        guard duration > 0 else { return nil }
        let clamped = min(position, duration)
        return ProgressReport(
            titleId: session.title.id,
            episodeId: session.episodeID,
            positionSec: Int(clamped.rounded()),
            durationSec: Int(duration.rounded())
        )
    }

    private func tearDownPlayer() {
        if let current = player {
            current.pause()
            if let token = timeObserver {
                current.removeTimeObserver(token)
            }
            current.replaceCurrentItem(with: nil)
        }
        timeObserver = nil
        statusObservation?.invalidate()
        statusObservation = nil
        player = nil
    }
}
