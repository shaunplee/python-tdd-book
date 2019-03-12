from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models


class List(models.Model):
    """
    Represents a single to-do list.
    """
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    def get_absolute_url(self):
        """
        Returns the absolute url to this list.
        """
        return reverse('view_list', args=[self.id])

    @property
    def name(self):
        """
        Returns the name of the list (first element)
        """
        return self.item_set.first().text

    @staticmethod
    def create_new(first_item_text, owner=None):
        """
        Create a new list. Takes an optional `owner` parameter identifying the
        user who owns this list.
        """
        list_ = List.objects.create(owner=owner)
        Item.objects.create(text=first_item_text, list=list_)
        return list_


class Item(models.Model):
    """
    Represents a single to-do item that goes into a List.
    """
    text = models.TextField(default="")
    list = models.ForeignKey(List, default=None)

    class Meta:
        ordering = ('id', )
        unique_together = ('list', 'text')

    def __str__(self):
        return self.text
