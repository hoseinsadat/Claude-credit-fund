from django.db import models


class DashboardSnapshot(models.Model):
    """Cache for expensive dashboard aggregations."""
    report_type = models.CharField('نوع گزارش', max_length=50)
    data = models.JSONField('داده', default=dict)
    generated_at = models.DateTimeField('تاریخ تولید', auto_now=True)
    parameters = models.JSONField('پارامترها', default=dict, blank=True)

    class Meta:
        verbose_name = 'اسنپ‌شات داشبورد'
        verbose_name_plural = 'اسنپ‌شات‌های داشبورد'

    def __str__(self):
        return f'{self.report_type} ({self.generated_at})'
