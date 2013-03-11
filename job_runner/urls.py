from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^chaining/', include('smart_selects.urls')),
    url(r'^admin/', include(admin.site.urls)),

    (r'^api/', include('job_runner.apps.job_runner.api_urls')),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(
        r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'},
        name='logout'
    ),

    (r'^', include('job_runner.apps.job_runner.urls', namespace='job_runner')),
)
