"""
Audit app uses django-auditlog for automatic model change tracking.
All critical models are registered in apps.py ready() method.
No custom models needed — auditlog provides its own LogEntry model.
"""
