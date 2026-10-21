from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from functools import wraps

from .account_forms import ManagedAccountForm, TempleGroupForm, safe_role_groups

User = get_user_model()


def _can_manage(user):
    return user.is_authenticated and user.is_staff and user.has_perm("temple.manage_temple_accounts")


def _context(request, title, **extra):
    return {**admin.site.each_context(request), "title": title, **extra}


def account_management_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not _can_manage(request.user):
            return render(request, "admin/temple/forbidden.html", _context(
                request,
                "沒有帳號管理權限",
                signed_in_user=request.user.get_username(),
            ), status=403)
        return view(request, *args, **kwargs)

    return wrapped


@account_management_required
def account_list(request):
    users = User.objects.filter(is_superuser=False).prefetch_related("groups").order_by("username")
    return render(request, "admin/temple/account_list.html", _context(request, "帳號管理", users=users))


@account_management_required
def account_edit(request, user_id=None):
    account = get_object_or_404(User, pk=user_id, is_superuser=False) if user_id else User()
    if account.pk and account.pk == request.user.pk:
        raise PermissionDenied("不可透過此頁修改自己的管理帳號。")
    form = ManagedAccountForm(request.POST or None, instance=account)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "帳號資料已儲存。")
        return redirect("temple-account-list")
    title = "編輯帳號" if account.pk else "新增帳號"
    return render(request, "admin/temple/account_form.html", _context(request, title, form=form))


@account_management_required
def role_list(request):
    roles = Group.objects.filter(pk__in=[group.pk for group in safe_role_groups()]).prefetch_related("permissions").order_by("name")
    return render(request, "admin/temple/role_list.html", _context(request, "角色與權限", roles=roles))


@account_management_required
def role_edit(request, group_id=None):
    if group_id:
        group = get_object_or_404(Group.objects.filter(pk__in=[g.pk for g in safe_role_groups()]), pk=group_id)
    else:
        group = Group()
    form = TempleGroupForm(request.POST or None, instance=group)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "角色與宮廟資料權限已儲存。")
        return redirect("temple-role-list")
    title = "編輯角色" if group.pk else "新增角色"
    return render(request, "admin/temple/role_form.html", _context(request, title, form=form))
