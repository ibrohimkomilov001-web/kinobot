import SwiftUI

/// Rasm (AsyncImage) + gradient o'rinbosar. Berilgan joyni to'liq egallaydi.
struct ArtworkView: View {
    let url: URL?
    let title: String
    let seed: Int
    var showsInitials: Bool = true

    var body: some View {
        Rectangle()
            .fill(Theme.placeholderGradient(seed: seed))
            .overlay {
                if showsInitials {
                    placeholderMark
                }
            }
            .overlay {
                if let url = url {
                    AsyncImage(url: url, transaction: Transaction(animation: .easeOut(duration: 0.25))) { phase in
                        if let image = phase.image {
                            image
                                .resizable()
                                .scaledToFill()
                        } else {
                            Color.clear
                        }
                    }
                }
            }
            .clipped()
    }

    private var placeholderMark: some View {
        VStack(spacing: 6) {
            Image(systemName: "film")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(Theme.accent.opacity(0.45))
            Text(Formatters.initials(title))
                .font(.system(size: 30, weight: .black, design: .rounded))
                .foregroundStyle(Theme.accentGradient)
                .opacity(0.55)
                .lineLimit(1)
                .minimumScaleFactor(0.4)
        }
        .padding(8)
    }
}

/// Vertikal 2:3 poster
struct PosterView: View {
    let card: TitleCard
    var cornerRadius: CGFloat = 14

    var body: some View {
        ArtworkView(url: card.posterImageURL ?? card.backdropImageURL, title: card.title, seed: card.id)
            .aspectRatio(2.0 / 3.0, contentMode: .fit)
            .clipShape(.rect(cornerRadius: cornerRadius))
            .overlay {
                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(Theme.stroke, lineWidth: 1)
            }
            .overlay(alignment: .topTrailing) {
                if card.isPremium {
                    PremiumBadge(compact: true)
                        .padding(6)
                }
            }
    }
}

/// Poster + sarlavha; bosilganda Detail sahifasiga zoom o'tish bilan ochiladi
struct PosterLink: View {
    let card: TitleCard
    let sourceID: String
    let zoom: Namespace.ID
    var width: CGFloat? = nil

    var body: some View {
        NavigationLink(value: TitleRoute(card: card, sourceID: sourceID)) {
            VStack(alignment: .leading, spacing: 6) {
                poster
                Text(card.title)
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(Theme.textPrimary)
                    .lineLimit(1)
                Text(card.subtitleLine)
                    .font(.caption2)
                    .foregroundStyle(Theme.textSecondary)
                    .lineLimit(1)
            }
            .frame(width: width, alignment: .leading)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private var poster: some View {
        if let width = width {
            PosterView(card: card)
                .frame(width: width, height: width * 1.5)
                .matchedTransitionSource(id: sourceID, in: zoom)
        } else {
            PosterView(card: card)
                .matchedTransitionSource(id: sourceID, in: zoom)
        }
    }
}

enum PosterGrid {
    static var columns: [GridItem] {
        [GridItem(.adaptive(minimum: 104, maximum: 170), spacing: 12, alignment: .top)]
    }
}
