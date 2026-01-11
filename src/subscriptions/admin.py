from django.contrib import admin

from .models import Subscription, SubscriptionPrice, UserSubscription
# Register your models here.
class SubscriptionPrice(admin.StackedInline):
    model = SubscriptionPrice
    extra = 0
    readonly_fields = ['stripe_id']
    can_delete = False


class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionPrice]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']

admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(UserSubscription)