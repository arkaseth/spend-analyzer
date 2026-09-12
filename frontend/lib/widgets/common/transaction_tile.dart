import 'package:flutter/material.dart';
import '../../models/transaction.dart';
import 'category_badge.dart';

class TransactionTile extends StatelessWidget {
  final Transaction transaction;
  final VoidCallback? onTap;

  const TransactionTile({super.key, required this.transaction, this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDebit = transaction.isDebit;
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      transaction.description,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(transaction.transactionDate, style: TextStyle(fontSize: 11, color: Colors.grey.shade600)),
                        const SizedBox(width: 8),
                        Text(transaction.bankName, style: TextStyle(fontSize: 11, color: Colors.grey.shade500)),
                        if (transaction.isEmi) ...[
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                            decoration: BoxDecoration(color: Colors.orange.shade100, borderRadius: BorderRadius.circular(4)),
                            child: Text('EMI', style: TextStyle(fontSize: 9, color: Colors.orange.shade800)),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '₹${transaction.amount.toStringAsFixed(0)}',
                    style: TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 15,
                      color: isDebit ? Colors.red.shade700 : const Color(0xFF2E7D32),
                    ),
                  ),
                  const SizedBox(height: 4),
                  CategoryBadge(category: transaction.category, classification: transaction.classification),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
