import base64
import json
from urllib.parse import quote

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _

from rdmo.core.imports import handle_fetched_file
from rdmo.projects.imports import RDMOXMLImport
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


class GitLabImport(GitLabProviderMixin, RDMOXMLImport):

    class Form(forms.Form):
        repo = forms.CharField(label=_('GitLab repository'),
                               help_text=_('Please use the form username/repository or organization/repository.'))
        path = forms.CharField(label=_('File path'),)
        ref = forms.CharField(label=_('Branch, tag, or commit'), initial='main')

    def render(self):
        return render(self.request, 'projects/project_import_form.html', {
            'source_title': self.gitlab_url,
            'form': self.Form()
        }, status=200)

    def submit(self):
        form = self.Form(self.request.POST)

        if 'cancel' in self.request.POST:
            if self.project is None:
                return redirect('projects')
            else:
                return redirect('project', self.project.id)

        if form.is_valid():
            self.request.session['import_source_title'] = form.cleaned_data['path']

            url = '{api_url}/projects/{repo}/repository/files/{path}?ref={ref}'.format(
                api_url=self.api_url,
                repo=quote(form.cleaned_data['repo'], safe=''),
                path=quote(form.cleaned_data['path'], safe=''),
                ref=quote(form.cleaned_data['ref'], safe='')
            )

            return self.get(self.request, url)

        return render(self.request, 'projects/project_import_form.html', {
            'source_title': self.gitlab_url,
            'form': form
        }, status=200)

    def get_success(self, request, response):
        file_content = response.json().get('content')
        request.session['import_file_name'] = handle_fetched_file(base64.b64decode(file_content))

        if self.current_project:
            return redirect('project_update_import', self.current_project.id)
        else:
            return redirect('project_create_import')
