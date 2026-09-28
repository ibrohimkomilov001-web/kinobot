import SwiftUI

/// To'liq ekranli pleyer (fullScreenCover ichida)
struct PlayerView: View {
    @Environment(AppState.self) private var app
    @Environment(\.dismiss) private var dismiss
    @State private var model: PlayerViewModel

    init(session: PlaybackSession, service: any KinoService) {
        _model = State(initialValue: PlayerViewModel(session: session, service: service))
    }

    var body: some View {
        ZStack {
            Color.black
                .ignoresSafeArea()

            if let player = model.player {
                PlayerControllerView(player: player)
                    .ignoresSafeArea()
            }

            if model.isBuffering && model.errorMessage == nil {
                ProgressView()
                    .controlSize(.large)
                    .tint(.white)
                    .allowsHitTesting(false)
            }

            if let message = model.errorMessage {
                PlayerErrorOverlay(
                    title: model.titleText,
                    message: message,
                    onRetry: {
                        Task { await model.retry() }
                    },
                    onClose: {
                        dismiss()
                    }
                )
            }
        }
        .overlay(alignment: .topTrailing) {
            closeButton
        }
        .statusBarHidden()
        .persistentSystemOverlays(.hidden)
        .onAppear {
            model.start()
        }
        .onDisappear {
            app.finishPlayback(report: model.stop())
        }
    }

    private var closeButton: some View {
        Button {
            dismiss()
        } label: {
            Image(systemName: "xmark")
                .font(.system(size: 15, weight: .bold))
                .foregroundStyle(.white)
                .frame(width: 22, height: 22)
        }
        .buttonStyle(.glass)
        .controlSize(.large)
        .padding(.top, 8)
        .padding(.trailing, 16)
        .accessibilityLabel("Yopish")
    }
}

/// Ijro xatosi uchun shisha oyna
struct PlayerErrorOverlay: View {
    let title: String
    let message: String
    let onRetry: () -> Void
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 14) {
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 34, weight: .semibold))
                .foregroundStyle(Theme.accent)
            Text("Videoni ijro etib bo'lmadi")
                .font(.headline)
                .foregroundStyle(Theme.textPrimary)
            Text(title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Theme.textSecondary)
                .lineLimit(1)
            Text(message)
                .font(.footnote)
                .foregroundStyle(Theme.textSecondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)

            GlassEffectContainer(spacing: 12) {
                HStack(spacing: 12) {
                    Button(action: onRetry) {
                        Label("Qayta urinish", systemImage: "arrow.clockwise")
                            .fontWeight(.bold)
                            .foregroundStyle(Theme.onAccent)
                    }
                    .buttonStyle(.glassProminent)
                    .tint(Theme.accent)

                    Button(action: onClose) {
                        Text("Yopish")
                            .fontWeight(.semibold)
                    }
                    .buttonStyle(.glass)
                }
                .controlSize(.large)
            }
            .padding(.top, 6)
        }
        .padding(24)
        .frame(maxWidth: 380)
        .glassEffect(.regular, in: .rect(cornerRadius: 28))
        .padding(24)
    }
}
