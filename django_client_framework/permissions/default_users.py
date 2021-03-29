from django.contrib.auth import get_user_model


def register_default_user(username):
    def make_decorator(config_user):
        DefaultUsers.usernames[username] = config_user

    return make_decorator


def do_nothing(group):
    pass


class DefaultUsers:

    usernames = {}

    def __getattr__(self, name):
        if name in self.usernames:
            return get_user_model().objects.get_or_create(username=name)[0]
        else:
            raise AttributeError(f"{name} is not a default user")

    def setup(self):
        for name, config_func in self.usernames.items():
            user = get_user_model().objects.get_or_create(username=name)[0]
            config_func(user)

    @property
    def anonymous(self):
        return get_user_model().get_anonymous()


default_users = DefaultUsers()
