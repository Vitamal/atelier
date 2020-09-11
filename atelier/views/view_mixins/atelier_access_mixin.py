
class AtelierFilterObjectsPreMixin:
    """
    to show objects in established atelier only (for superuser all objects are showed)
    """

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.model.objects.all()  # superuser access all objects
        else:
            # users have access to objects of his atelier only
            return self.model.objects.filter(atelier=self.request.user.atelier)
