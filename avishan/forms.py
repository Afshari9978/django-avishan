from django import forms


class LoginForm(forms.Form):
    phone = forms.CharField(label='شماره همراه', max_length=100, help_text='ti-mobile',
                            widget=forms.TextInput(attrs={
                                "type": "text",
                                "class": "form-control pl-15",
                                "placeholder": "شماره همراه"
                            }))
    password = forms.CharField(label='رمز عبور', max_length=100, help_text='ti-lock',
                               widget=forms.TextInput(attrs={
                                   "type": "password",
                                   "class": "form-control pl-15",
                                   "placeholder": "رمز عبور"
                               }))
