"""DEPRECATED — endi apps/common/admin_api/ paketidan foydalaning.

Eski importlar (`from apps.common.admin_views import DashboardStatsView`)
sinmasligi uchun qoldirilgan.
"""
from apps.common.admin_api.views import DashboardStatsView, RevenueStatsView

__all__ = ["DashboardStatsView", "RevenueStatsView"]
