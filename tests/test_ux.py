import json

import pytest
from sherlock_project import sherlock
from sherlock_project.sites import SitesInformation
from sherlock_interactives import Interactives
from sherlock_interactives import InteractivesSubprocessError

def test_remove_nsfw(sites_obj):
    nsfw_target: str = 'Xvideos'
    assert nsfw_target in {site.name: site.information for site in sites_obj}
    sites_obj.remove_nsfw_sites()
    assert nsfw_target not in {site.name: site.information for site in sites_obj}


# Parametrized sites should *not* include Motherless, which is acting as the control
@pytest.mark.parametrize('nsfwsites', [
    ['Xvideos'],
    ['Xvideos', 'Erome'],
])
def test_nsfw_explicit_selection(sites_obj, nsfwsites):
    for site in nsfwsites:
        assert site in {site.name: site.information for site in sites_obj}
    sites_obj.remove_nsfw_sites(do_not_remove=nsfwsites)
    for site in nsfwsites:
        assert site in {site.name: site.information for site in sites_obj}
        assert 'Motherless' not in {site.name: site.information for site in sites_obj}

def test_wildcard_username_expansion():
    assert sherlock.check_for_parameter('test{?}test') is True
    assert sherlock.check_for_parameter('test{.}test') is False
    assert sherlock.check_for_parameter('test{}test') is False
    assert sherlock.check_for_parameter('testtest') is False
    assert sherlock.check_for_parameter('test{?test') is False
    assert sherlock.check_for_parameter('test?}test') is False
    assert sherlock.multiple_usernames('test{?}test') == ["test_test" , "test-test" , "test.test"]


def test_site_manifest_preserves_unclaimed_username(tmp_path):
    manifest_path = tmp_path / 'targets.json'
    manifest = {
        'Example': {
            'url': 'https://example.com/{}',
            'urlMain': 'https://example.com',
            'username_claimed': 'alice',
            'username_unclaimed': 'noonewouldeverusethis',
            'errorType': 'status_code',
            'errorCode': 404,
            'isNSFW': False,
        }
    }
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

    sites = SitesInformation(data_file_path=str(manifest_path), honor_exclusions=False)
    example = next(iter(sites))

    assert example.username_unclaimed == 'noonewouldeverusethis'
    assert example.username_claimed == 'alice'


def test_remove_nsfw_sites_does_not_mutate_do_not_remove_list(tmp_path):
    manifest_path = tmp_path / 'targets.json'
    manifest = {
        'Example': {
            'url': 'https://example.com/{}',
            'urlMain': 'https://example.com',
            'username_claimed': 'alice',
            'errorType': 'status_code',
            'errorCode': 404,
            'isNSFW': True,
        }
    }
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

    sites = SitesInformation(data_file_path=str(manifest_path), honor_exclusions=False)
    do_not_remove = ['example']
    sites.remove_nsfw_sites(do_not_remove)

    assert do_not_remove == ['example']
    assert 'Example' in {site.name for site in sites}


@pytest.mark.parametrize('cliargs', [
    '',
    '--site urghrtuight --egiotr',
    '--',
])
def test_no_usernames_provided(cliargs):
    with pytest.raises(InteractivesSubprocessError, match=r"error: the following arguments are required: USERNAMES"):
        Interactives.run_cli(cliargs)
