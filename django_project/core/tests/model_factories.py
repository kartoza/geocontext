import factory

from django.contrib.auth.models import User
from django.utils import timezone


class UserF(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"username{n}")
    first_name = factory.Sequence(lambda n: f"first_name{n}")
    last_name = factory.Sequence(lambda n: f"last_name{n}")
    email = factory.Sequence(lambda n: f"email{n}@example.com")
    password = ''
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = timezone.datetime(2000, 1, 1).replace(tzinfo=timezone.utc)
    date_joined = timezone.datetime(1999, 1, 1).replace(
        tzinfo=timezone.utc)

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserF, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user
