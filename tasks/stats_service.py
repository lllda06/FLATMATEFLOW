from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from tasks.models import Task, Household


def get_month_period():
    today = date.today()
    start = today.replace(day=1)
    end = (start + relativedelta(months=1)) - timedelta(days=1)
    return start, end


def get_stats_for_household(house: Household):
    start, end = get_month_period()

    completed = (
        Task.objects
        .filter(
            household=house,
            is_completed=True,
            completed_at__date__gte=start,
            completed_at__date__lte=end,
        )
        .values("completed_by__username")
        .annotate(total=Sum("points"))
        .order_by("-total")
    )

    total_points = completed.aggregate(sum_total=Sum("total"))["sum_total"] or 0

    return {
        "period": (start, end),
        "completed": list(completed),  # list для API
        "total_points": total_points
    }