from django.db import models
from django.db.models import Max
from django.urls import reverse

from .utils import check_digit


class LocIdManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(barcode__regex=r'^\d{4}$')


class ItemIdManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(barcode__regex=r'^\d{7}$')


class Identifier(models.Model):
    barcode = models.CharField(max_length=8, primary_key=True)
    linked_code = models.CharField(max_length=16, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    LOC_LEN = 4     # Loc_IDs are four (4) digits
    ITM_LEN = 7     # Itm_IDs are seven (7) digits

    idents = models.Manager()   # default manager
    locIDs = LocIdManager()
    itemIDs = ItemIdManager()

    @classmethod
    def make_loc_id(self):
        qs = self.locIDs.aggregate(Max('barcode'))
        bcm = qs['barcode__max']
        if bcm:     # chop last digit, add one
            val = '{}'.format(1+int(bcm[0:3]))
        else:
            val = '100'
        id = '{}{}'.format(val, check_digit(val))
        return id

    @classmethod
    def make_item_id(self):
        qs = self.itemIDs.aggregate(Max('barcode'))
        bcm = qs['barcode__max']
        if bcm:     # chop last digit, add one
            val = '{}'.format(1+int(bcm[0:6]))
        else:
            val = '100000'
        id = '{}{}'.format(val, check_digit(val))
        return id

    def get_json_url(self):
        return reverse('identifier-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return '{}'.format(self.barcode)
