try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User


def create_superuser():
    superuser = User.objects.create_superuser('admin',
                                              'sthzg@gmx.net',
                                              'secret')
    return superuser