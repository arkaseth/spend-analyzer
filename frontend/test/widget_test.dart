import 'package:flutter_test/flutter_test.dart';
import 'package:spend_analyzer/app.dart';

void main() {
  testWidgets('App renders main shell', (WidgetTester tester) async {
    await tester.pumpWidget(const SpendAnalyzerApp());
    expect(find.text('Dashboard'), findsOneWidget);
  });
}
