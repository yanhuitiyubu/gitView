Summary: Test Package Sanity tools
Name: tps
Version: 2.44.5
Release: 1
Source0: %{name}-%{version}.tar.gz
License: Proprietary
Group: QA
BuildRoot: %{_tmppath}/%{name}-root
BuildRequires: /usr/bin/pod2man
Requires: /bin/bash
Requires: /usr/bin/sudo
Requires: /usr/bin/perl
Requires: redhat-release
Requires: /usr/bin/wget
Requires: perl-DateManip
Requires: perl-XML-Twig
Requires: perl-XML-Parser

BuildArch: noarch

%description
Dummy package, Do NOT use

%package polling
Summary: Test Package Sanity tools
Group: QA
Obsoletes: tps tps-stacks tps-devel
Provides: TPS
Requires: /usr/bin/perl
Requires: redhat-release
Requires: /usr/bin/wget
Requires: perl-DateManip
Requires: perl-XML-Twig
Requires: perl-XML-Parser

%description polling
Tools for testing sanity and rhnqa for errata packages.  Polls Errata Tool for jobs.
Red Hat Internal Use Only.

%package devel
Summary: Test Package Sanity tools for non-errata-stable-systems.  Most people want this version.
Group: QA
Provides: TPS
Obsoletes: tps-polling tps-stacks
Requires: /usr/bin/perl
Requires: redhat-release
Requires: /usr/bin/wget
Requires: perl-DateManip
Requires: perl-XML-Twig
Requires: perl-XML-Parser

%description devel
Standalone package-sanity tools without automation daemon
Red Hat Internal Use Only.

%package stacks
Summary: Special TPS version for working in the stacks environment
Group: QA
Provides: TPS
Conflicts: tps-polling tps-devel
Requires: /usr/bin/perl
Requires: redhat-release
Requires: /usr/bin/wget
Requires: perl-DateManip
Requires: perl-XML-Twig
Requires: perl-XML-Parser

%description stacks
Test Package Sanity tools for the stacks environment
Red Hat Internal Use Only.

%prep
%setup -q

%build
make

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT
DESTDIR=$RPM_BUILD_ROOT make install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/etc/profile.d/tps-cd.sh

%files polling
%defattr(-,root,root)
/etc/init.d/tpsd
/etc/profile.d/tps-cd.sh
/etc/rsyslog.d/tpsd.conf
%config(missingok) %verify(not md5 size mtime) /etc/tpsd.conf
/usr/lib/systemd/system/tpsd.service
%dir %attr(-,root,root)/usr/local/bin
/usr/local/bin/tps
/usr/local/bin/tps-auto
/usr/local/bin/tps-auto-rhnqa
/usr/local/bin/tpsd
/usr/local/bin/tps-brew-autoconf-cmp
/usr/local/bin/tps-cache-pkgs
/usr/local/bin/tps-check-channels
/usr/local/bin/tps-check-stable
/usr/local/bin/tps-channel-cache
/usr/local/bin/tps-channel-info
/usr/local/bin/tps-cmp-channels
/usr/local/bin/tps-collect-test-summary
/usr/local/bin/tps-diff-sources
/usr/local/bin/tps-downgrade
/usr/local/bin/tps-filter-filelist
/usr/local/bin/tps-ff
/usr/local/bin/tps-get-dist-from-spec
/usr/local/bin/tps-lib.pl
/usr/local/bin/tps-list-buildroot
/usr/local/bin/tps-make-lists
/usr/local/bin/tps-markup
/usr/local/bin/TpsNavMark.pm
/usr/local/bin/tps-query
/usr/local/bin/tps-parse-up2date-chan
/usr/local/bin/tps-parse-yum-chan
/usr/local/bin/tps-report
/usr/local/bin/tps_report.py
/usr/local/bin/tps-rhnqa
/usr/local/bin/tps-rpmtest
/usr/local/bin/tps-setup-channel-cache
/usr/local/bin/tps-show-channels
/usr/local/bin/tps-srpmtest
/usr/local/bin/tps-status
/usr/local/bin/tps-summarize
/usr/local/bin/tps-upgrade
/usr/local/bin/tps-vercmp.pl
/usr/local/bin/tps-waive
/usr/local/bin/tps-which
/usr/local/bin/tps-yumdownloader
/usr/local/bin/tps-yum-show-channels
/usr/local/bin/tps-yum-show-channels-old
/usr/local/bin/tpsserv-checkin-tpsd
/usr/local/bin/rhnqa-lib.pl
/usr/local/bin/update-tps
/usr/local/bin/update-tpsd-settings
/usr/local/bin/find_package
/usr/local/bin/get-packages
/usr/local/bin/rpm-vercmp
%dir %attr(-,root,root)/usr/local/lib/tps
/usr/local/lib/tps/tps-blacklist.txt
/usr/local/lib/tps/shlib-special-cases.txt
/usr/local/lib/tps/srpm-special-cases.txt
%dir %attr(-,root,root)/usr/local/lib/tps/modules
/usr/local/lib/tps/modules/tps-example.pl
/usr/local/lib/tps/modules/bash.pl
/usr/local/lib/tps/modules/glibc.pl
/usr/local/lib/tps/modules/krb5-libs.pl
#/usr/local/lib/tps/modules/kernel.pl
/usr/local/lib/tps/modules/rpm.pl
/usr/local/lib/tps/modules/pam.pl
/usr/local/lib/tps/modules/perl.pl
/usr/local/lib/tps/modules/samba.pl
%dir %attr(-,root,root)/usr/local/man/man1
/usr/local/man/man1/tps.1
/usr/local/man/man1/tpsd.1
/usr/local/man/man1/tps-cache-pkgs.1
/usr/local/man/man1/tps-collect-test-summary.1
/usr/local/man/man1/tps-get-dist-from-spec.1
/usr/local/man/man1/tps-query.1
/usr/local/man/man1/tps-rhnqa.1
/usr/local/man/man1/tps-report.1
/usr/local/man/man1/tps-rpmtest.1
/usr/local/man/man1/tps-srpmtest.1
/usr/local/man/man1/tps-make-lists.1
/usr/local/man/man1/tps-waive.1
/usr/local/man/man1/tps-markup.1
/usr/local/man/man1/update-tps.1
/usr/local/man/man1/tps-cd.1
/usr/local/man/man1/tps-ff.1
/usr/local/man/man1/tps-filter-filelist.1
/usr/local/man/man1/get-packages.1
/usr/local/man/man1/tps-downgrade.1
/usr/local/man/man1/tps-rhts.1
/usr/local/man/man1/tps-upgrade.1
/usr/local/man/man1/tps-which.1
/usr/local/man/man1/tps-setup-channel-cache.1
/usr/local/man/man1/tps-show-channels.1
/usr/local/man/man1/tps-check-channels.1
/usr/local/man/man1/tps-parse-yum-chan.1
/usr/local/man/man1/tps-parse-up2date-chan.1

%files devel
%defattr(-,root,root)
/etc/profile.d/tps-cd.sh
%config(missingok) %verify(not md5 size mtime) /etc/tpsd.conf
%dir %attr(-,root,root)/usr/local/bin
/usr/local/bin/Erratify
/usr/local/bin/tps
/usr/local/bin/tps-brew-autoconf-cmp
/usr/local/bin/tps-channel-cache
/usr/local/bin/tps-channel-info
/usr/local/bin/tps-cache-pkgs
/usr/local/bin/tps-check-channels
/usr/local/bin/tps-check-stable
/usr/local/bin/tps-cmp-channels
/usr/local/bin/tps-collect-test-summary
/usr/local/bin/tps-diff-sources
/usr/local/bin/tps-downgrade
/usr/local/bin/tps-filter-filelist
/usr/local/bin/tps-ff
/usr/local/bin/tps-get-dist-from-spec
/usr/local/bin/tps-lib.pl
/usr/local/bin/tps-list-buildroot
/usr/local/bin/tps-make-lists
/usr/local/bin/tps-markup
/usr/local/bin/TpsNavMark.pm
/usr/local/bin/tps-parse-up2date-chan
/usr/local/bin/tps-parse-yum-chan
/usr/local/bin/tps-query
/usr/local/bin/tps-report
/usr/local/bin/tps_report.py
/usr/local/bin/tps-rhnqa
/usr/local/bin/tps-rhts
/usr/local/bin/tps-rpmtest
/usr/local/bin/tps-setup-channel-cache
/usr/local/bin/tps-show-channels
/usr/local/bin/tps-srpmtest
/usr/local/bin/tps-upgrade
/usr/local/bin/tps-vercmp.pl
/usr/local/bin/tps-which
/usr/local/bin/tps-yumdownloader
/usr/local/bin/tps-yum-show-channels
/usr/local/bin/tps-yum-show-channels-old
/usr/local/bin/tpsserv-checkin-tpsd
/usr/local/bin/update-tps
/usr/local/bin/update-tpsd-settings
/usr/local/bin/rhnqa-lib.pl
/usr/local/bin/find_package
/usr/local/bin/get-packages
/usr/local/bin/rpm-vercmp
%dir %attr(-,root,root)/usr/local/lib/tps
/usr/local/lib/tps/tps-blacklist.txt
/usr/local/lib/tps/shlib-special-cases.txt
/usr/local/lib/tps/srpm-special-cases.txt
%dir %attr(-,root,root)/usr/local/lib/tps/modules
/usr/local/lib/tps/modules/tps-example.pl
/usr/local/lib/tps/modules/bash.pl
/usr/local/lib/tps/modules/glibc.pl
/usr/local/lib/tps/modules/krb5-libs.pl
#/usr/local/lib/tps/modules/kernel.pl
/usr/local/lib/tps/modules/rpm.pl
/usr/local/lib/tps/modules/pam.pl
/usr/local/lib/tps/modules/perl.pl
/usr/local/lib/tps/modules/samba.pl
%dir %attr(-,root,root)/usr/local/man/man1
/usr/local/man/man1/tps.1
/usr/local/man/man1/tps-cache-pkgs.1
/usr/local/man/man1/tps-collect-test-summary.1
/usr/local/man/man1/tps-rhnqa.1
/usr/local/man/man1/tps-rpmtest.1
/usr/local/man/man1/tps-srpmtest.1
/usr/local/man/man1/tps-make-lists.1
/usr/local/man/man1/tps-markup.1
/usr/local/man/man1/update-tps.1
/usr/local/man/man1/tps-cd.1
/usr/local/man/man1/tps-downgrade.1
/usr/local/man/man1/tps-report.1
/usr/local/man/man1/tps-rhts.1
/usr/local/man/man1/tps-upgrade.1
/usr/local/man/man1/tps-which.1
/usr/local/man/man1/tps-setup-channel-cache.1
/usr/local/man/man1/tps-show-channels.1
/usr/local/man/man1/tps-check-channels.1
/usr/local/man/man1/tps-ff.1
/usr/local/man/man1/tps-filter-filelist.1
/usr/local/man/man1/get-packages.1
/usr/local/man/man1/tps-parse-yum-chan.1
/usr/local/man/man1/tps-parse-up2date-chan.1

%files stacks
%defattr(-,root,root)
/etc/init.d/tpsd
/etc/profile.d/tps-cd.sh
%config(missingok) %verify(not md5 size mtime) /etc/tpsd.conf
%dir %attr(-,root,root)/usr/local/bin
/usr/local/bin/tps
/usr/local/bin/tps-auto
/usr/local/bin/tps-auto-rhnqa
/usr/local/bin/tpsd
/usr/local/bin/tps-brew-autoconf-cmp
/usr/local/bin/tps-channel-cache
/usr/local/bin/tps-channel-info
/usr/local/bin/tps-cache-pkgs
/usr/local/bin/tps-check-channels
/usr/local/bin/tps-check-stable
/usr/local/bin/tps-cmp-channels
/usr/local/bin/tps-collect-test-summary
/usr/local/bin/tps-diff-sources
/usr/local/bin/tps-downgrade
/usr/local/bin/tps-filter-filelist
/usr/local/bin/tps-ff
/usr/local/bin/tps-get-dist-from-spec
/usr/local/bin/tps-lib.pl
/usr/local/bin/tps-list-buildroot
/usr/local/bin/tps-make-lists
/usr/local/bin/tps-markup
/usr/local/bin/TpsNavMark.pm
/usr/local/bin/tps-parse-up2date-chan
/usr/local/bin/tps-parse-yum-chan
/usr/local/bin/tps-query
/usr/local/bin/tps-report
/usr/local/bin/tps-rhnqa
/usr/local/bin/tps-rpmtest
/usr/local/bin/tps-setup-channel-cache
/usr/local/bin/tps-show-channels
/usr/local/bin/tps-srpmtest
/usr/local/bin/tps-status
/usr/local/bin/tps-summarize
/usr/local/bin/tps-upgrade
/usr/local/bin/tps-vercmp.pl
/usr/local/bin/tps-waive
/usr/local/bin/tps-which
/usr/local/bin/tps-yumdownloader
/usr/local/bin/tps-yum-show-channels
/usr/local/bin/tps-yum-show-channels-old
/usr/local/bin/tpsserv-checkin-tpsd
/usr/local/bin/update-tps
/usr/local/bin/update-tpsd-settings
/usr/local/bin/rhnqa-lib.pl
/usr/local/bin/find_package
/usr/local/bin/get-packages
/usr/local/bin/rpm-vercmp
%dir %attr(-,root,root)/usr/local/lib/tps
/usr/local/lib/tps/tps-blacklist.txt
/usr/local/lib/tps/shlib-special-cases.txt
/usr/local/lib/tps/srpm-special-cases.txt
%dir %attr(-,root,root)/usr/local/lib/tps/modules
/usr/local/lib/tps/modules/tps-example.pl
/usr/local/lib/tps/modules/bash.pl
/usr/local/lib/tps/modules/glibc.pl
/usr/local/lib/tps/modules/krb5-libs.pl
#/usr/local/lib/tps/modules/kernel.pl
/usr/local/lib/tps/modules/rpm.pl
/usr/local/lib/tps/modules/pam.pl
/usr/local/lib/tps/modules/perl.pl
/usr/local/lib/tps/modules/samba.pl
%dir %attr(-,root,root)/usr/local/man/man1
/usr/local/man/man1/tps.1
/usr/local/man/man1/tpsd.1
/usr/local/man/man1/tps-cache-pkgs.1
/usr/local/man/man1/tps-collect-test-summary.1
/usr/local/man/man1/tps-query.1
/usr/local/man/man1/tps-rhnqa.1
/usr/local/man/man1/tps-report.1
/usr/local/man/man1/tps-rpmtest.1
/usr/local/man/man1/tps-srpmtest.1
/usr/local/man/man1/tps-make-lists.1
/usr/local/man/man1/tps-waive.1
/usr/local/man/man1/tps-markup.1
/usr/local/man/man1/update-tps.1
/usr/local/man/man1/tps-cd.1
/usr/local/man/man1/tps-downgrade.1
/usr/local/man/man1/tps-rhts.1
/usr/local/man/man1/tps-upgrade.1
/usr/local/man/man1/tps-which.1
/usr/local/man/man1/tps-setup-channel-cache.1
/usr/local/man/man1/tps-show-channels.1
/usr/local/man/man1/tps-check-channels.1
/usr/local/man/man1/tps-ff.1
/usr/local/man/man1/tps-filter-filelist.1
/usr/local/man/man1/get-packages.1
/usr/local/man/man1/tps-parse-yum-chan.1
/usr/local/man/man1/tps-parse-up2date-chan.1

%post polling
if type -a systemctl >/dev/null 2>&1 ; then
    # RHEL7+. Splitting tps-client by RHEL is not feasible.
    rm -f /etc/init.d/tpsd
    systemctl daemon-reload
    systemctl restart rsyslog
    systemctl enable tpsd
    systemctl start  tpsd
else
    # <= RHEL6
    /sbin/chkconfig --add tpsd
    /sbin/chkconfig tpsd --level 35 on
fi
/bin/rm -f /tmp/tps-query-cache.txt /tmp/tps-rhn-channels.txt /tmp/tps-rhn-channels-info.txt /tmp/tps-update-info.txt

%post devel
echo ' '

%post stacks
perl -npe "s/^TPS_MODE='normal'/TPS_MODE='stacks'/" -i /etc/tpsd.conf
/bin/rm -f /tmp/tps-query-cache.txt /tmp/tps-rhn-channels.txt /tmp/tps-rhn-channels-info.txt /tmp/tps-update-info.txt
echo ' '

%changelog
* Wed Jun 10 2015 Jon Orris <jorris@redhat.com> 2.44.5-1
- bz821892 - warn if package changes architecture
- bz1194426 - missing packages in tps-make-lists
- bz1219552 - TPS hangs in RPMtest, rpm.pl filelist & safety fix
- bz1228487 - Handle RHN Destinations better
- internal cleanups, docs, build process

* Tue May 26 2015 Ed Santiago <santiago@redhat.com> 2.44.4-2
- bz1224773 - missing tps_report.py from tps-devel

* Wed May 20 2015 John W. Lockhart <lockhart@redhat.com> 2.44.4-1
- bz1027309 - fix tpsd startup on RHEL7.1
- bz1151060, bz963231 - SharedLib exceptions
- bz1199144 - tps-cd without running tps-make-lists
- bz1204905 - tps-query: fix timestamp on tps.txt
- bz1208688 - tps-get-dist-from-spec: new; handle more cases
- tps-report: rewrite, use tps.html more often
- internal cleanups, build process + docs, and unit tests

* Sat Feb 14 2015 John W. Lockhart <lockhart@redhat.com> 2.44.3-4
- BZ 1181878: add tps-collect-test-summary and manpage
* Mon Jan 26 2015 John W. Lockhart <lockhart@redhat.com> 2.44.3-3beta02
- tpsserv-checkin-tpsd: change wording in help text to avoid a
  bug in rpmbuild.
* Fri Jan 23 2015 John W. Lockhart <lockhart@redhat.com> 2.44.3-3beta01
- BZ 1181848: stop pounding tps-server with checkins
- BZ 1181743: fix handling of $VERBOSE
- BZ 1126541: SharedLibTest special case for java-1.7.0-oracle-javafx
- BZ  850319: Add link to ET 'Builds' page in logs
* Tue Dec 16 2014 John W. Lockhart <lockhart@redhat.com> 2.44.3-2
- promote to production
* Thu Dec 11 2014 John W. Lockhart <lockhart@redhat.com> 2.44.3-0_beta01
- bz 1146977: allow local special-cases for srpmtest
- bz 1169896: handle duplicate name.arch correctly in ET filelists
- tps-make-lists: add debugging features around ET API calls
- tps-which manpage: clarify meaning of output.
* Tue Nov  4 2014 John W. Lockhart <lockhart@redhat.com> 2.44.2-1
- bz 1027309: change selinux context to avoid denials
- tps-lib: fix uninitialized variable msg on ARM.
- tps-make-lists: remove obsolete example in help text.
- tps-make-lists manpage: fix typo (thanks: Chenxiong Qi).
* Mon Oct 13 2014 John W. Lockhart <lockhart@redhat.com> 2.44.2-01beta
- bz 1151060: fixes for oracle java-1.8.0
- tps-update: update manpage to reflect correct mountpoint
- tps-lib, find_package: add support for aarch64 and ppc64le.
- tps-query: use tps-lib rather than wget, improve retries and
  error handling along the way.
* Thu Oct  2 2014 John W. Lockhart <lockhart@redhat.com> 2.44.2-00beta
- bz 1147155: flush rhn channel info on tpsd startup
- bz 1120204: do not override an already-set TPS_LIMIT_CHANNELS_TO
- bz 1110663: do not use spurious yum msgs as repo names.
- bz 1075214: PROVIDES_OUT file missing when newPkgList too big
* Wed Jun 18 2014 John W. Lockhart <lockhart@redhat.com> 2.44.1-3
- BZ 1110970: fix Uniqueness failure messages in tps-make-lists
* Sat Jun 14 2014 John W. Lockhart <lockhart@redhat.com> 2.44.1-2
- BZ 1107525: bump version for ibm-java srpm special case
- BZ 1109073: allow relative paths in tps-diff-sources; also
  remove spurious double-quotes from help text.
* Thu Jun  5 2014 John W. Lockhart <lockhart@redhat.com> 2.44.1-1
- Graduate from beta to production, first official RHEL-7 release.
- tps-query: remove OLD_FMT support, change TPS_USE_CHANNEL_MAP
  to TPS_RHN2PULP_MAP, to avoid accidental consumption of RHN jobs
  on pulp machines using the new tps.txt format.  Alter help and docs
  and debug messages accordingly.
- tps-report: update comments to help with unusual circumstances.
- tps-lib: respect environment vars set to empty strings or zero.
* Fri Apr 11 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta09
- tps-lib: fix uninitialized use problem uncovered by tps-srpmtest.
* Thu Apr 10 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta08
- rhnqa-lib, tps-check-stable, tps-lib, tps-rhnqa, tps-rhnqa.1:
  BZ 1085884, spruce up rhn-vs-pulp messages and functionality;
  introduce TPS_NO_YUM_SOURCE to control expectations around yum
  source downloads.  Update docs.
* Wed Apr  9 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta07
- rhnqa-lib, tps-lib, tps-rhnqa: BZ 1085884, basic fixes for pulp/rhel7
* Tue Apr  8 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta06
- tps-query: improve OldFmt handling, add ChannelMap feature,
  update help.
- tps-channel-cache: use oats-apply-test-profile, not rhn-profile.
- tps-setup-channel-cache: update text to avoid being RHN-centric.
* Sat Apr  5 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta05
- tps-lib: add routines centered around pulp repos and channels.
  Auto-detect DistMethod when possible, use correct ET API for fetching
  filelists based on DistMethod.
- tps: enable dumping of non-scalar variables, good for listing repos
  using the -g option.
- tps-make-lists: match the pulp-idname used by ET in its pulp
  channel lists.
- get-packages and manpage: update for pulp channels and dist_method.
- tps-channel-cache: never disable tps-profile.repo; add --quiet option;
  adjust default distmethod to use tps-lib.
- tps-query, tps-lib: use new --quiet option with tps-channel-cache.
* Thu Apr  3 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta04
- tpsserv-checkin-tpsd: use tps-lib for product/arch/stream info,
  and correct arch info for rhel-7.
* Thu Mar 27 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta03
- tps-lib: fix three important 1-character typos.
* Thu Mar 27 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta02
- tps-query: allow skip of channel cache refresh.  Improve error handling.
- tps-channel-cache: pulp support in progress; respect ENV; flag to
  skip most refreshes.  BZ 1058990.
- tps-lib: shellFileToEnv routine created.
* Tue Mar 25 2014 John W. Lockhart <lockhart@redhat.com> 2.43.0-1.beta01
- tps-lib, tps-query, tpsd: BZ 1066154: update for RHEL-7
  and new tps.txt format.
* Sat Feb 15 2014 John W. Lockhart <lockhart@redhat.com> 2.42.0-1
- tpsserv-checkin-tpsd: use tps-server.lab for default TpsServer.
- bz 1061807: fix SCL builds on RHEL-5
- bz 1061734: fix channel caches for RHEL-7
* Thu Jan  9 2014 John W. Lockhart <lockhart@redhat.com> 2.41.4-1
- bz 877192: also update tps-rhts for rhel-7 redhat-release handling.
* Wed Jan  8 2014 John W. Lockhart <lockhart@redhat.com> 2.41.3-3beta
- bz 877192: remember to chomp any newlines from the new query of
  redhat-release.
- bz 877192: also update tps-rhts for rhel-7 detection.
* Mon Dec 16 2013 John W. Lockhart <lockhart@redhat.com> 2.41.3-2beta
- bz 1043439: fix bash syntax error (RHEL-7)
- bz 877192: change all code that queries redhat-release
  for RHEL-7 compatibility.
* Wed Nov  6 2013 John W. Lockhart <lockhart@redhat.com> 2.41.3-1
- bz 1021634: update docs, comments, messages for SRPM_SKIP_CHANNELS.
- bz 1026678: srpmtest: mark fail correctly when present along
  with an unrelated special-case pass.
* Fri Nov  1 2013 John W. Lockhart <lockhart@redhat.com> 2.41.2-1
- bz 1013476: better handling for mixed and stray starts
- bz 1021634: honor SRPM_SKIP_CHANNELS in non-stacks mode
- bz 1013864: handle non-zero from file command for RHEL7
* Fri Sep 27 2013 John W. Lockhart <lockhart@redhat.com> 2.41.0-1
- tpsd.conf: document new variable for builds by non-root user
- tps-srpmtest manpage: document non-root builds
* Thu Sep 26 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-9pre.beta05
- tps-lib: bz 1012248, use only installed pkgs with DeleteTest
- tps-srpmtest: bz 784565, fix install/remove of sclBuildPackage
* Tue Sep 24 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-9pre.beta04
- srpmtest: bz 784565, c18: fix undefined subroutine from prior beta version.
- srpmtest: bz 913182, report package state at start of rebuilds
- srpmtest-special-cases: bz 966516 for rhev-guest-tools-iso
* Sat Sep 21 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-9pre.beta03
- bz 966512, tps-srpmtest: add special-case handler for
  extra packages built
- tps-lib: deal with VMs where hostname -f fails
- srpm-special-cases: add tag to comments for new handler
* Fri Sep 13 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-9pre.beta02
- bz 592028, more BuildReqs
- bz 1007542, false positive bites DeleteTest
- bz 1003853, rtas_errd error string
- bz 520672 for libofficebean in OO/libreoffice
* Fri Aug 23 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-pre9.beta01
- BZ 465477, 472459: partial support, non-root builds
- BZ 784565: first cut of SCL build support
- BZ 990891: use only uninstalled old packages when downgrading
* Wed Jul 17 2013 John W. Lockhart <lockhart@redhat.com> 2.40.8-1
- bz 980077: special case for virtio-win
- bz 985263: add message if tpsd is stopped
- fix BZ 913000, all-uppercase on test name
- BZ 979203: avoid calling getRHNChannels on unknown advisory number
* Tue Jun 25 2013 John W. Lockhart <lockhart@redhat.com> 2.40.7-1
- BZ 977369: Erratify: update for move from ntap-vader for engarchives
- BZ 725043: tps-srpmtest: dump build environment settings
  to tps-rebuild-env.log.
- BZ 516745: tps-rhnqa, resolve issues with multilib yum installs
* Wed Jun 12 2013 John W. Lockhart <lockhart@redhat.com> 2.40.6-5
- Erratify: also update for tpsdist dir.
* Wed Jun 12 2013 John W. Lockhart <lockhart@redhat.com> 2.40.6-4
- update-tps: use tpsdist directory rather than scratch/RPMS.
- tpsd.conf: set default for use_yum_install to 'true'
* Mon Apr 29 2013 John W. Lockhart <lockhart@redhat.com> 2.40.6-3
- tps-report: remove two debugging messages.
* Sat Apr 27 2013 John W. Lockhart <lockhart@redhat.com> 2.40.6-2
- add tps-query to the tps-devel package, since it is required for
  obtaining channel/release info from the ET's get_tps_txt.
* Sat Apr 27 2013 John W. Lockhart <lockhart@redhat.com> 2.40.6-1
- bz950100 fix: allow tps-report to use non-default directories
- bz877290 fix: add support for get_tps_txt
- bz592028 fix: make gatherBuildReqs smarter
- Erratify: update for change to storage.bos
* Fri Mar  1 2013 John W. Lockhart <lockhart@redhat.com> 2.40.5-1
- tpsd: refresh tps-server settings every 30 minutes or if missing.
- tpsd: BZ 850491, exit unless tps-server says the host is a stable system.
- tpsd: exit if DNS cannot resolve the local hostname.
- tps-make-lists: BZ 869977: remove WARN status when SRPMs are not
  found in released channels.
- tps-status: BZ 677965, 903765:  make tps-status handle multiple
  processes, add feature to report CWD of process.
- tps-cd: BZ 677965, 903765:  let tps-cd change to the CWD of the
  last active process.
- tps-vercmp: BZ 913239: fix cmp_rpmstrings() routine.
* Thu Jan 10 2013 John W. Lockhart <lockhart@redhat.com> 2.40.4-2
- bz 893382: Erratify: retire curly.devel as mnt_redhat
* Thu Jan 10 2013 John W. Lockhart <lockhart@redhat.com> 2.40.4-1
- bz 854911: tps-diff-sources: fix help docs and exit with error
  message if rpm fails to unpack a source rpm
- bz 876623: tps-cache-pkgs: process dep-errata; add option
  to skip dep-errata; update manpage.
* Wed Dec 19 2012 John W. Lockhart <lockhart@redhat.com> 2.40.3-1
- bz 888723: TpsNavMark: fix link to tps results in ET
- bz 839932: tps-cmp-channels: remove redundant output for executive
  summary when lists are identical, and remove trailing newline from
  reports.
* Mon Dec 17 2012 John W. Lockhart <lockhart@redhat.com> 2.40.2-2
- tps.spec: edit a few days of the week in changelog to make brewtap happy
* Mon Dec 17 2012 John W. Lockhart <lockhart@redhat.com> 2.40.2-1
- tps-make-lists manpage: add notes about ET API to help explain
  the Blocks/DependsOn options.
* Fri Dec 14 2012 John W. Lockhart <lockhart@redhat.com> 2.40.1-1
- bz 847780: shlib-special-cases: add special case for brlapi
- bz 484351: tps: tell user to see individual logfiles for subsequent runs
- bz 849677: tps-rhnqa: change "scary" wording around failure
  of tps-make-lists, add tip to see tps-make-lists logfile.
- bz 676261: tps-srpmtest: tweak wording for too many packages built
- bz 864483: tps-make-lists: add option to avoid checking
  blocks & deps on from ET
- tps-make-lists.1: document new options for avoiding the check
  on Blocks & Deps on from ET
- bz 849916: tps-rhnqa: fix problem with yum install
  and --exact not using the full NVRA
- bz 677965: tps-status: fix errors from tps-status by ensuring
  that pidof returns no more than one PID
- bz 867645: tps-make-lists: create channel cache before use if
  it was missing, handle troubles more gracefully if
  channel cache creation fails
- bz 878044: tps-make-lists, tps-check-stable: fix deprecation
  warnings on use of qw()
- tps-lib.pl: add fixChannelCache routine for programs that need it
- bz 876407: tps-channel-cache: use oats-apply-rhn-profile when
  fixing subscriptions
- bz 869793: tps-filter-filelist: add output options for name.arch
  and name-version-release.arch
* Fri Oct 12 2012 John W. Lockhart <lockhart@redhat.com> 2.39.1-1
- tps-markup, TpsNavMark: tweak to implement final visual
  scheme as voted on by QE.  Also added option for the old scheme.
- tps-markup.1: update manpage to document old-scheme option.
* Mon Oct  8 2012 John W. Lockhart <lockhart@redhat.com> 2.38-11beta
- BZ 862946, re-fix to remove regression.
* Thu Oct  4 2012 John W. Lockhart <lockhart@redhat.com> 2.38-10beta
- tps-markup: close the body/html tags, BZ 520794 and 852375.
- tps-make-lists: BZ 752819: enable new subtest called
  "Info on Released Package Accuracy" to warn of potential
  issues with the old-files list.
- tps-check-stable: BZ 863293: provide additional info in
  output: tps-server info plus tps-cmp-channels check.
* Wed Oct  3 2012 John W. Lockhart <lockhart@redhat.com> 2.38-9beta
- tps-markup, TpsNavMark: bugfixes towards BZ 520794 and 852375:
  fix navigation buttons when invoked on multiple files.
* Wed Oct  3 2012 John W. Lockhart <lockhart@redhat.com> 2.38-8beta
- tps-lib: fix BZ 862433: hide PackageName messages as TPSDEBUG
* Wed Oct  3 2012 John W. Lockhart <lockhart@redhat.com> 2.38-7beta
- tps-markup, TpsNavMark: bugfixes towards BZ 520794 and 852375.
- get-packages: fix BZ 862946: problems with -j option.
* Fri Sep 28 2012 John W. Lockhart <lockhart@redhat.com> 2.38-6beta
- tps-markup, TpsNavMark: complete rewrite of raw-to-html
  converter, BZ 520794 and 852375. tps-nav-markup.pl retired in the process.
- tps-srpmtest: Fix BZ 745958: improve TPSTIPs when extra packages are built
- shlib special cases: bz 755503 for audispd-plugins
- shlib special cases: bz 729347, special case for gfs-utils/gfs_edit
- tps-make-lists: BZ 841747: srpms omitted from filelists when duplicates
  exist from dep-errata
- tps-cmp-channels: BZ 839932: add -e option to print executive summary;
  also changes order of info that is printed.  Lists now come first,
  diffs come second.
- tps, tps-rhnqa, tps-rpmtest, tps-srpmtest: BZ 838506: exit with non-zero
  if bad option is supplied
- tps-lib: ensure that reference to global hash, if used, is available
  for any .pm files that need it.
* Fri Jun 22 2012 John W. Lockhart <lockhart@redhat.com> 2.38-5
- tps.spec, Makefile: BZ 800717, fix for tps-yum-show-channels
  not working with --noplugins and --all arguments.
- tps-rhnqa: Fix BZ 833840, ensure that tps-markup runs
  even if tps-make-lists fails.
- tps-markup: Fix bz 826029, incorrect begin/end with subtests;
  thanks to mcermak for the patch.
- samba.pl: latest version from mcermak.
* Fri May 25 2012 John W. Lockhart <lockhart@redhat.com> 2.38-4
- new: tps-cmp-channels, compare subscriptions to profile
- new: samba.pl module, disabled but included for debugging
- Erratify: update brq mounts, see also BZ 801224
- srpmtest-special-cases.txt: Update for java, BZ 805823/805824.
- tps-report.1 manpage: expand information about job/run IDs
  and ways to use variables-auto.sh
- tps-filter-filelist and its manpage: disambiguate the "-a"
  option.  -a now means --all, and -e means --name.
- tps-make-lists: Add TPSTIP for GetReleasedPackages failure message
- tps-check-channels and its manpage: add --separator feature
  for use by tps-make-lists.
- tpsd: report job start/completion to tps-server
* Tue Mar 13 2012 John W. Lockhart <lockhart@redhat.com> 2.38-3
- tpsd: fix BZ 802913: export settings discovered from tps-server
* Wed Mar  7 2012 John W. Lockhart <lockhart@redhat.com> 2.38-2
- rhnqa-lib.pl, tps, tps-lib.pl, tps-rhnqa, tps-rpmtest:
  Fix BZ 752624: repos to be disabled are now only gathered when needed.
- tpsd: use tps-server info to update which channels will be
  checked for jobs.
- update-tpsd-settings: new program, grabs tps-server info and
  creates settings for consumption by tpsd.  Included in all
  subpackages in case anything else needs the tps-server info
  in the future.
- tpsd.conf: explicitly declare the location of materials that
  are persistently cached by tps.
* Wed Feb 29 2012 John W. Lockhart <lockhart@redhat.com> 2.37-5
- tpsserv-checkin-tpsd: add fetch feature, and ability to report
  additional info per recent tps-server changes - such as Notes.
- tps-lib: fix deprecation warning from newer versions of perl
- tps-rhnqa: fix bz 768290, rhnswitch failures should be re-tried
- tps-yum-show-channels: add "traceback" to list of known yum errors
- tps-nav-markup.pl: update tps bz, helpdesk, eng-ops links
* Fri Nov 18 2011 John W. Lockhart <lockhart@redhat.com> 2.37-4
- tps-make-lists: correct invocation of find_package, which
  cannot find multiple packages in one call (BZ 750921).
* Thu Nov 17 2011 John W. Lockhart <lockhart@redhat.com> 2.37-3
- tps-make-lists: fix BZ 750921, modify report for NewlyReleased.
- tps-nav-markup: fix bz 754135: typos in linked names
- tps-yum-show-channels: fix bz 754251: ensure that error
  text is passed along so that RHN-Abuse messages can once again
  be auto-fixed.
- tps-rhnqa: add --exact feature for testing z-stream when newer
  mainstream package has already been pushed.
- tps-rhnqa.1: document --exact in manpage.
* Mon Oct 31 2011 John W. Lockhart <lockhart@redhat.com> 2.37-2
- Fix BZ 732188: fix false positives that happened with package names
  that contain the word 'error' or 'fail'.
- Fix BZ 742929: do not use error messages in piped command in tps-upgrade
- Fix BZ 736662, 681526: by default, get value for dist macro from brew.
- New: tps-list-buildroot, tps-brew-autoconf-cmp.  Both are used
  by tps-srpmtest.
- New: tpsserv-checkin-tpsd.  Early release, with more features to come.
  By default, reports various bits of system info to development
  version of tps-server.  Used by tpsd, with output turned off.
- tps-srpmtest: use new scripts and dist methods.
- tps-srpmtest.1: document new scripts and dist methods.
- tps-lib: new support routines, including updatePackageState.
- all: use updatePackageState liberally, making current state
  available to all routines for future use.
* Tue Sep  6 2011 John W. Lockhart <lockhart@redhat.com> 2.36-20
- Address BZ 733212 by attempting to work around inconsistencies
  in yum.  This release moves the old python code to
  tps-yum-show-channels-old, and only calls it if there is a
  need to list disabled repos.  Other uses rely on the verbose
  output of yum repolist to work consistently and reliably.
* Thu Jul 14 2011 John W. Lockhart <lockhart@redhat.com> 2.36-19
- tps-rhnqa, tps-lib, rhnqa-lib: fix BZ 620322 better; the prior
  update worked for yumdownloader, but not always for yum.
* Thu Jul 14 2011 John W. Lockhart <lockhart@redhat.com> 2.36-18
- tps-rhnqa, tps-lib, rhnqa-lib: support use of NVRA for
  kernel when using yum
- tps-lib: locate libperl.so for future shlib test features.
* Fri Jul  1 2011 John W. Lockhart <lockhart@redhat.com> 2.36-17
- tps-rhnqa: add another PackageState check in Binary Completeness,
  against the small chance that something else has altered the system
  during the test run.
- rhnqa-lib.pl: improve detection of repomd errors; also ensure
  that any yum retries are logged in the .raw file rather than
  being thrown away.  Fixes error observed with 2011:0650 and
  unwanted yum rpmdb-check messages.
* Tue Jun 28 2011 John W. Lockhart <lockhart@redhat.com> 2.36-16
- tpsd.conf: update url for devel instance of tps-server
* Tue Jun 21 2011 John W. Lockhart <lockhart@redhat.com> 2.36-15
- tps-make-lists: Ensure that erratum, release, arch, and
  ETRelease wind up on stdout for beaker logs
- tps-which: add --no-dep-errata feature per BZ 712347
- tps-which: add a --dump option to list all examined packages
- tps-which.1: update manpage for new features
- get-packages: fix overzealous channel-matching bug
* Tue Jun  7 2011 John W. Lockhart <lockhart@redhat.com> 2.36-14
- tps-lib.pl: fix broken behavior when stream==0.
* Mon May 23 2011 John W. Lockhart <lockhart@redhat.com> 2.36-13
- tps-channel-cache: fix for syntax error
* Mon May 23 2011 John W. Lockhart <lockhart@redhat.com> 2.36-12
- tps-make-lists: files-master.xml generation: fix xml, and for each
  rpm, add errata number as well as provides/requires and
  obsoletes/conflicts info.
- tps.spec: add perl-XML-Parse dep
- tps-channel-cache: try to deal with yum issues when listing channels
- tps-lib.pl: try to deal with yum issues when listing channels
* Mon May 16 2011 John W. Lockhart <lockhart@redhat.com> 2.36-11
- tps-lib: allow weedOut86 to resolve i386/i686 on x86_64-multilib errata.
- tps-upgrade: use only uninstalled new packages for the upgrade.
- tps-filter-filelist: move a function to tps-lib for re-use.
- tps-filter-filelist: add options to print basename or rpm-queried
  name of each package.  Update corresponding manpage.
* Thu Apr 14 2011 John W. Lockhart <lockhart@redhat.com> 2.36-10
- tps-make-lists: fix -x option
* Thu Apr 14 2011 John W. Lockhart <lockhart@redhat.com> 2.36-9
- get-packages: new program, replaces get_packages and
  get_released_packages (BZ 644051).
- tps-ff: new program for finding local copies of released rpms.
- tps-lib: absorb some functions from tps-make-lists
- tps-filter-filelist: add new --installed and --uninstalled options
- tps-make-lists: add -x feature to exclude dependent errata, and change -p behavior
  to limit further discovery of dependent errata.
- tps-channel-cache: unless TPS_ALLOW_LOCAL_REPOS is true, disable local/beaker
  repos before generating cache, and leave them disabled.
- Remember to update the changelog this time.
* Wed Apr  6 2011 John W. Lockhart <lockhart@redhat.com> 2.36-7
- tps-make-lists: do not consider the srpms of dependent errata
  when determining whether an upgrade is needed before srpm rebuilds.
* Tue Apr  5 2011 John W. Lockhart <lockhart@redhat.com> 2.36-6beta03
- tps-make-lists: consider dep-errata when determining whether to do an
  upgrade before tps-srpmtest tries to build.
- manpages: document --no-dep-errata where newly available.
* Fri Apr  1 2011 John W. Lockhart <lockhart@redhat.com> 2.36-6beta02
- tps-rpmtest: work on bz 669735: do not attempt to install
  nonexistent old files before test starts
* Fri Apr  1 2011 John W. Lockhart <lockhart@redhat.com> 2.36-6beta01
- Change to most programs: dependent errata filelists are now separate.
  (tps, tps-lib, tps-rpmtest, tps-srpmtest, tps-rhnqa, tps-which,
  tps-upgrade, tps-filter-filelist, tps-make-lists)
- Fix BZ 679090: do not duplicate tps-make-lists output.
- Fix BZ 680749: only attempt to rebuild primary errata files.
- tps-lib: fix primary marker for new file lists; add functionality
  for use by tps-install
- Fix BZ 690441: tps-rhnqa: use appropriate -debuginfo files
  in rhel6 for Binary Pkg Completeness
- tps-make-lists: explicitly announce when dependent errata files
  are being included.
- tps-lib: add instPkgToNVR routine to query an installed package
- Fix BZ 684179: tps-lib does not use oats STREAMEXT.
- srpm-special-cases: for BZ 669431, make the include test pass
  when src omitted
- Fix BZ 683592: tps-srpmtest: matching issues with missing srpm_name
* Wed Feb 16 2011 John W. Lockhart <lockhart@redhat.com> 2.36-5
- tps-make-lists: remove a seemingly innocuous extra slash in a
  URL that was causing unexpected problems for the Errata Tool.
- tps-srpmtest: grep the build log with the '-a' option to work
  around broken packages that spew binary streams into the
  build output (BZ 677679).
* Thu Feb 10 2011 John W. Lockhart <lockhart@redhat.com> 2.36-4
- tps-srpmtest: fix problem where --target=noarch could be used
  in a rebuild; now omits --target for the noarch case.
- srpm-special-cases: add exceptions for RHEV SRPMs for
  RHEL5 per BZ 669431
- tps-downgrade: fix BZ 674644, now returns non-zero on failure.
- tps-make-lists: Use errata-admin rather than errata-maint;
  re-word Newly Released tips/text; rename Processing; use ET
  depending_errata_for interface.
- tps-make-lists: do not set trueArch; it should always be the
  true cpu architecture from uname.
- tps-srpmtest: fix BZ 673280: ensure that /usr/src/redhat is used
  on all RHELs.  This should ensure garbage collection of successful builds.
- tps-lib, rhnqa-lib: move weedOutDebug to tps-lib for more general use
- tps-lib: add library functions for creating a detailed NVR
  string for use with yum.
- tps.spec: update license to indicate that TPS is intended for
  internal Red Hat use only.
* Tue Jan 11 2011 John W. Lockhart <lockhart@redhat.com> 2.36-3
- Official non-beta release; no code changes from beta.
* Fri Dec 17 2010 John W. Lockhart <lockhart@redhat.com> 2.36-2beta01
- tps-rpmtest: use system installer to install pkgnames-old files
  from RHNLive if the test begins with condition 'none' with no stray
  packages.  (E.g., assume that the system was improperly provisioned.)
- tps-srpmtest: No longer fail when a package without source is
  not rebuildable, if the missing source was intentional.  BZ 509512.
- shlib-special-cases: exceptions for dmraid (bz 515826) and
  ipvsadm (bz 663093).
- tps-make-lists, tps-rhnqa: improve messages and error reporting.
* Fri Nov 12 2010 John W. Lockhart <lockhart@redhat.com> 2.36-1
- tps-rhnqa: use x86-weeding routine to prevent problems with
  same-family multilib.  E.g., i686 and i386 are provided, but only
  one can be installed.
- Promote beta to production.
* Fri Nov  5 2010 John W. Lockhart <lockhart@redhat.com> 2.35-5beta02
- tps-rhnqa: correct the variable names used for the filtered file
  lists.  This was causing empty old-files lists and subsequent
  problems on RHEL6.
* Wed Nov  3 2010 John W. Lockhart <lockhart@redhat.com> 2.35-5beta01
- tps-lib: Deal with rhel6 -debuginfo issues, BZ 645310
  and BZ 446193; squash non-C locales on library init;
  fix error messages on log-file open failures
- glibc.pl: Rewritten, addresses BZ 648971.
- tps-downgrade: handle rhel6 -debuginfo (BZ 645310)
- tps-upgrade: handle rhel6 -debuginfo (BZ 645310)
- tps-srpmtest: fix BZ 648875; now uses native arch as
  basis for multilib decisions
- tps-srpmtest: fix ppc64 issues under RHEL6, BZ 647802
- tps-srpmtest: use rpmrc files under RHEL6, too.
- tps-filter-filelist: new program to make filelist filtering
  available to other scripts, needed for RHEL6 -debuginfo (BZ 645310)
- tps-rpmtest: handle rhel6 -debuginfo (BZ 645310)
- tps-rhnqa: handle rhel6 -debuginfo (BZ 645310)
- tps-make-lists: handle rhel6 -debuginfo (BZ 645310)
- tps-rhts: fix rhts tools install path (ohudlick)
- tps-report: fix BZ 576683, should no longer link to nonexistent files.
- shlib-special-cases: fix BZ 646794: add exceptions for util-linux
* Thu Oct 21 2010 John W. Lockhart <lockhart@redhat.com> 2.35-4
- tps-lib: ensure that tpsd.conf is always read when the library is initialized.
- tps-lib: unset G_SLICE for RHEL6-GA to avoid python/rhn issues.
- rhn-lib, tps-setup-channel-cache: when doing clean all, invoke yum without
  plugins to avoid messages if the cache directory has already been removed.
* Fri Oct 15 2010 John W. Lockhart <lockhart@redhat.com> 2.35-3
- tps, tps-make-lists, tps-rhnqa: fix regexp for pulling errata number
  from directory name.  Thanks to rbiba for the catch.
- tps: dump all global variables on request.  Force reading of tpsd.conf
  to pick up variables on manual runs.
- tps-lib: grow a Rhel6Live setting akin to the old Rhel5Live one.
- tps-lib: use ppc64 rather than ppc for RHEL >= 6.
- tps-devel: add tps-channel-cache for use by tps-make-lists when
  it wants to check a system's subscriptions.
- tpsd.conf: add RHEL6LIVE variable
* Wed Oct  6 2010 John W. Lockhart <lockhart@redhat.com> 2.35-2
- tps-vercmp.pl: fix bug where version 0.x and 0.y were miscompared due to
  the leading zero.
* Wed Sep 29 2010 John W. Lockhart <lockhart@redhat.com> 2.35-1beta3
- tps-srpmtest, tps-markup, tps-rhnqa: fix bad array size calculation (perl 5.10 change)
- tps-lib.pl: fix bad perl-version comparison (perl 5.10 change)
* Wed Sep 29 2010 John W. Lockhart <lockhart@redhat.com> 2.35-1beta1
- Updates to support RHEL6 changes, BZ 638655
- tps-setup-channel-cache: deal with different yum cache in RHEL6
- tps-make-lists.pl: exit informatively from infinite look when channel
  cache regeneration fails repeatedly.
- tps-rhnqa: teach it about a bunch of new signing keys
- Fix BZ 633254 - RFE: SharedLibTest exception for udisks
* Fri Sep 10 2010 John W. Lockhart <lockhart@redhat.com> 2.34-3
- BZ 632789: update tps, tps-make-lists to allow errata numbers
  greater than 9999.
* Tue Aug 17 2010 John W. Lockhart <lockhart@redhat.com> 2.34-2
- tps-setup-channel-cache: pay attention to yum cachefiles with odd
  names, such as a leading collection of hexadecimal digits.  BZ 624803.
- tps-make-lists, BZ 624807: allow alternative -debuginfo packages to be used
  regardless of the RHN channel check, since they do not appear on RHN.
  Also, trim find_package output to avoid generating blank lines.
* Thu Jul 22 2010 John W. Lockhart <lockhart@redhat.com> 2.34-1
- tps-setup-cache: read TPS_ALLOW_LOCAL_REPOS in case anyone (like RHTS)
  might want to use local repos.  Revise manpage to mention this feature.
- tpsd.conf: add ERRATA_DEV_XMLRPC to aid in testing xmlrpc fixes for the ET;
  also add TPS_ALLOW_LOCAL_REPOS.
- tps-rhnqa: fix for errata with multiple destination channels.
- tps-vercmp.pl: new file: perl version of rpm-vercmp
- tps-check-channels: new options: show only specified channels;
  show only newest available E:NVR.
- tps-check-channels.1: update manpage to cover new features.
- tps-make-lists: turn off signature-related warnings when checking
  unsigned packages
- tps-setup-channel-cache: ensure caches are cleaner
- tps-lib.pl: better error reporting for problems with RHN destination
  channel discovery.
- tps-channel-cache: regenerate tps-setup-channel-cache info
  if the subscriptions differ.  Also ensure that errata.stage is
  properly recognized.
- tps-make-lists: change ET interface used for get-released-package
  to get-released-channel-packages.  Fix for BZ 616030, should now
  be able to use unsigned packages in certain conditions.
* Tue Jul 13 2010 John W. Lockhart <lockhart@redhat.com> 2.33-11
- tps-make-lists: fix BZ 614208, now correctly adds obsoleted files
  to the old-files list.
* Thu Jun 24 2010 John W. Lockhart <lockhart@redhat.com> 2.33-10
- tps-make-lists: Changes for ET BZ 573113 to handle cases with multiple
  RHN Dest Channels.
- Add srpm exception for BZ 605270, java-ibm-sap.
- tps-make-lists: fix bz 594036: bad regex when package name
  contains special characters
* Thu May 13 2010 John W. Lockhart <lockhart@redhat.com> 2.33-9
- tps-make-lists: automate handling of dependent errata.
- tps-make-lists.1: update manpage to cover dep-errata feature.
* Thu Apr 15 2010 John W. Lockhart <lockhart@redhat.com> 2.33-8
- update-tps: use rpm-vercmp to determine if nfs-tps is newer
  than installed one.
- tps.spec: include update-tps in tps-devel, since it can be
  used outside of automation.
- tps-rhnqa: use 'RHNQA Server' rather than 'RHN.Stage', and
  mention the actual server name where it is helpful.
* Mon Apr 12 2010 John W. Lockhart <lockhart@redhat.com> 2.33-7
- Erratify: also recognize boston.devel network (bz 578270).
- release_helper: ensure systems use rhn.errata.stage for rhnqa.
* Wed Mar 17 2010 John W. Lockhart <lockhart@redhat.com> 2.33-6
- update-tps: if needed, execute helper script once on tspd startup.
- tps.spec: remove tps-update-info upon installation.
* Wed Mar 17 2010 John W. Lockhart <lockhart@redhat.com> 2.33-5
- update-tps: allow the use of version-specific helper scripts
  to aid in provisioning/configuring stable systems and Oats.
* Mon Mar 15 2010 John W. Lockhart <lockhart@redhat.com> 2.33-4
- tps-check-channels: rewrite to add more search features
- tps-check-channels.1: revise to document new features
- tps-make-lists: fix BZ 571838 by using new tps-check-channels
  features.
* Fri Mar  5 2010 John W. Lockhart <lockhart@redhat.com> 2.33-3
- tps-make-lists: fix BZ 570980, dups not being discarded.
* Fri Mar  5 2010 John W. Lockhart <lockhart@redhat.com> 2.33-2
- tps-make-libs: adjust Obsoletes code to avoid packages which
  are already on the old/new lists.
- Erratify: update for new /mnt/redhat for machines in .bos
* Tue Mar  2 2010 John W. Lockhart <lockhart@redhat.com> 2.33-1
- tps-lib, tps-yum-show-channels: make it possible to list
  currently disabled local repos to ensure that they are not
  accidentally used in any operations where specifying the repo
  would enable it.  This corrects a problem with tps-setup-channels.
* Fri Feb 19 2010 John W. Lockhart <lockhart@redhat.com> 2.32-10.beta
- tps-nav-markup: add tab for tps-make-lists results
* Fri Feb 19 2010 John W. Lockhart <lockhart@redhat.com> 2.32-9.beta
- tps-make-lists: additional fixes for Obsoletes and exit code.
* Thu Feb 18 2010 John W. Lockhart <lockhart@redhat.com> 2.32-8.beta
- Fix for BZ 562105, make the obs-lists more like the ones from
  prior releases of TPS.
- tps-rhnqa.1: update to reflect current realities, and to
  clarify some language, as spotted by kzhang on IRC.
* Tue Feb  9 2010 John W. Lockhart <lockhart@redhat.com> 2.32-7.beta
- tps-lib: additional fixes for BZ 200711, gripe about extra output on
  downgrade, delete, and install tests for tps-rpmtest.
- tps-setup-channel-cache: do not cache local repos by default.
- tps-setup-channel-cache manpage: document new option to allow
  caching of local repos, and explain why one should not use it
  in most cases.
- tps-channel-cache: improve help text
* Tue Feb  9 2010 John W. Lockhart <lockhart@redhat.com> 2.32-6.beta
- tps-lib: fix for BZ 200711, gripe about extra output on upgrades
- tps-make-lists: fix regexp for packages containing special chars.
- tps-make-lists: fix messages to better indicate the package and
  channel counts, since some counts come from get_channel_packages.
* Thu Feb  4 2010 John W. Lockhart <lockhart@redhat.com> 2.32-5.beta
- tps-make-lists: completely rewritten in perl, manpage updated.
  Note that neither get_packages nor get_released_packages is
  used any more; for now, they are still included for comparison
  purposes.
- tpsd: regenerate channel caches for live and qa on startup, or
  whenever /tmp/tps-generate-channel-cache.txt exists.  This
  is done by tps-setup-channel-cache.
- tps-channel-cache: recognize .bos.redhat, not just lab.bos.redhat.
- srpmtest special cases: fix for acroread
- tps-lib: support for tps-make-lists features, including
  url-fetching, initialization arguments, RHN channel determination.
- tps-rhnqa: updates to fix errata number recognition in odd cases
- rhnqa-lib: provide more info on re-runs of yum
- Makefile: use tps-make-lists.pl rather than the bash version.
  The bash version is still available in CVS for testing comparisons.
- This entry also itemizes changes since beta 3.
* Mon Jan 11 2010 John W. Lockhart <lockhart@redhat.com> 2.32-4.beta
- Pile of fixes, quick build for rbiba.  More detailed changelog to come.
* Mon Dec  7 2009 John W. Lockhart <lockhart@redhat.com> 2.32-3.beta
- tps, tps-lib, tps-make-lists: better base channel support for Z-stream,
  c.f. bz 545155.
- tps-setup-channel-cache: new program, with manpage.
- tps-rhnqa: fix bz 544210: test fails if rhn destination channel is empty
* Wed Dec  2 2009 John W. Lockhart <lockhart@redhat.com> 2.32-2.beta
- tps, tps-lib: add method to figure out proper RELEASE value for
  feeding to the Errata Tool and set rhnDestChannel as appropriate.
  Also add method to query any global variable from tps via new -g
  argument.
- tps-rhnqa: Fix BZ 511353 by detecting and reporting inadequate RHNQA
  channel subscriptions
- tps-show-channels: BZ 446649: new script to invoke the correct tool
  to show current subscribed channels
- tps-make-lists: bugfixes for identifying z-stream base channels
- tps-make-lists: use channel caches, if available, to determine
  whether an empty old-files list is correct, or just missing data
  from get_released_packages.
- tps-rhnqa, tps-lib: Improve error messages for the times when
  RHN.Stage serves up stale data
- tps-make-lists: fix bz 532651: extra backslash
- tps-parse-up2date-chan, tps-parse-yum-chan: new scripts to parse
  cached channel data from an RHN server.
- tps-check-channels: new script to see if a given package name exists
  in TPS's copy of the cached filelist from an RHN channel.
- manpage updates: tps, tps-show-channels, tps-check-channels,
  tps-parse-up2date-chan, tps-parse-yum-chan
- Makefile, .spec file: add new scripts and manpages, and describe
  the large pile of changes since the last release.
* Mon Nov 30 2009 John W. Lockhart <lockhart@redhat.com> 2.32-1.beta
- Many changes, initial test version.
* Tue Sep 29 2009 John W. Lockhart <lockhart@redhat.com> 2.31-19
- tps-waive: fix BZ 526186
* Thu Sep 24 2009 John W. Lockhart <lockhart@redhat.com> 2.31-18
- tps-make-lists: search for additional values of Release that
  may be what the Errata Tool expects.
- tps-waive, tps-waive.1: add -x option to invoke tps-report
  with the default waiver text, and document same. BZ 442211.
* Mon Aug 31 2009 John W. Lockhart <lockhart@redhat.com> 2.31-17
- update the special-cases files (BZ 519213 515826)
- tps-srpmtest: bz 513187: only use diff.py if it works
- tps-query: bz 513151: respect the TPSQUERY_URL setting in tpsd.conf.
- tps-report: add preliminary support for .nay /mnt/qa server
- tps-make-lists: add workaround for 5Server-VT
- tps-lib: bugfix: athlon is now considered part of the x86 family
- tpsd.conf: update TPSQUERY urls and add TPS_MNTQA for future use.
- tps-rhnqa, rhnqa-lib: minor formatting tweaks on tips.
* Thu Jul  2 2009 John W. Lockhart <lockhart@redhat.com> 2.31-16
- tps-make-lists: use TPSQ_RELEASE if the errata tool provides a value that
  differs from the locally determined value of RELEASE.
* Wed Jul  1 2009 John W. Lockhart <lockhart@redhat.com> 2.31-15
- tps-lib: teach DeleteTest and DowngradeTest to remove only installed pkgs.
- tps-lib: avoid matching rpm names that contain 'error' or 'fail', and
  tell the user if such a match might have occurred despite the avoidance.
* Tue Jun 23 2009 John W. Lockhart <lockhart@redhat.com> 2.31-14
- tps-srpmtest: specdiff: also provide graphical diff if diff.py is present.
- tps-srpmtest: specdiff: catch rpm2cpio errors if specfile unpacking fails.
- tps-srpmtest: fix BZ 482742: add test to ensure that matching SRPMs are shipped
- tps-srpmtest: fix BZ 492168: handle missing SRPMs in a more friendly fashion
- tps-srpmtest: fix rebuildTest's Untested result, formerly treated as a fail.
- tps-srpmtest: add 3 new tests: source inclusion, source exclusion, source relevance.
- tps-srpmtest.1: update manpage to cover the new tests and graphical diff.
- fix BZ 468444: RFE: Better handling for new packages
- tps-lib, tps-srpmtest, tps-rhnqa: alter cache files and package queries
  to include Epoch and SourceRPM names to support further srpm tests.
- spec: fix BZ 504859: add tps-report and its manpage to the tps-devel package.
* Fri May 29 2009 John W. Lockhart <lockhart@redhat.com> 2.31-12
- shlib-special-cases.txt: Correct a typo to re-fix BZ 489367: grub and ia32el exceptions.
- tps-lib.pl: correct a reference to produce correct warnings.
- tps-diff-sources: add the ability to pass your favorite options to diff.
- tpsd: prevent random incorrect invocations such as 'tpsd status'
- tps-make-lists: correct the name of RHTS variable to JOBID.
* Thu May  7 2009 John W. Lockhart <lockhart@redhat.com> 2.31-11
- Updated to handle new tps.txt and to provide RHTS recipe/job IDs if applicable:
  tps-query, tpsd, tps-make-lists; manpages for tps-query, tps-report
- tps.spec: remove cached query and channel info when updating tps-polling.
- tpsd.conf: include URLs for development and production TPS server.
- tps-lib.pl: fix trivial formatting issue in SharedLibTest.
* Thu Apr 30 2009 John W. Lockhart <lockhart@redhat.com> 2.31-10
- tps-lib.pl: fix BZ 497993, bad arch due to 'relocatable' not being examined
  like 'executable' in the output from the file command.
- tps-lib.pl: die gracefully if the old/new file lists are missing, and fix
  some of the fatal-error-handling code in the process.
- shlib-special-cases.txt: Update to fix BZ 489367, grub and ia32el exceptions.
- tps-make-lists: look for GRP_ERROR: exception from Errata Tool's
  get_released_packages implementation.  See also BZ 498114.
- get_released_packages: handle GRP_ERROR by exiting with rc 1, but
  still passing the message through on stdout.
* Tue Apr 21 2009 John W. Lockhart <lockhart@redhat.com> 2.31-9
- tps-query: hotfix for issues fetching tps.txt
- rhnqa-lib,tps-yumdownloader,tps-nav-markup: update soc-request to IS-Ops.
* Tue Mar 31 2009 John W. Lockhart <lockhart@redhat.com> 2.31-8
- Erratify: update for engarchive server change.
- tps-diff-sources: add current copy to get wider testing, address
  BZ 179161.
* Fri Mar  6 2009 John W. Lockhart <lockhart@redhat.com> 2.31-7
- tps-get-dist-from-spec: fix bz 488044; also use the rpmbuild
  parser to get Release info if the usual method fails, or if
  requested; add options to suppress rpm signature warnings;
  document environment variables in the help output.
- tps-lib: Add TpsTip for SpecialCase tags.
- tps-srpmtest: suppress rpm sig warnings from tps-get-dist
  in RHELs that support rpm's nosignature option.
* Tue Mar  3 2009 John W. Lockhart <lockhart@redhat.com> 2.31-6
- tps-lib: Fix BZ 488313.  Error and warning messages are now one
  per line and separated if a single file has multiple failures
  in the SharedLibTest.
- tps-lib: Fix BZ 488315.  Multilib files were not being properly
  detected due to a badly initialized hash, now fixed.
* Tue Feb 24 2009 John W. Lockhart <lockhart@redhat.com> 2.31-5
- tps-lib: fix debuginfo detection for i386 packages on ia64,
  add fallback to detect by rpm name in case path varies further.
* Mon Feb 23 2009 John W. Lockhart <lockhart@redhat.com> 2.31-4
- tps-lib: fix and tweak CPU-detection code: handle s390x correctly,
  provide more info about non-RHEL CPUs, change ERROR to UNKNOWN for
  instances where detection cannot work at all.
- tps-markup: Add newline to Html output before each TPSTIP to
  improve legibility.
* Fri Feb 20 2009 John W. Lockhart <lockhart@redhat.com> 2.31-3
- tps-get-dist-from-spec: fix BZ 486562 by parsing a bit more
  carefully, escaping backticks, and escaping rpm shell-escapes
  as well.  Thanks to jhutar for the patch suggestion.
- Drop shlibtest testing script.  It will return, see BZ 486666.
* Wed Feb 18 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta08
- tps-lib: fix serious issue with debuginfo files causing ldd
  to exit prematurely.  Debuginfo files are now checked last, and
  a Failure message is issued if all the regular binaries are not okay
  with ldd.
* Wed Feb 18 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta07
- tps-summarize: point users at html files; also, mention RHN errors
  directly in the summary if they occur in tps-rhnqa runs.
- tps-lib: add generic special case handler
- shlibtest: use special case handler; relies on
  newly added shlib-special-cases.txt file.
- shlib-special-cases: add handling for Xorg/XFree, RealPlayer, and
  debug files.
- tps-lib: add a crucial newline to separate the ldd error reports.
- tps-lib: improve TpsTip error messages.
- tps-nav-markup: add new TPS Help portal to footer.  Turn
  Tickets into a single instance in the footer.
- tps-rpmtest.1: mention the tests that are run.
- tps-rpmtest.1: document the special-cases file.
- tps-cd: Add suggested "tps-cd -c" help text as per BZ 467019
- shlibtest-tps: temporarily add to this beta for testing convenience.
* Mon Feb  9 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta06
- tps-report: alter URL so that the directory contents are sorted by
  date, or direct link to tps-rhnqa.html for rhnqa results.  BZ 484351.
- tps-lib: shlibtest: work around ldd BZ 484809 and fix multilib
  bug, BZ 484480.
- tps-lib: improve TPSTIP info for shlibtest.
- tps-rpmtest, tps-srpmtest: call tps-markup upon completion.
- tps-query: fix BZ 484467, logfile noise when job queue is empty.
- tps-query: add timestamp when reporting errors to tpsd logfile.
* Wed Feb  4 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta05
- tps-lib: Fix BZ 484123, SharedLibTest noise due to not using LD_LIBRARY_PATH
- tps-lib: Fix BZ 484124, SharedLibTest command-line length problem
* Tue Feb  3 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta04
- tps: Fix BZ 483800 so that all tps-make-lists warnings are captured.
- tps-markup, markup-tps: Change color of Passing cases that contain warnings
  from Green to Orange to provide a visual clue to investigate.
- shell scripts: use basename instead of full script path (rbiba)
* Fri Jan 30 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta03
- tps-lib: Work around RHEL5.3 ia64/ia32emul SELinux BZ 474152.
- tps-lib: Avoid putting rpm manifest into log files for SharedLibTest.
- tps-lib: Add TPSTips explaining the new failures for SharedLibTest.
- rpm-vercmp: add rpmdev-vercmp script from rpmdevtools (BZ 466950)
* Thu Jan 29 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta02
- tps-lib: debug SharedLibTest, should work better now.
* Thu Jan 29 2009 John W. Lockhart <lockhart@redhat.com> 2.30-9beta01
- tps-rpmtest: introduce SharedLibTest
- tps-rhnqa: handle kernels by not failing when Mixed is encountered post-update.
- Blacklisted-package failure was not linked in html logs (BZ 480683)
- new manpages: tps-cd, tps-downgrade, tps-rhts, tps-upgrade, tps-which. (jhutar)
- rhnqa-lib: attempt to work around rhn repomd.xml issues again.
- tps-nav-markup: fix browser-cache issue reported by cmeadors
- get_packages: ensure that the full package list can be retrieved.
- tps-waive.1: document new delay feature (rbiba) (BZ 446194)
- tps-markup.1: fix cut'n'paste error.
* Mon Nov  3 2008 John W. Lockhart <lockhart@redhat.com> 2.30-8
- tps-nav-markup: fix anchor links so that RawLinks work again in tps.html
- rhnqa-lib: only give archlist option to versions of yumdownloader that support it.
- tps-markup: improve error message if parsing errors occur.
* Thu Oct 30 2008 John W. Lockhart <lockhart@redhat.com> 2.30-7
- rhnqa-lib: add additional rhn.stage workarounds and messages
- tps-waive: add delay feature (rbiba) (BZ 446194)
- rhnqa-lib: ensure that system yumdownloader skips local repos
- tps-lib, tps-rhnqa, rhnqa-lib: system yumdownloader no longer grabs all
  arches, so make sure tps tells it to.
* Wed Oct 22 2008 John W. Lockhart <lockhart@redhat.com> 2.30-6
- tps-lib: fix selinux_ok variable for use by non-selinux boxes.
* Tue Oct 21 2008 John W. Lockhart <lockhart@redhat.com> 2.30-5
- tps.spec: update package requirements so that perl-DateManip is included
  for each subpackage.  (BZ 467382)
- tps-lib, tps-which, tps-markup: fix filehandle-duplication call that
  is too modern for the ancient perl shipped on RHEL2.1. (BZ 467926)
- Add SHELL variable to tpsd to help with certain packages (BZ 467977)
* Thu Oct  9 2008 John W. Lockhart <lockhart@redhat.com> 2.30-4
- update-tps: another bugfix, a safeguard, and another chance to test it.
* Thu Oct  9 2008 John W. Lockhart <lockhart@redhat.com> 2.30-3
- update-tps: make friendlier for tps-devel users
- update-tps.1: new manpage
- tps-markup.1: new manpage
- tps-cache-pkgs.1: fix up wording
* Thu Oct  9 2008 John W. Lockhart <lockhart@redhat.com> 2.30-2beta02
- update-tps: bugfixes, support manual update as well.
* Wed Oct  8 2008 John W. Lockhart <lockhart@redhat.com> 2.30-2beta01
- tps-nav-markup, tps-markup: fix subtest markers, generate more valid html, fix
  BZ 465024 (overlapping text), set document type.  Requires updated CSS file.
- tps-which: re-fix BZ 461891; original patch missed one line.
- update-tps: add program to update tps itself from tpsd
- tpsd: modify to call update-tps
- tps-make-lists: use LANG and LC_COLLATE to force consistency between
  manual and automated runs.
* Tue Sep 30 2008 John W. Lockhart <lockhart@redhat.com> 2.30-1
- tps-nav-markup: add a TopOfPage link; fix folding of non-test
  sections; remove boldface on links; add space between last item and
  footer to help keep important text from being obscurred.  Matching
  changes in markup-tps.css also released.
* Mon Sep 29 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta22
- rhnqa-lib: revert yum update/install change, since install didn't always
  know when to update instead.  Future changes will attempt to work around
  yum's defective inability to do an rpm -Uvh.
- rhnqa-lib: use the system yumdownloader, if available.  Seems that RHEL5.2
  or 5.3 has broken tps-yumdownloader.
- tps-lib: add routine for properly marked up fatal msg handling
- tps-rhnqa: handle fatal error msgs plus markup better
- tps-nav-markup: tidy up, make more compliant with html spec.
- tps-lib: redirect "which" stderr output to /dev/null, as it is not used.
* Sun Sep 28 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta21
- tps-markup: add/revise navigation, needs matching markup-tps.css
- tps-nav-markup.pl: new module to handle gobs of html
- add kernel-rt to blacklist per jneedle on irc
- tps-srpmtest: fix bz 464306, endTest was not called in 2 new
  error conditions.
* Mon Sep 22 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta20
- tps-lib: add absolute test numbers, add TPSRAWLINK
- tps-markup: rewrite, add support for anchors
- tps: use TPSRAWLINK, mark tests, clean up output
- tps-srpmtest: typo/message fixing, turn on SubTest calls
- tpsd service: handle stale lockfiles better
* Wed Sep 17 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta19
- tps-markup: add navigation, reduce whitespace between lines
- tps-markup: make first 'info' section foldable.
- tps-markup: hide passing cases by default.
- rhnqa-lib: use yum install rather than yum update, since the
  former is the equivalent of rpm -Uvh rather than the latter.
- tps-lib: add begin/endSubTest functionality
- tps-lib, tps, tps-srpmtest, tps-rpmtest, tps-rhnqa: use std intro text,
  lower priority of begin/end test timestamps
- tps-lib, tps-which: fix BZ 461891, duplicate package listing on stderr;
  also capitalize name of package set for usability
- tps-srpmtest: fix BZ 456209, check for rpm-build and redhat-rpm-config
- init-tpsd: fix BZ 456890 and BZ 457890: print success/failure when
  stopping tpsd, and only allow one tpsd to run at a time.  Also made
  the status command set the return code indicating status rather than
  the result of tailing the logfile.
- tps-lib: add message showing the version number of the .raw file format.
- tps-make-lists, tps-srpmtest: fix BZ 452161 by tracking build
  requirements provided by the new files in an erratum.
- tps-make-lists.1: update to mention the new files generated.
* Wed Sep 10 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta18
- tps-lib, tps-markup, tps-rhnqa: more markup/logging fixes.
* Wed Sep 10 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta17
- tps-lib: another fix for re-typing.
* Wed Sep 10 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta16
- tps-lib: fix problem with automatic re-type of numbered results.
* Wed Sep 10 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta15
- Address RFE BZ 461612: make tps-which less verbose
- Address RFE BZ 460592: skip srpm rebuild for certain stacks updates
- tpsd.conf: add SRPM_SKIP_CHANNELS variable for BZ 460592.
- tps-lib.pl: numerous logging changes/fixes
- tps: logging fixes
- tps-srpmtest: more logging fixes
- rpm.pl module: remove sudo commands (ohudlick)
- tps-markup: new, converts .raw files to .html
* Wed Aug 27 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta14
- tps-rhnqa: make downloadCheck test account for yum-source issues
- rhnqa-lib: make yum output more legible by trimming ETA messages
- tps-lib: downgrade the severity of InstalledState messages
* Tue Aug 26 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta13
- tps-rhnqa: fix bogus download-completion test result
* Tue Aug 26 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta12
- tps, tps-rhnqa, rhn-lib, tps-lib: additional reporting fixes
* Tue Aug 26 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta11
- tps: reporting fixes
- tps-srpmtest: reporting fixes
- tps-downgrade: turn off extra stderr output
* Tue Aug 26 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta10
- tps-downgrade: logging fixes
- tps-lib: chomp a newline, add sub-tests
- tps-srpmtest: logfile surgery, sub-tests, revisions to Rebuild, etc.
* Tue Aug 19 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta9
- tps-rhnqa: more logging
- tps-lib: set default testName
- rhnqa-lib: add '-r' to cleanup for var/cache/yum
* Tue Aug 19 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta8
- tps-rhnqa: logging updates
- tps-rhnqa: fix multilib yum install invocations to include arch
- tps-rhnqa: added DownloadCheck test to end confusion with SigVerify.
- tps-lib: add rhnSpoolDir to globals
- tps-lib: try to eliminate duplication of stderr msgs with manual tests.
* Sat Aug 16 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta7
- more selinux updates/tweaks
- tps-rhnqa: start changing logfile usage/commands
- tps-rhnqa: extra delete of /var/cache/yum/ contents
* Sat Aug 16 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta6
- tps-lib: selinux support turned on
- tps-check-stable: update for new logging
- tps-rpmtest: selinux, tweak logging
* Fri Aug 15 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta5
- tps-lib: more logging updates
- tps-which: updated for new logging
* Fri Aug 15 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta4
- tps-lib: quiet the package queries, tweak logging
- tps-rpmtest: use doLog, and close logfiles properly.
* Fri Aug 15 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta3
- tps-lib: more typeglob fixes
* Fri Aug 15 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta2
- tps, tps-lib: more logging changes, typeglob festivities, etc.
* Thu Aug 14 2008 John W. Lockhart <lockhart@redhat.com> 2.30-0beta1
- Re-work tps logging.  First step to see how well it serves.
* Thu Jul 31 2008 John W. Lockhart <lockhart@redhat.com> 2.24-7
- tps-cd: fix for bz 441144
* Wed Jul  2 2008 John W. Lockhart <lockhart@redhat.com> 2.24-6beta
- tps-make-lists: correct the 'missing file' check
- tps-cache-pkgs: update to latest, which falls back to HTTP if no NFS.
* Mon Jun 23 2008 John W. Lockhart <lockhart@redhat.com> 2.24-5beta
- tps-make-lists: turn off enforced defaults for stacks RELEXTRA.  This change
  could use additional testing, thus the 'beta' status.
- tps-make-lists: detect, discard, report any files missing from /mnt/redhat
- tps-make-lists: narrow scope of '-CS' for clusters RELEXTRA
- tps-lib.pl: make more verbose for bug 439370
- tps-channel-cache: fix BZ 446629, and also change 'rhn abuse' to a more
  generic 'rhn issue'.
- tps-rhnqa: add a tpshint for what to do when Mixed packages cannot be
  automagically fixed.
* Thu May 08 2008 John W. Lockhart <lockhart@redhat.com> 2.24-4
- tps-rhnqa: fatal error if there are no new packages to update to.
- tps-make-lists: fatal error if more than one redhat-release is installed.
- tps-report.1: add docs about checking tps.txt for job/run ID info.
- tps-lib.pl: improve message about stray packages, lose reference to beehive.
* Thu May 01 2008 John W. Lockhart <lockhart@redhat.com> 2.24-3
- tps-cd: add feature per bz 441145
- tps-channel-cache: update to handle .bos or .boston
- tps-rhts: update from .boston to .bos for qafiler.
- Erratify: another .boston/.bos update, now handles either.
* Tue Apr 08 2008 John W. Lockhart <lockhart@redhat.com> 2.24-2
- fix for bz 441438 - ppc/ppc64 native-compat arch confusion.
- fix for bz 441501 - do not run yum once per arch like up2date.
* Thu Apr 03 2008 John W. Lockhart <lockhart@redhat.com> 2.24-1
- tps-check-stable: fix bz 437330 by tossing rpm -qa info into the log;
  also fix auditd status info and ensure that yum repo filename is printed.
- tps-channel-cache: fix bz 440382 - bad regex for rhn.stage prevented
  auto-recovery from RHN Abuse.
* Wed Mar 19 2008 John W. Lockhart <lockhart@redhat.com> 2.23-10beta
- tps-yumdownloader: more exception handling fixes
- tps-rhnqa: report more info about bad signature keys
- tps-rhnqa: add skiplive switch for debugging errata that have shipped.
- tps-rhnqa.1: document skiplive in manpage.
- tps-check-stable: report the state of the RHN links/servers.
* Mon Mar 17 2008 John W. Lockhart <lockhart@redhat.com> 2.23-9beta
- tps-yumdownloader: fix reference to exception name.
* Mon Mar 17 2008 John W. Lockhart <lockhart@redhat.com> 2.23-8beta
- tps-yumdownloader: trap some exceptions and try to be useful,
  and report non-zero if nothing retrieved.
- rhnqa-lib: deal with yumdownloader issues
- tps-make-lists: do not use -DirServ except for RHEL4-AS.
- tps-lib: do not gather yum info unless RHEL revision is >=5.  BZ 434747.
- tps-check-stable: gather some additional yum and selinux info.
- tps-auto, tps-auto-rhnqa: invoke tps-check-stable to gather info before each run.
* Thu Feb 21 2008 John W. Lockhart <lockhart@redhat.com> 2.23-7
- tps-yum-show-channels: add --noplugin option to give a list of
  on-disk repos that should be disabled for rhnqa testing.
- tps-lib.pl: use tps-yum-show-channels rather than trying to
  sift through the yum repos directory.
- rhnqa-lib.pl: actually use the disablerepo options, and report same.
  Also use the correct global vars for YumPlugins settings.
* Tue Feb 12 2008 John W. Lockhart <lockhart@redhat.com> 2.23-5
- tps: fix missing semicolon.
* Tue Feb 12 2008 John W. Lockhart <lockhart@redhat.com> 2.23-4
- tpsd.conf and other files as appropriate: replace errata.devel with
  errata-xmlrpc.devel for all xmlrpc calls to the errata tool.
  Affected: tps-report, tps-channel-info, get_packages,
  get_released_packages.
- tps-cd: update for new stable machine naming scheme with -s option.
  Note that machines that do not follow the scheme will not be
  considered (same as old version).  (rbiba)
- tps, tps-make-lists: do not require an errata number if there
  is a working directory or .sh file from a prior run that can
  be used to determine the errata number automagically.
- tps.1, tps-make-lists.1: update to explain optional errata number.
- tps-rhnqa: print out tps version information in logs.
* Thu Jan 31 2008 John W. Lockhart <lockhart@redhat.com> 2.23-3
- tpsd: export TPS_AUTO more liberally to cut down on noise in the logs.
* Tue Jan 29 2008 John W. Lockhart <lockhart@redhat.com> 2.23-2beta
- tps-channel-cache: new program, checks rhn channels every 20 min
- tps-query: use channel cache; auto-filter channels if in stacks mode
  without TPS_LIMIT_CHANNELS_TO set.
- tps-query.1: update manpage to reflect new behavior.
- tps-status: fix 'Error getting requested information' msgs (rbiba)
- tpsd: refuse to run if tps-polling is launched on a 'dhcp' hostname
- tps: announce TPS rpm name and version in the results files.
- tpsd.conf: provided commented-out TPS_LIMIT_CHANNELS_TO section
  to make it easier to configure properly.
* Fri Jan 11 2008 John W. Lockhart <lockhart@redhat.com> 2.23-1
- tps-srpmtest: add new test to check dist usage in specfiles
- tps-query: fix BZ 428411, too many channels were being matched
- tps-rhnqa: print the actual serverUrls for rhn.live and rhn.qa.
- tps-waive: new program, see --help for usage (BZ 179197)
- tps-waive.1: new man page
- tps-report.1: add snippets about runID/jobID (lockhart, jhutar)
- tps-query: add info about input/output formats in --help.
- tps-rhts: disallow running in /mnt/testarea subdirs,
  missing WARN in possible test results; disallow running without
  arguments; performance testing - support multilple runs; improve
  script output (including quick results for every test).  (ohudlick, cward)
* Thu Dec 20 2007 John W. Lockhart <lockhart@redhat.com> 2.22-8
- tps-lib: fix the disablerepo settings for yum so only local repos are disabled.
- rhnqa-lib: fix typo, BZ 426360
* Mon Dec 17 2007 John W. Lockhart <lockhart@redhat.com> 2.22-7
- tps-rhnqa: fix global variable, which fixes BZ 426014.
* Mon Dec 17 2007 John W. Lockhart <lockhart@redhat.com> 2.22-6
- tps-get-dist-from-spec: handle 'Release' lines with multiple macros present (BZ 419731).
- tpsd: be more careful with cached data, retry failed reports, pause between jobs.
- tps-report: eliminate use of development system in debug mode.
- tps.1, tps-srpmtest.1, tps-rpmtest.1: revise manpages
- tps-make-lists.1, tps-rhnqa.1: revise manpages
- tps-query.1, tpsd.1: new manpages
- tps-report.1: new manpage (jhutar, lockhart)
* Tue Nov 27 2007 John W. Lockhart <lockhart@redhat.com> 2.22-5
- tps-query: fix bug that caused too many items to be classified as dupes.
* Tue Nov 27 2007 John W. Lockhart <lockhart@redhat.com> 2.22-4
- tps-query, tpsd: guard against job duplication when fetched tps.txt is stale.
- tpsd: export TPS_AUTO for tps-report to check.  tps-report is now verbose
  by default otherwise.
- tps-query: log all ignored jobs to /tmp/tps-query-dupes.txt when duplicates
  are detected.
- tps-cache-pkgs and manpage: new cachedir option (jhutar)
* Wed Nov 14 2007 John W. Lockhart <lockhart@redhat.com> 2.22-2
- tps-query: Add TPS_LIMIT_CHANNELS feature so that a system can be
  subscribed to RHEL, but only run (for instance) Stacks jobs.
- tps-get-dist-from-spec: new script to determine 'dist' value.
- tps-srpmtest: use whatever value of 'dist' matches the source rpm
  under test.  This should fix the '.elX_Y_random' false positives.
* Wed Nov  7 2007 John W. Lockhart <lockhart@redhat.com> 2.22-1
- tps-summarize-rhnqa: removed
- tps-summarize: now supports rhnqa, and missing srpmtest for RHGD.
- tps-query: Rewritten. Now uses static jobs list from the Errata Tool.  Also gives
  preference to RHSA jobs.  Now in Perl, no more buggy python-xmlrpc.
  Important: job selection is now done by subscribed RHN channels, so stable
  systems must be correctly subscribed in order to handle jobs.
- tpsd: exports new tps-query information, gives preference to RHNQA jobs
  since they ought to be faster.  Also exits if the hostname is not properly
  set; this should address BZ 366941, where the results could not easily be found.
- tps-auto, tps-auto-rhnqa: records time, query settings, and basic result from
  automated jobs.
- tps-rhnqa: Now refers to RHNLive and RHNQA throughout (jhutar)
* Wed Oct 17 2007 John W. Lockhart <lockhart@redhat.com> 2.21-10
- tps-cache-pkgs.1: New manpage (jhutar)
- tps-cache-pkgs: correct copying of pkgs (jhutar)
- tps-make-lists: fix for Stacks V2 on RHEL5 (lockhart)
- rhnqa-lib.pl: make sure yum commands are all logged (lockhart)
* Tue Sep 11 2007 John W. Lockhart <lockhart@redhat.com> 2.21-9
- tpsd.conf: fix bogus configuration file
* Tue Sep 11 2007 John W. Lockhart <lockhart@redhat.com> 2.21-8
- tps.spec: tweak tarball version format/number to suppress rpmdiff reports.
* Tue Sep 11 2007 John W. Lockhart <lockhart@redhat.com> 2.21-7
- tps-report: changes for ruby-ized ErrataTool 2.0
- tps-query: changes for ruby-ized ErrataTool 2.0
- tps-channel-info: changes for ruby-ized ErrataTool 2.0
- tpsd.conf: changes for ruby-ized ErrataTool 2.0
- tpsd, init.d/tpsd: LANG=C to work around bad locales
- get_package: changes for ruby-ized ErrataTool 2.0
- get_released_packages: changes for ruby-ized ErrataTool 2.0
- find_package: update for latest rel-eng compatibility
- tps-check-stable: new script
- tps-cache-pkgs: new script (jhutar)
- rpm.pl module: fix for proper /bin/cp usage (jhrozek)
* Thu Jul 26 2007 John W. Lockhart <lockhart@redhat.com> 2.21-6
- tps-make-lists: one more fix for clusters on RHEL5.
* Thu Jul 26 2007 John W. Lockhart <lockhart@redhat.com> 2.21-5
- tps: add -m option to skip creation of filelists
- tps: add date to tps.report
- tps-make-lists: handle cluster-storage-5 in a way palatable to
  the Errata Tool, revise code for easier special-casing.
* Wed Jul 11 2007 John W. Lockhart <lockhart@redhat.com> 2.21-4
- tps-auto: set HOME to /root if it was / or unset.
- tps-srpmtest: set HOME to /root if it was / or unset.
- Erratify: add to tps-devel
* Fri Jul 06 2007 John W. Lockhart <lockhart@redhat.com> 2.21-3
- tps-make-lists: better comment how GRP interfaces are used.
- tps-srpmtest: ensure that HOME=/root has been set up.
- tps-channel-info: fix bug #246714
* Fri Jun 22 2007 John W. Lockhart <lockhart@redhat.com> 2.21-2
- tps-lib.pl: revert some kernel.pl support in DeleteTest for now.
* Fri Jun 22 2007 John W. Lockhart <lockhart@redhat.com> 2.21-1
- tps-make-lists: fix routine that filters out unreadable files
* Wed Jun 06 2007 John W. Lockhart <lockhart@redhat.com> 2.20-1
- tps-report: use nest.test rather than hank.test.
- tps-rpmtest: handle stray packages better
- tps-lib.pl: more support for kernel.pl
* Tue Apr 03 2007 John W. Lockhart <lockhart@redhat.com> 2.19-1
- tps-srpmtest: work if ARCH has not been set
- tps-lib.pl: gather/set arch information.
* Fri Mar 30 2007 John W. Lockhart <lockhart@redhat.com> 2.18-1
- tps-rhnqa: check the proper result variable, be more verbose if error.
- tps-auto: define USER and HOME so that automated/manual results are identical.
* Thu Mar 29 2007 John W. Lockhart <lockhart@redhat.com> 2.17-1
- tps-rhnqa: protect against rhnswitch failures, allow for yum delays
- rhnqa-lib.pl: more rhnswitch-checking, also catch failure to download better.
* Wed Mar 28 2007 John W. Lockhart <lockhart@redhat.com> 2.16-1test
- tps-srpmtest: more workarounds for bug 203658
- tps-srpmtest: clean up environment-variable usage.
- tps-rhts: add to tps-devel (ohudlick)
- tps-rhts: cleanup, use cvs-id for version (lockhart)
- tps-make-lists: add error-checking on format of errata number
* Fri Mar 23 2007 John W. Lockhart <lockhart@redhat.com> 2.16-0test
- tps-rhnqa: yum locking adjustments
- rhnqa-lib.pl: collect more info, workaround rhel2.1 up2date issue
- tps-srpmtest: unset ARCH and other variables that we do not
  want to be passing around.
* Thu Mar 08 2007 John W. Lockhart <lockhart@redhat.com> 2.15-1
- tps-rhnqa: additional cleanup after switching from live to rhn.qa
- rhnqa-lib: clean up the up2date directory that tps-yumdownloader uses
* Thu Mar 08 2007 John W. Lockhart <lockhart@redhat.com> 2.14-1
- Fixes for RHEL5 issues
- Add tps-lib global hashref to everything that uses tps-lib
- tps-rhnqa: more yum-related fixes, also print start time/date of run.
- tps-rhnqa: enforce key signing policy from http://www.redhat.com/security/team/key/
- tps-make-lists: more unique sorting to handle possible dups on gp/grp returns
- tps-yumdownloader: new program, lifted from yum-utils and modified slightly.
- tps-yum-show-channels: new program to show full (not truncated) channel names
- sudo: only used if running as non-root user.
- tps-srpmtest: do not use sudo at all
- tpsd.conf: add to all packages since it controls g-r-p
- temporarily drop kernel.pl until fully tested
- rhnqa-lib.pl: new file for handling up2date/yum differences
* Wed Mar 07 2007 John W. Lockhart <lockhart@redhat.com> 2.12-1test
- tpsd.conf addition/changes: RHEL5LIVE variable
* Wed Mar 07 2007 John W. Lockhart <lockhart@redhat.com> 2.12-0test
- major changes for testing only
* Tue Jan 23 2007 John W. Lockhart <lockhart@redhat.com> 2.11-4
- tps.spec: add dkovalsk's kernel.pl module for kernel testing
- Add global tpsErrorText for error analysis between tests.
* Thu Dec 14 2006 John W. Lockhart <lockhart@redhat.com> 2.11-3
- tps-make-lists: use both rel-eng and errata tool get_released_packages
- tps-make-lists: new package-uniqueness code
- tps-make-lists: sort new-ALL uniquely
- bz 219642 should now be fixed.
* Thu Dec 14 2006 John W. Lockhart <lockhart@redhat.com> 2.11-2
- tps-query: also query for RHCS
- tps-rhnqa: weed out debuginfo from old-file*.list
- tps-lib: utility functions to support future features.
* Mon Dec 11 2006 John W. Lockhart <lockhart@redhat.com> 2.11-1
- tpsd.conf: use Errata Tools' get_released_packages interface
- tps-make-lists: avoid arch query on AS2.1
- tps-query: use correct name for RHCS queries
* Tue Nov 28 2006 John W. Lockhart <lockhart@redhat.com> 2.10-8
- tpsd.conf: fix erratatool urls for tps-gp and tps-channelinfo
- tps-make-lists: grow additional product awareness
* Thu Nov 16 2006 John W. Lockhart <lockhart@redhat.com> 2.10-7
- tps-query, tps-report, tps-channel-info: use configurable urls for xmlrpc
- get_released_packages, get_packages: ditto
- find_package: brew-related fixes
- tpsd.conf: add temporary zstream settings
- tps-make-lists: add more product awareness, should be better now with stacks.
* Mon Nov 06 2006 John W. Lockhart <lockhart@redhat.com> 2.10-6
- tps-report: fix return code
* Mon Nov 06 2006 John W. Lockhart <lockhart@redhat.com> 2.10-5
- tps-report: work around rhel2.1 python again
* Mon Nov 06 2006 John W. Lockhart <lockhart@redhat.com> 2.10-4
- tps-query: limit products to RHEL for 2.1AS
- tps-report: ensure that strings, no ints, are passed thru xmlrpc.
- add 'verbose' switch to both tps-query and tps-report.
* Thu Nov 02 2006 John W. Lockhart <lockhart@redhat.com> 2.10-3
- add tps-channel-info, update tps.1 to mention its existence.
- make sure the latest get_released_packages is included.
* Thu Nov 02 2006 John W. Lockhart <lockhart@redhat.com> 2.10-2
- tps-query: turn off some debugging output
* Wed Nov 01 2006 John W. Lockhart <lockhart@redhat.com> 2.10-1
- tpsd: refuse to run unless scratch and released dirs are present
- tps-query: add option handling code and product awareness, drop tps-query-rhnqa
- tps-report: add option handling code, drop tps-report-rhnqa.
- tpsd: use new tps-query and tps-report syntax.
- tps-cd: new features from dkovalsk, rbiba, and jwl.
* Tue Sep 26 2006 John W. Lockhart <lockhart@redhat.com> 2.9-8
- tps-upgrade: fix bz 208111 and 206647: send err to stderr, add -force.
* Tue Sep 26 2006 John W. Lockhart <lockhart@redhat.com> 2.9-7
- tps-lib.pl: ensure that arch is not used in rpm queries under RHEL2.1.
* Thu Sep 21 2006 John W. Lockhart <lockhart@redhat.com> 2.9-6
- tps-lib.pl: clean up and improve output for manual tps run
* Thu Sep 21 2006 John W. Lockhart <lockhart@redhat.com> 2.9-5
- tps-srpmtest: compress the build output from successful builds.
* Thu Sep 21 2006 John W. Lockhart <lockhart@redhat.com> 2.9-4
- tps: improve versioning information, BZ 207080
- tps-lib.pl: verbose output on determinePackageState, BZ 196457
- tps-which: BZ 196457 fixed by tps-lib.pl change above.
- tps-auto: add TPSAUTO variable so tools know if they are under automation.
- tps-auto-rhnqa: add TPSAUTO variable so tools know if they are under automation.
- spec: add a 'provides' tag to easily identify rpm version info
* Mon Sep 18 2006 John W. Lockhart <lockhart@redhat.com> 2.9-3
- tps-srpmtest: use comparison to the correct variable.
* Mon Sep 18 2006 John W. Lockhart <lockhart@redhat.com> 2.9-2
- tps-srpmtest: do not expect debuginfo if redhat/rpmrc omitted
- tps-srpmtest: use redhat/rpmrc if not ppc, or unless multilib
- pick up brew-aware get_released_packages (sanity2 tools)
* Fri Sep 01 2006 John W. Lockhart <lockhart@redhat.com> 2.9-1
- tps-rpmtest: overhaul VerifyTest to eliminate superfluous errors
- also add a few TPSINFO tags and newlines to highlight warnings/info.
* Wed Aug 09 2006 John W. Lockhart <lockhart@redhat.com> 2.8-1
- tps-srpmtest: use /tmp for rpmrc to avoid having a colon in the path.
* Thu Aug 03 2006 John W. Lockhart <lockhart@redhat.com> 2.8-0
- tps-srpmtest: #179196 - redirect build output to file, reduce RAM use.
- tps-srpmtest: #199508 - improve multilib rebuild reliability.
- tps-srpmtest: improve message log
- tps-blacklist.txt: change krb5 to krb5-libs, from rbiba.
- tps-lib.pl: add file redirection to doRpmCommand
- tps-lib.pl: include exit status in doRpmCommand log message
- tps-auto, tps-auto-rhnqa: #183182, #195619: ensure old packages present for rhnqa.
- tps-rhnqa: ensure that glibc-debuginfo-common is also treated as -debuginfo.
* Tue Jun 27 2006 John W. Lockhart <lockhart@redhat.com> 2.7-1
- specfile change so tps-polling obsoletes tps
* Tue Jun 27 2006 John W. Lockhart <lockhart@redhat.com> 2.7-0
- change package name to discourage rogue non-stable testing boxes
- tps-status: #194281 - display details of errata tested by tps - rbiba
- tps-make-lists: #193908 - new files showing up in old-files list.
* Tue May 23 2006 John W. Lockhart <lockhart@redhat.com> 2.6-5
- tps-cd: return 1 on error, use stderr for error msgs.  By rbiba.
* Mon May 22 2006 John W. Lockhart <lockhart@redhat.com> 2.6-4
- tps-report, tps-report-rhnqa: fix python error when reporting failed jobReport call.
* Fri May 19 2006 John W. Lockhart <lockhart@redhat.com> 2.6-3
- pick up perl,pam module fixes for return values from jlieskov
- tps-rhnqa: print the hostname when testing begins.
* Thu May 18 2006 John W. Lockhart <lockhart@redhat.com> 2.6-2
- Minor fixes and added information
* Thu Apr 27 2006 John W. Lockhart <lockhart@redhat.com> 2.6-1
- pick up rpm.pl changes for real this time.
* Thu Apr 27 2006 John W. Lockhart <lockhart@redhat.com> 2.6-0
- change porkchop to errata.devel throughout
- pick up new get_package and friends
- pick up rpm.pl changes
- tps-make-lists: ensure that no new files are added to old-files list
* Wed Apr 19 2006 John W. Lockhart <lockhart@redhat.com> 2.5-1
- Pick up new version of find_package
* Wed Apr 19 2006 John W. Lockhart <lockhart@redhat.com> 2.5-0
- Add new tps modules: pam and perl from jlieskov
- tps-make-lists: check output from get_released_packages for obvious errors
- tps: skip further tests if tps-make-lists fails
- tpsd: add kerberos bin and sbin directories to PATH
* Tue Apr 18 2006 John W. Lockhart <lockhart@redhat.com> 2.4-0
- Add new tps module: glibc from jhrozek
- Add new tps module: rpm from ohudlick
- tps-rhnqa: fix scoping bug involving rhnswitch
- Ensure that modules are present for -devel and -stacks, too.
* Thu Apr 13 2006 John W. Lockhart <lockhart@redhat.com> 2.3-0
- Add new tps modules: krb5-libs and bash from rbiba
- tps-rhnqa: changes for new rhnswitch from OATS.
* Mon Mar 27 2006 John W. Lockhart <lockhart@redhat.com> 2.2-1
- tps-make-lists: fix case where simple query fails, but what-provides query succeeds
* Thu Mar 23 2006 John W. Lockhart <lockhart@redhat.com> 2.2-0
- find_package: add to release
- tps-cd: fix installation so that it is source automagically
- tps-make-lists: gather info about obsoleted pkgs into the pkg lists
- tps-make-lists: gather info about build requirements
- tps-srpmtest: display missing build-req info and warn
- Thus if any installed pkg is obsoleted, it will be restored on downgrade.
* Mon Mar 06 2006 John W. Lockhart <lockhart@redhat.com> 2.1-5
- tps-make-lists: handle the -cluster product variant.
* Fri Mar 03 2006 John W. Lockhart <lockhart@redhat.com> 2.1-4
- turn off blacklist for stacks testing, since perl is included.
- add some convenience variables to tpsd.conf for debugging
* Fri Mar 03 2006 John W. Lockhart <lockhart@redhat.com> 2.1-3
- tps-report, tps-report-rhnqa: fix regexp to work with stacks-format names
* Fri Mar 03 2006 John W. Lockhart <lockhart@redhat.com> 2.1-2
- update specfile to clobber existing tpsd.conf so stacks-post works right.
* Fri Mar 03 2006 John W. Lockhart <lockhart@redhat.com> 2.1-1
- fix typo in tpsd.conf; thanks to dhm for spotting it.
* Fri Mar 03 2006 John W. Lockhart <lockhart@redhat.com> 2.1-0
- bump version
- tps-query, tps-query-rhnqa: correctly validate stacks return, add a default
* Thu Mar 02 2006 John W. Lockhart <lockhart@redhat.com> 2.0-5
- tps-cd: move to /etc/profile.d; also, provide in -devel.
- tpsd.conf: add to /etc for stacks support
- tpsd: update to use tpsd.conf
- tps-query, tps-report: stacks support; also timestamp error msgs (#179177).
- tps-query- and tps-report-rhnqa: as above: stacks and timestamps.
- specfile: general cleanup, especially of attr.
* Fri Feb 24 2006 John W. Lockhart <lockhart@redhat.com> 2.0-4
- tps: now print hostname in log and report files to help tps-auto users
- tps: bump release number
- tps-cd: add to rpm
- tps-status: add to rpm
- tps-rhnqa: show rhn channel subscription information and msg to check it.
- tps.1: update to mention helper utilities such as tps-cd (#178403)
- init.d/tpsd - quote the PID in case it is ever null. (#178950)
* Wed Jan 18 2006 John W. Lockhart <lockhart@redhat.com>
- init.d/tpsd - show currently running jobs for status command
- tps-srpmtest - escape package names when using them in a regular expression.
* Fri Dec 09 2005 John W. Lockhart <lockhart@redhat.com>
- tps-report-rhnqa: sync xmlrpc function name with errata tool.
* Thu Dec 08 2005 John W. Lockhart <lockhart@redhat.com>
- Add support for automated rhnqa testing
- Add: tps-query-rhnqa, tps-report-rhnqa, tps-summarize-rhnqa, tps-auto-rhnqa
- tps-query: also query for noarch packages.
- tps-make-lists: save job and run ID info if run from tpsd.
* Wed Nov 02 2005 John W. Lockhart <lockhart@redhat.com>
- tps-report: fix typo that caused traceback
* Tue Nov 01 2005 John W. Lockhart <lockhart@redhat.com>
- tps-query, tps-report: use only RHEL2.1-compatible python features.
* Fri Oct 28 2005 John W. Lockhart <lockhart@redhat.com>
- tpsd: check myArgs rather than Errata since that's what we set
* Fri Oct 28 2005 John W. Lockhart <lockhart@redhat.com>
- cause tps-query xmlrpc exceptions to go to stderr
* Fri Oct 28 2005 John W. Lockhart <lockhart@redhat.com>
- fix chkconfig command in post as well as mention of etc/init.d.
* Fri Oct 28 2005 John W. Lockhart <lockhart@redhat.com>
- Add tpsd automation package (auto,summarize,query,report)
- tps-rhnqa: fix array splice-in-place bug that caused skips and failures.
* Mon Oct 17 2005 John W. Lockhart <lockhart@redhat.com>
- tps-lib.pl: tweak determinePackageState to report new/old rather than mixed for partial installs.
* Mon Oct 17 2005 John W. Lockhart <lockhart@redhat.com>
- more fixes for -debuginfo, primarily in tps-rhnqa
- fixes for x86 filelists that contain both i386 and i686
- misc other small fixes
* Fri Oct 07 2005 John W. Lockhart <lockhart@redhat.com>
- tps-srpmtest: fix debuginfo building again.
* Thu Oct 06 2005 John W. Lockhart <lockhart@redhat.com>
- tps-srpmtest: rebuild the debuginfo when it appears in the errata's file list.
* Thu Oct 06 2005 John W. Lockhart <lockhart@redhat.com>
- add tps-which to the archive, for real this time.
* Thu Oct 06 2005 John W. Lockhart <lockhart@redhat.com>
- tps-lib: fix capitalization in function name
* Wed Oct 05 2005 John W. Lockhart <lockhart@redhat.com>
- Eliminate failures in delete test caused by dependencies.
- Handle cases where there are more new packages than old.
- Use LANG=C so as not to be thwarted by Japanese.
- Add the tps-which command to tell which package set is present.
- Use caching routines in tps-lib for performance.
- Make tps-downgrade use the actual DowngradeTest routine.
* Fri Aug 19 2005 John W. Lockhart <lockhart@redhat.com>
- fix Ctrl-C handling on tps-rhnqa.
* Wed Aug 17 2005 John W. Lockhart <lockhart@redhat.com>
- oops, remember to use oldpackage for actual downgrade cmd as well.
* Wed Aug 17 2005 John W. Lockhart <lockhart@redhat.com>
- add tps-upgrade and tps-downgrade
* Fri Aug 12 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rhnqa: fix typo so that "not found" is itself found.
* Tue Aug 09 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rhnqa: report signature used, warn if not master sig.
- tps-rhnqa: add test to install (not update) new multilib pkgs.
- tps-srpmtest: do not try to rebuild nonexistent source packages.
- tps-srpmtest: use rpm -p when querying multilib .rpm files.
- tps-srpmtest: use only one occurrence of each specfile.
- Bump version number due to new test and large bugfix count.
* Mon Aug 08 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rhnqa: fix error handling when doing up2date -u against live.
- tps-rhnqa.1: document workaround for gpg on RHEL2.1.
* Wed Aug 03 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rpmtest: Handle unregistered systems more cleverly.
* Tue Aug 02 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rpmtest: add Delete/Install test pair when starting with none of the packages installed.
* Tue Aug 02 2005 John W. Lockhart <lockhart@redhat.com>
- tps-srpmtest: if the number specfiles changes between old and new srpms, fail the diff test and force manual inspection.
- tps-make-lists: Add warning for running make-lists on the wrong release.
- tps-lib.pl: Fix rpm commands for noarch packages for RHEL2.1.
* Mon Jul 25 2005 John W. Lockhart <lockhart@redhat.com>
- tps-lib.pl: fix determinePackageState for previously unreleased packages.
* Mon Jul 11 2005 John W. Lockhart <lockhart@redhat.com>
- tps-rhnqa: do not attempt to download nonexistent src.
- tps-make-lists: use correct get_packages invocation for extras srpms.
* Fri Jul 08 2005 John W. Lockhart <lockhart@redhat.com>
- Fix tps -n option when -d is present and no product/variant.
- Allow more packages to be built than shipped for tps-srpmtest.
- Warn on empty files for tps-make-lists.
* Thu Jul 07 2005 John W. Lockhart <lockhart@redhat.com>
- Bugfix for building srpms on multilib.
* Thu Jul 07 2005 John W. Lockhart <lockhart@redhat.com>
- Further improve the logfile messages.
* Wed Jul 06 2005 John W. Lockhart <lockhart@redhat.com>
- Support LACD items in tps-make-lists.
- Further improve log/rpt messages in tps-rhnqa.
* Wed Jul 06 2005 John W. Lockhart <lockhart@redhat.com>
- Improve log and report messages.
* Wed Jul 06 2005 John W. Lockhart <lockhart@redhat.com>
- Add RHNQA testing materials.
* Wed Jun 29 2005 John W. Lockhart <lockhart@redhat.com>
- Chomp two sneaky newlines that caused an incorrect package state
  determination on ia64.  Also change PASSED to PASS and
  FAILED to FAIL in the srpmtest to match other usage.  Thanks
  to mgomes for the bug report.
* Wed Jun 29 2005 John W. Lockhart <lockhart@redhat.com>
- Add support for testing SRPMS.
- Fix handing under RHEL2.1.
- Avoid being tripped by rpm-signature messages.
- Move manpages to /usr/local/man for RHEL2.1 compatibility.
* Thu Jun 23 2005 John W. Lockhart <lockhart@redhat.com>
- Initial release.
