from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create default groups (Analysts, Accountants, Directors) with appropriate permissions.'

    # Permissions mapped by app_label.codename
    GROUP_PERMISSIONS = {
        'کارشناسان': {
            'clients': ['add_client', 'change_client', 'view_client',
                        'add_clientcontact', 'change_clientcontact', 'view_clientcontact',
                        'add_clientdocument', 'change_clientdocument', 'view_clientdocument',
                        'add_clientbankaccount', 'change_clientbankaccount', 'view_clientbankaccount'],
            'guarantees': ['add_guarantee', 'change_guarantee', 'view_guarantee',
                           'add_beneficiary', 'change_beneficiary', 'view_beneficiary',
                           'view_guaranteetype', 'view_feeschedule', 'view_payment'],
            'collaterals': ['add_collateral', 'change_collateral', 'view_collateral',
                            'add_collateraldocument', 'change_collateraldocument', 'view_collateraldocument'],
            'contracts': ['add_contract', 'change_contract', 'view_contract',
                          'view_documenttemplate'],
            'creditframework': ['view_creditevaluation', 'view_credittier',
                                'view_scorecardfactor'],
            'portal': ['view_guaranteerequest', 'change_guaranteerequest'],
        },
        'حسابداران': {
            'clients': ['view_client', 'view_clientbankaccount'],
            'guarantees': ['view_guarantee', 'change_guarantee',
                           'add_payment', 'change_payment', 'view_payment',
                           'view_feeschedule'],
            'contracts': ['view_contract'],
            'creditframework': ['view_creditevaluation'],
        },
        'مدیران': {
            'clients': ['add_client', 'change_client', 'delete_client', 'view_client',
                        'view_clientcontact', 'view_clientdocument', 'view_clientbankaccount'],
            'guarantees': ['add_guarantee', 'change_guarantee', 'delete_guarantee', 'view_guarantee',
                           'add_guaranteetype', 'change_guaranteetype', 'view_guaranteetype',
                           'view_beneficiary', 'view_feeschedule', 'view_payment'],
            'collaterals': ['view_collateral', 'change_collateral'],
            'contracts': ['add_contract', 'change_contract', 'view_contract',
                          'add_documenttemplate', 'change_documenttemplate', 'view_documenttemplate'],
            'creditframework': ['add_creditevaluation', 'change_creditevaluation', 'view_creditevaluation',
                                'add_credittier', 'change_credittier', 'view_credittier',
                                'add_scorecardfactor', 'change_scorecardfactor', 'view_scorecardfactor',
                                'add_scorecardcategory', 'change_scorecardcategory', 'view_scorecardcategory',
                                'add_directoroverride', 'view_directoroverride'],
            'portal': ['view_guaranteerequest', 'change_guaranteerequest'],
        },
    }

    def handle(self, *args, **options):
        for group_name, app_perms in self.GROUP_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            status = 'Created' if created else 'Updated'

            permissions = []
            for app_label, codenames in app_perms.items():
                for codename in codenames:
                    try:
                        perm = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename,
                        )
                        permissions.append(perm)
                    except Permission.DoesNotExist:
                        self.stderr.write(
                            self.style.WARNING(f'  Permission not found: {app_label}.{codename}')
                        )

            group.permissions.set(permissions)
            self.stdout.write(
                self.style.SUCCESS(f'{status} group "{group_name}" with {len(permissions)} permissions')
            )
