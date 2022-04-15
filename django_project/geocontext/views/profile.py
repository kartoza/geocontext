from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from geocontext.models.user_profile import UserProfile
from rest_framework.authtoken.models import Token


class ProfileView(DetailView):
    template_name = 'user/profile.html'
    model = get_user_model()
    slug_field = 'username'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)

        user_profile = UserProfile.objects.get(user=self.object)
        context['plan'] = user_profile.user_tier
        context['token'] = Token.objects.get(user=self.object).key

        return context