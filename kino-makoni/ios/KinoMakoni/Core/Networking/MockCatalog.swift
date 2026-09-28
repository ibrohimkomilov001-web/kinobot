import Foundation

/// Demo rejim uchun ichki katalog (tarmoqsiz ishlaydi, rasmlar — gradient o'rinbosarlar).
struct MockTitle: Sendable {
    let card: TitleCard
    let code: Int
    let overview: String
    let language: String
    let views: Int
    let isAvailable: Bool
    let addedOrder: Int
    let seasons: [Season]
}

enum MockCatalog {
    /// Apple'ning ochiq test oqimi
    static let streamURL = "https://devstreaming-cdn.apple.com/videos/streaming/examples/img_bipbop_adv_example_fmp4/master.m3u8"

    static let genres: [(slug: String, name: String)] = [
        ("jangari", "Jangari"),
        ("fantastika", "Fantastika"),
        ("drama", "Drama"),
        ("komediya", "Komediya"),
        ("triller", "Triller"),
        ("sarguzasht", "Sarguzasht"),
        ("melodrama", "Melodrama"),
        ("tarixiy", "Tarixiy"),
        ("detektiv", "Detektiv"),
        ("oilaviy", "Oilaviy"),
        ("multfilm", "Multfilm"),
        ("qorqinchli", "Qo'rqinchli")
    ]

    static let heroIDs = [1, 18, 4, 5, 12]
    static let initialFavorites = [1, 19]

    static let previewCard = TitleCard(
        id: 1,
        kind: .movie,
        title: "Samarqand sirlari",
        year: 2024,
        genres: ["Sarguzasht", "Tarixiy"],
        posterUrl: nil,
        backdropUrl: nil,
        isPremium: false,
        quality: "1080p",
        durationSec: 7560
    )

    static func genreName(for slug: String) -> String? {
        genres.first(where: { $0.slug == slug })?.name
    }

    static func makeTitles() -> [MockTitle] {
        [
            movie(1, "Samarqand sirlari", 2024, ["Sarguzasht", "Tarixiy"], "1080p", 126, code: 1024, views: 48_210, order: 20,
                  "Yosh arxeolog Registon yaqinidagi qazishmalarda qadimiy xaritani topib oladi. Xarita uni asrlar davomida yashirib kelingan sirga — Amir Temur davridan qolgan yo'qolgan kutubxonaga yetaklaydi. Ammo bu sirni qidirayotgan yagona odam u emas."),
            movie(2, "Oxirgi poyezd", 2023, ["Triller", "Drama"], "1080p", 108, code: 1025, views: 31_540, order: 12,
                  "Toshkentdan Nukusga ketayotgan tungi poyezdda yo'lovchilardan biri g'oyib bo'ladi. Iste'fodagi tergovchi tong otguncha haqiqatni topishi kerak."),
            movie(3, "Tog'lar ortida", 2022, ["Drama", "Oilaviy"], "720p", 97, code: 1026, views: 12_870, order: 6,
                  "Shahardagi hayotdan charchagan oila bobosining Chimyondagi uyiga ko'chib o'tadi. Tog'lar ularga bir-birini qayta kashf etishni o'rgatadi."),
            movie(4, "Yulduzlar yo'li", 2025, ["Fantastika", "Sarguzasht"], "4K", 149, code: 1027, views: 57_300, order: 19, premium: true,
                  "2090-yil. Birinchi o'zbek kosmik ekspeditsiyasi Yupiterning yo'ldoshida qadimiy signalni qabul qiladi. Ekipaj uyga qaytish yoki noma'lumlikka qadam qo'yish orasida tanlov qilishi kerak."),
            movie(5, "Cho'l shamoli", 2021, ["Jangari", "Sarguzasht"], "1080p", 115, code: 1028, views: 39_910, order: 8,
                  "Qizilqum cho'lida adashib qolgan karvon va ularni ta'qib qilayotgan qaroqchilar. Yolg'iz sayyoh hammani qutqarish uchun o'z o'tmishiga qaytadi."),
            movie(6, "Qora quti", 2024, ["Detektiv", "Triller"], "1080p", 102, code: 1029, views: 22_450, order: 15,
                  "Samolyot halokatidan keyin topilgan qora qutidagi yozuvlar rasmiy versiyaga to'g'ri kelmaydi. Jurnalist qiz haqiqatni ochishga qaror qiladi."),
            movie(7, "Ikki yurak", 2020, ["Melodrama"], "720p", 90, code: 1030, views: 18_600, order: 3,
                  "Farg'onalik rassom va toshkentlik musiqachi tasodifan bir poyezd kupesida uchrashib qolishadi. Ularning hikoyasi o'n yil davom etadi."),
            movie(8, "Shahar chiroqlari", 2023, ["Komediya", "Oilaviy"], "1080p", 95, code: 1031, views: 26_780, order: 11,
                  "Taksi haydovchisi Botir bir kechada shahardagi eng g'alati yo'lovchilarni tashiydi. Har bir safar — alohida kulgili sarguzasht."),
            movie(9, "Tungi ov", 2022, ["Qo'rqinchli", "Triller"], "1080p", 91, code: 1032, views: 14_230, order: 7,
                  "Do'stlar guruhi tashlandiq qishloqda tunashga qaror qiladi. Tunda ular yolg'iz emasliklarini tushunib yetishadi."),
            movie(10, "Oltin vodiy", 2019, ["Tarixiy", "Drama"], "1080p", 138, code: 1033, views: 21_090, order: 1,
                  "XIX asr Farg'ona vodiysi. Ipak savdogarining o'g'li oilasi va yurti sha'nini himoya qilish uchun katta sinovlarga duch keladi."),
            movie(11, "Sirli orol", 2025, ["Sarguzasht", "Oilaviy"], "1080p", 100, code: 1034, views: 3_120, order: 18, available: false,
                  "Orol dengizining qurigan tubida bolalar qadimiy kemani topishadi. Tez orada ilovada!"),
            movie(12, "Po'lat qanotlar", 2024, ["Jangari", "Fantastika"], "4K", 133, code: 1035, views: 44_670, order: 16, premium: true,
                  "Sinov uchuvchisi maxfiy loyiha doirasida yaratilgan eksperimental samolyotni boshqaradi. Loyiha ortida esa xavfli fitna yashiringan."),
            movie(13, "Buvijonning retsepti", 2021, ["Komediya", "Oilaviy"], "720p", 85, code: 1036, views: 16_340, order: 5,
                  "Nevaralar buvisining mashhur palov retseptini topish uchun butun mahallani ostin-ustun qilishadi."),
            movie(14, "Yashirin yo'lak", 2023, ["Detektiv"], "1080p", 105, code: 1037, views: 11_520, order: 10,
                  "Buxorodagi eski madrasa ostidan topilgan yashirin yo'lak shaharda sodir bo'lgan o'g'irliklarni bir-biriga bog'laydi."),
            movie(15, "Kichkina qahramon", 2024, ["Multfilm", "Oilaviy"], "1080p", 88, code: 1038, views: 29_870, order: 14,
                  "Kichkina lochin bolasi uchishdan qo'rqadi. Ammo tog'dagi do'stlarini qutqarish uchun u qo'rquvini yengishi kerak."),
            movie(16, "Bahor qaytganda", 2022, ["Melodrama", "Drama"], "1080p", 101, code: 1039, views: 13_410, order: 9,
                  "Ko'p yillardan so'ng ona yurtiga qaytgan ayol o'tmishda qoldirgan sevgisi va o'z tanlovlari bilan yuzma-yuz keladi."),
            movie(17, "Mars ekspeditsiyasi", 2025, ["Fantastika"], "4K", 122, code: 1040, views: 35_760, order: 17,
                  "Marsdagi birinchi koloniyada suv zaxiralari kutilmaganda yo'qola boshlaydi. Muhandis ekipajni qutqarish yo'lini izlaydi."),
            serial(18, "Toshkent 2049", 2025, ["Fantastika", "Triller"], "1080p", episodeMinutes: 45, seasons: [8, 8],
                   code: 2001, views: 61_200, order: 21,
                   "Kelajak Toshkenti: aqlli shahar hamma narsani kuzatadi. Bir kuni tizim begunoh odamni jinoyatchi deb e'lon qiladi va u o'z nomini oqlash uchun qochishga majbur bo'ladi."),
            serial(19, "Mahalla hangomalari", 2023, ["Komediya", "Oilaviy"], "720p", episodeMinutes: 25, seasons: [10, 10, 8],
                   code: 2002, views: 52_840, order: 13,
                   "Bir mahalla, o'nlab qo'shnilar va har kuni yangi hangoma. Oilaviy tomosha uchun iliq va kulgili serial."),
            serial(20, "Sharq darvozasi", 2024, ["Tarixiy", "Drama"], "1080p", episodeMinutes: 50, seasons: [12],
                   code: 2003, views: 33_950, order: 4,
                   "Buyuk Ipak yo'li chorrahasida joylashgan shahar darvozasi qo'riqchilari haqida epik hikoya.")
        ]
    }

    // MARK: - Yordamchilar

    private static func movie(
        _ id: Int,
        _ title: String,
        _ year: Int,
        _ genres: [String],
        _ quality: String,
        _ minutes: Int,
        code: Int,
        views: Int,
        order: Int,
        premium: Bool = false,
        available: Bool = true,
        _ overview: String
    ) -> MockTitle {
        let card = TitleCard(
            id: id,
            kind: .movie,
            title: title,
            year: year,
            genres: genres,
            posterUrl: nil,
            backdropUrl: nil,
            isPremium: premium,
            quality: quality,
            durationSec: minutes * 60
        )
        return MockTitle(
            card: card,
            code: code,
            overview: overview,
            language: "O'zbek tilida",
            views: views,
            isAvailable: available,
            addedOrder: order,
            seasons: []
        )
    }

    private static func serial(
        _ id: Int,
        _ title: String,
        _ year: Int,
        _ genres: [String],
        _ quality: String,
        episodeMinutes: Int,
        seasons episodeCounts: [Int],
        code: Int,
        views: Int,
        order: Int,
        premium: Bool = false,
        _ overview: String
    ) -> MockTitle {
        let card = TitleCard(
            id: id,
            kind: .serial,
            title: title,
            year: year,
            genres: genres,
            posterUrl: nil,
            backdropUrl: nil,
            isPremium: premium,
            quality: quality,
            durationSec: nil
        )
        var seasons: [Season] = []
        for (index, count) in episodeCounts.enumerated() {
            let seasonNumber = index + 1
            var episodes: [Episode] = []
            for number in 1...max(count, 1) {
                // Oxirgi faslning oxirgi qismi "tez orada"
                let isLastUpcoming = seasonNumber == episodeCounts.count && number == count && count > 3
                episodes.append(
                    Episode(
                        id: id * 1000 + seasonNumber * 100 + number,
                        number: number,
                        title: nil,
                        durationSec: episodeMinutes * 60,
                        isAvailable: !isLastUpcoming,
                        progressSec: 0
                    )
                )
            }
            seasons.append(Season(id: id * 10 + seasonNumber, number: seasonNumber, title: nil, episodes: episodes))
        }
        return MockTitle(
            card: card,
            code: code,
            overview: overview,
            language: "O'zbek tilida",
            views: views,
            isAvailable: true,
            addedOrder: order,
            seasons: seasons
        )
    }
}
