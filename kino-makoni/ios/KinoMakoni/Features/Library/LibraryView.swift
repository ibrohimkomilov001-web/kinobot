import SwiftUI

enum LibrarySegment: String, CaseIterable, Identifiable {
    case favorites
    case continueWatching

    var id: String { rawValue }

    var title: String {
        switch self {
        case .favorites: return "Saqlanganlar"
        case .continueWatching: return "Davom ettirish"
        }
    }
}

/// "Saqlanganlar" tabi: sevimlilar panjarasi va davom ettirish ro'yxati
struct LibraryView: View {
    @Environment(AppState.self) private var app
    @State private var model: LibraryViewModel
    @State private var segment: LibrarySegment = .favorites
    @Namespace private var zoom

    init(service: any KinoService) {
        _model = State(initialValue: LibraryViewModel(service: service))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Picker("Bo'lim", selection: $segment) {
                        ForEach(LibrarySegment.allCases) { item in
                            Text(item.title).tag(item)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal, 16)

                    switch segment {
                    case .favorites:
                        favoritesContent
                    case .continueWatching:
                        continueContent
                    }
                }
                .padding(.top, 8)
                .padding(.bottom, 32)
            }
            .background { AppBackground() }
            .navigationTitle("Saqlanganlar")
            .refreshable {
                await model.reloadAll()
            }
            .task {
                await model.loadIfNeeded()
                if model.hasLoadedFavorites {
                    app.adoptServerFavorites(model.favorites.map { $0.id })
                }
            }
            .onChange(of: app.favoritesVersion) { _, _ in
                Task { await model.reloadFavorites() }
            }
            .onChange(of: app.playbackEndedTick) { _, _ in
                Task { await model.reloadContinue() }
            }
            .kinoDestinations(zoom: zoom)
        }
    }

    // MARK: - Sevimlilar

    @ViewBuilder
    private var favoritesContent: some View {
        if model.favorites.isEmpty {
            if let message = model.favoritesError, !model.isLoadingFavorites {
                ErrorStateView(message: message) {
                    Task { await model.reloadFavorites() }
                }
                .padding(.top, 40)
            } else if !model.hasLoadedFavorites {
                ProgressView()
                    .tint(Theme.accent)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 80)
            } else {
                EmptyStateView(
                    title: "Hali hech narsa saqlanmagan",
                    systemImage: "bookmark",
                    message: "Kino sahifasidagi xatcho'p tugmasini bosib, uni shu yerga qo'shing."
                )
                .padding(.top, 40)
            }
        } else {
            LazyVGrid(columns: PosterGrid.columns, alignment: .leading, spacing: 18) {
                ForEach(model.favorites) { card in
                    PosterLink(card: card, sourceID: "fav-\(card.id)", zoom: zoom)
                        .contextMenu {
                            Button(role: .destructive) {
                                model.removeFavoriteLocally(card.id)
                                app.setFavorite(card, isFavorite: false)
                            } label: {
                                Label("Olib tashlash", systemImage: "bookmark.slash")
                            }
                        }
                }
            }
            .padding(.horizontal, 16)
        }
    }

    // MARK: - Davom ettirish

    @ViewBuilder
    private var continueContent: some View {
        if model.continueItems.isEmpty {
            if let message = model.continueError, !model.isLoadingContinue {
                ErrorStateView(message: message) {
                    Task { await model.reloadContinue() }
                }
                .padding(.top, 40)
            } else if !model.hasLoadedContinue {
                ProgressView()
                    .tint(Theme.accent)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 80)
            } else {
                EmptyStateView(
                    title: "Davom ettiriladigan kino yo'q",
                    systemImage: "play.circle",
                    message: "Ko'rishni boshlagan kinolaringiz shu yerda paydo bo'ladi."
                )
                .padding(.top, 40)
            }
        } else {
            LazyVStack(spacing: 10) {
                ForEach(model.continueItems) { item in
                    ContinueListRow(item: item)
                }
            }
            .padding(.horizontal, 16)
        }
    }
}

#Preview {
    LibraryView(service: MockKinoService(latency: 0))
        .environment(AppState.preview)
        .preferredColorScheme(.dark)
}
