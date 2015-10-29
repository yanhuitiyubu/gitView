# -*- perl -*-
#
# tests for tps-yum-show-channels
#
use strict;
use warnings;

use Test::More;
use Test::Differences;
use File::Temp          qw(tempdir);

###############################################################################
# BEGIN easily-customizable section

our $UUT = 'tps-yum-show-channels';

our @Tests;
while (my $line = <DATA>) {
    chomp $line;

    if ($line =~ /^\*\s*(.*)/) {        # "* rhel7" -> test name
        push @Tests, { name => $1, yum_output => '', expect => [] };
    }
    elsif ($line =~ /^>\s(.*)/) {       # "> aaa" -> expected output
        # Saving as a list makes it easy to see diffs if a test fails
        push @{$Tests[-1]{expect}}, $1;
    }
    elsif ($line =~ /^\s*#/) {          # Anything starting with '#': comment
        # ignore
    }
    elsif ($line) {                     # Anything else: output from yum cmd
        # Saving as a string makes it easy to write our dummy yum command
        $Tests[-1]{yum_output} .= $line . "\n";
    }
}

# END   easily-customizable section
###############################################################################

plan tests => scalar(@Tests);

# Create a temporary directory. We'll write one subdirectory here for each
# test, and in each subdirectory we'll put a fake 'yum' binary. We do it
# this way so if there's any test failure you can run 'DEBUG=1 prove ...',
# preserve all test directories, and verify/run the fake yum commands
# for your own manual testing.
my $tempdir = tempdir("_test__$UUT.XXXXXXX", CLEANUP => !$ENV{DEBUG});

my $i = 0;
for my $t (@Tests) {
    # New subdirectory for each test: 01, 02, 03, ...
    my $subdir = sprintf("%s/%02d", $tempdir, ++$i);
    mkdir $subdir, 02755 or die "Cannot mkdir $subdir: $!";
    local $ENV{PATH} = "$subdir:/usr/bin:/bin";

    # Write a fake 'yum' command; that's what tps-yum-* will invoke
    my $yum_bin = "$subdir/yum";
    open my $yum_fh, '>', $yum_bin
        or die "Cannot create $yum_bin: $!";
    print { $yum_fh } <<"END_YUM";
#!/bin/sh

cat <<EOF
$t->{yum_output}
EOF
exit 0
END_YUM
    close $yum_fh
        or die "Error writing $yum_bin: $!";
    chmod 0755 => $yum_bin;

    # Invoke tps-yum-* and get its actual output
    # FIXME: what about any flags to tps-yum-* ?
    # FIXME: what about testing error status?
    my @actual;
    open my $uut_fh, '-|', "./bin/$UUT"
        or die "Cannot fork: $!";
    while (my $line = <$uut_fh>) {
        chomp $line;
        push @actual, $line;
    }
    close $uut_fh
        or die "Error running ./bin/$UUT";

    # Compare
    eq_or_diff \@actual, $t->{expect}, $t->{name};
}


__DATA__

#
# Format: '*' introduces a test; '>' is expected output from our tps-yum
# command; everything else is the output of 'yum -e 1 repolist enabled'
#
###############################################################################
#
# Short and simple test. Output collected on Ed's F20 laptop.
#

* Fedora
Loaded plugins: langpacks
repo id            repo name                                            status
!beaker-client/20  Beaker Client - Fedora20                                 15
!bluejeans         Blue Jeans Network, Inc. - x86_64 software and updates   83
!brew/20           Brew Buildsystem for Fedora 20 - x86_64                  10
fedora/20/x86_64   Fedora 20 - x86_64                                   38,597
!rhpkg/20          rhpkg for Fedora 20                                       8
!updates/20/x86_64 Fedora 20 - x86_64 - Updates                         22,336
repolist: 61,049

> beaker-client
> bluejeans
> brew
> fedora
> rhpkg
> updates

################################################################################
#
# Simple case. Output collected 2015-05-29 on x86-64-7s-m1.ss
#

* RHEL7 simple case

Loaded plugins: aliases, auto-update-debuginfo, changelog, fastestmirror,
              : filter-data, fs-snapshot, kabi, keys, langpacks, list-data,
              : merge-conf, post-transaction-actions, priorities, product-id,
              : protectbase, ps, refresh-packagekit, remove-with-leaves, rpm-
              : warm-cache, show-leaves, subscription-manager, tmprepo, tsflags,
              : upgrade-helper, verify, versionlock
This system is registered to Red Hat Subscription Management, but is not receiving updates. You can use subscription-manager to assign subscriptions.
Loading support for Red Hat kernel ABI
Loading mirror speeds from cached hostfile
0 packages excluded due to repository protections
repo id                                           repo name               status
beaker-Server-optional                            beaker-Server-optional  4,072
beaker-Server-optional-debuginfo                  beaker-Server-optional-   234
rhel-7-server-cert-source-rpms                    rhel-7-server-cert-sour    14
rhel-7-server-debug-rpms                          rhel-7-server-debug-rpm 2,750
rhel-7-server-extras-debug-rpms                   rhel-7-server-extras-de     7
rhel-7-server-extras-rpms                         rhel-7-server-extras-rp    44
rhel-7-server-extras-source-rpms                  rhel-7-server-extras-so    30
rhel-7-server-fastrack-debug-rpms                 rhel-7-server-fastrack-    32
rhel-7-server-fastrack-rpms                       rhel-7-server-fastrack-   105
rhel-7-server-fastrack-source-rpms                rhel-7-server-fastrack-     2
rhel-7-server-hts-rpms                            rhel-7-server-hts-rpms/    14
rhel-7-server-hts-source-rpms                     rhel-7-server-hts-sourc     8
rhel-7-server-openstack-6.0-cts-source-rpms       rhel-7-server-openstack     0
rhel-7-server-openstack-6.0-debug-rpms            rhel-7-server-openstack    51
rhel-7-server-openstack-6.0-installer-debug-rpms  rhel-7-server-openstack    17
rhel-7-server-openstack-6.0-installer-source-rpms rhel-7-server-openstack   131
rhel-7-server-openstack-6.0-source-rpms           rhel-7-server-openstack   280
rhel-7-server-optional-debug-rpms                 rhel-7-server-optional- 1,689
rhel-7-server-optional-fastrack-debug-rpms        rhel-7-server-optional-     3
rhel-7-server-optional-fastrack-rpms              rhel-7-server-optional-    50
rhel-7-server-optional-fastrack-source-rpms       rhel-7-server-optional-    12
rhel-7-server-optional-source-rpms                rhel-7-server-optional- 1,795
rhel-7-server-rh-common-debug-rpms                rhel-7-server-rh-common    18
rhel-7-server-rh-common-rpms                      rhel-7-server-rh-common   131
rhel-7-server-rh-common-source-rpms               rhel-7-server-rh-common    69
rhel-7-server-rhevh-debug-rpms                    rhel-7-server-rhevh-deb     0
rhel-7-server-rhevh-rpms                          rhel-7-server-rhevh-rpm     8
rhel-7-server-rhevh-source-rpms                   rhel-7-server-rhevh-sou     6
rhel-7-server-rhn-tools-debug-rpms                rhel-7-server-rhn-tools     2
rhel-7-server-rhn-tools-rpms                      rhel-7-server-rhn-tools    75
rhel-7-server-rhn-tools-source-rpms               rhel-7-server-rhn-tools    44
rhel-7-server-rt-debug-rpms                       rhel-7-server-rt-debug-    14
rhel-7-server-rt-rpms                             rhel-7-server-rt-rpms/7    28
rhel-7-server-rt-source-rpms                      rhel-7-server-rt-source     9
rhel-7-server-source-rpms                         rhel-7-server-source-rp 2,516
rhel-7-server-supplementary-debug-rpms            rhel-7-server-supplemen     0
rhel-7-server-supplementary-rpms                  rhel-7-server-supplemen    62
rhel-7-server-supplementary-source-rpms           rhel-7-server-supplemen     6
rhel-7-server-thirdparty-oracle-java-rpms         rhel-7-server-thirdpart    94
rhel-7-server-thirdparty-oracle-java-source-rpms  rhel-7-server-thirdpart     4
rhel-7-server-v2vwin-1-debug-rpms                 rhel-7-server-v2vwin-1-     0
rhel-7-server-v2vwin-1-rpms                       rhel-7-server-v2vwin-1-     0
rhel-7-server-v2vwin-1-source-rpms                rhel-7-server-v2vwin-1-     1
rhel-atomic-host-debug-rpms                       rhel-atomic-host-debug-    14
rhel-atomic-host-source-rpms                      rhel-atomic-host-source    21
rhel-ha-for-rhel-7-server-debug-rpms              rhel-ha-for-rhel-7-serv    43
rhel-ha-for-rhel-7-server-fastrack-debug-rpms     rhel-ha-for-rhel-7-serv     0
rhel-ha-for-rhel-7-server-fastrack-rpms           rhel-ha-for-rhel-7-serv     0
rhel-ha-for-rhel-7-server-fastrack-source-rpms    rhel-ha-for-rhel-7-serv     0
rhel-ha-for-rhel-7-server-rpms                    rhel-ha-for-rhel-7-serv   128
rhel-ha-for-rhel-7-server-source-rpms             rhel-ha-for-rhel-7-serv    28
rhel-rs-for-rhel-7-server-debug-rpms              rhel-rs-for-rhel-7-serv    50
rhel-rs-for-rhel-7-server-fastrack-debug-rpms     rhel-rs-for-rhel-7-serv     0
rhel-rs-for-rhel-7-server-fastrack-rpms           rhel-rs-for-rhel-7-serv     0
rhel-rs-for-rhel-7-server-fastrack-source-rpms    rhel-rs-for-rhel-7-serv     0
rhel-rs-for-rhel-7-server-rpms                    rhel-rs-for-rhel-7-serv   146
rhel-rs-for-rhel-7-server-source-rpms             rhel-rs-for-rhel-7-serv    32
rhel-sap-for-rhel-7-server-debug-rpms             rhel-sap-for-rhel-7-ser    12
rhel-sap-for-rhel-7-server-rpms                   rhel-sap-for-rhel-7-ser    23
rhel-sap-for-rhel-7-server-source-rpms            rhel-sap-for-rhel-7-ser    13
rhel-server-rhscl-7-debug-rpms                    rhel-server-rhscl-7-deb   147
rhel-server-rhscl-7-rpms                          rhel-server-rhscl-7-rpm 2,387
rhel-server-rhscl-7-source-rpms                   rhel-server-rhscl-7-sou   903
repolist: 18,374

> beaker-Server-optional
> beaker-Server-optional-debuginfo
> rhel-7-server-cert-source-rpms
> rhel-7-server-debug-rpms
> rhel-7-server-extras-debug-rpms
> rhel-7-server-extras-rpms
> rhel-7-server-extras-source-rpms
> rhel-7-server-fastrack-debug-rpms
> rhel-7-server-fastrack-rpms
> rhel-7-server-fastrack-source-rpms
> rhel-7-server-hts-rpms
> rhel-7-server-hts-source-rpms
> rhel-7-server-openstack-6.0-cts-source-rpms
> rhel-7-server-openstack-6.0-debug-rpms
> rhel-7-server-openstack-6.0-installer-debug-rpms
> rhel-7-server-openstack-6.0-installer-source-rpms
> rhel-7-server-openstack-6.0-source-rpms
> rhel-7-server-optional-debug-rpms
> rhel-7-server-optional-fastrack-debug-rpms
> rhel-7-server-optional-fastrack-rpms
> rhel-7-server-optional-fastrack-source-rpms
> rhel-7-server-optional-source-rpms
> rhel-7-server-rh-common-debug-rpms
> rhel-7-server-rh-common-rpms
> rhel-7-server-rh-common-source-rpms
> rhel-7-server-rhevh-debug-rpms
> rhel-7-server-rhevh-rpms
> rhel-7-server-rhevh-source-rpms
> rhel-7-server-rhn-tools-debug-rpms
> rhel-7-server-rhn-tools-rpms
> rhel-7-server-rhn-tools-source-rpms
> rhel-7-server-rt-debug-rpms
> rhel-7-server-rt-rpms
> rhel-7-server-rt-source-rpms
> rhel-7-server-source-rpms
> rhel-7-server-supplementary-debug-rpms
> rhel-7-server-supplementary-rpms
> rhel-7-server-supplementary-source-rpms
> rhel-7-server-thirdparty-oracle-java-rpms
> rhel-7-server-thirdparty-oracle-java-source-rpms
> rhel-7-server-v2vwin-1-debug-rpms
> rhel-7-server-v2vwin-1-rpms
> rhel-7-server-v2vwin-1-source-rpms
> rhel-atomic-host-debug-rpms
> rhel-atomic-host-source-rpms
> rhel-ha-for-rhel-7-server-debug-rpms
> rhel-ha-for-rhel-7-server-fastrack-debug-rpms
> rhel-ha-for-rhel-7-server-fastrack-rpms
> rhel-ha-for-rhel-7-server-fastrack-source-rpms
> rhel-ha-for-rhel-7-server-rpms
> rhel-ha-for-rhel-7-server-source-rpms
> rhel-rs-for-rhel-7-server-debug-rpms
> rhel-rs-for-rhel-7-server-fastrack-debug-rpms
> rhel-rs-for-rhel-7-server-fastrack-rpms
> rhel-rs-for-rhel-7-server-fastrack-source-rpms
> rhel-rs-for-rhel-7-server-rpms
> rhel-rs-for-rhel-7-server-source-rpms
> rhel-sap-for-rhel-7-server-debug-rpms
> rhel-sap-for-rhel-7-server-rpms
> rhel-sap-for-rhel-7-server-source-rpms
> rhel-server-rhscl-7-debug-rpms
> rhel-server-rhscl-7-rpms
> rhel-server-rhscl-7-source-rpms

###############################################################################
#
# AHA! This actually tests bz1194426: if we revert our fix, tps-yum-*
# gives us empty results.
#
# Output collected from 'yum -e 1 repolist enabled' on tps005.ceph.redhat.com
#

* bz1194426
repo id                                   repo name                       status
!rhel-7-server-optional-rpms              rhel-7-server-optional-rpms/7Se 5,830
!rhel-7-server-rhceph-1.2-mon-debug-rpms  rhel-7-server-rhceph-1.2-mon-de     5
!rhel-7-server-rhceph-1.2-mon-rpms        rhel-7-server-rhceph-1.2-mon-rp    25
!rhel-7-server-rhceph-1.2-mon-source-rpms rhel-7-server-rhceph-1.2-mon-so     9
!rhel-7-server-rpms                       rhel-7-server-rpms/7Server/x86_ 7,049
repolist: 12,918

> rhel-7-server-optional-rpms
> rhel-7-server-rhceph-1.2-mon-debug-rpms
> rhel-7-server-rhceph-1.2-mon-rpms
> rhel-7-server-rhceph-1.2-mon-source-rpms
> rhel-7-server-rpms

###############################################################################
#
# Please add more tests.
