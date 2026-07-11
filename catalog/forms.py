"""HTML forms for the server-rendered shop frontend."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from catalog.models import Category, Item

User = get_user_model()


class EmailAuthenticationForm(AuthenticationForm):
    """Session login form labelled for email-based users."""

    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))


class UserRegistrationForm(UserCreationForm):
    """Browser signup — same rules as POST /auth/register."""

    class Meta:
        model = User
        fields = ["email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.setdefault("autofocus", True)
        self.fields["password1"].help_text = "At least 8 characters."
        self.fields["password2"].label = "Confirm password"

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ItemFilterForm(forms.Form):
    """GET filters for the item list page."""

    name_contains = forms.CharField(required=False, label="Name contains")
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All categories",
    )
    min_price = forms.DecimalField(required=False, min_value=0, decimal_places=2, label="Min price")
    max_price = forms.DecimalField(required=False, min_value=0, decimal_places=2, label="Max price")


class ItemForm(forms.ModelForm):
    """Create/edit item in the browser (uses ItemService on save)."""

    class Meta:
        model = Item
        fields = ["name", "description", "price", "category"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
