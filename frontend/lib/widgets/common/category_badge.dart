import 'package:flutter/material.dart';

class CategoryBadge extends StatelessWidget {
  final String category;
  final String classification;

  const CategoryBadge({super.key, required this.category, required this.classification});

  @override
  Widget build(BuildContext context) {
    Color bgColor;
    Color textColor;

    switch (classification) {
      case 'mandatory':
        bgColor = const Color(0xFFE8F5E9);
        textColor = const Color(0xFF2E7D32);
        break;
      case 'discretionary':
        bgColor = const Color(0xFFFFF8E1);
        textColor = const Color(0xFFFF8F00);
        break;
      case 'income':
        bgColor = const Color(0xFFE3F2FD);
        textColor = const Color(0xFF1565C0);
        break;
      default:
        bgColor = Colors.grey.shade200;
        textColor = Colors.grey.shade700;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        category.length > 12 ? '${category.substring(0, 10)}..' : category,
        style: TextStyle(fontSize: 10, color: textColor, fontWeight: FontWeight.w500),
      ),
    );
  }
}
