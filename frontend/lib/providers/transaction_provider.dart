import 'package:flutter/foundation.dart';
import '../models/transaction.dart';
import '../models/analysis.dart';
import '../services/api_service.dart';

class TransactionProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  List<Transaction> _transactions = [];
  bool _isLoading = false;
  String? _error;
  int _totalCount = 0;
  int _currentPage = 0;
  static const int _pageSize = 50;

  List<Transaction> get transactions => _transactions;
  bool get isLoading => _isLoading;
  String? get error => _error;
  int get totalCount => _totalCount;
  bool get hasMore => _currentPage * _pageSize < _totalCount;

  TransactionFilter _filter = TransactionFilter();
  TransactionFilter get filter => _filter;

  void setFilter(TransactionFilter newFilter) {
    _filter = newFilter;
    _currentPage = 0;
    _transactions = [];
    loadTransactions();
  }

  void clearFilter() {
    _filter = TransactionFilter();
    _currentPage = 0;
    _transactions = [];
    loadTransactions();
  }

  Future<void> loadTransactions({bool loadMore = false}) async {
    if (_isLoading) return;
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      if (loadMore && hasMore) {
        _currentPage++;
      } else if (!loadMore) {
        _currentPage = 0;
      }
      _filter.offset = _currentPage * _pageSize;
      _filter.limit = _pageSize;

      final data = await _api.getTransactions(filter: _filter);
      final List<dynamic> items = data['transactions'] ?? [];
      _totalCount = data['total'] as int? ?? 0;

      if (loadMore) {
        _transactions.addAll(items.map((e) => Transaction.fromJson(e)));
      } else {
        _transactions = items.map((e) => Transaction.fromJson(e)).toList();
      }
    } catch (e) {
      _error = e.toString();
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> recategorize(String id, String category, String classification) async {
    try {
      await _api.recategorizeTransaction(id, category, classification);
      final idx = _transactions.indexWhere((t) => t.id == id);
      if (idx != -1) {
        _transactions[idx].category = category;
        _transactions[idx].classification = classification;
        notifyListeners();
      }
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  Future<void> deleteTransaction(String id) async {
    try {
      await _api.deleteTransaction(id);
      _transactions.removeWhere((t) => t.id == id);
      _totalCount--;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  List<Transaction> getByClassification(String classification) {
    return _transactions.where((t) => t.classification == classification).toList();
  }

  List<Transaction> getByCategory(String category) {
    return _transactions.where((t) => t.category == category).toList();
  }
}
