"""Server-rendered HTML views (full Django frontend)."""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView

from catalog.forms import EmailAuthenticationForm, ItemFilterForm, ItemForm, UserRegistrationForm
from catalog.models import Item
from catalog.services import ItemService


class ShopHomeView(TemplateView):
    """Landing page with catalog stats."""

    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = ItemService.get_stats()
        return context


class ItemListView(ListView):
    """Browse items with optional filters (HTML table, not JSON)."""

    template_name = "catalog/item_list.html"
    context_object_name = "items"
    paginate_by = 10

    def get_queryset(self):
        form = ItemFilterForm(self.request.GET)
        filters: dict = {}
        if form.is_valid():
            if form.cleaned_data["name_contains"]:
                filters["name_contains"] = form.cleaned_data["name_contains"]
            if form.cleaned_data["category"]:
                filters["category_id"] = form.cleaned_data["category"].pk
            if form.cleaned_data["min_price"] is not None:
                filters["min_price"] = form.cleaned_data["min_price"]
            if form.cleaned_data["max_price"] is not None:
                filters["max_price"] = form.cleaned_data["max_price"]

        page = self.request.GET.get("page", "1")
        try:
            page_number = max(int(page), 1)
        except ValueError:
            page_number = 1

        skip = (page_number - 1) * self.paginate_by
        rows, self.total_count = ItemService.list_items(
            skip=skip,
            limit=self.paginate_by,
            **filters,
        )
        self.filter_form = form
        return rows

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = getattr(self, "filter_form", ItemFilterForm())
        context["total_count"] = getattr(self, "total_count", 0)
        return context


class ItemDetailView(DetailView):
    """Single item page."""

    model = Item
    template_name = "catalog/item_detail.html"
    context_object_name = "item"

    def get_queryset(self):
        return Item.objects.select_related("category")


class ItemCreateView(LoginRequiredMixin, CreateView):
    """Add an item via HTML form + session auth (not JWT)."""

    form_class = ItemForm
    template_name = "catalog/item_form.html"
    login_url = reverse_lazy("shop-login")

    def form_valid(self, form):
        category = form.cleaned_data.get("category")
        item = ItemService.create(
            name=form.cleaned_data["name"],
            price=Decimal(str(form.cleaned_data["price"])),
            description=form.cleaned_data.get("description"),
            category_id=category.pk if category else None,
        )
        messages.success(self.request, f"Created “{item.name}”.")
        return redirect("shop-item-detail", pk=item.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Add item"
        return context


class ShopLoginView(LoginView):
    """Browser login — sets a session cookie, separate from /auth/login JWT."""

    template_name = "catalog/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "You are logged in.")
        return super().form_valid(form)


class ShopLogoutView(LogoutView):
    """End the browser session."""

    next_page = reverse_lazy("shop-home")

    def dispatch(self, request, *args, **kwargs):
        if request.method.lower() == "post":
            messages.info(request, "You are logged out.")
        return super().dispatch(request, *args, **kwargs)


class ShopRegisterView(FormView):
    """Create an account in the browser and log the user in."""

    template_name = "catalog/register.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("shop-home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("shop-home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Account created. You are logged in.")
        return super().form_valid(form)
