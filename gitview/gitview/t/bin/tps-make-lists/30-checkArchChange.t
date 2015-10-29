# -*- perl -*-
#
# tests for checkArchChange
#
use strict;
use warnings;

use Test::More;
use Test::Differences;

sub href_ify {
    my $str = shift; # foo-bar-1.1-3.el6.x86_64.rpm etc

    $str =~ /^(.*)-.*-.*\.(.*)\.rpm$/
        or die "Internal error: '$str' does not match 'N-V-R.A.rpm'";
    return +{n => $1, a => $2};
}
###############################################################################
# BEGIN test setup

our @Tests;
while (my $line = <DATA>) {
    chomp $line;
    $line =~ s/\s+$//;                  # strip trailing whitespace
    $line =~ s/^\s*#.*$//;              # strip comments

    # * My Test Name
    if ($line =~ /^\*\s+(.*)/) {
        push @Tests, { name => $1, old => [], new => [], expect => [] };
    }

    #                 old-rpm   | new-rpm
    elsif ($line =~ /^(\S+)?\s+\|(\s+(\S+))$/) {
        my ($first, $third) = ($1, $3);
        if (defined $first) {
            push @{$Tests[-1]{old}}, href_ify($first);
        }
        if (defined $third) {
            push @{$Tests[-1]{new}}, href_ify($third);
        }
    }

    # 37,7,WARNING: etc etc
    elsif ($line =~ /^>\s+(.*)/) {
        push @{$Tests[-1]{expect}}, $1 . "\n";
    }
    elsif ($line =~ /^<\s+(\d+)/) {
        $Tests[-1]{rc} = $1;
    }
    elsif ($line) {
        die "Cannot grok: '$line'";
    }
}

plan tests => 1 + (2 * @Tests);

# BEGIN test setup
###############################################################################

# Override FindBin; otherwise the script's "require tps-lib" will fail
use FindBin;
$FindBin::RealBin = 'bin';
ok(require('bin/tps-make-lists'), 'loaded tps-make-lists') or exit;

# Override doLog(): preserve messages, then compare against a known list.
our @tps_log;
{
    no warnings qw(redefine once);
    *TPS::MakeLists::doLog = sub  {
        push @tps_log, [ @_ ];
    };
}

for my $t (@Tests) {
    @tps_log = ();
    my $rc = TPS::MakeLists::checkArchChange($t->{old}, $t->{new});
    eq_or_diff \@tps_log, $t->{expect}, $t->{name};
    is($rc, $t->{rc}, "rc==$t->{rc}");
}

# WARNING: Package tzdata changed arch from i386,src to i386,src,x86_64
__DATA__

###############################################################################

* No arch change

foo-1.1-2.el6.x86_64.rpm                  | foo-1.1-3.el6.x86_64.rpm
< 0

###############################################################################

* x86_64 -> noarch

foo-1.1-2.el6.x86_64.rpm                  | foo-1.1-3.el6.noarch.rpm

> 37,7,WARNING: Package foo changed arch from x86_64 to noarch
< 1
###############################################################################

* x86_64 -> noarch,x86_64

foo-1.1-2.el6.x86_64.rpm                  | foo-1.1-3.el6.noarch.rpm
                                          | foo-1.1-3.el6.x86_64.rpm

> 37,7,WARNING: Package foo changed arch from x86_64 to noarch,x86_64
< 1
###############################################################################

* two packages: x86_64 -> noarch and x86_64 -> noarch,x86_64,src

foo-1.1-2.el6.x86_64.rpm                  | foo-1.1-3.el6.noarch.rpm
bar-1.1-2.el6.x86_64.rpm                  | bar-1.1-3.el6.noarch.rpm
                                          | foo-1.1-3.el6.x86_64.rpm
                                          | foo-1.1-3.el6.src.rpm

> 37,7,WARNING: Package bar changed arch from x86_64 to noarch
> 37,7,WARNING: Package foo changed arch from x86_64 to noarch,src,x86_64
< 2
###############################################################################

* package with multiple dashes

foo-the-bar-1.1-2.el6.x86_64.rpm          | foo-the-bar-1.1-3.el6.noarch.rpm

> 37,7,WARNING: Package foo-the-bar changed arch from x86_64 to noarch
< 1
