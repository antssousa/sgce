import json

from django import forms
from django_select2.forms import Select2Widget
from tinymce.widgets import TinyMCE

from sgce.certificates.models import Template, Certificate, Participant
from sgce.core.models import Event


class HomeForm(forms.Form):
    dni = forms.CharField(
        max_length=14,
        label='DNI',
        widget=forms.TextInput(),
    )

    def clean_dni(self):
        dni = self.cleaned_data['dni']
        return dni


class CertificateValidateForm(forms.Form):
    hash = forms.CharField(label='Código de Autenticação')


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        exclude = ('created_by',)
        widgets = {
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),
            'event': Select2Widget,
        }


class TemplateDuplicateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('event',)
        widgets = {
            'event': Select2Widget,
        }
        help_texts = {
            'event': 'Escolha o evento que você quer aplicar este modelo',
        }

    def __init__(self, user, *args, **kwargs):
        super(TemplateDuplicateForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['event'].queryset = Event.objects.filter(
                created_by=user)


class CertificatesCreatorForm(forms.Form):
    template = forms.ModelChoiceField(
        queryset=Template.objects, widget=Select2Widget)
    certificates = forms.CharField()

    def __init__(self, user, *args, **kwargs):
        super(CertificatesCreatorForm, self).__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['template'].queryset = Template.objects.filter(
                event__created_by=user)

    def clean_certificates(self):
        # TODO: Refactor
        data = self.cleaned_data['certificates']

        template = self.cleaned_data['template']

        certificates = json.loads(data)

        any_object = False

        for line, attrs_certificate in enumerate(certificates, 1):
            if any(attrs_certificate):
                any_object = True
                # ('' in attrs_certificate[1:] = Remove ENDERECO_EMAIL (optional)
                if (None in attrs_certificate) or ('' in attrs_certificate) or (len(template.template_fields()) != len(attrs_certificate)):
                    raise forms.ValidationError(
                        'A tabela não pode conter valores em branco')
                    break
                else:
                    attrs_certificate[0] = attrs_certificate[0].strip()
                    if not attrs_certificate[0]:
                        raise forms.ValidationError(
                            'O DNI {} da linha {} é inválido.'.format(attrs_certificate[0], line))
            else:
                certificates.remove(attrs_certificate)

        if any_object is False:
            raise forms.ValidationError(
                'A tabela não pode conter valores em branco')

        data = json.dumps(certificates)

        return data


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        exclude = ()


class CertificateEvaluationForm(forms.Form):
    event = forms.ModelChoiceField(
        Event.objects.all(), label='Evento', widget=Select2Widget)
    template = forms.ModelChoiceField(
        Template.objects.all(), label='Modelo', widget=Select2Widget)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not user.is_superuser:
            self.fields['event'].queryset = Event.objects.filter(
                created_by=user)

        self.fields['template'].queryset = Template.objects.none()

        if 'event' in self.data:
            try:
                event_id = int(self.data.get('event'))
                self.fields['template'].queryset = Template.objects.filter(
                    event_id=event_id)
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty Template queryset


class CertificateEvaluationTemplateForm(forms.Form):
    notes = forms.CharField(label='Observações', required=False)
    status = forms.ChoiceField(
        choices=Certificate.STATUS_CHOICES, label='Avaliação', initial=Certificate.VALID)
    certificates = forms.ModelMultipleChoiceField(
        queryset=Certificate.objects.all(),
        label='Certificados',
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, template_pk, *args, **kwargs):
        super(CertificateEvaluationTemplateForm,
              self).__init__(*args, **kwargs)
        self.fields['certificates'].queryset = Certificate.objects.filter(
            template_id=template_pk)
