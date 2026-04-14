from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audit'
    verbose_name = 'لاگ تغییرات'

    def ready(self):
        from auditlog.registry import auditlog

        from apps.clients.models import Client
        from apps.collaterals.models import Collateral
        from apps.contracts.models import Contract
        from apps.creditframework.models import CreditEvaluation, DirectorOverride
        from apps.guarantees.models import Guarantee, Payment

        auditlog.register(Client)
        auditlog.register(Guarantee)
        auditlog.register(Collateral)
        auditlog.register(Contract)
        auditlog.register(Payment)
        auditlog.register(CreditEvaluation)
        auditlog.register(DirectorOverride)
