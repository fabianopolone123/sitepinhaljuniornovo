from django.urls import path

from . import views

urlpatterns = [
    path("", views.login_screen, name="login"),
    path("cadastro/", views.register, name="register"),
    path("admin/cadastro/", views.admin_register, name="admin_register"),
    path("admin/logs/", views.admin_logs, name="admin_logs"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("cadastros/responsavel/", views.update_responsible, name="update_responsible"),
    path("cadastros/aventureiro/<int:pk>/", views.update_adventurer, name="update_adventurer"),
    path("financeiro/mensalidades/<int:year>/<int:month>/pagar/", views.pay_monthly_fees, name="pay_monthly_fees"),
    path("financeiro/mensalidades/<int:year>/<int:month>/pix/", views.finance_pix, name="finance_pix"),
    path("recuperar-senha/", views.forgot_password, name="forgot_password"),
    path("recuperar-senha/<int:recovery_id>/verificar/", views.verify_code, name="verify_code"),
    path("mp/webhook/", views.mp_webhook, name="mp_webhook"),
]
