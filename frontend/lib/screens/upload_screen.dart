import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/analysis_provider.dart';
import '../providers/transaction_provider.dart';
import '../services/api_service.dart';

class UploadScreen extends StatelessWidget {
  const UploadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload Statement'), centerTitle: true),
      body: Consumer<AnalysisProvider>(
        builder: (context, provider, _) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    children: [
                      Icon(Icons.picture_as_pdf, size: 64, color: Theme.of(context).colorScheme.primary),
                      const SizedBox(height: 16),
                      Text('Upload PDF Statements', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      Text('Select single or multiple statements — supported bank formats auto-detected',
                          textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton.icon(
                          onPressed: provider.isLoading ? null : () => _pickFile(context),
                          icon: provider.isLoading
                              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                              : const Icon(Icons.upload_file),
                          label: Text(provider.isLoading ? 'Uploading & Analyzing...' : 'Select PDF Statement(s)'),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Text('Supported Banks', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _BankChip('SBI', Icons.account_balance),
                  _BankChip('SBI Cashback', Icons.credit_card),
                  _BankChip('ICICI Amazon Pay', Icons.credit_card),
                  _BankChip('YES BANK', Icons.credit_card),
                  _BankChip('AU Zenith+', Icons.credit_card),
                  _BankChip('AMEX', Icons.credit_card),
                  _BankChip('HDFC Swiggy', Icons.credit_card),
                  _BankChip('HSBC', Icons.credit_card),
                  _BankChip('IDFC FIRST', Icons.account_balance),
                  _BankChip('IndusInd', Icons.account_balance),
                ],
              ),
              const SizedBox(height: 24),
              Text('Manual Entry', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.add_circle_outline),
                  title: const Text('Add transaction manually'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => _showManualEntryDialog(context),
                ),
              ),
              const SizedBox(height: 24),
              Text('Data Management', style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600)),
              const SizedBox(height: 8),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.sync_outlined, color: Colors.indigo),
                  title: const Text('Reclassify Transactions', style: TextStyle(color: Colors.indigo, fontWeight: FontWeight.w500)),
                  subtitle: const Text('Re-apply latest categorization rules to existing data'),
                  trailing: const Icon(Icons.chevron_right, color: Colors.indigo),
                  onTap: () => _reclassifyTransactions(context),
                ),
              ),
              const SizedBox(height: 8),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.delete_sweep_outlined, color: Colors.red),
                  title: const Text('Reset Database', style: TextStyle(color: Colors.red, fontWeight: FontWeight.w500)),
                  subtitle: const Text('Clear all uploaded statements & start fresh'),
                  trailing: const Icon(Icons.chevron_right, color: Colors.red),
                  onTap: () => _confirmReset(context),
                ),
              ),
              if (provider.error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 16),
                  child: Card(
                    color: Colors.red.shade50,
                    child: ListTile(
                      leading: const Icon(Icons.error_outline, color: Colors.red),
                      title: Text(provider.error!, style: const TextStyle(color: Colors.red, fontSize: 13)),
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _pickFile(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf'],
      withData: true,
      allowMultiple: true,
    );
    if (result == null || result.files.isEmpty) return;

    final validFiles = result.files
        .where((f) => f.bytes != null && f.name.toLowerCase().endsWith('.pdf'))
        .map((f) => (name: f.name, bytes: f.bytes!))
        .toList();

    if (validFiles.isEmpty) return;

    if (context.mounted) {
      final uploadRes = await context.read<AnalysisProvider>().uploadMultiplePdfs(validFiles);
      if (context.mounted && uploadRes != null) {
        context.read<TransactionProvider>().loadTransactions();
        if (validFiles.length > 1) {
          _showBatchUploadResultDialog(context, uploadRes);
        } else {
          final msg = uploadRes['message'] ?? 'Statement uploaded successfully';
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(msg),
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
    }
  }

  void _showBatchUploadResultDialog(BuildContext context, Map<String, dynamic> res) {
    final results = (res['results'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    final message = res['message'] ?? 'Upload completed';
    final totalFiles = res['total_files'] ?? results.length;
    final successfulFiles = res['successful_files'] ?? 0;

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          children: [
            Icon(
              successfulFiles == totalFiles ? Icons.check_circle : Icons.info_outline,
              color: successfulFiles == totalFiles ? Colors.green : Colors.orange,
            ),
            const SizedBox(width: 8),
            const Text('Batch Upload Summary'),
          ],
        ),
        content: SizedBox(
          width: 460,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                message,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13.5),
              ),
              const SizedBox(height: 16),
              const Divider(),
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  itemCount: results.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (_, i) {
                    final item = results[i];
                    final isSuccess = item['status'] == 'success';
                    return ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(
                        isSuccess ? Icons.picture_as_pdf : Icons.error_outline,
                        color: isSuccess ? Colors.teal : Colors.red,
                        size: 24,
                      ),
                      title: Text(item['filename'] ?? 'Statement', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500)),
                      subtitle: isSuccess
                          ? Text('${item['bank'] ?? 'Bank'} • ${item['count'] ?? 0} new txns (${item['skipped'] ?? 0} duplicates skipped)', style: const TextStyle(fontSize: 12))
                          : Text(item['error'] ?? 'Failed to parse', style: TextStyle(color: Colors.red.shade700, fontSize: 12)),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(),
            child: const Text('Done'),
          ),
        ],
      ),
    );
  }

  Future<void> _reclassifyTransactions(BuildContext context) async {
    try {
      final res = await ApiService().reclassifyAll();
      if (context.mounted) {
        final msg = res['message'] ?? 'Transactions reclassified successfully';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(msg),
            backgroundColor: const Color(0xFF2E7D32),
            duration: const Duration(seconds: 4),
          ),
        );
        context.read<AnalysisProvider>().loadAnalysis();
        context.read<TransactionProvider>().loadTransactions();
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Reclassification error: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _confirmReset(BuildContext context) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Reset Database?'),
        content: const Text(
          'This will delete all parsed transactions from the database so you can re-upload your statements cleanly. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Reset All Data'),
          ),
        ],
      ),
    );

    if (confirmed == true && context.mounted) {
      try {
        final res = await ApiService().resetData();
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(res['message'] ?? 'Database cleared successfully')),
          );
          context.read<AnalysisProvider>().loadAnalysis();
          context.read<TransactionProvider>().loadTransactions();
        }
      } catch (e) {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  void _showManualEntryDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => _ManualEntryForm(),
    );
  }
}

class _ManualEntryForm extends StatefulWidget {
  @override
  State<_ManualEntryForm> createState() => _ManualEntryFormState();
}

class _ManualEntryFormState extends State<_ManualEntryForm> {
  final _formKey = GlobalKey<FormState>();
  final _descCtrl = TextEditingController();
  final _amountCtrl = TextEditingController();
  final _api = ApiService();
  DateTime _selectedDate = DateTime.now();
  String _type = 'debit';
  String _category = 'Uncategorized';
  String _classification = 'uncategorized';
  String _bankName = 'Manual';
  bool _saving = false;

  final _categories = ['Housing', 'Groceries', 'Utilities', 'Insurance', 'EMI/Loans',
    'Fuel', 'Medical', 'Transport', 'Education', 'Dining', 'Entertainment',
    'Shopping', 'Travel', 'Fitness', 'Personal Care', 'Subscriptions',
    'Fees & Charges', 'Income', 'Uncategorized'];
  final _classifications = ['mandatory', 'discretionary', 'income', 'uncategorized'];
  final _banks = ['Manual', 'SBI', 'SBI Cashback', 'ICICI Amazon Pay', 'YES BANK', 'AU Zenith+', 'AMEX'];

  List<String> _suggestions = [];

  @override
  void dispose() {
    _descCtrl.dispose();
    _amountCtrl.dispose();
    super.dispose();
  }

  Future<void> _fetchSuggestions(String query) async {
    if (query.length < 2) {
      setState(() => _suggestions = []);
      return;
    }
    final results = await _api.autocompleteDescriptions(query);
    if (mounted) setState(() => _suggestions = results);
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    try {
      await _api.addManualTransaction({
        'transaction_date': DateFormat('yyyy-MM-dd').format(_selectedDate),
        'description': _descCtrl.text.trim(),
        'amount': double.parse(_amountCtrl.text.trim()),
        'type': _type,
        'category': _category,
        'classification': _classification,
        'bank_name': _bankName,
      });
      if (!mounted) return;
      Navigator.pop(context);
      context.read<TransactionProvider>().loadTransactions();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Transaction added')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e'), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add Transaction'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              InkWell(
                onTap: _pickDate,
                child: InputDecorator(
                  decoration: const InputDecoration(labelText: 'Date', prefixIcon: Icon(Icons.calendar_today)),
                  child: Text(DateFormat('dd MMM yyyy').format(_selectedDate)),
                ),
              ),
              const SizedBox(height: 12),
              Autocomplete<String>(
                optionsBuilder: (textEditingValue) {
                  final text = textEditingValue.text.toLowerCase();
                  if (text.length < 2) return [];
                  _fetchSuggestions(text);
                  return _suggestions.where((s) => s.toLowerCase().contains(text));
                },
                onSelected: (selection) => _descCtrl.text = selection,
                fieldViewBuilder: (context, controller, focusNode, onSubmitted) {
                  return TextFormField(
                    controller: controller,
                    focusNode: focusNode,
                    decoration: const InputDecoration(labelText: 'Description', prefixIcon: Icon(Icons.notes)),
                    validator: (v) => v == null || v.trim().isEmpty ? 'Required' : null,
                    onFieldSubmitted: (_) => onSubmitted(),
                  );
                },
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _amountCtrl,
                decoration: const InputDecoration(labelText: 'Amount', prefixIcon: Icon(Icons.currency_rupee)),
                keyboardType: TextInputType.number,
                validator: (v) {
                  if (v == null || v.trim().isEmpty) return 'Required';
                  if (double.tryParse(v.trim()) == null) return 'Invalid number';
                  return null;
                },
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _type,
                decoration: const InputDecoration(labelText: 'Type', prefixIcon: Icon(Icons.swap_horiz)),
                items: const [
                  DropdownMenuItem(value: 'debit', child: Text('Debit (Spend)')),
                  DropdownMenuItem(value: 'credit', child: Text('Credit (Income)')),
                ],
                onChanged: (v) => setState(() => _type = v!),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _classification,
                decoration: const InputDecoration(labelText: 'Classification'),
                items: _classifications.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setState(() => _classification = v!),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _category,
                decoration: const InputDecoration(labelText: 'Category'),
                items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (v) => setState(() => _category = v!),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _bankName,
                decoration: const InputDecoration(labelText: 'Bank'),
                items: _banks.map((b) => DropdownMenuItem(value: b, child: Text(b))).toList(),
                onChanged: (v) => setState(() => _bankName = v!),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
        FilledButton.icon(
          onPressed: _saving ? null : _submit,
          icon: _saving
              ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
              : const Icon(Icons.add),
          label: Text(_saving ? 'Saving...' : 'Add'),
        ),
      ],
    );
  }
}

class _BankChip extends StatelessWidget {
  final String label;
  final IconData icon;
  const _BankChip(this.label, this.icon);

  @override
  Widget build(BuildContext context) {
    return Chip(
      avatar: Icon(icon, size: 16),
      label: Text(label, style: const TextStyle(fontSize: 12)),
      side: BorderSide(color: Colors.grey.shade300),
    );
  }
}
