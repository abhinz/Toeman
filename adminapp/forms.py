from django import forms
from .models import ProductAttribute

class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        fields = [ 'size', 'quantity']
      