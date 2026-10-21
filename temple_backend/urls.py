"""
URL configuration for temple_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from temple.reports import reports
from temple import account_views

admin.site.index_template = "admin/temple_index.html"

urlpatterns = [
    path('admin/reports/', admin.site.admin_view(reports), name='temple-reports'),
    path('admin/reports/export/', admin.site.admin_view(reports), name='temple-reports-export'),
    path('admin/temple-management/accounts/', admin.site.admin_view(account_views.account_list), name='temple-account-list'),
    path('admin/temple-management/accounts/add/', admin.site.admin_view(account_views.account_edit), name='temple-account-add'),
    path('admin/temple-management/accounts/<int:user_id>/', admin.site.admin_view(account_views.account_edit), name='temple-account-edit'),
    path('admin/temple-management/roles/', admin.site.admin_view(account_views.role_list), name='temple-role-list'),
    path('admin/temple-management/roles/add/', admin.site.admin_view(account_views.role_edit), name='temple-role-add'),
    path('admin/temple-management/roles/<int:group_id>/', admin.site.admin_view(account_views.role_edit), name='temple-role-edit'),
    path('admin/', admin.site.urls),
]
