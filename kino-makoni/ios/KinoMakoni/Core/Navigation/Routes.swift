import SwiftUI

/// Detail sahifasiga o'tish. `sourceID` — zoom o'tish manbasi (har bo'limda noyob).
struct TitleRoute: Hashable {
    let card: TitleCard
    let sourceID: String
}

/// Katalog ro'yxati (janr, turkum, "Hammasi")
struct CatalogQuery: Hashable, Identifiable {
    var title: String
    var kind: TitleKind? = nil
    var genre: String? = nil
    var sort: TitleSort? = nil
    var systemImage: String = "film"

    var id: String {
        "\(kind?.rawValue ?? "all")|\(genre ?? "all")|\(sort?.rawValue ?? "default")"
    }

    /// Bosh sahifa bo'limidan "Hammasi" so'rovi
    static func forSection(_ section: HomeSection) -> CatalogQuery? {
        switch section.id {
        case "new":
            return CatalogQuery(title: section.title, sort: .new)
        case "popular":
            return CatalogQuery(title: section.title, sort: .popular)
        case "serials":
            return CatalogQuery(title: section.title, kind: .serial)
        default:
            if section.id.hasPrefix("genre:") {
                let slug = String(section.id.dropFirst("genre:".count))
                return CatalogQuery(title: section.title, genre: slug)
            }
            return nil
        }
    }

    /// Qidiruv sahifasidagi tezkor turkumlar
    static var quickCategories: [CatalogQuery] {
        [
            CatalogQuery(title: "Kinolar", kind: .movie, systemImage: "film"),
            CatalogQuery(title: "Seriallar", kind: .serial, systemImage: "tv"),
            CatalogQuery(title: "Yangi qo'shilganlar", sort: .new, systemImage: "sparkles"),
            CatalogQuery(title: "Ko'p ko'rilganlar", sort: .popular, systemImage: "flame.fill")
        ]
    }
}

/// Har bir NavigationStack ildiziga ulanadigan umumiy yo'nalishlar
struct KinoDestinations: ViewModifier {
    let zoom: Namespace.ID
    @Environment(AppState.self) private var app

    func body(content: Content) -> some View {
        content
            .navigationDestination(for: TitleRoute.self) { route in
                DetailView(card: route.card, service: app.service)
                    .navigationTransition(.zoom(sourceID: route.sourceID, in: zoom))
            }
            .navigationDestination(for: CatalogQuery.self) { query in
                TitleGridView(query: query, service: app.service, zoom: zoom)
            }
    }
}

extension View {
    func kinoDestinations(zoom: Namespace.ID) -> some View {
        modifier(KinoDestinations(zoom: zoom))
    }
}
