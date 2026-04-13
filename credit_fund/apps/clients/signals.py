from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Client, LegalPersonProfile, RealPersonProfile


@receiver(post_save, sender=Client)
def create_client_profile(sender, instance, created, **kwargs):
    """Auto-create the appropriate profile based on client_type."""
    if not created:
        return

    if instance.client_type == Client.ClientType.LEGAL:
        if not hasattr(instance, 'legal_profile'):
            LegalPersonProfile.objects.create(client=instance, company_name='')
    else:
        if not hasattr(instance, 'real_profile'):
            RealPersonProfile.objects.create(
                client=instance, first_name='', last_name='', national_code='',
            )
