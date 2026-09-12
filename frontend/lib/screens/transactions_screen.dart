import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/transaction_provider.dart';
import '../models/transaction.dart';
import '../models/analysis.dart';
import '../services/api_service.dart';
import '../widgets/common/transaction_tile.dart';
import '../widgets/common/empty_state.dart';
import '../widgets/auth/user_account_button.dart';

class TransactionsScreen extends StatefulWidget {
  const TransactionsScreen({super.key});

  @override
  State<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends State<TransactionsScreen> {
  final _searchController = TextEditingController();
  final _api = ApiService();
  String? _selectedClassification;
  String? _selectedCategory;

  final _categories = ['All', 'Housing', 'Groceries', 'Utilities', 'Insurance', 'EMI/Loans',
    'Fuel', 'Medical', 'Transport', 'Education', 'Dining', 'Entertainment',
    'Shopping', 'Travel', 'Fitness', 'Personal Care', 'Subscriptions',
    'Fees & Charges', 'UPI', 'POS', 'Transfer', 'Income', 'Uncategorized'];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TransactionProvider>().loadTransactions();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _downloadExport(String format) async {
    final url = Uri.parse(format == 'csv' ? _api.exportCsvUrl : _api.exportJsonUrl);
    if (await canLaunchUrl(url)) {
      await launchUrl(url, webOnlyWindowName: '_blank');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Transactions'),
        centerTitle: true,
        actions: [
          const UserAccountButton(),
          PopupMenuButton<String>(
            icon: const Icon(Icons.download),
            tooltip: 'Export',
            onSelected: _downloadExport,
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'csv', child: ListTile(leading: Icon(Icons.table_chart), title: Text('Download CSV'), dense: true)),
              PopupMenuItem(value: 'json', child: ListTile(leading: Icon(Icons.data_object), title: Text('Download JSON'), dense: true)),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search transactions...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchController.text.isNotEmpty
                    ? IconButton(icon: const Icon(Icons.clear), onPressed: () { _searchController.clear(); _applyFilters(); })
                    : null,
              ),
              onChanged: (_) => _applyFilters(),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
            child: SizedBox(
              height: 32,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  _FilterChip2('All', null, _selectedClassification),
                  const SizedBox(width: 6),
                  _FilterChip2('Mandatory', 'mandatory', _selectedClassification),
                  const SizedBox(width: 6),
                  _FilterChip2('Discretionary', 'discretionary', _selectedClassification),
                  const SizedBox(width: 6),
                  _FilterChip2('Income', 'income', _selectedClassification),
                  const SizedBox(width: 12),
                  _CategoryDropdown(),
                  const SizedBox(width: 6),
                  _DateRangeButton(),
                ],
              ),
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: Consumer<TransactionProvider>(
              builder: (context, provider, _) {
                if (provider.isLoading && provider.transactions.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (provider.transactions.isEmpty) {
                  return const EmptyState(
                    icon: Icons.receipt_long,
                    title: 'No transactions',
                    subtitle: 'Upload a statement to see transactions',
                  );
                }
                return RefreshIndicator(
                  onRefresh: () => provider.loadTransactions(),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    itemCount: provider.transactions.length + (provider.hasMore ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index >= provider.transactions.length) {
                        WidgetsBinding.instance.addPostFrameCallback((_) {
                          if (!provider.isLoading && provider.hasMore) {
                            provider.loadTransactions(loadMore: true);
                          }
                        });
                        return const Center(child: Padding(padding: EdgeInsets.all(16), child: CircularProgressIndicator()));
                      }
                      final txn = provider.transactions[index];
                      return Dismissible(
                        key: Key(txn.id),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20),
                          color: Colors.red.shade100,
                          child: const Icon(Icons.delete_outline, color: Colors.red),
                        ),
                        onDismissed: (_) => provider.deleteTransaction(txn.id),
                        child: TransactionTile(
                          transaction: txn,
                          onTap: () => _showRecategorizeDialog(context, txn),
                        ),
                      );
                    },
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _applyFilters() {
    final filter = TransactionFilter();
    filter.classification = _selectedClassification;
    filter.search = _searchController.text;
    if (_selectedCategory != null && _selectedCategory != 'All') {
      filter.category = _selectedCategory;
    }
    context.read<TransactionProvider>().setFilter(filter);
  }

  Widget _FilterChip2(String label, String? value, String? current) {
    final isSelected = current == value;
    return FilterChip(
      label: Text(label, style: TextStyle(fontSize: 11, color: isSelected ? Colors.white : null)),
      selected: isSelected,
      onSelected: (_) {
        setState(() {
          if (isSelected) {
            _selectedClassification = null;
          } else {
            _selectedClassification = value;
            _selectedCategory = null;
          }
        });
        _applyFilters();
      },
      visualDensity: VisualDensity.compact,
      color: WidgetStateProperty.resolveWith((states) {
        if (states.contains(WidgetState.selected)) return Theme.of(context).colorScheme.primary;
        return null;
      }),
    );
  }

  Widget _CategoryDropdown() {
    return Container(
      constraints: const BoxConstraints(maxWidth: 140),
      child: DropdownButtonFormField<String>(
        value: _selectedCategory,
        isDense: true,
        decoration: const InputDecoration(
          contentPadding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          border: OutlineInputBorder(),
          labelText: 'Category',
          labelStyle: TextStyle(fontSize: 11),
        ),
        items: _categories.map((c) => DropdownMenuItem(value: c == 'All' ? null : c, child: Text(c, style: const TextStyle(fontSize: 11)))).toList(),
        onChanged: (v) {
          setState(() => _selectedCategory = v);
          _applyFilters();
        },
      ),
    );
  }

  Widget _DateRangeButton() {
    return OutlinedButton.icon(
      onPressed: () async {
        final range = await showDateRangePicker(
          context: context,
          firstDate: DateTime(2020),
          lastDate: DateTime.now(),
        );
        if (range != null && mounted) {
          final filter = TransactionFilter();
          filter.classification = _selectedClassification;
          filter.search = _searchController.text;
          filter.startDate = DateFormat('yyyy-MM-dd').format(range.start);
          filter.endDate = DateFormat('yyyy-MM-dd').format(range.end);
          context.read<TransactionProvider>().setFilter(filter);
        }
      },
      icon: const Icon(Icons.date_range, size: 16),
      label: const Text('Dates', style: TextStyle(fontSize: 11)),
      style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(horizontal: 8)),
    );
  }

  void _showRecategorizeDialog(BuildContext context, Transaction txn) {
    final categories = ['Housing', 'Groceries', 'Utilities', 'Insurance', 'EMI/Loans', 'Fuel', 'Medical', 'Transport', 'Education',
                        'Dining', 'Entertainment', 'Shopping', 'Travel', 'Fitness', 'Personal Care', 'Subscriptions',
                        'Fees & Charges', 'Income', 'Uncategorized'];
    final classifications = ['mandatory', 'discretionary', 'income', 'uncategorized'];

    String selectedCat = txn.category;
    String selectedClass = txn.classification;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDState) => AlertDialog(
          title: const Text('Recategorize'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(txn.description, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
                const SizedBox(height: 4),
                Text('₹${txn.amount.toStringAsFixed(0)}', style: Theme.of(context).textTheme.titleMedium),
                const Divider(),
                const Text('Type', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  children: classifications.map((c) => ChoiceChip(
                    label: Text(c, style: const TextStyle(fontSize: 11)),
                    selected: selectedClass == c,
                    onSelected: (_) => setDState(() => selectedClass = c),
                  )).toList(),
                ),
                const SizedBox(height: 12),
                const Text('Category', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 12)),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: categories.map((c) => ChoiceChip(
                    label: Text(c, style: const TextStyle(fontSize: 11)),
                    selected: selectedCat == c,
                    onSelected: (_) => setDState(() => selectedCat = c),
                  )).toList(),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            FilledButton(onPressed: () {
              context.read<TransactionProvider>().recategorize(txn.id, selectedCat, selectedClass);
              Navigator.pop(ctx);
            }, child: const Text('Save')),
          ],
        ),
      ),
    );
  }
}
