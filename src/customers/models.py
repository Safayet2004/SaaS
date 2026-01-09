from django.db import models
from django.conf import settings
import helpers.billing

User = settings.AUTH_USER_MODEL 

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username}"
    
    def save(self, *args, **kwargs):
        email = self.user.email
        if not self.stripe_id:
            if email and email.strip():
                try:
                    stripe_id = helpers.billing.create_customer(email=email, raw=False)
                    self.stripe_id = stripe_id
                except Exception as e:
                    print(f"Stripe error: {e}")
                    
        super().save(*args, **kwargs)