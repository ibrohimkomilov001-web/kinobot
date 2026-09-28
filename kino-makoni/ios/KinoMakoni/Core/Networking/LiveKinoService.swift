import Foundation

/// Haqiqiy backend bilan ishlovchi servis.
/// Birinchi so'rovda qurilma orqali avtorizatsiya qiladi, 401 bo'lsa bir marta qayta urinadi.
actor LiveKinoService: KinoService {
    private let baseURL: URL
    private let session: URLSession
    private let decoder = JSONDecoder.kino()
    private let encoder = JSONEncoder()
    private var accessToken: String?
    private var authTask: Task<String, Error>?

    init(baseURL: URL) {
        self.baseURL = baseURL
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 20
        configuration.timeoutIntervalForResource = 60
        configuration.httpAdditionalHeaders = [
            "Accept": "application/json",
            "Accept-Language": "uz"
        ]
        self.session = URLSession(configuration: configuration)
        self.accessToken = TokenStore.load()
    }

    // MARK: - Katalog

    func home() async throws -> HomeResponse {
        try await get("v1/home")
    }

    func titles(kind: TitleKind?, genre: String?, sort: TitleSort?, cursor: String?, limit: Int) async throws -> TitlePage {
        var query: [URLQueryItem] = [URLQueryItem(name: "limit", value: String(limit))]
        if let kind = kind {
            query.append(URLQueryItem(name: "kind", value: kind.rawValue))
        }
        if let genre = genre, !genre.isEmpty {
            query.append(URLQueryItem(name: "genre", value: genre))
        }
        if let sort = sort {
            query.append(URLQueryItem(name: "sort", value: sort.rawValue))
        }
        if let cursor = cursor, !cursor.isEmpty {
            query.append(URLQueryItem(name: "cursor", value: cursor))
        }
        return try await get("v1/titles", query: query)
    }

    func titleDetail(id: Int) async throws -> TitleDetail {
        try await get("v1/titles/\(id)")
    }

    func genres() async throws -> [Genre] {
        let response: ItemsResponse<Genre> = try await get("v1/genres")
        return response.items
    }

    func search(query: String, limit: Int) async throws -> [TitleCard] {
        let items = [
            URLQueryItem(name: "q", value: query),
            URLQueryItem(name: "limit", value: String(limit))
        ]
        let response: ItemsResponse<TitleCard> = try await get("v1/search", query: items)
        return response.items
    }

    // MARK: - Ijro

    func playback(titleID: Int, episodeID: Int?) async throws -> PlaybackInfo {
        let body = try encoder.encode(PlaybackRequest(titleId: titleID, episodeId: episodeID))
        let data = try await send(method: "POST", path: "v1/playback", body: body)
        return try decode(PlaybackInfo.self, from: data)
    }

    // MARK: - Foydalanuvchi

    func me() async throws -> UserInfo {
        try await get("v1/me")
    }

    func favorites() async throws -> [TitleCard] {
        let response: ItemsResponse<TitleCard> = try await get("v1/me/favorites")
        return response.items
    }

    func setFavorite(titleID: Int, isFavorite: Bool) async throws {
        let method = isFavorite ? "PUT" : "DELETE"
        _ = try await send(method: method, path: "v1/me/favorites/\(titleID)")
    }

    func continueWatching() async throws -> [ContinueItem] {
        let response: ItemsResponse<ContinueItem> = try await get("v1/me/continue")
        return response.items
    }

    func reportProgress(_ report: ProgressReport) async throws {
        let body = try encoder.encode(report)
        _ = try await send(method: "PUT", path: "v1/me/progress", body: body)
    }

    // MARK: - So'rov yadrosi

    private func get<T: Decodable>(_ path: String, query: [URLQueryItem] = []) async throws -> T {
        let data = try await send(method: "GET", path: path, query: query)
        return try decode(T.self, from: data)
    }

    private func send(
        method: String,
        path: String,
        query: [URLQueryItem] = [],
        body: Data? = nil,
        requiresAuth: Bool = true,
        isRetry: Bool = false
    ) async throws -> Data {
        var request = try makeRequest(method: method, path: path, query: query, body: body)
        var usedToken: String?
        if requiresAuth {
            let token = try await validToken()
            usedToken = token
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await perform(request)

        // Token eskirgan — yangisini olib, bir marta qayta urinamiz
        if response.statusCode == 401, requiresAuth, !isRetry {
            invalidateToken(ifEqualTo: usedToken)
            return try await send(
                method: method,
                path: path,
                query: query,
                body: body,
                requiresAuth: true,
                isRetry: true
            )
        }

        guard (200..<300).contains(response.statusCode) else {
            throw APIError.from(data: data, status: response.statusCode)
        }
        return data
    }

    private func makeRequest(method: String, path: String, query: [URLQueryItem], body: Data?) throws -> URLRequest {
        let url = baseURL.appending(path: path)
        guard var components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            throw APIError(code: .invalidResponse, message: "Server manzili noto'g'ri.")
        }
        if !query.isEmpty {
            components.queryItems = query
            // "+" belgisi server tomonida bo'sh joy deb o'qilmasligi uchun
            components.percentEncodedQuery = components.percentEncodedQuery?
                .replacingOccurrences(of: "+", with: "%2B")
        }
        guard let finalURL = components.url else {
            throw APIError(code: .invalidResponse, message: "Server manzili noto'g'ri.")
        }
        var request = URLRequest(url: finalURL)
        request.httpMethod = method
        if let body = body {
            request.httpBody = body
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        return request
    }

    private func perform(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw APIError(code: .invalidResponse)
            }
            return (data, http)
        } catch let error as URLError {
            if error.code == .cancelled {
                throw CancellationError()
            }
            throw APIError.network(error)
        }
    }

    private func decode<T: Decodable>(_ type: T.Type, from data: Data) throws -> T {
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            #if DEBUG
            print("[KinoMakoni] Dekodlash xatosi (\(T.self)): \(error)")
            #endif
            throw APIError(code: .decoding)
        }
    }

    // MARK: - Avtorizatsiya

    private func validToken() async throws -> String {
        if let token = accessToken {
            return token
        }
        if let running = authTask {
            return try await running.value
        }
        let task = Task { try await self.requestDeviceToken() }
        authTask = task
        do {
            let token = try await task.value
            accessToken = token
            authTask = nil
            return token
        } catch {
            authTask = nil
            throw error
        }
    }

    private func requestDeviceToken() async throws -> String {
        let payload = DeviceAuthRequest(
            deviceId: DeviceIdentity.current,
            platform: "ios",
            appVersion: AppConfig.appVersion
        )
        let body = try encoder.encode(payload)
        let data = try await send(method: "POST", path: "v1/auth/device", body: body, requiresAuth: false)
        let auth = try decode(AuthResponse.self, from: data)
        TokenStore.save(auth.accessToken)
        return auth.accessToken
    }

    private func invalidateToken(ifEqualTo token: String?) {
        // Boshqa so'rov allaqachon yangi token olgan bo'lsa, uni o'chirmaymiz
        guard accessToken == nil || accessToken == token else { return }
        accessToken = nil
        TokenStore.clear()
    }
}
