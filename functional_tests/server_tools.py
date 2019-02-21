from fabric.api import run
from fabric.context_managers import cd, settings, shell_env


def _get_manage_dot_py(host):
    return f'~/sites/{host}/virtualenv/python ~/sites/{host}/manage.py'


def _get_path(host):
    return f'~/sites/{host}/'


def reset_database(host):
    with settings(host_string=f'shaun@{host}'):
        with cd(_get_path(host)):
            run(f'pipenv run python manage.py flush --noinput')


def _get_server_env_vars(host):
    env_lines = run(f'cat ~/sites/{host}/.env').splitlines()
    return dict(l.split('=') for l in env_lines if l)


def create_session_on_server(host, email):
    with settings(host_string=f'shaun@{host}'):
        env_vars = _get_server_env_vars(host)
        with shell_env(**env_vars):
            with cd(_get_path(host)):
                session_key = run(
                    f'pipenv run python manage.py create_session {email}'
                )
                return session_key.strip()
