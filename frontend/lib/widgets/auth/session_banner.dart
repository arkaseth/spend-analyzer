import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import '../../providers/transaction_provider.dart';
import '../../providers/analysis_provider.dart';

class SessionBanner extends StatelessWidget {
  const SessionBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        if (!auth.isTransientMode && !auth.isDemoMode) {
          return const SizedBox.shrink();
        }

        final isDemo = auth.isDemoMode;
        final theme = Theme.of(context);
        final bgColor = isDemo ? Colors.blue.shade50 : Colors.amber.shade50;
        final borderColor = isDemo ? Colors.blue.shade200 : Colors.amber.shade300;
        final textColor = isDemo ? Colors.blue.shade900 : Colors.amber.shade900;
        final icon = isDemo ? Icons.auto_awesome : Icons.visibility_off;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: bgColor,
            border: Border(bottom: BorderSide(color: borderColor)),
          ),
          child: Row(
            children: [
              Icon(icon, size: 18, color: textColor),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  isDemo
                      ? 'Exploring Sample Data — Try out analytics, filters, and charts without uploading real statements.'
                      : 'Incognito Mode — Data uploaded in this session is temporary and will be deleted when you exit.',
                  style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w500, color: textColor),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.tonal(
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  visualDensity: VisualDensity.compact,
                ),
                onPressed: () async {
                  if (isDemo) {
                    await auth.clearDemoData();
                  } else {
                    await auth.exitTransientMode();
                  }
                  if (context.mounted) {
                    context.read<TransactionProvider>().loadTransactions();
                    context.read<AnalysisProvider>().loadAnalysis();
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text(isDemo ? 'Demo data cleared' : 'Incognito session ended & data purged')),
                    );
                  }
                },
                child: Text(
                  isDemo ? 'Clear Demo' : 'Exit & Purge',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
