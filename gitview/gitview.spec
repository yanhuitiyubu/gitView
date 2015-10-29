%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%global pkg_name gitview

Name: python-%{pkg_name}
Version: 1.0.0
Release: 1%{?dist}
Summary: A Web project gathering git data from projects repositories

Group: Development/Languages
License: GPLv3
URL: https://github.com/GitView/GitView
Source0: %{pkg_name}-%{version}.tar.gz
BuildArch: noarch

BuildRequires:	python-setuptools

Requires:	Django >= 1.5
Requires:	git
Requires:	logrotate
Requires:	httpd
Requires:	mod_auth_kerb
Requires:	mod_wsgi
Requires:	python-reportlab >= 2.5
Requires:	python-psycopg2
Requires(post):	crontabs


%description
A Web project gathering git data from projects repositories.


%prep
%setup -q -n %{pkg_name}-%{version}


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Apache conf
install -m 0644 -D -p conf/gitview.conf ${RPM_BUILD_ROOT}%{_sysconfdir}/httpd/conf.d/%{pkg_name}.conf

# logrotate conf
install -m 0644 -D -p conf/logrotate/gitview ${RPM_BUILD_ROOT}%{_sysconfdir}/logrotate.d/%{pkg_name}
install -m 0755 -D -p bin/gitview-sync-projects ${RPM_BUILD_ROOT}%{_sbindir}/gitview-sync-projects

# Make all necessary directories, including
# 1. project data directory holding all necessary files for gitview running
# 2. runtime data directory holding all data generated during the runtime. For
#    example, the cloned projects, logs produced from gitview features and the
#    scheduled cron job, etc.
# 3. configuration directory holding necessary configuraiton files, including
#    cron job control file for now.

# Project data directory, /usr/share/gitview
# These are necessary for project to run normally.
# Different from that directory that holds data generated during runtime
mkdir -p ${RPM_BUILD_ROOT}%{_datadir}/%{pkg_name}

# Project runtime data directories, root is /var/gitview
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/%{pkg_name}
mkdir ${RPM_BUILD_ROOT}%{_localstatedir}/%{pkg_name}/projects
mkdir ${RPM_BUILD_ROOT}%{_localstatedir}/%{pkg_name}/reports
mkdir ${RPM_BUILD_ROOT}%{_localstatedir}/%{pkg_name}/pdfs

# Directory holding cron job logs
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/log/%{pkg_name}

# Configuration directories
mkdir -p ${RPM_BUILD_ROOT}%{_sysconfdir}/%{pkg_name}

# Run directory holding PID file
mkdir -p ${RPM_BUILD_ROOT}%{_localstatedir}/run/%{pkg_name}


# Crontab schedule conf
install -m 0644 -D -p conf/cron/gitview-sync-projects.cron ${RPM_BUILD_ROOT}%{_sysconfdir}/%{pkg_name}/

# Template files locates /usr/share/gitview/templates
cp -r gitview/templates ${RPM_BUILD_ROOT}%{_datadir}/%{pkg_name}/


%post
crontab %{_sysconfdir}/%{pkg_name}/gitview-sync-projects.cron


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc MANIFEST.in README.md VERSION.txt
%{_sbindir}/*
%{python_sitelib}/%{pkg_name}/
%{python_sitelib}/%{pkg_name}-%{version}-py*.egg-info/
%{_datadir}/%{pkg_name}/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{pkg_name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{pkg_name}
%config(noreplace) %{python_sitelib}/%{pkg_name}/%{pkg_name}/product_settings.py
%{_sysconfdir}/%{pkg_name}

%defattr(-,apache,apache,-)
%{_localstatedir}/%{pkg_name}
%{_localstatedir}/run/%{pkg_name}
%{_localstatedir}/log/%{pkg_name}


%changelog
* Wed Mar 11 2015 Zheng Liu <zheliu@redhat.com> - 1.0.0-1
- Bump to version 1.0.0

* Mon Jan 27 2014 Chenxiong Qi <cqi@redhat.com> - 0.1.0-1
- Bump to version 0.1.0

* Thu Jan 23 2014 Chenxiong Qi <cqi@redhat.com> - 0.0.1-2
- Build RPM package, ready for deployment

* Mon Dec 16 2013 Chenxiong Qi <cqi@redhat.com> - 0.0.1-1
- Initial RPM package build
