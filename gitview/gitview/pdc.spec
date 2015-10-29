%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define srcname pdc
%define major 0
%define minor 3
%define patchlevel 0
%define _release_ 0.2.beta

%{!?version: %define version %{major}.%{minor}.%{patchlevel}}
%{!?release: %define release %{_release_}}

Name:           python-%{srcname}
Version:        %{version}
Release:        %{release}
Summary:        Red Hat Product Definition Center
Group:          Development/Libraries
License:        GPL
URL:            https://docs.engineering.redhat.com/display/HTD/PDC
Source0:        %{srcname}-%{version}-%{release}.tar.bz2
BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-sphinx

%description
The Product Definition Center, at its core, is a database that defines every Red Hat products, and their relationships with several important entities.


%package -n %{srcname}-test-data
Summary: Product Definition Center test data
Requires: %{srcname}-server = %{version}-%{release}

%description -n %{srcname}-test-data
This package contains initial data (fixtures) for testing PDC functionality


%package -n %{srcname}-client
Summary: Console client for interacting with Product Definition Center
Requires: python-%{srcname} = %{version}-%{release}
Requires: beanbag

%description -n %{srcname}-client
This package contains a console client for interacting with Product Definition
Center (PDC)


%package -n %{srcname}-server
Summary: Product Definition Center (PDC) server part
Requires:       Django >= 1.8.1
Requires:       django-rest-framework >= 3.1
Requires:       django-mptt >= 0.7.1
Requires:       kobo >= 0.4.2
Requires:       kobo-django
Requires:       kobo-rpmlib
Requires:       koji
Requires:       patternfly1
Requires:       productmd
Requires:       python-django-filter >= 0.9.2
Requires:       python-ldap
Requires:       python-markdown
Requires:       python-mock
Requires:       python-psycopg2
Requires:       python-requests
Requires:       python-requests-kerberos

%description -n %{srcname}-server
This package contains server part of Product Definition Center (PDC)


%prep
%setup -q -n %{srcname}-%{version}-%{release}

%build
make -C docs/ html

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}
mkdir -p %{buildroot}/%{_datadir}/%{srcname}/static
mkdir -p %{buildroot}%{_defaultdocdir}/%{srcname}
mkdir -p %{buildroot}%{_defaultdocdir}/%{srcname}_client
cp -R _test_data %{buildroot}/%{python_sitelib}/%{srcname}
cp sync_to_psql.sh %{buildroot}/%{python_sitelib}/%{srcname}
cp pdc/settings_local.py.dist %{buildroot}/%{python_sitelib}/%{srcname}
cp -R docs %{buildroot}%{_defaultdocdir}/%{srcname}
cp manage.py %{buildroot}/%{python_sitelib}/%{srcname}

install -m 0755 -D -p pdc/pdc-sync-ldap %{buildroot}%{_sysconfdir}/cron.daily/pdc-sync-ldap

# don't need egg info
egg_info=%{buildroot}/%{python_sitelib}/%{srcname}-*.egg-info
if [ -d $egg_info ]; then
  rm -fr $egg_info
fi

# Install apache config for the app:
install -m 0644 -D -p conf/pdc-httpd.conf.sample %{buildroot}%{_defaultdocdir}/pdc/pdc.conf.sample

# Install PDC 'point of contact' command line interface
install -m 0644 -D -p pdc_client/bin/poc %{buildroot}%{_bindir}/poc

# Install PDC client command line interface
install -m 0644 -D -p pdc_client/bin/pdc_client %{buildroot}%{_bindir}/pdc_client

install -m 0644 -D -p docs/pdc_client.1 %{buildroot}%{_mandir}/man1/pdc_client.1
gzip %{buildroot}%{_mandir}/man1/pdc_client.1


# only remove static dir when it's a uninstallation
# $1 == 0: uninstallation
# $1 == 1: upgrade
%preun
if [ "$1" = 0 ]; then
  rm -rf %{_datadir}/%{srcname}/static
fi


%files
%{python_sitelib}/%{srcname}_client

%files -n %{srcname}-server
%defattr(-,root,apache,-)
%{_defaultdocdir}/pdc
%{python_sitelib}/%{srcname}
%{python_sitelib}/contrib
%{python_sitelib}/rhpdc
%exclude %{python_sitelib}/%{srcname}/_test_data
%{_datadir}/%{srcname}
%attr(755, root, root) %{_sysconfdir}/cron.daily/pdc-sync-ldap

%files -n %{srcname}-test-data
%{python_sitelib}/%{srcname}/_test_data

%files -n %{srcname}-client
%attr(755, root, root) %{_bindir}/poc
%attr(755, root, root) %{_bindir}/pdc_client
%{_mandir}/man1/pdc_client.1.gz

%changelog
* Fri Apr 24 2015 Eric Huang <jiahuang@redhat.com> 0.3.0-0.2.beta
- Update migrations for release, release_component, repo, linked_release.

* Thu Apr 23 2015 Eric Huang <jiahuang@redhat.com> 0.3.0-0.1.beta
- Get integrated layered products to release
- Bulk operations in REST APIs
- Track component versions in composes
- Store Engineering Products (ids)
- Mapping bugzilla products to releases
- Track bugzilla subcomponents as well as specific components
- Support loading data from a specific json file for pdc_client

* Fri Mar 13 2015 Eric Huang <jiahuang@redhat.com> 0.2.0-0.2.beta
- Main rpm package name refactor to pdc-server
- CLI client working with any PDC instance(pdc_client)
- Record what components are in specific docker base images
- Ability to query docker images containing specific components
- Find composes with an older version of a package
- Ability to connect releases with brew tags
- Track bugzilla components for release-components
- Populate rpm mappings for releases without composes
- Map a brew build to a release the build was made for
- Improve the performance issue for import rpms

* Thu Jan 29 2015 Eric Huang <jiahuang@redhat.com> 0.1.0-0.2.beta
- As a QE I need to be able to determine the composes where specific rpm NVR is included
- As a Dev|RCM|QE I want to assign and query labels to global components
- query point of contact from CLI
- Implement remaining API for RPM mapping from XMLRPC in REST
- Revisit anonymous access to PDC REST API
- Link PDC release to a bugzilla product
- Sync data source of dist-git repositories and branches
- As an RCM I want to be able to clone releases

* Wed Dec 17 2014 Eric Huang <jiahuang@redhat.com> 0.1.0-0.1.beta
- REST APIs for product, release, component and contact
