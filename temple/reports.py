import csv
from datetime import date

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.dateparse import parse_date

from .models import EventRegistration, FinanceRecord, TempleEvent


def _date_range(request):
    today = date.today()
    start = parse_date(request.GET.get("start", "")) or today.replace(day=1)
    end = parse_date(request.GET.get("end", "")) or today
    if start > end:
        start, end = end, start
    return start, end


@staff_member_required
def reports(request):
    if not request.user.has_perm("temple.view_temple_reports"):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    start, end = _date_range(request)
    finances = FinanceRecord.objects.filter(transaction_date__range=(start, end))
    income = finances.filter(record_type=FinanceRecord.INCOME).aggregate(total=Sum("amount"))["total"] or 0
    expenses = finances.filter(record_type=FinanceRecord.EXPENSE).aggregate(total=Sum("amount"))["total"] or 0
    event_rows = list(
        TempleEvent.objects.filter(event_date__range=(start, end))
        .annotate(registration_count=Count("registrations", distinct=True))
        .values("name", "event_date", "status", "capacity", "registration_count")
        .order_by("event_date", "name")
    )
    registration_total = EventRegistration.objects.filter(
        event__event_date__range=(start, end)
    ).exclude(status="cancelled").count()

    if request.GET.get("format") == "csv":
        if not request.user.has_perm("temple.export_temple_reports"):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="temple-report.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["期間", start.isoformat(), end.isoformat()])
        writer.writerow(["收入合計", income])
        writer.writerow(["支出合計", expenses])
        writer.writerow(["收支結餘", income - expenses])
        writer.writerow(["活動報名人次", registration_total])
        writer.writerow([])
        writer.writerow(["活動名稱", "活動日期", "狀態", "名額", "報名人數"])
        for row in event_rows:
            writer.writerow([
                "'" + row["name"] if row["name"].startswith(("=", "+", "-", "@", "\t", "\r")) else row["name"],
                row["event_date"], row["status"], row["capacity"], row["registration_count"],
            ])
        return response

    return render(request, "admin/temple/reports.html", {
        **admin.site.each_context(request),
        "title": "宮廟營運報表",
        "start": start,
        "end": end,
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "registration_total": registration_total,
        "event_rows": event_rows,
        "can_export": request.user.has_perm("temple.export_temple_reports"),
    })
