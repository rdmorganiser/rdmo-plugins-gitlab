from django.conf import settings
from django.urls import reverse

from rdmo.services.providers import OauthProviderMixin


class GitLabProviderMixin(OauthProviderMixin):

    @property
    def gitlab_url(self):
        return settings.GITLAB_PROVIDER['gitlab_url'].strip('/')

    @property
    def authorize_url(self):
        return f'{self.gitlab_url}/oauth/authorize'

    @property
    def token_url(self):
        return f'{self.gitlab_url}/oauth/token'

    @property
    def api_url(self):
        return f'{self.gitlab_url}/api/v4'

    @property
    def client_id(self):
        return settings.GITLAB_PROVIDER['client_id']

    @property
    def client_secret(self):
        return settings.GITLAB_PROVIDER['client_secret']

    @property
    def redirect_path(self):
        return reverse('oauth_callback', args=['gitlab'])

    def get_authorize_params(self, request, state):
        return {
            'client_id': self.client_id,
            'redirect_uri': request.build_absolute_uri(self.redirect_path),
            'response_type': 'code',
            'scope': 'api',
            'state': state
        }

    def get_callback_params(self, request):
        return {
            'token_url': self.token_url,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': request.GET.get('code'),
            'grant_type': 'authorization_code',
            'redirect_uri': request.build_absolute_uri(self.redirect_path)
        }
