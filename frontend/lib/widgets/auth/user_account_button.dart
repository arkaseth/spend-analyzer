import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';
import 'login_dialog.dart';

class UserAccountButton extends StatelessWidget {
  const UserAccountButton({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (context, auth, _) {
        if (auth.isAuthenticated) {
          final name = auth.displayName;
          final initial = name.isNotEmpty ? name[0].toUpperCase() : 'U';
          return Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ActionChip(
              avatar: CircleAvatar(
                radius: 11,
                backgroundColor: Theme.of(context).colorScheme.primary,
                child: Text(
                  initial,
                  style: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ),
              label: Text(
                name,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
              ),
              onPressed: () => LoginDialog.show(context),
            ),
          );
        }

        if (auth.isDemoMode) {
          return Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ActionChip(
              avatar: const Icon(Icons.auto_awesome, size: 16, color: Colors.blue),
              label: const Text('Demo Mode', style: TextStyle(fontSize: 13, color: Colors.blue, fontWeight: FontWeight.w600)),
              backgroundColor: Colors.blue.shade50,
              side: BorderSide(color: Colors.blue.shade200),
              onPressed: () => LoginDialog.show(context),
            ),
          );
        }

        if (auth.isTransientMode) {
          return Padding(
            padding: const EdgeInsets.only(right: 12),
            child: ActionChip(
              avatar: const Icon(Icons.visibility_off, size: 16, color: Colors.amber),
              label: const Text('Incognito', style: TextStyle(fontSize: 13, color: Colors.amber, fontWeight: FontWeight.w600)),
              backgroundColor: Colors.amber.shade50,
              side: BorderSide(color: Colors.amber.shade300),
              onPressed: () => LoginDialog.show(context),
            ),
          );
        }

        return Padding(
          padding: const EdgeInsets.only(right: 12),
          child: TextButton.icon(
            style: TextButton.styleFrom(
              visualDensity: VisualDensity.compact,
            ),
            icon: const Icon(Icons.account_circle_outlined, size: 18),
            label: const Text('Sign In / Demo'),
            onPressed: () => LoginDialog.show(context),
          ),
        );
      },
    );
  }
}
