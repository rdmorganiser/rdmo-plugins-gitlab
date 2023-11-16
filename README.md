rdmo-gitlab
===========

This plugin implements an [issue provider](https://rdmo.readthedocs.io/en/latest/plugins/index.html#issue-providers) for RDMO, which lets users push their tasks from RDMO to GitLab issues. The plugin uses [OAUTH 2.0](https://oauth.net/2/), so that users use their respective accounts in both systems.


Setup
-----

Install the plugin in your RDMO virtual environment using pip (directly from GitHub):

```bash
pip install git+https://github.com/rdmorganiser/rdmo-gitlab
```

Add the plugin to `PROJECT_ISSUE_PROVIDERS` in `config/settings/local.py`:

```python
PROJECT_ISSUE_PROVIDERS += [
    ('gitlab', _('GitLab Provider'), 'rdmo_gitlab.providers.GitLab'),
]
```

In addition, an “App” has to be registered with the particular GitLab instance. For GitLab.com, go to https://gitlab.com/-/profile/applications and create an application with the callback URL `https://<rdmo_url>/services/oauth/gitlab/callback/` and the scope `api`.

The `client_id` and the `client_secret`, together with the `gitlab_url`, need to be configured in `config/settings/local.py`:

```python
GITLAB_PROVIDER = {
    'gitlab_url': 'https://gitlab.com',
    'client_id': '',
    'client_secret': ''
}
```


Usage
-----

After the setup, users can add a GitLab intergration to their projects. They need to provide the URL to their repository. Afterwards, project tasks can be pushed to the GitLab repository.

Additionally, a secret can be added to enable GitLab to communicate to RDMO when the status of a work package changed. For this, a webhook has to be added at `https://<repo_url>/-/hooks`. The webhook has to point to `https://<rdmo_url>/projects/<project_id>/integrations/<integration_id>/webhook/` and the secret token has to be exactly the secret entered in the integration.
