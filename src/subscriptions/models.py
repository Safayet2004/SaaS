from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import Group, Permission
from django.conf import settings
import helpers.billing

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
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group)
    permissions = models.ManyToManyField(Permission, 
    limit_choices_to={
        "content_type__app_label": "subscriptions", 
        "codename__in": [x[0] for x in SUBSCRIPTION_PERMISSIONS]
        }
    )
    stripe_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        permissions = SUBSCRIPTION_PERMISSIONS

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            try:
                stripe_id = helpers.billing.create_product(
                    name=self.name,
                    metadata={
                        "subscription_plan_id": self.id,
                    },raw=False)
                self.stripe_id = stripe_id
            except Exception as e:
                print(f"Stripe error: {e}")
                
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"
    


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups = subscription_obj.groups.all()
    if not ALLOW_CUSTOM_GROUPS:
        # Core django auth behaviour
        user.groups.set(groups)
    else:
        subs_qs = Subscription.objects.filter(active=True).exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list('groups__id', flat=True)
        subs_groups_set = set(subs_groups)
        
        groups_ids = groups.values_list('id', flat=True)
        groups_ids_set = set(groups_ids)

        current_groups = user.groups.all().values_list('id', flat=True)
        current_groups_set = set(current_groups) - subs_groups_set
        
        final_groups_ids = list(groups_ids_set | current_groups_set)
        # Core django auth behaviour
        user.groups.set(final_groups_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)