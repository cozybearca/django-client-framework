from django.contrib.auth.models import Group


def register_default_group(group_name):
    def make_decorator(config_group):
        DefaultGroups.group_names[group_name] = config_group

    return make_decorator


def do_nothing(group):
    pass


class DefaultGroups:
    group_names = {
        "anyone": do_nothing,
        "logged_in": do_nothing,
    }

    def __getattr__(self, name):
        if name in self.group_names:
            return Group.objects.get_or_create(name=name)[0]
        else:
            raise AttributeError(f"{name} is not a default group")

    def setup(self):
        for name, config_func in self.group_names.items():
            group = Group.objects.get_or_create(name=name)[0]
            config_func(group)


default_groups = DefaultGroups()
