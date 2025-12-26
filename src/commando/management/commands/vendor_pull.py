import helpers

from django.conf import settings
from django.core.management.base import BaseCommand

STATICFILES_VENDOR_DIR = getattr(settings, 
'STATICFILES_VENDOR_DIR')

VENDOR_STATICFILES = {
    "flowbite.min.css": "https://cdnjs.cloudflare.com/ajax/libs/flowbite/3.1.0/flowbite.min.css",
    "flowbite.min.js": "https://cdnjs.cloudflare.com/ajax/libs/flowbite/3.1.0/flowbite.min.js",
    "flowbite.min.js.map": "https://cdnjs.cloudflare.com/ajax/libs/flowbite/3.1.0/flowbite.min.js.map",
}

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        self.stdout.write('Downloading vendor static files...')

        completed_urls = []
        
        for name, url in VENDOR_STATICFILES.items():
            out_path = STATICFILES_VENDOR_DIR / name
            dl_success = helpers.download_to_local(url, out_path)
            if dl_success:
                completed_urls.append(url)
                self.stdout.write(f"Successfully downloaded {name} from {url} to {out_path}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"Failed to download {name} from {url}")
                )

        if set(completed_urls) == set(VENDOR_STATICFILES.values()):
            self.stdout.write(
                self.style.SUCCESS("Successfully updated all vendor files!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Some files were not updated!")
            )