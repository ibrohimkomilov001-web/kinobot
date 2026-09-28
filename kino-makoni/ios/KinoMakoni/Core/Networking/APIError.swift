import Foundation

/// API xatosi. Server javobi: `{ "error": { "code": "...", "message": "..." } }`
struct APIError: Error, LocalizedError, Equatable, Sendable {
    enum Code: String, Sendable {
        case unauthorized
        case forbidden
        case premiumRequired = "premium_required"
        case notFound = "not_found"
        case unavailable
        case validationError = "validation_error"
        case rateLimited = "rate_limited"
        case internalError = "internal"
        // Mahalliy (client) xatolar
        case network
        case decoding
        case invalidResponse = "invalid_response"
        case unknown
    }

    let code: Code
    let message: String
    let status: Int?

    init(code: Code, message: String = "", status: Int? = nil) {
        self.code = code
        self.message = message
        self.status = status
    }

    var errorDescription: String? { userMessage }

    /// Foydalanuvchiga ko'rsatiladigan matn (server matni bo'lmasa — standart)
    var userMessage: String {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        if !trimmed.isEmpty {
            return trimmed
        }
        switch code {
        case .unauthorized: return "Avtorizatsiya muddati tugadi. Qayta urinib ko'ring."
        case .forbidden: return "Bu amalga ruxsat yo'q."
        case .premiumRequired: return "Bu kino Premium obunachilar uchun."
        case .notFound: return "Ma'lumot topilmadi."
        case .unavailable: return "Bu video hozircha mavjud emas."
        case .validationError: return "So'rov noto'g'ri."
        case .rateLimited: return "Juda ko'p so'rov. Birozdan so'ng urinib ko'ring."
        case .internalError: return "Serverda xatolik yuz berdi."
        case .network: return "Internet aloqasini tekshiring."
        case .decoding: return "Server javobini o'qib bo'lmadi."
        case .invalidResponse: return "Serverdan noto'g'ri javob keldi."
        case .unknown: return "Nimadir xato ketdi. Qaytadan urinib ko'ring."
        }
    }

    // MARK: - Yasovchilar

    private struct Envelope: Decodable {
        struct Body: Decodable {
            let code: String?
            let message: String?
        }
        let error: Body
    }

    static func from(data: Data, status: Int) -> APIError {
        if let envelope = try? JSONDecoder().decode(Envelope.self, from: data) {
            let code = envelope.error.code.flatMap { Code(rawValue: $0) } ?? fallbackCode(for: status)
            return APIError(code: code, message: envelope.error.message ?? "", status: status)
        }
        return APIError(code: fallbackCode(for: status), message: "", status: status)
    }

    static func fallbackCode(for status: Int) -> Code {
        switch status {
        case 401: return .unauthorized
        case 403: return .forbidden
        case 404: return .notFound
        case 409: return .unavailable
        case 422: return .validationError
        case 429: return .rateLimited
        case 500...599: return .internalError
        default: return .unknown
        }
    }

    static func network(_ error: URLError) -> APIError {
        let message: String
        switch error.code {
        case .notConnectedToInternet, .networkConnectionLost, .dataNotAllowed:
            message = "Internet aloqasi yo'q. Tarmoqni tekshiring."
        case .timedOut:
            message = "Server javob bermadi. Birozdan so'ng urinib ko'ring."
        case .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed:
            message = "Serverga ulanib bo'lmadi."
        case .secureConnectionFailed, .serverCertificateUntrusted, .serverCertificateHasBadDate:
            message = "Xavfsiz ulanish o'rnatilmadi."
        default:
            message = "Tarmoq xatosi. Qaytadan urinib ko'ring."
        }
        return APIError(code: .network, message: message, status: nil)
    }
}

/// Har qanday xatoni o'zbekcha matnga aylantiradi
enum ErrorText {
    static func message(for error: Error) -> String {
        if let apiError = error as? APIError {
            return apiError.userMessage
        }
        if let urlError = error as? URLError {
            return APIError.network(urlError).userMessage
        }
        return "Nimadir xato ketdi. Qaytadan urinib ko'ring."
    }
}
