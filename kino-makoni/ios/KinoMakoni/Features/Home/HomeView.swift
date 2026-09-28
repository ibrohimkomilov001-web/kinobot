import SwiftUI

/// Bosh sahifa: hero karusel, davom ettirish, poster qatorlari
struct HomeView: View {
    @Environment(AppState.self) private var app
    @State private var model: HomeViewModel
    @Namespace private var zoom

    private let heroHeight: CGFloat = 540

    init(service: any KinoService) {
        _model = State(initialValue: HomeViewModel(service: service))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                content
            }
            .ignoresSafeArea(edges: .top)
            .background { AppBackground() }
            .refreshable {
                await model.reload()
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    BrandTitle()
                }
            }
            .task {
                await model.loadIfNeeded()
            }
            .onChange(of: app.playbackEndedTick) { _, _ in
                Task { await model.reload() }
            }
            .kinoDestinations(zoom: zoom)
        }
    }

    @ViewBuilder
    private var content: some View {
        if model.sections.isEmpty {
            if let message = model.errorMessage, !model.isLoading {
                ErrorStateView(message: message) {
                    Task { await model.reload() }
                }
                .padding(.top, 160)
            } else {
                HomeSkeleton(heroHeight: heroHeight)
            }
        } else {
            LazyVStack(alignment: .leading, spacing: 30) {
                if model.sections.first?.style != .hero {
                    Color.clear
                        .frame(height: 100)
                }
                ForEach(model.sections) { section in
                    sectionView(section)
                }
            }
            .padding(.bottom, 40)
        }
    }

    @ViewBuilder
    private func sectionView(_ section: HomeSection) -> some View {
        switch section.style {
        case .hero:
            HeroCarousel(items: section.items, height: heroHeight, zoom: zoom)
        case .continueWatching:
            ContinueRow(title: section.title, items: section.continueItems ?? [])
        case .row, .unknown:
            PosterRow(section: section, zoom: zoom)
        }
    }
}

/// Oddiy gorizontal poster qatori
struct PosterRow: View {
    let section: HomeSection
    let zoom: Namespace.ID

    var body: some View {
        if !section.items.isEmpty {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeader(title: section.title, query: CatalogQuery.forSection(section))
                    .padding(.horizontal, 16)
                ScrollView(.horizontal, showsIndicators: false) {
                    LazyHStack(alignment: .top, spacing: 12) {
                        ForEach(section.items) { card in
                            PosterLink(
                                card: card,
                                sourceID: "row-\(section.id)-\(card.id)",
                                zoom: zoom,
                                width: 118
                            )
                        }
                    }
                    .scrollTargetLayout()
                }
                .contentMargins(.horizontal, 16, for: .scrollContent)
                .scrollTargetBehavior(.viewAligned)
            }
        }
    }
}

/// Bosh sahifa yuklanayotgandagi skelet
struct HomeSkeleton: View {
    let heroHeight: CGFloat

    var body: some View {
        VStack(alignment: .leading, spacing: 30) {
            SkeletonBlock(cornerRadius: 0)
                .frame(height: heroHeight)
            PosterRowSkeleton()
            PosterRowSkeleton()
        }
    }
}

#Preview {
    HomeView(service: MockKinoService(latency: 0))
        .environment(AppState.preview)
        .preferredColorScheme(.dark)
}
