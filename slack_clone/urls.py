"""slack_clone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth import views
from core.views import *
from core.forms import LoginForm

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', 'core.views.home', name='home'),
    url(r'^node_api$', 'core.views.node_api', name='node_api'),
    url(r'^home/$', homes),
    url(r'^userlogout/$', logout_page),
    url(r'^register/$', register),
    url(r'^register/success/$', register_success),
    url(r'^login/$', views.login, {'template_name': 'registration/login.html', 'authentication_form': LoginForm}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^channel/(?P<chatroom>[^/]*)/$', channel),
    url(r'^p_channel/(?P<chatroom>[^/]*)/$', p_channel),
    url(r'^add_users/(?P<chatroom>[^/]*)/$', add_user_to_private),
]