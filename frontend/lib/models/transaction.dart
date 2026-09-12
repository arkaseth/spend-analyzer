class Transaction {
  final String id;
  final String bankName;
  final String accountType;
  final String transactionDate;
  final String description;
  final double amount;
  final String type;
  String category;
  String classification;
  final String? merchantCategory;
  final bool isEmi;
  final bool isRecurring;

  Transaction({
    required this.id,
    required this.bankName,
    required this.accountType,
    required this.transactionDate,
    required this.description,
    required this.amount,
    required this.type,
    required this.category,
    required this.classification,
    this.merchantCategory,
    this.isEmi = false,
    this.isRecurring = false,
  });

  factory Transaction.fromJson(Map<String, dynamic> json) {
    return Transaction(
      id: json['id'] as String,
      bankName: json['bank_name'] as String? ?? '',
      accountType: json['account_type'] as String? ?? '',
      transactionDate: json['transaction_date'] as String? ?? '',
      description: json['description'] as String? ?? '',
      amount: (json['amount'] as num?)?.toDouble() ?? 0.0,
      type: json['type'] as String? ?? 'debit',
      category: json['category'] as String? ?? 'Uncategorized',
      classification: json['classification'] as String? ?? 'uncategorized',
      merchantCategory: json['merchant_category'] as String?,
      isEmi: json['is_emi'] as bool? ?? false,
      isRecurring: json['is_recurring'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'bank_name': bankName,
      'account_type': accountType,
      'transaction_date': transactionDate,
      'description': description,
      'amount': amount,
      'type': type,
      'category': category,
      'classification': classification,
      'merchant_category': merchantCategory,
      'is_emi': isEmi,
      'is_recurring': isRecurring,
    };
  }

  bool get isDebit => type == 'debit';
  bool get isCredit => type == 'credit';
  String get formattedAmount {
    return '₹${amount.toStringAsFixed(0)}';
  }
}
