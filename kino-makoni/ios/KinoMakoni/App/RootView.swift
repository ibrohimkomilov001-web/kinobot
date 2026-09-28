import SwiftUI

enum AppTab: Hashable {
    case home
    case library
    case profile
    case search
}

/// Asosiy TabView (iOS 26 Liquid Glass tab bar, alohida qidiruv tabi)
struct RootView: View {
    @Environment(AppState.self) private var app
    @State private var selection: AppTab = .home

    var body: some View {
        @Bindable var state = app

        TabView(selection: $selection) {
            Tab("Bosh sahifa", systemImage: "house.fill", value: AppTab.home) {
                HomeView(service: app.service)
            }
            Tab("Saqlanganlar", systemImage: "bookmark.fill", value: AppTab.library) {
                LibraryView(service: app.service)
            }
            Tab("Profil", systemImage: "person.crop.circle", value: AppTab.profile) {
                ProfileView(service: app.service)
            }
            Tab(value: AppTab.search, role: .search) {
                SearchView(service: app.service)
            }
        }
        .tabBarMinimizeBehavior(.onScrollDown)
        .overlay(alignment: .top) {
            ToastOverlay(message: app.toastMessage)
                .animation(.snappy, value: app.toastMessage)
        }
        .task {
            await app.bootstrap()
        }
        .task(id: app.toastMessage) {
            // Toast 2.4 soniyadan keyin yo'qoladi
            let shown = app.toastMessage
            guard shown != nil else { return }
            try? await Task.sleep(nanoseconds: 2_400_000_000)
            if !Task.isCancelled {
                withAnimation(.snappy) {
                    app.clearToast(ifMatches: shown)
                }
            }
        }
        .fullScreenCover(item: $state.activePlayback) { session in
            PlayerView(session: session, service: app.service)
                .environment(app)
        }
        .sheet(item: $state.premiumPrompt) { prompt in
            PremiumSheet(prompt: prompt)
        }
        .alert("Ijro etib bo'lmadi", isPresented: playbackErrorBinding) {
            Button("Yaxshi", role: .cancel) {}
        } message: {
            Text(app.playbackErrorMessage ?? "")
        }
    }

    private var playbackErrorBinding: Binding<Bool> {
        Binding(
            get: { app.playbackErrorMessage != nil },
            set: { isPresented in
                if !isPresented {
                    app.playbackErrorMessage = nil
                }
            }
        )
    }
}

#Preview {
    RootView()
        .environment(AppState.preview)
        .preferredColorScheme(.dark)
}
