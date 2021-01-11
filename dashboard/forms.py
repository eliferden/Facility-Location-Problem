from django import forms

class ModelParametersForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)
    integer = forms.IntegerField()
