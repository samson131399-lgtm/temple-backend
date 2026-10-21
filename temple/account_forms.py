from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

ROLE_PERMISSION_CODENAMES = {
    "add_devotee", "change_devotee", "delete_devotee", "view_devotee", "export_devotee",
    "add_financerecord", "change_financerecord", "delete_financerecord", "view_financerecord", "export_financerecord",
    "add_templeevent", "change_templeevent", "delete_templeevent", "view_templeevent", "export_tempevent",
    "add_eventfeeitem", "change_eventfeeitem", "delete_eventfeeitem", "view_eventfeeitem",
    "add_eventregistration", "change_eventregistration", "delete_eventregistration", "view_eventregistration",
    "view_temple_reports", "export_temple_reports",
}

_PERMISSION_LABELS = {
    "devotee": "信眾資料",
    "financerecord": "收支資料",
    "tempevent": "活動資料",
    "templeevent": "活動資料",
    "eventfeeitem": "活動費用項目",
    "eventregistration": "活動報名資料",
    "temple_reports": "營運報表",
}
_ACTION_LABELS = {
    "view": "查看", "add": "新增", "change": "修改", "delete": "刪除", "export": "匯出",
}


class PermissionChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, permission):
        codename = permission.codename
        action, _, model = codename.partition("_")
        subject = next((label for key, label in _PERMISSION_LABELS.items() if model == key or model.endswith(key)), model)
        if action == "export" and model == "temple_reports":
            subject = "營運報表"
        return f"{subject}－{_ACTION_LABELS.get(action, action)}"


def safe_role_groups():
    """Only expose groups whose entire permission set is within the role allowlist."""
    groups = Group.objects.all().order_by("name")
    return [
        group for group in groups
        if not group.permissions.filter(
            ~Q(content_type__app_label="temple") | ~Q(codename__in=ROLE_PERMISSION_CODENAMES)
        ).exists()
    ]


class TempleGroupForm(forms.ModelForm):
    permissions = PermissionChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="宮廟資料權限",
    )

    class Meta:
        model = Group
        fields = ("name", "permissions")
        labels = {"name": "角色名稱"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = Permission.objects.filter(
            content_type__app_label="temple",
            codename__in=ROLE_PERMISSION_CODENAMES,
        ).select_related("content_type").order_by("content_type__model", "codename")
        if self.instance.pk:
            self.initial["permissions"] = self.instance.permissions.filter(
                content_type__app_label="temple", codename__in=ROLE_PERMISSION_CODENAMES
            )


class ManagedAccountForm(forms.ModelForm):
    role = forms.ModelChoiceField(queryset=Group.objects.none(), label="指派角色")
    password1 = forms.CharField(label="初始密碼", widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label="再次輸入密碼", widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active")
        labels = {
            "username": "登入帳號",
            "first_name": "名字",
            "last_name": "姓氏",
            "email": "電子郵件",
            "is_active": "帳號啟用",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = Group.objects.filter(
            pk__in=[group.pk for group in safe_role_groups()]
        )
        if self.instance.pk:
            self.fields["password1"].required = False
            self.fields["password1"].help_text = "留空表示不變更密碼。"
            self.fields["role"].initial = self.instance.groups.first()

    def clean(self):
        cleaned = super().clean()
        first, second = cleaned.get("password1"), cleaned.get("password2")
        if not self.instance.pk and not first:
            self.add_error("password1", "建立帳號時必須設定初始密碼。")
        if first or second:
            if first != second:
                self.add_error("password2", "兩次輸入的密碼不一致。")
            elif first:
                validate_password(first, self.instance)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # Managed accounts can sign into Django admin but never gain global admin rights.
        user.is_staff = True
        user.is_superuser = False
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
            user.groups.set([self.cleaned_data["role"]])
        return user
