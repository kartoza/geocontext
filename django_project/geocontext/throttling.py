from rest_framework import throttling

from django.conf import settings

from geocontext.models import UserProfile


class UserTierRateThrottle(throttling.UserRateThrottle):
    def allow_request(self, request, view):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
        """
        if settings.ENABLE_API_TOKEN:
            token = request.auth.key
            if not token:
                return False
            user = UserProfile.objects.filter(
                user__auth_token__key=token
            ).first()
            if user and user.user_tier:
                self.rate = user.user_tier.request_limit
                if self.rate == '-': # Unlimited, always true
                    return True
        else:
            return True
        self.num_requests, self.duration = self.parse_rate(self.rate)
        return super(UserTierRateThrottle, self).allow_request(request, view)
