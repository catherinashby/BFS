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

    def urlize(self):
        return reverse('identifier-detail', kwargs={'pk': self.barcode})

    def __str__(self):
        return '{}'.format(self.barcode)

    class Meta:
        ordering = ['barcode']


class Location(models.Model):
    identifier = models.OneToOneField(Identifier, on_delete=models.CASCADE,
                                      primary_key=True)
    name = models.CharField(max_length=32, unique=True)
    description = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        ordering = ['identifier']


class Supplier(models.Model):
    #   id
    name = models.CharField(max_length=64, unique=True)
    street = models.CharField(max_length=64, null=True, blank=True)
    street_ext = models.CharField(max_length=64, null=True, blank=True)
    city = models.CharField(max_length=32, null=True, blank=True)
    state = models.CharField(max_length=16, null=True, blank=True)
    zip5 = models.CharField(max_length=5, null=True, blank=True)
    phone_1 = models.CharField(max_length=16, null=True, blank=True)
    phone_2 = models.CharField(max_length=16, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        ordering = ['id']


class ItemTemplate(models.Model):
    identifier = models.OneToOneField(Identifier, on_delete=models.CASCADE,
                                      primary_key=True)
    description = models.CharField(max_length=120)
    brand = models.CharField(max_length=32, null=True, blank=True)
    #   Hoffmann, Timeless Treasures, Moda, .... ; Prym, Clover, Dritz, ....
    content = models.CharField(max_length=32, null=True, blank=True)
    #   cotton, crepe de chine, jersey knit, .... ; book, notion, ....
    part_unit = models.CharField(max_length=32, null=True, blank=True)
    # by the yard, panel, 4 yd cut, .... ; unit, ....
    yardage = models.BooleanField(default=True)
    out_of_stock = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.description)

    class Meta:
        ordering = ['identifier']


class Picture(models.Model):
    #   id
    photo = models.FileField(upload_to='%Y/%m/%d/')
    uploaded = models.DateField(auto_now_add=True)
    item = models.ForeignKey(ItemTemplate, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return 'Photo {}'.format(self.id)

    class Meta:
        ordering = ['id']


class StockBook(models.Model):

    itm = models.OneToOneField(ItemTemplate, on_delete=models.CASCADE,
                               primary_key=True)
    loc = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)
    units = models.PositiveSmallIntegerField(null=True, blank=True)
    eighths = models.PositiveSmallIntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Stock Record for Item {}'.format(self.itm_id)


class Price(models.Model):

    itm = models.OneToOneField(ItemTemplate, on_delete=models.CASCADE,
                               primary_key=True)
    price = models.DecimalField(max_digits=6, decimal_places=2,
                                null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'Price for Item {} is {}'.format(self.itm_id,
                                                self.price)


class Invoice(models.Model):
    # id    (>100)
    vendor = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    received = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Invoice #{} from {}'.format(self.id, self.vendor.name)


class Purchase(models.Model):
    # id
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    item = models.ForeignKey(ItemTemplate, on_delete=models.CASCADE)
    cost = models.DecimalField(max_digits=8, decimal_places=2,
                               null=True, blank=True)

    def __str__(self):
        return 'Inv:{} Item:{}'.format(self.invoice_id, self.item_id)

    class Meta:
        unique_together = ['invoice', 'item']
