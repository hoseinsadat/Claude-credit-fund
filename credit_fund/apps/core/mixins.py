class UserTrackingAdminMixin:
    """
    Admin mixin that auto-sets created_by/updated_by from request.user in save_model().
    Use this on any ModelAdmin whose model inherits from UserTrackingModel.
    """

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
