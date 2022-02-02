from django.test import TestCase, override_settings

from rest_framework.test import APIRequestFactory

from .unit.model_factories import *
from geocontext.views.api_v2 import GenericAPIView


class TestAPI(TestCase):

    def setUp(self):
        service = ServiceF.create()
        group = GroupF.create()
        GroupServicesF.create(
            service=service,
            group=group
        )
        self.api_url = (
            '/api/v2/query?registry=group&key={}&x=22.910152673721317&'
            'y=-32.53952445888535'.format(
                group.key
        ))

    @override_settings(ENABLE_API_TOKEN=False)
    def test_token_setting_disabled(self):

        view = GenericAPIView.as_view()
        api_factory = APIRequestFactory()

        request = api_factory.get(self.api_url)
        response = view(request)

        self.assertEqual(response.status_code, 200)


    @override_settings(ENABLE_API_TOKEN=True)
    def test_token_setting_enabled(self):
        view = GenericAPIView.as_view()
        api_factory = APIRequestFactory()

        request = api_factory.get(self.api_url)
        response = view(request)

        self.assertEqual(response.status_code, 401)

        user = UserF.create()
        token = user.auth_token.key

        api_url_with_token = self.api_url + '&token=' + token

        request = api_factory.get(api_url_with_token)
        response = view(request)

        self.assertEqual(response.status_code, 200)


    @override_settings(ENABLE_API_TOKEN=True)
    def test_api_throttling(self):
        view = GenericAPIView.as_view()
        api_factory = APIRequestFactory()

        user = UserF.create()
        token = user.auth_token.key

        user_tier = UserTierF.create(
            request_limit='1/day'
        )

        UserProfileF.create(
            user=user,
            user_tier=user_tier
        )

        api_url_with_token = self.api_url + '&token=' + token

        request = api_factory.get(api_url_with_token)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        request = api_factory.get(api_url_with_token)
        response = view(request)

        self.assertEqual(response.status_code, 429) # throttled

