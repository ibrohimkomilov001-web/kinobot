import SwiftUI

/// Janr / turkum bo'yicha sahifalangan poster panjarasi
struct TitleGridView: View {
    @State private var model: TitleGridViewModel
    let zoom: Namespace.ID

    init(query: CatalogQuery, service: any KinoService, zoom: Namespace.ID) {
        _model = State(initialValue: TitleGridViewModel(query: query, service: service))
        self.zoom = zoom
    }

    var body: some View {
        ScrollView {
            content
        }
        .background { AppBackground() }
        .navigationTitle(model.query.title)
        .navigationBarTitleDisplayMode(.large)
        .refreshable {
            await model.reload()
        }
        .task {
            await model.loadIfNeeded()
        }
    }

    @ViewBuilder
    private var content: some View {
        if model.items.isEmpty {
            if let message = model.errorMessage, !model.isLoading {
                ErrorStateView(message: message) {
                    Task { await model.reload() }
                }
                .padding(.top, 60)
            } else if model.hasLoaded && !model.isLoading {
                EmptyStateView(title: "Hech narsa topilmadi", systemImage: "film.stack")
                    .padding(.top, 60)
            } else {
                LazyVGrid(columns: PosterGrid.columns, spacing: 18) {
                    ForEach(0..<9, id: \.self) { _ in
                        SkeletonBlock()
                            .aspectRatio(2.0 / 3.0, contentMode: .fit)
                    }
                }
                .padding(16)
            }
        } else {
            LazyVGrid(columns: PosterGrid.columns, alignment: .leading, spacing: 18) {
                ForEach(model.items) { card in
                    PosterLink(card: card, sourceID: "grid-\(model.query.id)-\(card.id)", zoom: zoom)
                        .onAppear {
                            model.itemAppeared(card)
                        }
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)

            if model.isLoadingMore {
                ProgressView()
                    .tint(Theme.accent)
                    .padding(.vertical, 20)
            }
            Color.clear
                .frame(height: 24)
        }
    }
}
