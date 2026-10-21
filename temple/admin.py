import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import (
    Devotee,
    EventFeeItem,
    EventRegistration,
    FinanceRecord,
    TempleEvent,
)


def _csv_response(filename, headers, rows):
    """Build a spreadsheet-friendly CSV response and neutralize formula cells."""
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([
            "'" + value if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
            for value in row
        ])
    return response


@admin.register(Devotee)
class DevoteeAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "address", "contact_consent", "joined_on")
    search_fields = ("name", "phone", "address")
    list_filter = ("contact_consent",)
    actions = ("export_devotees_csv",)

    def has_export_devotee_permission(self, request):
        return request.user.has_perm("temple.export_devotee")

    @admin.action(description="匯出所選信眾資料 CSV", permissions=["export_devotee"])
    def export_devotees_csv(self, request, queryset):
        rows = queryset.order_by("name").values_list(
            "name", "phone", "address", "contact_consent", "joined_on", "note"
        )
        return _csv_response(
            "devotees.csv",
            ("姓名", "聯絡電話", "通訊地址", "同意聯絡", "加入日期", "備註"),
            rows,
        )


@admin.register(FinanceRecord)
class FinanceRecordAdmin(admin.ModelAdmin):
    list_display = (
        "record_type", "title", "category", "amount",
        "transaction_date", "handled_by",
    )
    search_fields = ("title", "category", "receipt_number", "handled_by")
    list_filter = ("record_type", "category", "transaction_date")
    actions = ("export_finance_csv",)

    def has_export_financerecord_permission(self, request):
        return request.user.has_perm("temple.export_financerecord")

    @admin.action(description="匯出所選收支紀錄 CSV", permissions=["export_financerecord"])
    def export_finance_csv(self, request, queryset):
        rows = queryset.order_by("-transaction_date").values_list(
            "record_type", "title", "category", "amount", "transaction_date",
            "receipt_number", "handled_by", "note",
        )
        return _csv_response(
            "finance-records.csv",
            ("收支類型", "項目名稱", "類別", "金額", "日期", "收據／憑證編號", "經手人", "備註"),
            rows,
        )


class EventFeeItemInline(admin.TabularInline):
    model = EventFeeItem
    extra = 1


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 1
    fields = ("devotee", "status", "amount_paid", "note")


@admin.register(TempleEvent)
class TempleEventAdmin(admin.ModelAdmin):
    list_display = (
        "name", "event_date", "location", "status", "capacity", "fee_amount",
    )
    search_fields = ("name", "location")
    list_filter = ("status", "event_date")
    inlines = (EventFeeItemInline, EventRegistrationInline)
    actions = ("export_events_csv",)

    def has_export_tempevent_permission(self, request):
        return request.user.has_perm("temple.export_tempevent")

    @admin.action(description="匯出所選活動資料 CSV", permissions=["export_tempevent"])
    def export_events_csv(self, request, queryset):
        rows = queryset.order_by("event_date").values_list(
            "name", "event_date", "event_time", "location", "status", "capacity",
            "fee_amount", "description",
        )
        return _csv_response(
            "temple-events.csv",
            ("活動名稱", "活動日期", "活動時間", "活動地點", "活動狀態", "報名名額", "活動費用（元）", "活動說明"),
            rows,
        )
