# -*- coding: utf-8 -*-
import json
import mock
from StringIO import StringIO

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from rest_framework.test import APITestCase
from rest_framework import status

from pdc.apps.bindings import models as binding_models
from pdc.apps.common.test_utils import create_user, TestCaseWithChangeSetMixin
from pdc.apps.release.models import Release, ProductVersion
from pdc.apps.component.models import (ReleaseComponent,
                                       BugzillaComponent)
import pdc.apps.release.models as release_models
import pdc.apps.common.models as common_models
from . import models


class ComposeModelTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.compose = models.Compose.objects.get(id=1)

    def test_get_rpms_existing(self):
        self.assertEqual(unicode(self.compose.get_rpms('bash')),
                         '[<RPM: bash-0:4.2.45-5.x86_64.rpm>]')

    def test_get_rpms_nonexisting(self):
        self.assertEqual(list(self.compose.get_rpms('foo')), [])


class VersionFinderTestCase(APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
        "pdc/apps/compose/fixtures/tests/more_composes.json",
    ]

    def setUp(self):
        self.url = reverse('findcomposewitholderpackage-list')

    def test_bad_args_missing_rpm_name(self):
        response = self.client.get(self.url, {'compose': 'compose-1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('rpm_name', response.data.get('detail'))

    def test_bad_args_missing_release_and_compose(self):
        response = self.client.get(self.url, {'rpm_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('release', response.data.get('detail'))
        self.assertIn('compose', response.data.get('detail'))

    def test_missing_previous_compose(self):
        response = self.client.get(self.url, {'compose': 'compose-1', 'rpm_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_previous_compose_has_same_version(self):
        response = self.client.get(self.url, {'compose': 'compose-2', 'rpm_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_previous_compose_has_older_rpm(self):
        response = self.client.get(self.url, {'compose': 'compose-3', 'rpm_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('compose'), "compose-2")
        self.assertEqual(response.data.get('packages'), ["bash-0:4.2.45-5.x86_64.rpm"])

    def test_same_version_different_arch(self):
        """There is a previous compose with same version of package, but with different RPM.arch."""
        models.ComposeRPM.objects.filter(pk=1).update(rpm=3)
        response = self.client.get(self.url, {'compose': 'compose-2', 'rpm_name': 'bash'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_for_release(self):
        response = self.client.get(self.url, {'rpm_name': 'bash', 'release': 'rhel-7.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-1', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']},
                          {'compose': 'compose-2', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']},
                          {'compose': 'compose-3', 'packages': ['bash-0:4.2.46-5.x86_64.rpm']}])

    def test_get_for_release_with_latest(self):
        response = self.client.get(self.url, {'rpm_name': 'bash', 'release': 'rhel-7.0', 'latest': 'True'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-3', 'packages': ['bash-0:4.2.46-5.x86_64.rpm']}])

    def test_get_for_release_to_dict(self):
        response = self.client.get(self.url, {'rpm_name': 'bash', 'release': 'rhel-7.0', 'to_dict': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = [
            {'compose': u'compose-1', 'packages': [
                {'name': u'bash', 'version': u'4.2.45', 'epoch': 0, 'release': u'5',
                 'arch': u'x86_64', 'srpm_name': u'bash', 'srpm_nevra': u'bash-0:4.2.45-5.el7.src',
                 'filename': 'bash-4.2.45-5.x86_64.rpm'}]},
            {'compose': u'compose-2', 'packages': [
                {'name': u'bash', 'version': u'4.2.45', 'epoch': 0, 'release': u'5',
                 'arch': u'x86_64', 'srpm_name': u'bash', 'srpm_nevra': u'bash-0:4.2.45-5.el7.src',
                 'filename': 'bash-4.2.45-5.x86_64.rpm'}]},
            {'compose': u'compose-3', 'packages': [
                {'name': u'bash', 'version': u'4.2.46', 'epoch': 0, 'release': u'5',
                 'arch': u'x86_64', 'srpm_name': u'bash', 'srpm_nevra': None,
                 'filename': 'bash-4.2.46-5.x86_64.rpm'}]}
        ]
        self.assertEqual(response.data, expected)

    def test_get_for_product_version(self):
        product_version = ProductVersion.objects.get(short='rhel', version='7')
        release = Release.objects.get(release_id='rhel-7.0')
        release.product_version = product_version
        release.save()
        response = self.client.get(self.url, {'rpm_name': 'bash', 'product_version': 'rhel-7'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-1', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']},
                          {'compose': 'compose-2', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']},
                          {'compose': 'compose-3', 'packages': ['bash-0:4.2.46-5.x86_64.rpm']}])

    def test_get_for_product_version_with_latest(self):
        product_version = ProductVersion.objects.get(short='rhel', version='7')
        release = Release.objects.get(release_id='rhel-7.0')
        release.product_version = product_version
        release.save()
        response = self.client.get(self.url, {'rpm_name': 'bash', 'product_version': 'rhel-7', 'latest': 'True'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-3', 'packages': ['bash-0:4.2.46-5.x86_64.rpm']}])

    def test_get_for_included_compose_type(self):
        response = self.client.get(self.url, {'rpm_name': 'bash', 'release': 'rhel-7.0',
                                              'included_compose_type': 'production'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-1', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']},
                          {'compose': 'compose-2', 'packages': ['bash-0:4.2.45-5.x86_64.rpm']}])

    def test_get_for_excluded_compose_type(self):
        response = self.client.get(self.url, {'rpm_name': 'bash', 'release': 'rhel-7.0',
                                              'excluded_compose_type': 'production'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,
                         [{'compose': 'compose-3', 'packages': ['bash-0:4.2.46-5.x86_64.rpm']}])


class ComposeAPITestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def test_get_existing(self):
        response = self.client.get(reverse('compose-detail', args=["compose-1"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['sigkeys'], ['ABCDEF'])
        self.assertEqual(response.data['rpm_mapping_template'],
                         'http://testserver/rest_api/v1/composes/compose-1/rpm-mapping/{{package}}/')

    def test_compose_with_unsigned_package(self):
        crpm = models.ComposeRPM.objects.all()[0]
        crpm.sigkey = None
        crpm.save()
        response = self.client.get(reverse('compose-detail', args=["compose-1"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertItemsEqual(response.data['sigkeys'], ['ABCDEF', None])

    def test_get_nonexisting(self):
        response = self.client.get(reverse('compose-detail', args=["does-not-exist"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list(self):
        response = self.client.get(reverse('compose-list'), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_composeid(self):
        response = self.client.get(reverse('compose-list'), {"compose_id": "compose-1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_composeid_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"compose_id": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmname(self):
        response = self.client.get(reverse('compose-list'), {"rpm_name": "bash"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmname_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_name": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_srpmname(self):
        response = self.client.get(reverse('compose-list'), {"srpm_name": "bash"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_srpmname_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"srpm_name": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmversion(self):
        response = self.client.get(reverse('compose-list'), {"rpm_version": "4.2.45"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmversion_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_version": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmrelease(self):
        response = self.client.get(reverse('compose-list'), {"rpm_release": "5"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmrelease_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_release": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmarch(self):
        response = self.client.get(reverse('compose-list'), {"rpm_arch": "x86_64"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmarch_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_arch": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmnvr(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvr": "bash-4.2.45-5"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmnvr_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvr": "does-not-exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmnvr_invalid(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvr": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_compose_rpmnvra(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvra": "bash-4.2.45-5.x86_64"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_rpmnvra_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvra": "does-not-exist.arch"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_query_compose_rpmnvra_invalid(self):
        response = self.client.get(reverse('compose-list'), {"rpm_nvra": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_compose_acceptance_testing(self):
        response = self.client.get(reverse('compose-list'), {"acceptance_testing": "untested"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_query_compose_acceptance_testing_nonexisting(self):
        response = self.client.get(reverse('compose-list'), {"acceptance_testing": "broken"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


class ComposeApiOrderingTestCase(APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/product.json",
        "pdc/apps/release/fixtures/tests/product_version.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
        "pdc/apps/compose/fixtures/tests/more_composes.json",
    ]

    def test_compose_list_is_ordered(self):
        response = self.client.get(reverse('compose-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [x['compose_id'] for x in response.data.get('results', [])],
            ['compose-1', 'compose-2', 'compose-3']
        )

    def test_compose_in_release_are_ordered(self):
        response = self.client.get(reverse('release-detail', args=['rhel-7.0']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('compose_set', []),
                         ['compose-1', 'compose-2', 'compose-3'])


class ComposeUpdateTestCase(TestCaseWithChangeSetMixin, APITestCase):
    fixtures = [
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/more_releases.json",
    ]

    def test_can_not_perform_full_update(self):
        response = self.client.put(reverse('compose-detail', args=['compose-1']), {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_can_update_acceptance_testing_state(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'acceptance_testing': 'passed'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('acceptance_testing'), 'passed')
        self.assertNumChanges([1])

    def test_can_not_update_compose_label(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'compose_label': 'i am a label'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_linked_releases(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': ['rhel-7.0-updates']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('linked_releases'),
                         ['rhel-7.0-updates'])
        self.assertNumChanges([1])

    def test_update_both_linked_release_and_acceptance(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': ['rhel-7.0-updates'],
                                      'acceptance_testing': 'passed'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('linked_releases'),
                         ['rhel-7.0-updates'])
        self.assertEqual(response.data.get('acceptance_testing'), 'passed')
        self.assertNumChanges([2])

    def test_update_acceptance_preserves_links(self):
        self.client.patch(reverse('compose-detail', args=['compose-1']),
                          {'linked_releases': ['rhel-7.0-updates']},
                          format='json')
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'acceptance_testing': 'passed'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('linked_releases'),
                         ['rhel-7.0-updates'])
        self.assertNumChanges([1, 1])

    def test_update_can_not_link_to_same_release(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': ['rhel-7.0']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_update_can_not_link_to_same_release_twice(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': ['rhel-7.0-updates', 'rhel-7.0-updates']},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('linked_releases'), ['rhel-7.0-updates'])

    def test_partial_update_empty(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_linked_releases_not_a_list(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': 'rhel-7.0-updates'},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'linked_releases': ['Expected a list.']})
        self.assertNumChanges([])

    def test_patch_linked_releases_null(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': None},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'linked_releases': ['This field may not be null.']})
        self.assertNumChanges([])

    def test_patch_linked_releases_list_with_null(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'linked_releases': [None]},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data,
                         {'linked_releases': ['Expected a string instead of <None>.']})
        self.assertNumChanges([])

    def test_bulk_update_put(self):
        response = self.client.put(reverse('compose-list'),
                                   {'compose-1': {'linked_releases': []}},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertNumChanges([])

    def test_bulk_update_patch(self):
        response = self.client.patch(reverse('compose-list'),
                                     {'compose-1': {'linked_releases': ['rhel-7.0-updates']}},
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNumChanges([1])
        self.assertEqual(response.data.keys(), ['compose-1'])
        self.assertEqual(response.data['compose-1'].get('linked_releases'),
                         ['rhel-7.0-updates'])

    def test_partial_update_extra_field(self):
        response = self.client.patch(reverse('compose-detail', args=['compose-1']),
                                     {'foo': 'bar'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OverridesRPMAPITestCase(APITestCase):
    fixtures = [
        'pdc/apps/release/fixtures/tests/release.json',
        'pdc/apps/compose/fixtures/tests/compose_overriderpm.json',
    ]

    def setUp(self):
        self.release = release_models.Release.objects.get(release_id='rhel-7.0')
        self.override_rpm = {'release': 'rhel-7.0', 'variant': 'Server', 'arch': 'x86_64',
                             'srpm_name': 'bash', 'rpm_name': 'bash-doc', 'rpm_arch': 'x86_64',
                             'include': False, 'comment': '', 'do_not_delete': False}
        self.do_not_delete_orpm = {'release': 'rhel-7.0', 'variant': 'Server', 'arch': 'x86_64',
                                   'srpm_name': 'bash', 'rpm_name': 'bash-doc', 'rpm_arch': 'src',
                                   'include': True, 'comment': '', 'do_not_delete': True}

    def test_query_existing(self):
        response = self.client.get(reverse('overridesrpm-list'), {'release': 'rhel-7.0'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0], self.override_rpm)

    def test_query_nonexisting(self):
        response = self.client.get(reverse('overridesrpm-list'), {'release': 'rhel-7.1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_delete_existing(self):
        response = self.client.delete(reverse('overridesrpm-list'),
                                      {'release': 'rhel-7.0',
                                       'variant': 'Server', 'arch': 'x86_64',
                                       'rpm_name': 'bash-doc', 'rpm_arch': 'x86_64'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.override_rpm)
        self.assertEqual(models.OverrideRPM.objects.count(), 0)

    def test_delete_wrong_data(self):
        response = self.client.delete(reverse('overridesrpm-list'),
                                      {'release': 'rhel-7.0',
                                       'variant': 'Server', 'arch': 'x86_64'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.OverrideRPM.objects.count(), 1)
        self.assertIn('rpm_name', response.data[0])
        self.assertIn('rpm_arch', response.data[0])

    def test_create_duplicit(self):
        response = self.client.post(reverse('overridesrpm-list'), self.override_rpm)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.OverrideRPM.objects.count(), 1)

    def test_create_correct(self):
        self.override_rpm["rpm_name"] = "bash-debuginfo"
        response = self.client.post(reverse('overridesrpm-list'), self.override_rpm)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.OverrideRPM.objects.count(), 2)

    def test_create_extra_field(self):
        self.override_rpm["rpm_name"] = "bash-debuginfo"
        self.override_rpm["foo"] = "bar"
        response = self.client.post(reverse('overridesrpm-list'), self.override_rpm)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_clear(self):
        response = self.client.delete(reverse('overridesrpm-list'), {'release': 'rhel-7.0'})
        self.assertEqual(models.OverrideRPM.objects.count(), 0)
        self.assertItemsEqual(response.data, [self.override_rpm])

    def test_clear_preserve_do_not_delete(self):
        models.OverrideRPM.objects.create(release=self.release, variant="Server", arch="x86_64",
                                          rpm_name="bash-doc", rpm_arch="src", include=True,
                                          do_not_delete=True, srpm_name="bash")

        response = self.client.delete(reverse('overridesrpm-list'), {'release': 'rhel-7.0'})
        self.assertEqual(models.OverrideRPM.objects.count(), 1)
        self.assertItemsEqual(response.data, [self.override_rpm])

    def test_clear_force(self):
        models.OverrideRPM.objects.create(release=self.release, variant="Server", arch="x86_64",
                                          rpm_name="bash-doc", rpm_arch="src", include=True,
                                          do_not_delete=True, srpm_name="bash")

        response = self.client.delete(reverse('overridesrpm-list'), {'release': 'rhel-7.0', 'force': True})
        self.assertEqual(models.OverrideRPM.objects.count(), 0)
        self.assertItemsEqual(response.data, [self.override_rpm, self.do_not_delete_orpm])


class ComposeRPMViewAPITestCase(APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
    ]

    def setUp(self):
        with open('pdc/apps/release/fixtures/tests/composeinfo.json', 'r') as f:
            self.compose_info = json.loads(f.read())
        with open('pdc/apps/compose/fixtures/tests/rpm-manifest.json', 'r') as f:
            self.manifest = json.loads(f.read())
        # Caching ids makes it faster, but the cache needs to be cleared for each test.
        models.Path.CACHE = {}
        common_models.SigKey.CACHE = {}

    def test_import_and_retrieve_manifest(self):
        response = self.client.post(reverse('releaseimportcomposeinfo-list'),
                                    self.compose_info, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(reverse('composerpm-list'),
                                    {'rpm_manifest': self.manifest,
                                     'release_id': 'tp-1.0',
                                     'composeinfo': self.compose_info},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ComposeRPM.objects.count(), 6)
        response = self.client.get(reverse('composerpm-detail', args=['TP-1.0-20150310.0']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(dict(response.data),
                             self.manifest)

    def test_deprecated_import_url(self):
        response = self.client.post(reverse('releaseimportcomposeinfo-list'),
                                    self.compose_info, format='json')
        response = self.client.post(reverse('composeimportrpms-list'),
                                    {'rpm_manifest': self.manifest,
                                     'release_id': 'tp-1.0',
                                     'composeinfo': self.compose_info},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(models.ComposeRPM.objects.count(), 6)


class RPMMappingAPITestCase(APITestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.release = release_models.Release.objects.latest('id')
        self.compose = models.Compose.objects.get(compose_id='compose-1')
        self.url = reverse('composerpmmapping-detail', args=[self.compose.compose_id, 'bash'])

    def test_get_rpm_mapping(self):
        response = self.client.get(self.url, {}, format='json')
        expected_data = {
            'Server': {
                'x86_64': {
                    'bash': ['x86_64'],
                }
            }
        }
        self.assertEqual(response.data, expected_data)

    def test_get_rpm_mapping_for_nonexisting_compose(self):
        url = reverse('composerpmmapping-detail', args=['foo-bar', 'bash'])
        response = self.client.get(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rpm_mapping_includes_overrides(self):
        models.OverrideRPM.objects.create(variant='Server', arch='x86_64', srpm_name='bash', rpm_name='bash',
                                          rpm_arch='src', include=True, release=self.release)
        response = self.client.get(self.url, {}, format='json')
        expected_data = {
            'Server': {
                'x86_64': {
                    'bash': ['src', 'x86_64'],
                }
            }
        }
        self.assertEqual(response.data, expected_data)

    def test_rpm_mapping_can_exclude_overrides(self):
        models.OverrideRPM.objects.create(variant='Server', arch='x86_64', srpm_name='bash', rpm_name='bash',
                                          rpm_arch='src', include=True, release=self.release)
        self.url += '?disable_overrides=1'
        response = self.client.get(self.url, {}, format='json')
        expected_data = {
            'Server': {
                'x86_64': {
                    'bash': ['x86_64'],
                    'bash-doc': ['x86_64'],
                }
            }
        }
        self.assertEqual(response.data, expected_data)

    def test_does_not_return_empty_container(self):
        models.OverrideRPM.objects.create(variant='Server', arch='x86_64', srpm_name='bash', rpm_name='bash',
                                          rpm_arch='x86_64', include=False, release=self.release)
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.data, {})

    def test_partial_update(self):
        self.client.force_authenticate(create_user("user", perms=[]))
        self.client.patch(self.url, [{"action": "create", "srpm_name": "bash", "rpm_name": "bash-magic",
                                      "rpm_arch": "src", "variant": "Client", "arch": "x86_64",
                                      "do_not_delete": False, "comment": "", "include": True}],
                          format='json')
        orpm = models.OverrideRPM.objects.get(srpm_name="bash", rpm_name="bash-magic", rpm_arch="src",
                                              variant="Client", arch="x86_64", include=True,
                                              do_not_delete=False, comment="")
        self.assertIsNotNone(orpm)

    def test_update(self):
        self.client.force_authenticate(create_user("user", perms=[]))
        new_mapping = {'Server': {'x86_64': {'bash': ['x86_64', 'i386']}}}
        response = self.client.put(self.url, new_mapping, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{'action': 'create', 'srpm_name': 'bash', 'rpm_name': 'bash',
                                          'rpm_arch': 'i386', 'variant': 'Server', 'arch': 'x86_64',
                                          'include': True, 'release_id': 'rhel-7.0'}])
        self.assertEqual(0, models.OverrideRPM.objects.filter(rpm_arch='i386').count())

    def test_update_with_perform(self):
        self.client.force_authenticate(create_user("user", perms=[]))
        new_mapping = {'Server': {'x86_64': {'bash': ['x86_64', 'i386']}}}
        response = self.client.put(self.url + '?perform=1', new_mapping, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [{'action': 'create', 'srpm_name': 'bash', 'rpm_name': 'bash',
                                          'rpm_arch': 'i386', 'variant': 'Server', 'arch': 'x86_64',
                                          'include': True, 'release_id': 'rhel-7.0'}])
        self.assertEqual(1, models.OverrideRPM.objects.filter(rpm_arch='i386').count())


class FilterBugzillaProductsAndComponentsTestCase(APITestCase):
    fixtures = [
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/component/fixtures/tests/release_component.json",
        "pdc/apps/component/fixtures/tests/upstream.json",
        "pdc/apps/component/fixtures/tests/global_component.json"
    ]

    def setUp(self):
        # Construct a new release and release component
        self.release = Release.objects.create(
            release_id='rhel-6.0',
            short='rhel',
            version='6.0',
            name='Red Hat Enterprise Linux',
            release_type_id=1,
        )
        self.bugzilla_component = BugzillaComponent.objects.create(name='kernel')
        filesystems = BugzillaComponent.objects.create(name='filesystems', parent_component=self.bugzilla_component)
        BugzillaComponent.objects.create(name='ext4', parent_component=filesystems)
        pyth = BugzillaComponent.objects.create(name='python', parent_component=self.bugzilla_component)
        BugzillaComponent.objects.create(name='bin', parent_component=pyth)

        ReleaseComponent.objects.create(
            release=self.release,
            global_component_id=1,
            name='kernel',
            bugzilla_component=self.bugzilla_component
        )

    def test_filter_bugzilla_products_components_with_rpm_nvr(self):
        url = reverse('bugzilla-list')
        response = self.client.get(url + '?nvr=bash-4.2.45-5', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_with_invalid_nvr(self):
        url = reverse('bugzilla-list')
        response = self.client.get(url + '?nvr=xxx', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_with_nvr_without_rpms(self):
        url = reverse('bugzilla-list')
        response = self.client.get(url + '?nvr=GConf2-3.2.6-8.el71', format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_without_nvr(self):
        url = reverse('bugzilla-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch('pdc.apps.compose.models.Compose.objects.filter')
    def test_filter_without_srpm_component_name_mapping(self, mock_filter):
        release_component, _ = ReleaseComponent.objects.get_or_create(
            global_component_id=1,
            release=self.release,
            bugzilla_component=self.bugzilla_component,
            name='bash')

        mock_filter.return_value = mock.Mock()
        mock_filter.return_value.distinct.return_value = [mock.Mock()]
        mock_filter.return_value.distinct.return_value[0].release = self.release.release_id
        url = reverse('bugzilla-list')
        response = self.client.get(url + '?nvr=bash-4.2.45-5', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('kernel', response.content)

    @mock.patch('pdc.apps.compose.models.Compose.objects.filter')
    def test_filter_with_srpm_component_name_mapping(self, mock_filter):
        release_component, _ = ReleaseComponent.objects.get_or_create(
            global_component_id=1,
            release=self.release,
            name='kernel')
        binding_models.ReleaseComponentSRPMNameMapping.objects.create(
            srpm_name='bash',
            release_component=release_component)

        mock_filter.return_value = mock.Mock()
        mock_filter.return_value.distinct.return_value = [mock.Mock()]
        mock_filter.return_value.distinct.return_value[0].release = self.release.release_id
        url = reverse('bugzilla-list')
        response = self.client.get(url + '?nvr=bash-4.2.45-5', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('kernel', response.content)


class RPMMappingTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.compose = models.Compose.objects.get(compose_id='compose-1')
        self.mapping, _ = self.compose.get_rpm_mapping('bash')

    def test_compute_diff_add_new(self):
        new_mapping = models.ComposeRPMMapping(data={'Server': {'x86_64': {'bash': ['src', 'x86_64']}}})
        changes = self.mapping.compute_changes(new_mapping)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], {'action': 'create', 'variant': 'Server', 'arch': 'x86_64',
                                      'include': True, 'release_id': 'rhel-7.0', 'rpm_name': 'bash',
                                      'srpm_name': 'bash', 'rpm_arch': 'src'})

    def test_compute_diff_add_excluded(self):
        new_mapping = models.ComposeRPMMapping(data={'Server': {'x86_64': {'bash': ['x86_64'],
                                                                           'bash-doc': ['x86_64']}}})
        changes = self.mapping.compute_changes(new_mapping)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], {'action': 'delete', 'variant': 'Server', 'arch': 'x86_64',
                                      'include': False, 'release_id': 'rhel-7.0', 'rpm_name': 'bash-doc',
                                      'srpm_name': 'bash', 'rpm_arch': 'x86_64'})

    def test_compute_diff_remove_existing(self):
        new_mapping = models.ComposeRPMMapping(data={})
        changes = self.mapping.compute_changes(new_mapping)
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0], {'action': 'create', 'variant': 'Server', 'arch': 'x86_64',
                                      'include': False, 'release_id': 'rhel-7.0', 'rpm_name': 'bash',
                                      'srpm_name': 'bash', 'rpm_arch': 'x86_64'})


class OverrideManagementTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.initial_form_data = {
            'checks-0-included': 'on',
            'checks-0-variant': 'Server',
            'checks-0-arch': 'x86_64',
            'checks-0-rpm_name': 'bash',
            'checks-0-rpm_arch': 'x86_64',

            'checks-1-variant': 'Server',
            'checks-1-arch': 'x86_64',
            'checks-1-rpm_name': 'bash-doc',
            'checks-1-rpm_arch': 'x86_64',

            'checks-MAX_NUM_FORMS': '1000',
            'checks-INITIAL_FORMS': 2,
            'checks-TOTAL_FORMS': 2,
            'news-MAX_NUM_FORMS': '1000',
            'news-INITIAL_FORMS': 1,
            'news-TOTAL_FORMS': 0,
            'vararch-MAX_NUM_FORMS': '1000',
            'vararch-INITIAL_FORMS': 1,
            'vararch-TOTAL_FORMS': 0,
            'for_new_vararch-MAX_NUM_FORMS': '1000',
            'for_new_vararch-INITIAL_FORMS': 0,
            'for_new_vararch-TOTAL_FORMS': 0,
        }

    def test_can_access_management_form(self):
        client = Client()
        response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
        self.assertEqual(response.status_code, 200)
        # There is one package in fixtures
        self.assertEqual(len(response.context['forms']), 1)

    def test_submit_no_changes(self):
        client = Client()
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 0)

    def test_submit_disable(self):
        client = Client()
        del self.initial_form_data['checks-0-included']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 1)
        self.assertEqual({'variant': 'Server', 'arch': 'x86_64', 'rpm_name': 'bash', 'rpm_arch': 'x86_64',
                          'include': False, 'action': 'create', 'srpm_name': 'bash', 'release_id': 'rhel-7.0'},
                         data[0])

    def test_submit_enable(self):
        client = Client()
        self.initial_form_data['checks-1-included'] = 'on'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 1)
        self.assertEqual({'variant': 'Server', 'arch': 'x86_64', 'rpm_name': 'bash-doc', 'rpm_arch': 'x86_64',
                          'include': False, 'action': 'delete', 'srpm_name': 'bash', 'release_id': 'rhel-7.0',
                          'comment': '', 'do_not_delete': False},
                         data[0])

    def test_submit_new_override(self):
        client = Client()
        self.initial_form_data.update({
            'news-0-variant': 'Server',
            'news-0-arch': 'x86_64',
            'news-0-rpm_name': 'bash-completion',
            'news-0-rpm_arch': 'x86_64',
            'news-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 1)
        self.assertEqual({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server',
                          'arch': 'x86_64', 'rpm_name': 'bash-completion', 'rpm_arch': 'x86_64', 'include': True},
                         data[0])

    def test_submit_new_override_on_new_variant(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-new_variant': 0,
            'for_new_vararch-0-rpm_name': 'bash-completion',
            'for_new_vararch-0-rpm_arch': 'x86_64',

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 1)
        self.assertEqual({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server-optional',
                          'arch': 'x86_64', 'rpm_name': 'bash-completion', 'rpm_arch': 'x86_64', 'include': True},
                         data[0])

    def test_submit_more_different_changes(self):
        client = Client()
        del self.initial_form_data['checks-0-included']
        self.initial_form_data.update({
            'news-0-variant': 'Server',
            'news-0-arch': 'x86_64',
            'news-0-rpm_name': 'bash-completion',
            'news-0-rpm_arch': 'x86_64',

            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-new_variant': 0,
            'for_new_vararch-0-rpm_name': 'bash-completion',
            'for_new_vararch-0-rpm_arch': 'x86_64',

            'news-TOTAL_FORMS': 1,
            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 3)
        self.assertIn({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server',
                       'arch': 'x86_64', 'rpm_name': 'bash-completion', 'rpm_arch': 'x86_64', 'include': True},
                      data)
        self.assertIn({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server-optional',
                       'arch': 'x86_64', 'rpm_name': 'bash-completion', 'rpm_arch': 'x86_64', 'include': True},
                      data)
        self.assertIn({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server',
                       'arch': 'x86_64', 'rpm_name': 'bash', 'rpm_arch': 'x86_64', 'include': False},
                      data)

    def test_submit_more_same_changes(self):
        client = Client()
        self.initial_form_data.update({
            'news-0-variant': 'Server',
            'news-0-arch': 'x86_64',
            'news-0-rpm_name': 'bash-completion',
            'news-0-rpm_arch': 'x86_64',

            'news-1-variant': 'Server',
            'news-1-arch': 'x86_64',
            'news-1-rpm_name': 'bash-magic',
            'news-1-rpm_arch': 'src',

            'news-TOTAL_FORMS': 2,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 2)
        self.assertIn({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server',
                       'arch': 'x86_64', 'rpm_name': 'bash-completion', 'rpm_arch': 'x86_64', 'include': True},
                      data)
        self.assertIn({'action': 'create', 'release_id': 'rhel-7.0', 'srpm_name': 'bash', 'variant': 'Server',
                       'arch': 'x86_64', 'rpm_name': 'bash-magic', 'rpm_arch': 'src', 'include': True},
                      data)

    def test_submit_enable_and_disable(self):
        client = Client()
        del self.initial_form_data['checks-0-included']
        self.initial_form_data['checks-1-included'] = 'on'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('compressed', response.context)
        data = json.loads(response.context['compressed'])
        self.assertEqual(len(data), 2)
        self.assertIn({'variant': 'Server', 'arch': 'x86_64', 'rpm_name': 'bash-doc', 'rpm_arch': 'x86_64',
                       'include': False, 'action': 'delete', 'srpm_name': 'bash', 'release_id': 'rhel-7.0',
                       'comment': '', 'do_not_delete': False},
                      data)
        self.assertIn({'variant': 'Server', 'arch': 'x86_64', 'rpm_name': 'bash', 'rpm_arch': 'x86_64',
                       'include': False, 'action': 'create', 'srpm_name': 'bash', 'release_id': 'rhel-7.0'},
                      data)

    def test_submit_incorrect_new_override_missing_rpm_arch(self):
        client = Client()
        self.initial_form_data.update({
            'news-0-variant': 'Server',
            'news-0-arch': 'x86_64',
            'news-0-rpm_name': 'bash-completion',
            'news-0-rpm_arch': '',
            'news-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'override_forms', 0, None, 'Both RPM name and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_missing_rpm_name(self):
        client = Client()
        self.initial_form_data.update({
            'news-0-variant': 'Server',
            'news-0-arch': 'x86_64',
            'news-0-rpm_name': '',
            'news-0-rpm_arch': 'src',
            'news-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'override_forms', 0, None, 'Both RPM name and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_for_new_variant_missing_rpm_arch(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-rpm_name': 'bash-completion',
            'for_new_vararch-0-rpm_arch': '',
            'for_new_vararch-0-new_variant': 0,

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'override_v_forms', 0, None, 'Both RPM name and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_for_new_variant_missing_rpm_name(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-rpm_name': '',
            'for_new_vararch-0-rpm_arch': 'src',
            'for_new_vararch-0-new_variant': 0,

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'override_v_forms', 0, None, 'Both RPM name and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_for_new_variant_missing_variant_name(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': '',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-rpm_name': 'bash-magic',
            'for_new_vararch-0-rpm_arch': 'src',
            'for_new_vararch-0-new_variant': 0,

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'variant_forms', 0, None, 'Both variant and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_for_new_variant_missing_variant_arch(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': '',

            'for_new_vararch-0-rpm_name': 'bash-magic',
            'for_new_vararch-0-rpm_arch': 'src',
            'for_new_vararch-0-new_variant': 0,

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'variant_forms', 0, None, 'Both variant and arch must be filled in.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_incorrect_new_override_for_new_variant_and_old_variant(self):
        client = Client()
        self.initial_form_data.update({
            'vararch-0-variant': 'Server-optional',
            'vararch-0-arch': 'x86_64',

            'for_new_vararch-0-rpm_name': 'bash-magic',
            'for_new_vararch-0-rpm_arch': 'src',
            'for_new_vararch-0-new_variant': 0,
            'for_new_vararch-0-variant': 'Server',
            'for_new_vararch-0-arch': 'i686',

            'vararch-TOTAL_FORMS': 1,
            'for_new_vararch-TOTAL_FORMS': 1,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormsetError(response, 'override_v_forms', 0, None, 'Can not reference both old and new variant.arch.')
        self.assertContains(response, 'There are errors in the form.')

    def test_submit_preview_no_change(self):
        client = Client()
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No changes')


class OverridePreviewTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.form_data = {
            'checks-0-included': 'on',
            'checks-0-variant': 'Server',
            'checks-0-arch': 'x86_64',
            'checks-0-rpm_name': 'bash',
            'checks-0-rpm_arch': 'x86_64',

            'checks-1-variant': 'Server',
            'checks-1-arch': 'x86_64',
            'checks-1-rpm_name': 'bash-doc',
            'checks-1-rpm_arch': 'x86_64',

            'checks-MAX_NUM_FORMS': '1000',
            'checks-INITIAL_FORMS': 2,
            'checks-TOTAL_FORMS': 2,
            'news-MAX_NUM_FORMS': '1000',
            'news-INITIAL_FORMS': 1,
            'news-TOTAL_FORMS': 0,
            'vararch-MAX_NUM_FORMS': '1000',
            'vararch-INITIAL_FORMS': 1,
            'vararch-TOTAL_FORMS': 0,
            'for_new_vararch-MAX_NUM_FORMS': '1000',
            'for_new_vararch-INITIAL_FORMS': 0,
            'for_new_vararch-TOTAL_FORMS': 0,
        }
        self.preview_form_data = {
            'preview_submit': True,
            'form-TOTAL_FORMS': 0,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        }

    def _populate_preview_form(self, response):
        """Parse response and prepare form data for preview submission."""
        def set_val(dict, key, val):
            if isinstance(val, bool):
                if val:
                    dict[key] = 'on'
            dict[key] = val

        for (i, action) in enumerate(json.loads(response.context['compressed'])):
            for k in action:
                set_val(self.preview_form_data, 'form-%d-%s' % (i, k), action[k])
            self.preview_form_data['form-TOTAL_FORMS'] += 1
        self.preview_form_data['initial_data'] = response.context['compressed']

    def test_submit_with_comment_and_missing_do_not_delete(self):
        client = Client()
        del self.form_data['checks-0-included']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        self.preview_form_data['form-0-comment'] = 'do not delete me'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There are errors in the form.')
        self.assertFormsetError(response, 'forms', 0, None, 'Comment needs do_not_delete checked.')

    def test_submit_ok_no_comment(self):
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        del self.form_data['checks-0-included']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 2)
        orpm = models.OverrideRPM.objects.latest('id')
        self.assertEqual(orpm.include, False)
        self.assertEqual(orpm.do_not_delete, False)
        self.assertEqual(orpm.comment, '')

    def test_submit_ok_with_comment(self):
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        del self.form_data['checks-0-included']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        self.preview_form_data.update({
            'form-0-do_not_delete': 'on',
            'form-0-comment': 'do not delete me',
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 2)
        orpm = models.OverrideRPM.objects.latest('id')
        self.assertEqual(orpm.include, False)
        self.assertEqual(orpm.do_not_delete, True)
        self.assertEqual(orpm.comment, 'do not delete me')

    def test_submit_ok_should_delete(self):
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        self.form_data['checks-1-included'] = 'on'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        del self.preview_form_data['form-0-do_not_delete']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 0)

    def test_submit_ok_should_set_do_not_delete(self):
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        self.form_data['checks-1-included'] = 'on'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        self.preview_form_data.update({
            'form-0-comment': 'comment',
            'form-0-do_not_delete': 'on',
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 1)
        orpm = models.OverrideRPM.objects.latest('id')
        self.assertEqual(orpm.do_not_delete, True)
        self.assertEqual(orpm.comment, 'comment')
        self.assertEqual(orpm.include, True)

    def test_submit_ok_should_remove_do_not_delete_and_delete(self):
        orpm = models.OverrideRPM.objects.latest('id')
        orpm.do_not_delete = True
        orpm.save()

        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        self.form_data['checks-1-included'] = 'on'
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self._populate_preview_form(response)
        del self.preview_form_data['form-0-do_not_delete']
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 0)

    def test_submit_ok_disable_override_without_compose_rpm__should_delete(self):
        orpm = models.OverrideRPM.objects.latest('id')
        orpm.rpm_name = 'bash-magic'
        orpm.include = True
        orpm.save()

        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        self.form_data.update({
            'checks-1-included': 'on',
            'checks-2-variant': 'Server',
            'checks-2-arch': 'x86_64',
            'checks-2-rpm_name': 'bash-magic',
            'checks-2-rpm_arch': 'x86_64',

            'checks-TOTAL_FORMS': 3,
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.form_data)
        self.assertEqual(len(response.context['forms']), 1)
        self._populate_preview_form(response)

        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(models.OverrideRPM.objects.count(), 0)


class OverridePreviewBulkTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm_more.json",
    ]

    def setUp(self):
        self.initial_form_data = {
            'checks-0-variant': 'Server',
            'checks-0-arch': 'x86_64',
            'checks-0-rpm_name': 'bash',
            'checks-0-rpm_arch': 'x86_64',

            'checks-1-variant': 'Server',
            'checks-1-arch': 'x86_64',
            'checks-1-rpm_name': 'bash-completion',
            'checks-1-rpm_arch': 'x86_64',

            'checks-2-included': 'on',
            'checks-2-variant': 'Server',
            'checks-2-arch': 'x86_64',
            'checks-2-rpm_name': 'bash-debuginfo',
            'checks-2-rpm_arch': 'x86_64',

            'checks-3-included': 'on',
            'checks-3-variant': 'Server',
            'checks-3-arch': 'x86_64',
            'checks-3-rpm_name': 'bash-doc',
            'checks-3-rpm_arch': 'x86_64',

            'checks-4-variant': 'Server',
            'checks-4-arch': 'x86_64',
            'checks-4-rpm_name': 'bash-magic',
            'checks-4-rpm_arch': 'x86_64',

            'checks-MAX_NUM_FORMS': '1000',
            'checks-INITIAL_FORMS': 5,
            'checks-TOTAL_FORMS': 5,
            'news-MAX_NUM_FORMS': '1000',
            'news-INITIAL_FORMS': 1,
            'news-TOTAL_FORMS': 0,
            'vararch-MAX_NUM_FORMS': '1000',
            'vararch-INITIAL_FORMS': 1,
            'vararch-TOTAL_FORMS': 0,
            'for_new_vararch-MAX_NUM_FORMS': '1000',
            'for_new_vararch-INITIAL_FORMS': 0,
            'for_new_vararch-TOTAL_FORMS': 0,
        }
        self.preview_form_data = {
            'preview_submit': True,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
        }

    def test_more_changes_at_the_same_time(self):
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.initial_form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['forms']), 5)
        self.preview_form_data.update({
            'initial_data': response.context['compressed'],
            'form-TOTAL_FORMS': 5,
            'form-0-action': 'create',
            'form-0-variant': 'Server',
            'form-0-arch': 'x86_64',
            'form-0-rpm_name': 'bash',
            'form-0-rpm_arch': 'x86_64',
            'form-0-include': 'False',

            'form-1-action': 'create',
            'form-1-variant': 'Server',
            'form-1-arch': 'x86_64',
            'form-1-rpm_name': 'bash-competion',
            'form-1-rpm_arch': 'x86_64',
            'form-1-include': 'False',

            'form-2-action': 'delete',
            'form-2-variant': 'Server',
            'form-2-arch': 'x86_64',
            'form-2-rpm_name': 'bash-debuginfo',
            'form-2-rpm_arch': 'x86_64',
            'form-2-include': 'False',

            'form-3-action': 'delete',
            'form-3-variant': 'Server',
            'form-3-arch': 'x86_64',
            'form-3-rpm_name': 'bash-doc',
            'form-3-rpm_arch': 'x86_64',
            'form-3-include': 'False',

            'form-4-action': 'delete',
            'form-4-variant': 'Server',
            'form-4-arch': 'x86_64',
            'form-4-rpm_name': 'bash-magic',
            'form-4-rpm_arch': 'x86_64',
            'form-4-include': 'False',
        })
        response = client.post('/override/manage/rhel-7.0/?package=bash', self.preview_form_data)
        self.assertEqual(response.status_code, 302)
        self.assertItemsEqual(
            [o.export() for o in models.OverrideRPM.objects.all()],
            [{"release_id": 'rhel-7.0', "variant": 'Server', "arch": 'x86_64',
              "srpm_name": 'bash', "rpm_name": 'bash', "rpm_arch": 'x86_64',
              "include": False, "comment": '', "do_not_delete": False},
             {"release_id": 'rhel-7.0', "variant": 'Server', "arch": 'x86_64',
              "srpm_name": 'bash', "rpm_name": 'bash-completion', "rpm_arch": 'x86_64',
              "include": False, "comment": '', "do_not_delete": False}]
        )


class UselessOverrideTestCase(TestCase):
    fixtures = [
        "pdc/apps/common/fixtures/test/sigkey.json",
        "pdc/apps/package/fixtures/test/rpm.json",
        "pdc/apps/release/fixtures/tests/release.json",
        "pdc/apps/release/fixtures/tests/variant.json",
        "pdc/apps/release/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/variant.json",
        "pdc/apps/compose/fixtures/tests/variant_arch.json",
        "pdc/apps/compose/fixtures/tests/compose_overriderpm.json",
        "pdc/apps/compose/fixtures/tests/compose.json",
        "pdc/apps/compose/fixtures/tests/compose_composerpm.json",
    ]

    def setUp(self):
        self.release = release_models.Release.objects.latest('id')

    def test_delete_unused_include_override(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash',
                                                 rpm_arch='x86_64',
                                                 include=True)
        client = Client()
        with mock.patch('sys.stdout', new_callable=StringIO) as out:
            response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
            self.assertEqual(response.context['useless_overrides'], [])
            self.assertIn('NOTICE', out.getvalue())
            self.assertIn(str(orpm), out.getvalue())
        self.assertEqual(models.OverrideRPM.objects.count(), 1)

    def test_delete_unused_exclude_override(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash-missing',
                                                 rpm_arch='x86_64',
                                                 include=False)
        client = Client()
        with mock.patch('sys.stdout', new_callable=StringIO) as out:
            response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
            self.assertEqual(response.context['useless_overrides'], [])
            self.assertIn('NOTICE', out.getvalue())
            self.assertIn(str(orpm), out.getvalue())
        self.assertEqual(models.OverrideRPM.objects.count(), 1)

    def test_delete_unused_exclude_override_on_new_variant_arch(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash',
                                                 rpm_arch='rpm_arch',
                                                 include=False)
        client = Client()
        with mock.patch('sys.stdout', new_callable=StringIO) as out:
            response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
            self.assertEqual(response.context['useless_overrides'], [])
            self.assertIn('NOTICE', out.getvalue())
            self.assertIn(str(orpm), out.getvalue())
        self.assertEqual(models.OverrideRPM.objects.count(), 1)

    def test_do_not_delete_unused_include_override(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash',
                                                 rpm_arch='x86_64',
                                                 include=True,
                                                 do_not_delete=True)
        client = Client()
        response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
        self.assertEqual(response.context['useless_overrides'], [orpm])
        self.assertEqual(models.OverrideRPM.objects.count(), 2)

    def test_do_not_delete_unused_exclude_override(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash-missing',
                                                 rpm_arch='x86_64',
                                                 include=False,
                                                 do_not_delete=True)
        client = Client()
        response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
        self.assertEqual(response.context['useless_overrides'], [orpm])
        self.assertEqual(models.OverrideRPM.objects.count(), 2)

    def test_do_not_delete_unused_exclude_override_on_new_variant_arch(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash',
                                                 rpm_arch='rpm_arch',
                                                 include=False,
                                                 do_not_delete=True)
        client = Client()
        response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
        self.assertEqual(response.context['useless_overrides'], [orpm])
        self.assertEqual(models.OverrideRPM.objects.count(), 2)

    def test_update_unused_override_when_creating_conflict(self):
        orpm = models.OverrideRPM.objects.create(release=self.release,
                                                 variant='Server',
                                                 arch='x86_64',
                                                 srpm_name='bash',
                                                 rpm_name='bash',
                                                 rpm_arch='x86_64',
                                                 include=True,
                                                 do_not_delete=True)
        client = Client()
        create_user("user", perms=["pdc.overrides"])
        client.login(username="user", password="user")
        response = client.get('/override/manage/rhel-7.0/', {'package': 'bash'})
        self.assertEqual(response.context['useless_overrides'], [orpm])
        form_data = {
            'checks-0-variant': 'Server',
            'checks-0-arch': 'x86_64',
            'checks-0-rpm_name': 'bash',
            'checks-0-rpm_arch': 'x86_64',

            'checks-MAX_NUM_FORMS': '1000',
            'checks-INITIAL_FORMS': 1,
            'checks-TOTAL_FORMS': 1,
            'news-MAX_NUM_FORMS': '1000',
            'news-INITIAL_FORMS': 1,
            'news-TOTAL_FORMS': 0,
            'vararch-MAX_NUM_FORMS': '1000',
            'vararch-INITIAL_FORMS': 1,
            'vararch-TOTAL_FORMS': 0,
            'for_new_vararch-MAX_NUM_FORMS': '1000',
            'for_new_vararch-INITIAL_FORMS': 0,
            'for_new_vararch-TOTAL_FORMS': 0,
        }
        response = client.post('/override/manage/rhel-7.0/?package=bash', form_data)
        self.assertContains(response, 'warning')
        self.assertContains(response, 'Will modify override with do_not_delete set.')
        preview_data = {
            'preview_submit': True,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': 1000,
            'form-TOTAL_FORMS': 1,

            'initial_data': response.context['compressed'],
            'form-0-action': 'create',
            'form-0-variant': 'Server',
            'form-0-arch': 'x86_64',
            'form-0-rpm_name': 'bash',
            'form-0-rpm_arch': 'x86_64',
            'form-0-include': 'False',
        }
        response = client.post('/override/manage/rhel-7.0/?package=bash', preview_data)
        self.assertEqual(response.status_code, 302)
        orpm = models.OverrideRPM.objects.latest('id')
        self.assertFalse(orpm.include)
