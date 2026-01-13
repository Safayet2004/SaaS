import re
import helpers.billing
from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import Group, Permission
from django.conf import settings
import stripe


User = settings.AUTH_USER_MODEL # "auth.User"

ALLOW_CUSTOM_GROUPS = True
SUBSCRIPTION_PERMISSIONS = [
    ("advanced", "Advanced Perm"), # subscriptions.advanced
    ("pro", "Pro Perm"), # subscriptions.pro
    ("basic", "Basic Perm"), # subscriptions.basic
    ("basic-ai", "Basic AI Perm") # subscriptions.basic-ai
]


# Create your models here.
class Subscription(models.Model):
    """
    Subscription Plan = Stripe Product
    """

    name = models.CharField(max_length=100)
    subtitle = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission, 
    limit_choices_to={
        "content_type__app_label": "subscriptions", 
        "codename__in": [x[0] for x in SUBSCRIPTION_PERMISSIONS]
        }
    )
    stripe_id = models.CharField(max_length=100, blank=True, null=True)

    order = models.IntegerField(default=-1, help_text="Orderding on django pricing page")
    featured = models.BooleanField(default=True, help_text="Featured on Django pricing page")
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    features = models.TextField(help_text="List of features separated by comma", blank=True, null=True)

    class Meta:
        ordering = ['order', 'featured', '-updated']
        permissions = SUBSCRIPTION_PERMISSIONS

    def get_features_as_list(self):
        if not self.features:
            return []
        return [x.strip() for x in self.features.splitlines() if x.strip()]

    def __str__(self):
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                name=self.name,
                metadata={
                    "subscription_plan_id": self.id,
                },raw=False)
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)


class SubscriptionPrice(models.Model):
    """
    Subscription Price = Stripe Price
    """
    class IntervalChoices(models.TextChoices):
        MONTHLY = "month", "Monthly"
        YEARLY = "year", "Yearly"

    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True)
    stripe_id = models.CharField(max_length=100, blank=True, null=True)
    interval = models.CharField(
        max_length=100, 
        default=IntervalChoices.MONTHLY, 
        choices=IntervalChoices.choices # get_<field_name>_display
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, default=99.99)
    order = models.IntegerField(default=-1, help_text='Ordering on Django pricing page')
    featured = models.BooleanField(default=True, help_text='Featured on Django pricing page')
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['subscription__order', 'order', 'featured', '-updated']
    
    @property
    def display_features_list(self):
        if not self.subscription:
            return []
        return self.subscription.get_features_as_list()
    
    @property
    def display_sub_name(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.name
    
    @property
    def display_sub_subtitle(self):
        if not self.subscription:
            return "Plan"
        return self.subscription.subtitle
    
    @property
    def product_stripe_id(self):
        if not self.subscription:
            return None
        return self.subscription.stripe_id
    
    @property
    def stripe_price(self):
        """
        Remove decimal places
        """
        return int(self.price * 100)
    
    @property
    def stripe_currency(self):
        return "usd"
    
    
    def save(self, *args, **kwargs):
        if (not self.stripe_id and self.product_stripe_id is not None):
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency,
                unit_amount=self.stripe_price,
                interval=self.interval,
                product=self.product_stripe_id,
                metadata={
                    "subscription_plan_price_id": self.id
                },
                raw=False
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)    


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)

    if not ALLOW_CUSTOM_GROUPS:
        # Core django auth behaviour
        user.groups.set(groups_ids)
    else:
        subs_qs = Subscription.objects.filter(active=True).exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list('groups__id', flat=True)
        subs_groups_set = set(subs_groups)
        groups_ids_set = set(groups_ids)

        current_groups = user.groups.all().values_list('id', flat=True)
        current_groups_set = set(current_groups) - subs_groups_set
        
        final_group_ids = list(groups_ids_set | current_groups_set)
        # Core django auth behaviour
        user.groups.set(final_group_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)