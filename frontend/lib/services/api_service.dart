import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/analysis.dart';

class ApiService {
  static String _customBaseUrl = '';
  static String _authToken = '';
  static String _sessionId = '';
  static bool _isTransient = false;

  static String get baseUrl {
    if (_customBaseUrl.isNotEmpty) return _customBaseUrl;
    if (kIsWeb) {
      var host = Uri.base.host.isNotEmpty ? Uri.base.host : '127.0.0.1';
      if (host == 'localhost') host = '127.0.0.1';
      return 'http://$host:8000';
    }
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  static void setBaseUrl(String url) {
    var trimmed = url.trim();
    if (trimmed.isNotEmpty && !trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
      trimmed = 'http://$trimmed';
    }
    while (trimmed.endsWith('/')) {
      trimmed = trimmed.substring(0, trimmed.length - 1);
    }
    _customBaseUrl = trimmed;
  }

  static void setAuthToken(String token) {
    _authToken = token.trim();
  }

  static void setSessionId(String sessionId) {
    _sessionId = sessionId.trim();
  }

  static void setTransientMode(bool enabled) {
    _isTransient = enabled;
  }

  static String get authToken => _authToken;
  static String get sessionId => _sessionId;
  static bool get isTransient => _isTransient;

  static Map<String, String> getHeaders({bool jsonContent = true}) {
    final headers = <String, String>{};
    if (jsonContent) {
      headers['Content-Type'] = 'application/json';
    }
    if (_authToken.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    if (_sessionId.isNotEmpty) {
      headers['X-Session-ID'] = _sessionId;
    }
    if (_isTransient) {
      headers['X-Transient-Mode'] = 'true';
    }
    return headers;
  }

  final http.Client _client = http.Client();

  // --- Authentication Endpoints ---

  Future<Map<String, dynamic>> register(String email, String username, String password) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: getHeaders(),
      body: json.encode({'email': email, 'username': username, 'password': password}),
    );
    final data = json.decode(response.body);
    if (response.statusCode == 200) {
      return data;
    }
    throw Exception(data['detail'] ?? 'Registration failed');
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: getHeaders(),
      body: json.encode({'email': email, 'password': password}),
    );
    final data = json.decode(response.body);
    if (response.statusCode == 200) {
      return data;
    }
    throw Exception(data['detail'] ?? 'Login failed');
  }

  Future<Map<String, dynamic>> getMe() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to get user profile');
  }

  // --- Demo & Transient Endpoints ---

  Future<Map<String, dynamic>> seedDemoData() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/seed-demo'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load demo data: ${response.body}');
  }

  Future<Map<String, dynamic>> clearDemoData() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/clear-demo'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to clear demo data: ${response.body}');
  }

  Future<Map<String, dynamic>> clearTransientSession() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/auth/transient/clear'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to clear transient session: ${response.body}');
  }

  // --- Analytics & Statements ---

  Future<Analysis> getAnalysis() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/analysis/overview'),
      headers: getHeaders(jsonContent: false),
    );
    if (response.statusCode == 200) {
      return Analysis.fromJson(json.decode(response.body));
    }
    throw Exception('Failed to load analysis: ${response.statusCode}');
  }

  Future<Map<String, dynamic>> uploadPdf(String fileName, Uint8List bytes) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/upload/pdf'));
    request.headers.addAll(getHeaders(jsonContent: false));
    request.files.add(http.MultipartFile.fromBytes('file', bytes, filename: fileName));
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Upload failed: ${response.body}');
  }

  Future<Map<String, dynamic>> uploadMultiplePdfs(List<({String name, Uint8List bytes})> files) async {
    final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/upload/batch'));
    request.headers.addAll(getHeaders(jsonContent: false));
    for (final f in files) {
      request.files.add(http.MultipartFile.fromBytes('files', f.bytes, filename: f.name));
    }
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Batch upload failed: ${response.body}');
  }

  Future<Map<String, dynamic>> getTransactions({TransactionFilter? filter}) async {
    var uri = Uri.parse('$baseUrl/transactions/');
    if (filter != null) {
      uri = uri.replace(queryParameters: filter.toQueryParams());
    }
    final response = await _client.get(
      uri,
      headers: getHeaders(jsonContent: false),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load transactions: ${response.statusCode}');
  }

  Future<void> recategorizeTransaction(String id, String category, String classification) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/transactions/$id'),
      headers: getHeaders(),
      body: json.encode({'category': category, 'classification': classification}),
    );
    if (response.statusCode != 200) {
      throw Exception('Recategorization failed: ${response.body}');
    }
  }

  Future<void> deleteTransaction(String id) async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/transactions/$id'),
      headers: getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Delete failed: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> addManualTransaction(Map<String, dynamic> txnData) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/upload/manual'),
      headers: getHeaders(),
      body: json.encode(txnData),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to add transaction: ${response.body}');
  }

  Future<List<String>> getBanks() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/upload/banks'),
      headers: getHeaders(jsonContent: false),
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['banks']);
    }
    return [];
  }

  Future<List<String>> autocompleteDescriptions(String query) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/transactions/descriptions?q=${Uri.encodeComponent(query)}&limit=10'),
      headers: getHeaders(jsonContent: false),
    );
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['descriptions']);
    }
    return [];
  }

  Future<http.Response> downloadBytes(Uri url) async {
    return await _client.get(url, headers: getHeaders(jsonContent: false));
  }

  String get exportCsvUrl => '$baseUrl/transactions/export/csv';
  String get exportJsonUrl => '$baseUrl/transactions/export/json';

  Future<Map<String, dynamic>> resetData() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/upload/reset'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Reset failed: ${response.body}');
  }

  Future<Map<String, dynamic>> reclassifyAll() async {
    final response = await _client.post(
      Uri.parse('$baseUrl/transactions/reclassify'),
      headers: getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Reclassification failed: ${response.body}');
  }

  void dispose() {
    _client.close();
  }
}
