import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/analysis_provider.dart';
import '../models/analysis.dart';
import '../widgets/common/empty_state.dart';

class InsightsScreen extends StatelessWidget {
  const InsightsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Insights'),
        centerTitle: true,
      ),
      body: Consumer<AnalysisProvider>(
        builder: (context, provider, _) {
          if (provider.isLoading && !provider.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          if (!provider.hasData) {
            return const EmptyState(
              icon: Icons.lightbulb_outline,
              title: 'No insights yet',
              subtitle: 'Upload statements to get personalized insights',
            );
          }
          final analysis = provider.analysis!;
          return RefreshIndicator(
            onRefresh: () => provider.loadAnalysis(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _MetricRow(analysis: analysis),
                const SizedBox(height: 20),
                Text('Actionable Insights', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                ...analysis.insights.map((i) => _InsightCard(insight: i)),
                const SizedBox(height: 24),
                Text('Spending by Category', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                const SizedBox(height: 12),
                ...analysis.categoryBreakdown.where((c) => c.total > 0).map((c) => _CategoryBar(category: c)),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  final Analysis analysis;
  const _MetricRow({required this.analysis});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        _MiniCard(
          label: 'Mandatory',
          value: '${analysis.mandatoryPercentage.toStringAsFixed(0)}%',
          color: const Color(0xFF2E7D32),
          icon: Icons.shield,
        ),
        const SizedBox(width: 12),
        _MiniCard(
          label: 'Discretionary',
          value: '${analysis.discretionaryPercentage.toStringAsFixed(0)}%',
          color: const Color(0xFFFF8F00),
          icon: Icons.shopping_bag,
        ),
        const SizedBox(width: 12),
        _MiniCard(
          label: 'Transactions',
          value: '${analysis.totalTransactions}',
          color: Theme.of(context).colorScheme.primary,
          icon: Icons.receipt_long,
        ),
      ],
    );
  }
}

class _MiniCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final IconData icon;
  const _MiniCard({required this.label, required this.value, required this.color, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Icon(icon, color: color, size: 22),
              const SizedBox(height: 8),
              Text(value, style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: color)),
              const SizedBox(height: 2),
              Text(label, style: const TextStyle(fontSize: 11), overflow: TextOverflow.ellipsis),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoryBar extends StatelessWidget {
  final CategoryBreakdown category;
  const _CategoryBar({required this.category});

  @override
  Widget build(BuildContext context) {
    final color = category.isMandatory ? const Color(0xFF2E7D32) : (category.isDiscretionary ? const Color(0xFFFF8F00) : Colors.grey);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(child: Text(category.category, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14))),
                  Text('₹${category.total.toStringAsFixed(0)}', style: const TextStyle(fontWeight: FontWeight.w600)),
                  const SizedBox(width: 8),
                  Text('${category.percentage.toStringAsFixed(0)}%', style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 8),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: category.percentage / 100,
                  backgroundColor: Colors.grey.shade200,
                  color: color,
                  minHeight: 6,
                ),
              ),
            ],
          ),
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
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: insight.savingsPotential != null ? const Color(0xFFE8F5E9) : Colors.grey.shade100,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                insight.savingsPotential != null ? Icons.savings : Icons.trending_up,
                color: insight.savingsPotential != null ? const Color(0xFF2E7D32) : Colors.grey.shade600,
                size: 20,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(insight.title, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                  const SizedBox(height: 4),
                  Text(insight.description, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
