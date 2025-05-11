from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.urls import reverse_lazy
from apps.base.forms.loginForm import LoginForm
from django.contrib.auth.views import LoginView as AuthLoginView
from django.utils.decorators import method_decorator
from django.contrib.contenttypes.models import ContentType
from apps.audit.models import AuditLog

@method_decorator(csrf_protect, name='dispatch')
class CustomLoginView(AuthLoginView):
    """
    Vista personalizada para el inicio de sesión de usuarios con redirección basada en grupos
    """
    template_name = 'auth/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Iniciar sesión'
        return context
    
    def form_valid(self, form):
        """
        Maneja el formulario cuando es válido, incluyendo la funcionalidad de "recordarme"
        """
        # Llamar primero a form_valid del padre para autenticar al usuario
        response = super().form_valid(form)
        
        # Ahora self.request.user está autenticado
        remember_me = form.cleaned_data.get('remember_me', False)
        
        if not remember_me:
            # Configurar la sesión para que expire cuando el usuario cierre el navegador
            self.request.session.set_expiry(0)
        else:
            # Configurar la sesión para que expire después de 14 días
            self.request.session.set_expiry(1209600)  # 2 semanas en segundos
        
        # Mensaje de éxito
        messages.success(self.request, _("Has iniciado sesión correctamente."))
        
        # Registrar en auditoría
        AuditLog.objects.create(
            user=self.request.user,
            action='LOGIN',
            description=f"Inicio de sesión del usuario: {self.request.user.username}"
        )
        
        return response
    
    def form_invalid(self, form):
        """
        Maneja el formulario cuando es inválido, añadiendo mensajes de error
        """
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{error}")
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """
        Determina la URL de redirección basada en el grupo del usuario
        """
        user = self.request.user
        
        if user.groups.filter(name='Group1').exists():
            return reverse_lazy('configuracion:home')
        elif user.groups.filter(name='Group2').exists():
            return reverse_lazy('configuracion:dashboard')
        else:
            return reverse_lazy('configuracion:users_list')

def logout_view(request):
    """
    Vista para cerrar sesión
    """
    user = request.user
    
    # Registrar en auditoría antes de cerrar sesión
    if user.is_authenticated:
        AuditLog.objects.create(
            user=user,
            action='LOGOUT',
            description=f"Cierre de sesión del usuario: {user.username}"
        )
    
    logout(request)
    messages.success(request, _('Has cerrado sesión correctamente'))
    return redirect('auth:login')