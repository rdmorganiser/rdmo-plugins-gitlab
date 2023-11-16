import json
from urllib.parse import quote

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _

from rdmo.projects.providers import OauthIssueProvider

from .mixins import GitLabProviderMixin


class GitLabIssueProvider(GitLabProviderMixin, OauthIssueProvider):
    add_label = _('Add GitLab integration')
    send_label = _('Send to GitLab')

    @property
    def description(self):
        return _(f'This integration allow the creation of issues in arbitrary repositories on {self.gitlab_url}. '
                 'The upload of attachments is not supported by GitLab.')

    def get_post_url(self, request, issue, integration, subject, message, attachments):
        repo_url = integration.get_option_value('repo_url')
        if repo_url:
            repo = repo_url.replace(self.gitlab_url, '').strip('/')
            return '{}/api/v4/projects/{}/issues'.format(self.gitlab_url, quote(repo, safe=''))

    def get_post_data(self, request, issue, integration, subject, message, attachments):
        return {
            'title': subject,
            'description': message
        }

    def get_issue_url(self, response):
        return response.json().get('web_url')

    def webhook(self, request, integration):
        secret = integration.get_option_value('secret')
        header_token = request.headers.get('X-Gitlab-Token')

        if (secret is not None) and (header_token is not None) and (header_token == secret):
            try:
                payload = json.loads(request.body.decode())
                state = payload.get('object_attributes', {}).get('state')
                issue_url = payload.get('object_attributes', {}).get('url')

                if state and issue_url:
                    try:
                        issue_resource = integration.resources.get(url=issue_url)
                        if state == 'closed':
                            issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_CLOSED
                        else:
                            issue_resource.issue.status = issue_resource.issue.ISSUE_STATUS_IN_PROGRESS

                        issue_resource.issue.save()
                    except ObjectDoesNotExist:
                        pass

                return HttpResponse(status=200)

            except json.decoder.JSONDecodeError as e:
                return HttpResponse(e, status=400)

        raise Http404

    @property
    def fields(self):
        return [
            {
                'key': 'repo_url',
                'placeholder': f'{self.gitlab_url}/username/repo',
                'help': _('The URL of the GitLab repository to send issues to.')
            },
            {
                'key': 'secret',
                'placeholder': 'Secret (random) string',
                'help': _('The secret for a GitLab webhook to close a task (optional).'),
                'required': False,
                'secret': True
            }
        ]
