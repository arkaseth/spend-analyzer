import 'dart:math';
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  Map<String, dynamic>? _user;
  String? _token;
  String? _sessionId;
  bool _isTransientMode = false;
  bool _isDemoMode = false;
  bool _isLoading = false;
  String? _error;

  Map<String, dynamic>? get user => _user;
  String? get token => _token;
  String? get sessionId => _sessionId;
  bool get isAuthenticated => _user != null && _token != null;
  bool get isTransientMode => _isTransientMode;
  bool get isDemoMode => _isDemoMode;
  bool get isLoading => _isLoading;
  String? get error => _error;

  String get displayName {
    if (_user != null) {
      return _user!['username'] ?? _user!['email'] ?? 'User';
    }
    if (_isTransientMode) return 'Guest (Incognito)';
    if (_isDemoMode) return 'Demo Explorer';
    return 'Guest';
  }

  String _generateSessionId() {
    final rand = Random();
    final bytes = List<int>.generate(16, (_) => rand.nextInt(256));
    return bytes.map((b) => b.toRadixString(16).padLeft(2, '0')).join();
  }

  Future<bool> register(String email, String username, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _api.register(email, username, password);
      _token = res['token'];
      _user = res['user'];
      _isTransientMode = false;

      ApiService.setAuthToken(_token ?? '');
      ApiService.setTransientMode(false);

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> login(String email, String password) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final res = await _api.login(email, password);
      _token = res['token'];
      _user = res['user'];
      _isTransientMode = false;

      ApiService.setAuthToken(_token ?? '');
      ApiService.setTransientMode(false);

      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  void logout() {
    _token = null;
    _user = null;
    _isTransientMode = false;
    _isDemoMode = false;
    ApiService.setAuthToken('');
    ApiService.setTransientMode(false);
    notifyListeners();
  }

  void enableTransientMode() {
    _sessionId = _generateSessionId();
    _isTransientMode = true;
    _isDemoMode = false;
    _user = null;
    _token = null;

    ApiService.setAuthToken('');
    ApiService.setSessionId(_sessionId!);
    ApiService.setTransientMode(true);
    notifyListeners();
  }

  Future<void> exitTransientMode() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _api.clearTransientSession();
    } catch (_) {}

    _isTransientMode = false;
    _sessionId = null;
    ApiService.setSessionId('');
    ApiService.setTransientMode(false);
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> loadDemoData() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      if (!_isTransientMode && _user == null) {
        _sessionId = _generateSessionId();
        ApiService.setSessionId(_sessionId!);
      }
      await _api.seedDemoData();
      _isDemoMode = true;
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> clearDemoData() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _api.clearDemoData();
      _isDemoMode = false;
    } catch (_) {}

    _isLoading = false;
    notifyListeners();
  }
}
