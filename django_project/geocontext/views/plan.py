from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import JsonResponse
from django.views.generic import ListView
from rest_framework.views import APIView
from geocontext.models.user_tier import UserTier
from geocontext.models.user_profile import UserProfile


class PlanListView(ListView):
    """List view for UserTier."""

    model = UserTier
    template_name = 'geocontext/plan.html'
    object_name = 'plan_list'


class UpdatePlanApiView(UserPassesTestMixin, APIView):

    def test_func(self):
        return self.request.user.is_active

    def get(self, request, *args):
        user_tier_id = request.GET.get('user_tier', None)
        user_tier = None

        messages = {
            'success': 'OK'
        }
        if user_tier_id:
            try:
                user_tier = UserTier.objects.get(id=user_tier_id)
            except UserTier.DoesNotExist:
                return JsonResponse({'error': 'UserTier does not exist'})

        if user_tier:
            try:
                user_profile = UserProfile.objects.get(user=request.user.id)
                user_profile.user_tier = user_tier
                user_profile.save()
                messages['Plan changed'] = UserProfile.objects.get(user=request.user.id).user.username

            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=request.user.id, user_tier=user_tier)

        return JsonResponse(messages)

