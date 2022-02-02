from typing import Any, Dict

from django.views.generic import TemplateView

from geocontext.models import UserTier


class PricingPlanTemplateView(TemplateView):
    template_name = 'pricing_plan.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        ctx = super(PricingPlanTemplateView, self).get_context_data(**kwargs)

        ctx['user_tiers'] = UserTier.objects.all()

        return ctx