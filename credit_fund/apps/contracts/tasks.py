import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_document_async(template_id, context_data, format='pdf'):
    """Generate a document asynchronously for heavy workloads."""
    from .models import DocumentTemplate

    try:
        template = DocumentTemplate.objects.get(id=template_id)
        logger.info('Generating %s document from template: %s', format, template.code)

        if format == 'pdf' and template.template_content:
            from .document_generator import PDFGenerator
            return PDFGenerator.generate(template.template_content, context_data)
        elif format == 'docx' and template.file:
            from .document_generator import DOCXGenerator
            return DOCXGenerator.generate(template.file.path, context_data)
    except DocumentTemplate.DoesNotExist:
        logger.error('Template %s not found', template_id)
    return None
