from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()


class Command(BaseCommand):
    help = "Создаёт EmailAddress для старых пользователей без подтверждения"

    def handle(self, *args, **kwargs):
        count = 0
        for user in User.objects.all():
            if user.email and not EmailAddress.objects.filter(user=user).exists():
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=False,
                    primary=True
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Создано записей: {count}"))
