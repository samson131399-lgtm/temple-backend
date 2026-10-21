from django.db import models

# Create your models here.
from django.db import models


class Devotee(models.Model):
    name = models.CharField("姓名", max_length=100)
    phone = models.CharField("聯絡電話", max_length=30, blank=True)
    address = models.CharField("通訊地址", max_length=255, blank=True)
    contact_consent = models.BooleanField("同意聯絡", default=False)
    joined_on = models.DateField("加入日期", null=True, blank=True)
    note = models.TextField("備註", blank=True)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "信眾"
        verbose_name_plural = "信眾"
        permissions = [
            ("export_devotee", "Can export devotee data"),
        ]

    def __str__(self):
        return self.name
class FinanceRecord(models.Model):
    INCOME = "income"
    EXPENSE = "expense"
    TYPE_CHOICES = [
        (INCOME, "收入"),
        (EXPENSE, "支出"),
    ]

    record_type = models.CharField("收支類型", max_length=10, choices=TYPE_CHOICES)
    title = models.CharField("項目名稱", max_length=150)
    category = models.CharField("類別", max_length=80)
    amount = models.DecimalField("金額", max_digits=12, decimal_places=0)
    transaction_date = models.DateField("日期")
    receipt_number = models.CharField("收據／憑證編號", max_length=100, blank=True)
    handled_by = models.CharField("經手人", max_length=100, blank=True)
    note = models.TextField("備註", blank=True)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)

    class Meta:
        ordering = ["-transaction_date"]
        verbose_name = "收支紀錄"
        verbose_name_plural = "收支紀錄"
        permissions = [
            ("export_financerecord", "Can export finance records"),
        ]

    def __str__(self):
        return f"{self.get_record_type_display()}｜{self.title}｜{self.amount}"
class TempleEvent(models.Model):
    STATUS_CHOICES = [
        ("preparing", "籌備中"),
        ("open", "報名中"),
        ("full", "已額滿"),
        ("ended", "已結束"),
    ]

    name = models.CharField("活動名稱", max_length=150)
    event_date = models.DateField("活動日期")
    event_time = models.CharField("活動時間", max_length=100, blank=True)
    location = models.CharField("活動地點", max_length=150, blank=True)
    capacity = models.PositiveIntegerField("報名名額", default=50)
    status = models.CharField(
        "活動狀態",
        max_length=20,
        choices=STATUS_CHOICES,
        default="preparing",
    )
    fee_amount = models.DecimalField(
        "活動費用（元）",
        max_digits=12,
        decimal_places=0,
        default=0,
    )
    description = models.TextField("活動說明", blank=True)
    created_at = models.DateTimeField("建立時間", auto_now_add=True)
    participants = models.ManyToManyField(
        "Devotee",
        through="EventRegistration",
        related_name="registered_events",
        blank=True,
        verbose_name="報名信眾",
    )

    class Meta:
        ordering = ["event_date"]
        verbose_name = "活動"
        verbose_name_plural = "活動"
        permissions = [
            ("export_tempevent", "Can export temple events"),
            ("view_temple_reports", "Can view temple reports"),
            ("export_temple_reports", "Can export temple reports"),
            ("manage_temple_accounts", "Can manage temple accounts and roles"),
        ]

    def __str__(self):
        return self.name
class EventFeeItem(models.Model):
    event = models.ForeignKey(
        TempleEvent,
        on_delete=models.CASCADE,
        related_name="fee_items",
        verbose_name="所屬活動",
    )
    name = models.CharField("費用項目", max_length=100)
    amount = models.DecimalField("金額", max_digits=12, decimal_places=0, default=0)
    note = models.CharField("備註", max_length=200, blank=True)

    class Meta:
        verbose_name = "活動費用項目"
        verbose_name_plural = "活動費用項目"

    def __str__(self):
        return f"{self.name}｜{self.amount}"


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ("pending", "待確認"),
        ("confirmed", "已確認"),
        ("cancelled", "已取消"),
    ]

    event = models.ForeignKey(
        TempleEvent,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name="活動",
    )
    devotee = models.ForeignKey(
        Devotee,
        on_delete=models.PROTECT,
        related_name="event_registrations",
        verbose_name="報名信眾",
    )
    registered_at = models.DateTimeField("報名時間", auto_now_add=True)
    status = models.CharField(
        "報名狀態",
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )
    amount_paid = models.DecimalField("已繳金額", max_digits=12, decimal_places=0, default=0)
    note = models.CharField("備註", max_length=200, blank=True)

    class Meta:
        ordering = ["-registered_at"]
        verbose_name = "活動報名"
        verbose_name_plural = "活動報名"
        constraints = [
            models.UniqueConstraint(
                fields=["event", "devotee"],
                name="unique_devotee_per_event",
            ),
        ]

    def __str__(self):
        return f"{self.event}｜{self.devotee}"
