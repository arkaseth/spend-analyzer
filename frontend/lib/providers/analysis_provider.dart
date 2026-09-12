import 'package:flutter/foundation.dart';
import '../models/analysis.dart';
import '../services/api_service.dart';

class AnalysisProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  Analysis? _analysis;
  bool _isLoading = false;
  String? _error;

  Analysis? get analysis => _analysis;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasData => _analysis != null && _analysis!.totalTransactions > 0;

  List<String> _supportedBanks = [];
  List<String> get supportedBanks => _supportedBanks;

  Future<void> loadAnalysis() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _analysis = await _api.getAnalysis();
    } catch (e) {
      _error = e.toString();
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<Map<String, dynamic>?> uploadPdf(String fileName, Uint8List bytes) async {
    return uploadMultiplePdfs([(name: fileName, bytes: bytes)]);
  }

  Future<Map<String, dynamic>?> uploadMultiplePdfs(List<({String name, Uint8List bytes})> files) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    Map<String, dynamic>? res;
    try {
      res = await _api.uploadMultiplePdfs(files);
      await loadAnalysis();
    } catch (e) {
      _error = e.toString().replaceAll('Exception: ', '');
    }

    _isLoading = false;
    notifyListeners();
    return res;
  }

  Future<void> loadBanks() async {
    try {
      _supportedBanks = await _api.getBanks();
      notifyListeners();
    } catch (e) {
      // Silently fail
    }
  }
}
