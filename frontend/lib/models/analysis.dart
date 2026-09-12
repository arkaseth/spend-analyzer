class Analysis {
  final double totalSpend;
  final double mandatorySpend;
  final double discretionarySpend;
  final double mandatoryPercentage;
  final double discretionaryPercentage;
  final List<MonthlyTrend> monthlyTrends;
  final List<CategoryBreakdown> categoryBreakdown;
  final List<Insight> insights;
  final int totalTransactions;

  Analysis({
    required this.totalSpend,
    required this.mandatorySpend,
    required this.discretionarySpend,
    required this.mandatoryPercentage,
    required this.discretionaryPercentage,
    required this.monthlyTrends,
    required this.categoryBreakdown,
    required this.insights,
    required this.totalTransactions,
  });

  factory Analysis.fromJson(Map<String, dynamic> json) {
    return Analysis(
      totalSpend: (json['total_spend'] as num?)?.toDouble() ?? 0,
      mandatorySpend: (json['mandatory_spend'] as num?)?.toDouble() ?? 0,
      discretionarySpend: (json['discretionary_spend'] as num?)?.toDouble() ?? 0,
      mandatoryPercentage: (json['mandatory_percentage'] as num?)?.toDouble() ?? 0,
      discretionaryPercentage: (json['discretionary_percentage'] as num?)?.toDouble() ?? 0,
      monthlyTrends: (json['monthly_trends'] as List?)
              ?.map((e) => MonthlyTrend.fromJson(e))
              .toList() ?? [],
      categoryBreakdown: (json['category_breakdown'] as List?)
              ?.map((e) => CategoryBreakdown.fromJson(e))
              .toList() ?? [],
      insights: (json['insights'] as List?)
              ?.map((e) => Insight.fromJson(e))
              .toList() ?? [],
      totalTransactions: json['total_transactions'] as int? ?? 0,
    );
  }
}

class MonthlyTrend {
  final String month;
  final double mandatory;
  final double discretionary;
  final double total;

  MonthlyTrend({
    required this.month,
    required this.mandatory,
    required this.discretionary,
    required this.total,
  });

  factory MonthlyTrend.fromJson(Map<String, dynamic> json) {
    return MonthlyTrend(
      month: json['month'] as String? ?? '',
      mandatory: (json['mandatory'] as num?)?.toDouble() ?? 0,
      discretionary: (json['discretionary'] as num?)?.toDouble() ?? 0,
      total: (json['total'] as num?)?.toDouble() ?? 0,
    );
  }
}

class CategoryBreakdown {
  final String category;
  final String classification;
  final double total;
  final int count;
  final double percentage;

  CategoryBreakdown({
    required this.category,
    required this.classification,
    required this.total,
    required this.count,
    required this.percentage,
  });

  factory CategoryBreakdown.fromJson(Map<String, dynamic> json) {
    return CategoryBreakdown(
      category: json['category'] as String? ?? '',
      classification: json['classification'] as String? ?? '',
      total: (json['total'] as num?)?.toDouble() ?? 0,
      count: json['count'] as int? ?? 0,
      percentage: (json['percentage'] as num?)?.toDouble() ?? 0,
    );
  }

  bool get isMandatory => classification == 'mandatory';
  bool get isDiscretionary => classification == 'discretionary';
}

class Insight {
  final String title;
  final String description;
  final double? savingsPotential;
  final String? category;

  Insight({
    required this.title,
    required this.description,
    this.savingsPotential,
    this.category,
  });

  factory Insight.fromJson(Map<String, dynamic> json) {
    return Insight(
      title: json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      savingsPotential: (json['savings_potential'] as num?)?.toDouble(),
      category: json['category'] as String?,
    );
  }
}

class TransactionFilter {
  String? bankName;
  String? category;
  String? classification;
  String? startDate;
  String? endDate;
  String? search;
  double? minAmount;
  double? maxAmount;
  String? type;
  int limit;
  int offset;

  TransactionFilter({
    this.bankName,
    this.category,
    this.classification,
    this.startDate,
    this.endDate,
    this.search,
    this.minAmount,
    this.maxAmount,
    this.type,
    this.limit = 100,
    this.offset = 0,
  });

  Map<String, String> toQueryParams() {
    final params = <String, String>{};
    if (bankName != null) params['bank_name'] = bankName!;
    if (category != null) params['category'] = category!;
    if (classification != null) params['classification'] = classification!;
    if (startDate != null) params['start_date'] = startDate!;
    if (endDate != null) params['end_date'] = endDate!;
    if (search != null) params['search'] = search!;
    if (minAmount != null) params['min_amount'] = minAmount.toString();
    if (maxAmount != null) params['max_amount'] = maxAmount.toString();
    if (type != null) params['type'] = type!;
    params['limit'] = limit.toString();
    params['offset'] = offset.toString();
    return params;
  }
}
