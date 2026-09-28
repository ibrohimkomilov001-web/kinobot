import SwiftUI

/// Qidiruv tabi (iOS 26: tab bar'dagi alohida Liquid Glass qidiruv tugmasi)
struct SearchView: View {
    @State private var model: SearchViewModel
    @Namespace private var zoom

    init(service: any KinoService) {
        _model = State(initialValue: SearchViewModel(service: service))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                if model.trimmedQuery.isEmpty {
                    GenreBrowseView(
                        genres: model.genres,
                        isLoading: model.isLoadingGenres,
                        errorMessage: model.genresError,
                        onRetry: {
                            Task { await model.loadGenres() }
                        }
                    )
                } else {
                    results
                }
            }
            .scrollDismissesKeyboard(.immediately)
            .background { AppBackground() }
            .navigationTitle("Qidiruv")
            .searchable(text: $model.query, prompt: "Kino, serial yoki kod")
            .task {
                await model.loadGenresIfNeeded()
            }
            .task(id: model.query) {
                await model.search()
            }
            .kinoDestinations(zoom: zoom)
        }
    }

    @ViewBuilder
    private var results: some View {
        if model.results.isEmpty {
            if model.isSearching || !model.hasSearched {
                ProgressView()
                    .controlSize(.large)
                    .tint(Theme.accent)
                    .frame(maxWidth: .infinity)
                    .padding(.top, 80)
            } else if let message = model.searchError {
                ErrorStateView(message: message) {
                    Task { await model.retrySearch() }
                }
                .padding(.top, 40)
            } else {
                EmptyStateView(
                    title: "Hech narsa topilmadi",
                    systemImage: "film.stack",
                    message: "Boshqa nom yoki kino kodini kiritib ko'ring"
                )
                .padding(.top, 40)
            }
        } else {
            LazyVGrid(columns: PosterGrid.columns, alignment: .leading, spacing: 18) {
                ForEach(model.results) { card in
                    PosterLink(card: card, sourceID: "search-\(card.id)", zoom: zoom)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .opacity(model.isSearching ? 0.6 : 1)
            .animation(.easeOut(duration: 0.2), value: model.isSearching)
        }
    }
}

#Preview {
    SearchView(service: MockKinoService(latency: 0))
        .environment(AppState.preview)
        .preferredColorScheme(.dark)
}
