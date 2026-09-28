import SwiftUI

/// Qidiruv so'zi bo'sh bo'lganda: tezkor turkumlar + janr chiplari
struct GenreBrowseView: View {
    let genres: [Genre]
    let isLoading: Bool
    let errorMessage: String?
    let onRetry: () -> Void

    private let tileColumns = [
        GridItem(.flexible(), spacing: 12),
        GridItem(.flexible(), spacing: 12)
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 28) {
            VStack(alignment: .leading, spacing: 12) {
                Text("Turkumlar")
                    .font(.title3.weight(.bold))
                    .foregroundStyle(Theme.textPrimary)
                GlassEffectContainer(spacing: 12) {
                    LazyVGrid(columns: tileColumns, spacing: 12) {
                        ForEach(CatalogQuery.quickCategories) { query in
                            NavigationLink(value: query) {
                                CategoryTile(query: query)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }

            VStack(alignment: .leading, spacing: 12) {
                Text("Janrlar")
                    .font(.title3.weight(.bold))
                    .foregroundStyle(Theme.textPrimary)
                genreContent
            }
        }
        .padding(16)
    }

    @ViewBuilder
    private var genreContent: some View {
        if genres.isEmpty {
            if let message = errorMessage, !isLoading {
                ErrorStateView(message: message, retry: onRetry)
            } else {
                ProgressView()
                    .tint(Theme.accent)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 24)
            }
        } else {
            GlassEffectContainer(spacing: 10) {
                FlowLayout(spacing: 10, lineSpacing: 10) {
                    ForEach(genres) { genre in
                        NavigationLink(value: CatalogQuery(title: genre.name, genre: genre.slug)) {
                            GlassChip(title: genre.name, count: genre.count)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }
}

/// Turkum plitkasi (shisha, oltin tus bilan)
struct CategoryTile: View {
    let query: CatalogQuery

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: query.systemImage)
                .font(.title3.weight(.semibold))
                .foregroundStyle(Theme.accentGradient)
                .frame(width: 28)
            Text(query.title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(Theme.textPrimary)
                .lineLimit(2)
                .minimumScaleFactor(0.85)
                .multilineTextAlignment(.leading)
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 14)
        .frame(maxWidth: .infinity, minHeight: 64, alignment: .leading)
        .glassEffect(.regular.tint(Theme.accent.opacity(0.12)).interactive(), in: .rect(cornerRadius: 20))
        .contentShape(Rectangle())
    }
}
