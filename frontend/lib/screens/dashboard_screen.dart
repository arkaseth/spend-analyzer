import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/analysis_provider.dart';
import '../providers/auth_provider.dart';
import '../providers/transaction_provider.dart';
import '../widgets/auth/user_account_button.dart';
import '../widgets/auth/login_dialog.dart';
import '../models/analysis.dart';
import '../widgets/common/empty_state.dart';
import '../services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AnalysisProvider>().loadAnalysis();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Spend Analyzer'),
        centerTitle: true,
        actions: const [
          UserAccountButton(),
        ],
      ),
      body: Consumer<AnalysisProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && !provider.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          if (provider.error != null && !provider.hasData) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.cloud_off, size: 80, color: Colors.grey.shade300),
                    const SizedBox(height: 16),
                    Text('Could not connect', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    Text('Attempted: ${ApiService.baseUrl}\nError: ${provider.error}',
                        textAlign: TextAlign.center, style: TextStyle(color: Colors.grey.shade600, fontSize: 13)),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        FilledButton.tonal(
                          onPressed: () => provider.loadAnalysis(),
                          child: const Text('Retry'),
                        ),
                        const SizedBox(width: 12),
                        OutlinedButton(
                          onPressed: () => _showChangeUrlDialog(context),
                          child: const Text('Change URL'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          }
          if (!provider.hasData) {
            return EmptyState(
              icon: Icons.account_balance_outlined,
              title: 'No transactions yet',
              subtitle: 'Upload your bank/credit card statements, or load sample demo data to test insights and charts',
              action: 'Sign In / Account',
              onAction: () => LoginDialog.show(context),
              secondaryAction: 'Explore with Demo Data',
              onSecondaryAction: () async {
                final auth = context.read<AuthProvider>();
                final success = await auth.loadDemoData();
                if (success && context.mounted) {
                  context.read<TransactionProvider>().loadTransactions();
                  context.read<AnalysisProvider>().loadAnalysis();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('✨ Demo data loaded! 35 transactions across 3 months.')),
                  );
                }
              },
            );
          }
          return RefreshIndicator(
            onRefresh: () => provider.loadAnalysis(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildSummaryGrid(provider.analysis!),
                  const SizedBox(height: 24),
                  _buildSectionTitle(context, 'Monthly Trends'),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 220,
                    child: _MonthlyBarChart(provider.analysis!.monthlyTrends),
                  ),
                  const SizedBox(height: 24),
                  _buildSectionTitle(context, 'Category Breakdown'),
                  const SizedBox(height: 12),
                  SizedBox(
                    height: 300,
                    child: _CategoryPieChart(provider.analysis!.categoryBreakdown),
                  ),
                  const SizedBox(height: 24),
                  _buildSectionTitle(context, 'Quick Insights'),
                  const SizedBox(height: 12),
                  ...provider.analysis!.insights.take(3).map(
                    (i) => _InsightCard(insight: i),
                  ),
                  const SizedBox(height: 32),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildSummaryGrid(Analysis analysis) {
    return LayoutBuilder(
      builder: (context, constraints) {
        return Row(
          children: [
            Expanded(child: _SummaryCard(
              title: 'Total Spend',
              value: '₹${analysis.totalSpend.toStringAsFixed(0)}',
              icon: Icons.payments,
              color: Theme.of(context).colorScheme.primary,
            )),
            const SizedBox(width: 12),
            Expanded(child: _SummaryCard(
              title: 'Mandatory',
              value: '${analysis.mandatoryPercentage.toStringAsFixed(0)}%',
              subtitle: '₹${analysis.mandatorySpend.toStringAsFixed(0)}',
              icon: Icons.shield,
              color: const Color(0xFF2E7D32),
            )),
          ],
        );
      },
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Text(title, style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w600));
  }

  void _showChangeUrlDialog(BuildContext context) {
    final controller = TextEditingController(text: ApiService.baseUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Backend API URL'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Enter the backend URL (e.g. http://127.0.0.1:8000 or http://localhost:8000):',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                labelText: 'API Base URL',
              ),
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              children: [
                ActionChip(
                  label: const Text('127.0.0.1:8000'),
                  onPressed: () => controller.text = 'http://127.0.0.1:8000',
                ),
                ActionChip(
                  label: const Text('localhost:8000'),
                  onPressed: () => controller.text = 'http://localhost:8000',
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () {
              final newUrl = controller.text.trim();
              if (newUrl.isNotEmpty) {
                ApiService.setBaseUrl(newUrl);
                Navigator.pop(ctx);
                context.read<AnalysisProvider>().loadAnalysis();
              }
            },
            child: const Text('Save & Reconnect'),
          ),
        ],
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final String title;
  final String value;
  final String? subtitle;
  final IconData icon;
  final Color color;

  const _SummaryCard({required this.title, required this.value, this.subtitle, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 12),
            Text(title, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey.shade600)),
            const SizedBox(height: 4),
            Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            if (subtitle != null) ...[
              const SizedBox(height: 2),
              Text(subtitle!, style: Theme.of(context).textTheme.bodySmall),
            ],
          ],
        ),
      ),
    );
  }
}

class _MonthlyBarChart extends StatelessWidget {
  final List<MonthlyTrend> trends;
  const _MonthlyBarChart(this.trends);

  @override
  Widget build(BuildContext context) {
    if (trends.isEmpty) return const Center(child: Text('No trend data'));
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 24, 16, 12),
        child: BarChart(
          BarChartData(
            alignment: BarChartAlignment.spaceAround,
            maxY: trends.fold<double>(0, (max, t) => t.total > max ? t.total : max) * 1.1,
            barTouchData: BarTouchData(enabled: true),
            titlesData: FlTitlesData(
              leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40, getTitlesWidget: (v, _) => Text('₹${(v / 1000).toInt()}k', style: const TextStyle(fontSize: 10)))),
              bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) {
                final idx = v.toInt();
                if (idx >= 0 && idx < trends.length) {
                  return Padding(padding: const EdgeInsets.only(top: 4), child: Text(trends[idx].month.split(' ')[0], style: const TextStyle(fontSize: 9)));
                }
                return const Text('');
              })),
              rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
              topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
            ),
            gridData: FlGridData(show: true, drawVerticalLine: false, horizontalInterval: null),
            borderData: FlBorderData(show: false),
            barGroups: List.generate(trends.length, (i) {
              final t = trends[i];
              return BarChartGroupData(x: i, barRods: [
                BarChartRodData(toY: t.mandatory, color: const Color(0xFF2E7D32), width: 12, borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(4))),
                BarChartRodData(toY: t.discretionary, color: const Color(0xFFFF8F00), width: 12, borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(4))),
              ]);
            }),
          ),
        ),
      ),
    );
  }
}

class _CategoryPieChart extends StatelessWidget {
  final List<CategoryBreakdown> categories;
  const _CategoryPieChart(this.categories);

  @override
  Widget build(BuildContext context) {
    if (categories.isEmpty) return const Center(child: Text('No category data'));
    final top = categories.where((c) => c.percentage > 2).toList();
    final others = categories.where((c) => c.percentage <= 2).toList();
    final display = [...top];
    if (others.isNotEmpty) {
      display.add(CategoryBreakdown(
        category: 'Others',
        classification: '',
        total: others.fold<double>(0, (s, c) => s + c.total),
        count: others.fold<int>(0, (s, c) => s + c.count),
        percentage: others.fold<double>(0, (s, c) => s + c.percentage),
      ));
    }

    final colors = [
      const Color(0xFF2E7D32), const Color(0xFFFF8F00), const Color(0xFF1565C0),
      const Color(0xFF6A1B9A), const Color(0xFFD84315), const Color(0xFF00838F),
      const Color(0xFFAD1457), const Color(0xFF558B2F), const Color(0xFF283593),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: PieChart(
                PieChartData(
                  sectionsSpace: 2,
                  centerSpaceRadius: 30,
                  sections: List.generate(display.length, (i) {
                    return PieChartSectionData(
                      color: colors[i % colors.length],
                      value: display[i].percentage,
                      title: '${display[i].percentage.toStringAsFixed(0)}%',
                      titleStyle: const TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
                      radius: 50,
                    );
                  }),
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: List.generate(display.length, (i) {
                  final c = display[i];
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Row(
                      children: [
                        Container(width: 10, height: 10, decoration: BoxDecoration(color: colors[i % colors.length], borderRadius: BorderRadius.circular(2))),
                        const SizedBox(width: 6),
                        Expanded(child: Text(c.category, style: const TextStyle(fontSize: 11), overflow: TextOverflow.ellipsis)),
                      ],
                    ),
                  );
                }),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InsightCard extends StatelessWidget {
  final Insight insight;
  const _InsightCard({required this.insight});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: CircleAvatar(
          backgroundColor: insight.savingsPotential != null ? const Color(0xFFE8F5E9) : Colors.grey.shade100,
          child: Icon(
            insight.savingsPotential != null ? Icons.savings : Icons.info_outline,
            color: insight.savingsPotential != null ? const Color(0xFF2E7D32) : Colors.grey.shade600,
          ),
        ),
        title: Text(insight.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
        subtitle: Text(insight.description, style: const TextStyle(fontSize: 12)),
      ),
    );
  }
}
