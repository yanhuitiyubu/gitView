# -*- perl -*-
#
# tests for find_rhn_dest_channel()
#
use strict;
use warnings;

use Test::More;
use Test::Differences;

###############################################################################
# BEGIN test setup -- see bottom of file for tests and their format.

my @tests;
for my $line (<DATA>) {
    chomp $line;
    $line =~ s/\s+$//;                  # strip trailing whitespace
    $line =~ s/^#.*$//;                 # remove comments

    if ($line =~ /^\*\s+(.*)/) {        # '* foo' : test name
        push @tests, {
            name       => $1,
            subscribed => [],
            dest       => '',
            expected   => '',
            loglines   => [],
        };
    }
    elsif ($line =~ /^s\s+(\S+)$/) {    # 's foo' : subscribed channel
        push @{ $tests[-1]{subscribed} }, $1;
    }
    elsif ($line =~ /^d\s+(\S+)$/) {    # 'd foo' : rhn dest channel
        # This seems to be a single string of newline-terminated chan names
        $tests[-1]{dest} .= "$1\n";
    }
    elsif ($line =~ /^>\s+(\S+)$/) {    # '> foo' : what we expect
        $tests[-1]{expected} = $1;
    }
    elsif ($line =~ /^\!\s+(.*)$/) {
        push @{ $tests[-1]{loglines} }, [ split /,\s*/, "$1\n", 3 ];
    }
    elsif ($line) {
        die "Internal error: cannot grok test definition line '$line'";
    }
}

plan tests => 1 + 2 * @tests;

# END   test setup
###############################################################################

# Override FindBin; otherwise the script's "require tps-lib" will fail
use FindBin;
$FindBin::RealBin = 'bin';

ok(require('bin/tps-make-lists'), 'loaded tps-make-lists') or exit;

# Override certain functions which there's no way to get working in a test env
package TPS::MakeLists;
use subs qw(getSubscribedChannels doLog);
package main;

# Main look: run each test
for my $t (@tests) {
    my @logged_messages;

    # Setup: prepare the globs and environment needed by the tested function
    no warnings qw(redefine once);
    *TPS::MakeLists::getSubscribedChannels = sub { return @{$t->{subscribed}} };
    $TPS::MakeLists::globs->{rhnDestChannel} = $t->{dest};
    *TPS::MakeLists::doLog = sub { push @logged_messages, [ @_ ] };

    # Invoke the function, and compare the results
    my $actual = TPS::MakeLists::find_rhn_dest_channel();

    is $actual, $t->{expected}, $t->{name};
    eq_or_diff \@logged_messages, $t->{loglines}, "$t->{name} [log]";
}


__DATA__

* test a single subscribed destination

s channel-1
s channel-2
s channel-3

d channel-1

> channel-1

#------------------------------------------------------------------------------

* test a single unsubscribed destination

s channel-1
s channel-2
s channel-3

d channel-nosub-9

> channel-nosub-9

#------------------------------------------------------------------------------

* no dest channel

s channel-spirits
s channel-english
s channel-surfing

! 37, 7, WARNING: no destination channel found

#------------------------------------------------------------------------------

* pick the shortest subscribed name

s channel-1
s channel-2-with-longer-name
s channel-3-with-longest-name

d wtf
d channel-1
d channel-2-with-longer-name
d channel-3-with-longest-name

> channel-1

! 37, 7, WARNING: too many destination channels found
! 37, 7, INFO: Destination Channel set to 'channel-1'

#------------------------------------------------------------------------------

* pick the shortest subscribed name, but testing different order

s channel-2-with-longer-name
s channel-1
s channel-3-with-longest-name

d channel-3-with-longest-name
d channel-2-with-longer-name
d channel-1

> channel-1

! 37, 7, WARNING: too many destination channels found
! 37, 7, INFO: Destination Channel set to 'channel-1'

#------------------------------------------------------------------------------

* empty subscription list, pick shortest destination name

d channel-3-with-longest-name
d channel-2-with-longer-name
d channel-1

> channel-1

! 37, 7, WARNING: too many destination channels found
! 37, 7, WARNING: Destination Channel set to 'channel-1', which is not in our subscribed list
