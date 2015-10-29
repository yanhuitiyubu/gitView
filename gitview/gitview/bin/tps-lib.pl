#!/usr/bin/perl
use File::Basename;
use Date::Manip;
use IPC::Open3;
require HTTP::Request;
require HTTP::Headers;
require LWP::UserAgent;

## Message Types, Most to Least important, batched by 10's.
# 40-49: fatal errors, bugs, severe problems
*TPSFATAL   = \49;
*TPSBUG     = \48;
*TPSERROR   = \47;
# 30-39: warnings
*TPSWARN    = \37; # synonym to help against forgetfulness
*TPSWARNING = \37;
# 20-29: test messages
*TPSFAILTXT = \29; # block of output which likely contains cause of failure.
*TPSTXT     = \28; # important tpsinfo, must-have text message.
*TPSRESULT  = \26; # test result
*TPSBEGIN   = \25; # begin test - use only with beginTest().
*TPSEND     = \24; # end test - use only with endTest().
# Certain things, like the Srpm Rebuild Test, have a lot of steps.  Allow those steps to have separate begin/end markers.
*TPSSUBBEGIN= \21; # begin sub-test
*TPSSUBEND  = \20; # end sub-test
# 10-19: hints, tips, instructions
*TPSHINT    = \18; # "Here's what might cause this condition..."
*TPSTIP     = \17; # "Here's what you should do next."
*TPSINFO    = \16; # "By the way, $foo is happening..."
# 1-9: commands and output
*TPSCMD     = \9;  # "Executing: rpm --perform-miracles"
*TPSCMDOUT  = \8;  # "Command returned 256: unknown option"
*TPSMISC    = \1;  # Debug messages, miscellaneous output

## Importance Levels -- 'TPS' + logfile name, except we use 'raw' for noise :)
*TPSDEBUG = \1;  # Debug information.
*TPSRAWLINK = \2;  # Content is from a .raw file and should be turned into a link.
*TPSNOISE = \4;  # Supplemental information which is rarely useful.
*TPSLOG   = \7;  # Info for LOG file.
*TPSRPT   = \14; # Info for RPT file, and stdout if manually run.
*TPSCRIT  = \21; # Critical information, appears everywhere.

# TPSRAWLINK format:
#  (std doLog::) (basename of html file) (output message from foreign .raw file)

# doLog - write msg of given type and severity level to appropriate logs, and return the msg.
# this lets you accumulate strings if needed -- $str .= doLog(stuff...);
sub doLog {
    my ($mType, $mLevel, $msg) = @_;
    my %printTo = ( 'dbg' => 0, 'log' => 0, 'rpt' => 0 );
    my $timeStamp = UnixDate(ParseDate("today"), qw( %Y%m%d%H%M%S ));
    my $tmpType;
    my $tstTrack;

    $tstTrack = ($globs->{'testCount'} . '@' .
                 ((0 == $globs->{'inTest'}) ? 0 : $globs->{'curTestNumber'}) . '.' .
                 ((0 == $globs->{'inSubTest'}) ? 0 : $globs->{'curSubTestNumber'}));

    # Always print out a marked-up raw data-log line:
    my $rawlinkFile = '';
    foreach my $i (split(/\n/,$msg)) {
        if (($mType == $TPSTXT or $mType < $TPSSUBEND) && ($i =~ m/^\s*(TPS)*RESULT: /)) {
            # some programs call others and do not get marked-up output... mark results if possible.
            $tmpType = $TPSRESULT;
        } else {
            $tmpType = $mType;
        }
        chomp($i); chomp($i); chomp($i); chomp($i);
        if ($i) {
            if (($mLevel == $TPSRAWLINK) && (!$rawlinkFile)) {
                $rawlinkFile = ((split(/\s+/,$i))[0] . ' ');
                $i =~ s/^${rawlinkFile}\s*//;
            }
            if ($i) {
                print RAW $timeStamp . ':' . $globs->{testName} . " ${tstTrack}:" . $mLevel . ':' . $tmpType . ":: $rawlinkFile" . "$i\n";
            }
        }
    }

    # Output to debugging log (possibly STDERR) if we're being verbose.
    print DBG $msg if (($globs->{verbose}) || ($globs->{tmpStderr}));

    # everyone hears it if type is TPSEND or higher; or if level is TPSRPT or better.
    if (($mType >= $TPSSUBEND) || ($mLevel >= $TPSRPT)) {
        print DBG $msg unless (($globs->{verbose}) || ($globs->{quietStderr}));
        print LOG $msg;
        print RPT $msg;
        print $msg; # stdout gets a copy, too.
        return $msg;
    }
    $printTo{log} = 1 if $mLevel >= $TPSLOG;
    $printTo{log} = 1 if $mType  >= $TPSINFO;
    $printTo{rpt} = 1 if $mLevel >= $TPSRPT;
    print LOG $msg if ($printTo{log} == 1);
    print RPT $msg if ($printTo{rpt} == 1);
    print $msg if ($printTo{rpt} == 1);
    return $msg;
}
## openLogFileSet('>raw.log',STDERR,'>prog.rpt','>prog.log') and such.
sub openLogFileSet($$$$) {
    my ($rawName, $dbugName, $rptName, $logName) = @_;
    open(RAW,$rawName) or die "Cannot open RAW filehandle: $rawName";
    open(RPT,$rptName) or die "Cannot open RPT filehandle: $rptName";
    open(LOG,$logName) or die "Cannot open LOG filehandle: $logName";
    $globs->{dupStderr} = 0;
    $globs->{quietStderr} = 0;
    # open OLDERR,     ">&", \*STDERR or die "Can't dup STDERR: $!";
    if ((!defined($dbugName)) || (!$dbugName) || (ref($dbugName) ne 'GLOB')) {
        open(DBG,$dbugName) || die "Cannot open DBG filehandle: $dbugName";
    } else {
        if ((ref($dbugName) eq 'GLOB') && ($dbugName == \*STDERR)) {
            # if ($^V and $^V lt (chr(5).chr(8).chr(0))) {
	    if ($^V and $^V lt v5.8.0) {
                # ancient perl couldn't dup the fh the same way.
                open(DBG, ">&STDERR") or die "Cannot open dup of STDERR: $!";
            } else {
                open(DBG, ">&", \*STDERR) or die "Cannot open dup of STDERR: $!";
            }
            $globs->{dupStderr} = 1;
            $globs->{quietStderr} = 1 if (1 == $globs->{isManual});
        } else {
            if ($^V and $^V lt (chr(5).chr(8).chr(0))) {
                # ancient perl again; this may not be correct.
                open(DBG, ">&$dbugName") or die "Cannot open dup of $dbugName: $!";  # correct typeglob hackery?
            } else {
                open(DBG, ">&", \*{$dbugName}) or die "Cannot open dup of $dbugName: $!";  # correct typeglob hackery?
            }
        }
    }
    LOG->autoflush(1);
    RPT->autoflush(1);
    DBG->autoflush(1);
    RAW->autoflush(1);
    STDERR->autoflush(1);
    STDOUT->autoflush(1);
}
sub closeLogFileSet() {
    close(LOG);
    close(RPT);
    close(RAW);
    close(DBG);
}

### given a .raw file, this functions grabs the marked-up TPSEND and TPSSUBEND lines.
sub grepRawEndMarks() {
    my ($fname) = @_;
    my $res = '';
    my $re = '[[:digit:]]+@[[:digit:]]+\.[[:digit:]]+:[[:digit:]]+:';
    if (-r $fname) {
        $res = `egrep '${re}(${TPSEND}|${TPSSUBEND})::' $fname`;
    }
    return $res;
}

sub disableLocalRepoList {
    # Get list of local *.repo files, and provide them as disable args for yum.
    # Requires File::Basename.
    my ($g) = @_;
    my $theList = '';
    my @pulpList = ();
    my $isPulp = 0;

    $g = $globs if (!defined($g));

    $isPulp = 1 if ('pulp' eq $g->{tpsDistMethod});
    if ($isPulp) {
        @pulpList = keys(%{$g->{tpsRepoChannelsProfile}});
    }
    foreach my $i (`/usr/local/bin/tps-yum-show-channels --noplugins --all`) {
        chomp($i);
        if ($i) {
            if ($isPulp) {
                $theList .= (' --disablerepo=' . $i) unless listInclude(\@pulpList,$i);
            } else {
                $theList .= (' --disablerepo=' . $i);
            }
        }
    }
    return $theList;
}
sub readPulpRepoInfo {
    # _TestProfile_ stable-rhel-7-server
    # _server_ pulp.qa.engineering.redhat.com
    # _generated_ Thu Apr 03 22:45:35 -0400 2014
    my (@fields);
    my (%ret,$fName,$fCount);
    my $lines = `egrep '^\# _(TestProfile|server|generated)_ ' "$globs->{tpsProfileRepo}"`;
    if ($? == 0) {
        chomp($lines);
        foreach my $ln (split(/\n/,$lines)) {
            chomp($ln);
            @fields = split(/\s+/,$ln);
            $fCount = scalar(@fields) - 1;
            if ($fCount >= 2) {
                $fName = $fields[1];
                $fName =~ s/_//g;
                $ret{$fName} = join(' ',@fields[2..$fCount]);
            }
        }
    }
    return \%ret;
}
#########################################
# fixChannelCache: run tps-setup-channel-cache on specified cache (live or qa) if needed
#
sub fixChannelCache {
    my ($whichCache) = @_;
    my @caches = ();
    my $ret = 1;
    my $lookIn = '';
    my $dirsSearched = $ENV{TPS_CHAN_CACHE_DIR} || '/var/cache/tps/channels';
    if ((!defined($whichCache)) || (!$whichCache) || ($whichCache =~ m/live/i)) {
	push(@caches,'live');
    } elsif ($whichCache =~ m/both/i) {
	push(@caches,'live');
	push(@caches,'qa');
    } else {
	push(@caches,'qa');
    }
    foreach my $loc (@caches) {
	$lookIn = ($dirsSearched . '/' . $loc);
	my @filesSearched = glob("$lookIn/*");
	if (scalar(@filesSearched) < 1) {
	    doLog($TPSWARN,$TPSLOG,"WARNING: TPS Channel Caches appear to be ".
		  "missing for $loc; attempting to fix that now.\n");
	    my $setupOut = `tps-setup-channel-cache -r $loc 2>&1`;
	    if (0 != $?) {
		doLog($TPSWARN,$TPSLOG,"WARNING: tps-setup-channel-cache -r $loc ".
		      "failed: $setupOut\n");
		doLog($TPSWARN,$TPSLOG,"WARNING: You should manually ".
		      "verify the package info.\n");
	    } else {
		$ret = 0;
	    }
	} else {
	    $ret = 0;
	}
    }
    return $ret;
}
#########################################
# getSubscribedChannels
sub getSubscribedChannels {
    my $cacheFile = '/tmp/tps-rhn-channels.txt';
    my ($chans,$cacheOut);
    $chans = '';
    if ((-r $cacheFile) && (-s $cacheFile)) {
        $chans = `cat $cacheFile`;
    } else {
        # do we have OATS installed?  If so, try tps-channel-cache.
        if ($globs->{tpsOatsVersion}) {
            doLog($TPSINFO,$TPSLOG,
		  "Cannot use cached channel info, trying to regenerate it\n");
            doLog($TPSCMD,$TPSNOISE,"Executing: tps-channel-cache -q\n");
            $cacheOut = `tps-channel-cache -q 2>&1`;
            if (($? == 0) && (-r $cacheFile)) {
                $chans = `cat $cacheFile`;
            } else {
                doLog($TPSINFO,$TPSLOG,"Cannot use cached channel info, ".
                      "assuming only a base channel subscription is available.\n");
                doLog($TPSTIP,$TPSLOG,
		      "Use oats-config-rhn or oats-apply-test-profile to properly configure your system.\n");
            }
            doLog($TPSCMDOUT,$TPSNOISE,"Returned: $cacheOut\n");
        }
    }
    return (split(/\n/,$chans));
}

### Uses (and sets) global info to get an erratum's destination channel
sub getRHNDestChannel {
    if (exists($globs->{rhnDestChannel}) &&
        defined($globs->{rhnDestChannel}) &&
        ($globs->{rhnDestChannel})) {
        return($globs->{rhnDestChannel});
    }
    my $ret;
    $ret = $ENV{'TPSQ_RHNDEST'};
    unless ((defined($ret)) && ($ret)) {
        if (-r './variables-auto.sh') {
            cacheToEnv('./variables-auto.sh');
            $ret = $ENV{'TPSQ_RHNDEST'};
        }
    }
    if ((defined($ret)) && ($ret)) {
        $globs->{rhnDestChannel} = $ret;
        return($ret);
    }
    if (($globs->{'tpsErratum'}) && ('unknown' ne $globs->{'tpsErratum'})) {
	my $cmdMsg = ("tps-channel-info $globs->{'tpsErratum'} ".
	    "$globs->{'tpsETRelease'} $globs->{'arch'}");
        doLog($TPSMISC,$TPSDEBUG,"tpslib: $cmdMsg\n") if (tell(RAW) >= 0);
        $ret = `tps-channel-info $globs->{'tpsErratum'} $globs->{'tpsETRelease'} $globs->{'arch'}`;
        if (($? == 0) && ($ret !~ m/failed: server/)) {
            chomp($ret);
        } else {
            if (tell(RAW) >= 0) {
                doLog($TPSWARN,$TPSLOG,"getRHNDestChannel: \"$cmdMsg\" failed: $ret\n");
            } else {
                print STDERR "getRHNDestChannel: \"$cmdMsg\" failed: $ret";
            }
            $ret = '';
        }
        $globs->{rhnDestChannel} = $ret;
        $ENV{'TPSQ_RHNDEST'} = $ret;
    }
    return($ret);
}

sub initTpsLibVars {
    # @testFunctionList @testFunctionUserNames $tpsErrorText $debug
    # RPT LOG
    # $is21
    # $rhelNum (2,3,4,5,...) or 0 if not rhel
    # $fcNum   (1,2,3,...)   or 0 if not fedora
    # $variant, $release, $arch
    # $verbose
    # $trueArch
    # $tpsAuto
    # $tpsMode
    my ($presets) = @_;
    $presets = {} if (!defined($presets));
    my %t = (); # t for tpsLibVars
    my @testFunctionList = ();
    my @testFunctionUserNames = ();
    my $aud_init = '/etc/init.d/auditd';
    my $selinuxCmd_d = '/usr/sbin/selinuxenabled';
    my $selinuxEnfCmd_d = '/usr/sbin/getenforce';
    my $selinuxCmd;
    my $selinuxEnfCmd;
    my @delayInitItems = qw( tpsReposLive tpsReposQA );
    my @depErrataVars = qw( DEP_SRC_OUT DEP_FILES_OUT DEP_OLDSRC_OUT DEP_OLDFILES_OUT
			    DEP_PKGNAMES_OUT DEP_OLDPKGNAMES_OUT DEP_ERRATA );

    # Ensure that TPS settings are read, but do not override
    # anything the user has set up manually.
    shellExportsToEnv('/etc/tpsd.conf',0);

    # This number should be incremented whenever the *TPSWHATNOT constants
    # at the top of this file change, so that any parsers can deal with it.
    $t{'tpsLoggingVersion'} = '231';

    # Which mode, stacks testing or normal?
    $t{'tpsMode'} =  $ENV{'TPS_MODE'} || 'normal';
    # And which TPS are we?
    $t{'tpsRpmVersion'} = `rpm -q --whatprovides TPS`;
    chomp($t{'tpsRpmVersion'});
    $t{'tpsOatsVersion'} = `rpm -q --whatprovides oats 2>&1 | grep -v 'no package provides'` || '';
    chomp($t{'tpsOatsVersion'});

    # are we running automatically under tpsd or manually?
    $t{'tpsAuto'} = 1;
    $t{'isManual'} = 0;
    if (($FindBin::Script =~ m/tps-which/) || (!exists($ENV{'TPSAUTO'}))) {
        $t{'tpsAuto'} = 0;
        $t{'isManual'} = 1;
    }

    unless (exists($ENV{TPS_ALLOW_LOCALE})) {
	foreach my $c (qw(LC_CTYPE LC_COLLATE LC_NUMERIC LC_MONETARY LC_MESSAGES LANG)) {
	    $ENV{$c} = 'C';
	}
	# this is required to match the selinux/avc datestamps we use.
	$ENV{LC_TIME} = 'en_US';
    }

    $t{delayInitItems} = \@delayInitItems;
    $t{tpsIsPreRelease} = 0; 

    # Implement any presets we were supplied with
    foreach my $k (%$presets) {
        $t{$k} = $presets->{$k};
    }

    # Errata number
    $t{'tpsErratum'} =  $ENV{'ERRATA'} || $ENV{'TPSQ_ERRATA'} || 'unknown';

    $t{quietStderr} = 0; # whether to suppress stderr msgs that go to stdout
    $t{dupStderr} = 0;   # whether DBG is a dup of STDERR
    $t{silentReportPkgs} = 0; # whether to hush reportPkgs() output.

    # Dependent Errata Handling
    $t{depErrataVars} = \@depErrataVars;
    $t{forbidDepErrata} = 0;

    # which tps script are we?
    $t{'progName'} = $FindBin::Script;
    # and what test (for logging)?  Default: program name, until beginTest is called.
    $t{'testName'} = $FindBin::Script;
    $t{'subName'} = '';  # subTest name, default none.
    # These two are for use by routines that handle fatal errors and then exit, because
    # the results-markup program gets upset if Begin/End markers are mismatched.
    $t{'inTest'} = 0;    # within a beginTest/endTest block (1), or not (0).
    $t{'inSubTest'} = 0; # within a beginSubTest/endSubTest block (1), or not (0).
    # counters.  testCount is absolute and does not distinguish between test/subtest.
    $t{'testCount'} = 0; # count of tests, incremented by beginTest/beginSubTest.
    $t{'curTestNumber'} = 0; # the number of the test currently producing output, 0 for none.
    $t{'prevTestNumber'} = 0; # the number of the test currently producing output, 0 for none.
    $t{'curSubTestNumber'} = 0; # the number of the subtest currently producing output, 0 for none.
    # combined format: testCount@curTestNumber.curSubTestNumber

    # Locations of files containing special-cases rules.
    # Note: hash key names should follow the scheme of {key}_fileType here.
    $t{'shlib_scFile'} = "${RealBin}/../lib/tps/shlib-special-cases.txt";
    $t{'srpm_scFile'}  = "${RealBin}/../lib/tps/srpm-special-cases.txt";
    $t{'rpm_scFile'}   = "${RealBin}/../lib/tps/rpm-special-cases.txt";
    $t{'lists_scFile'} = "${RealBin}/../lib/tps/lists-special-cases.txt";
    $t{'rhnqa_scFile'} = "${RealBin}/../lib/tps/rhnqa-special-cases.txt";
    # Local special-cases for special customizations & testing --
    # See BZ 1146977
    # Note: hash key names should follow the scheme of {key}_fileType here.
    $t{'shlib_lscFile'} = "${RealBin}/../lib/tps/shlib-local-cases.txt";
    $t{'srpm_lscFile'}  = "${RealBin}/../lib/tps/srpm-local-cases.txt";
    $t{'rpm_lscFile'}   = "${RealBin}/../lib/tps/rpm-local-cases.txt";
    $t{'lists_lscFile'} = "${RealBin}/../lib/tps/lists-local-cases.txt";
    $t{'rhnqa_lscFile'} = "${RealBin}/../lib/tps/rhnqa-local-cases.txt";

    # HostName information
    $t{'hostInfo'} = `hostname -f 2>/dev/null || hostname -s || echo Unset_Hostname`;
    chomp($t{'hostInfo'});

    # Non-root rebuildability status
    $t{tpsBuilder} = $ENV{'TPS_BUILDER_USERNAME'} || 'test';
    $t{tpsBuilderOkay} = 0;
    $t{tpsBuilderDir} = '';
    my $builderDir = scalar(glob('~' . $t{tpsBuilder}));
    if (-d $builderDir) {
        $t{tpsBuilderOkay} = 1;
        $t{tpsBuilderDir} = $builderDir;
    }
    $t{neverCleanBuildDir} = 'false';
    if ((exists($ENV{'TPS_BUILD_SKIP_CLEANUP'})) &&
        ($ENV{'TPS_BUILD_SKIP_CLEANUP'} eq 'true')) {
        $t{neverCleanBuildDir} = 'true';
    }

    # LD_LIBRARY_PATHs for scripting languages
    # This is a hash of entries intended to be filled as follows:
    #   perl => "string:of:ldd:paths"
    #   java => "like:wise"
    # and so on.
    $t{script_ld_paths} = {};
    {
	# Do perl here; add others elsewhere, as researched.
	use Config;
	my $perlInfo = $Config{ccdlflags};
	# 'perl' => '-Wl,-E -Wl,-rpath,/usr/lib64/perl5/5.8.8/x86_64-linux-thread-multi/CORE'
	$perlInfo =~ s/.*,//g;
	$t{script_ld_paths}->{perl} = $perlInfo if ($perlInfo);
    }

    # Handle distro properties: RHEL: 5Client, 4Desktop, 3AS, 2.1AW; FC: 4.
    #   tpsProductVer: output from whatprovides redhat release ^^
    #   tpsProductFam: RHEL or Fedora
    #   tpsProductRel: major Release number: 4, 5, 2.1, whatever.
    #   tpsProductVariant: Desktop, Client, AS, ES, and so on.
    $t{is21} = 0;

    # tps-make-lists may need a manually-suppiled ProductVer, for instance
    # inquiring about an update for 4AS from a Fedora system.  Make it possible here.
    initProductInfo(\%t);

    # Figure out what sort of value for $RELEASE to feed to the Errata Tool when needed.
    # Typically it's stuff like 5Server, but can be 5Server-5.3.Z for z-stream.
    initStreamInfo(\%t);

    # Special handling for RHEL5 GA, since it's not on RHN Live yet.
    $t{tpsRhel5Live} = -1;
    if ($t{tpsProductRel} == 5) {
        if (exists($ENV{'RHEL5LIVE'})) {
            $t{tpsRhel5Live} = $ENV{'RHEL5LIVE'};
        }
    }
    $t{tpsRhel6Live} = -1;
    if ($t{tpsProductRel} == 6) {
        if (exists($ENV{'RHEL6LIVE'})) {
            $t{tpsRhel6Live} = $ENV{'RHEL6LIVE'};
        }
    }
    if (($t{tpsRhel6Live} == 0) && ($t{tpsProductRel} == 6)) {
	if (exists($ENV{'G_SLICE'})) {
	    delete $ENV{'G_SLICE'};
	}
    }

    ## Handle variances in Yum, Up2date, and RHN
    $t{tpsHasYum} = (( -x '/usr/bin/yum' ) ? 1 : 0);
    # Use yum if (a) it's present and (b) Distro is Fedora or RHEL >=5.
    $t{tpsUseYum} = 0;
    if (($t{tpsHasYum}) &&
        (($t{tpsProductFam} eq 'Fedora') || ($t{tpsProductFam} eq 'RHGD') ||
         (($t{tpsProductFam} eq 'RHEL') && ($t{tpsProductRel} >= 5)))) {
        $t{tpsUseYum} = 1;
    }

    # Grab all the info we need from local repos
    initRepoChannelInfo(\%t);

    # Default Yum values
    $t{tpsRelyOnRHNLive} = 1;
    $t{tpsReposLive} = '';
    $t{tpsReposQA} = '';
    if ($t{tpsUseYum} != 0) {
        # Only use yum to determine the exclusion list... if we're using yum. :)
        $t{tpsReposLive} = disableLocalRepoList(\%t);
        $t{tpsReposQA} = disableLocalRepoList(\%t);
    }
    $t{tpsYumPluginsLive} = '';  # eg, do not use --noplugins by default
    $t{tpsYumPluginsQA} = '';  # eg, do not use --noplugins by default
    # At GA, we expect that yum downloading of src.rpms will fail.
    # Set to 0 if srpm downloads should succeed.
    $t{tpsNoYumSource} = 1;
    $t{tpsNoYumSource} = $ENV{TPS_NO_YUM_SOURCE} if (exists($ENV{TPS_NO_YUM_SOURCE}));
    $t{yumArchList} = '';  # for yumdownloader, fill in later if needed.

    # Spool dir for yum/up2date tests
    $t{rhnSpoolDir} = '/var/spool/up2date';

    # RHEL5-GA special casing
    # NB: if the product is >= 5, and "tpsRhel5Live" is 0: tpsIsPreRelease is set. 
    # This triggers all the rules about which RHNs/Repos are okay, etc.
    # it doesn't literally *have* to be RHEL-5....
    if ((($t{tpsProductFam} eq 'RHEL') && ($t{tpsProductRel} >= 5)) &&
        ($t{tpsRhel5Live} eq '0')) {
	$t{tpsIsPreRelease} = 1;
        $t{tpsRelyOnRHNLive} = 0;
	## these 2 are now set by ensureInit:
        ##  $t{tpsReposLive} = '--enablerepo=*';
        ##  $t{tpsReposQA} = '--disablerepo=*';
        # THE FOLLOWING DISABLES TALKING TO RHN-LIVE
        $t{tpsYumPluginsLive} = '--noplugins';
    }

    # Modules, Tests, and ErrorMsg Buffers
    $t{'tpsErrorText'} = \$tpsErrorText;
    $t{testFunctionList} = \@testFunctionList;
    $t{testFunctionUserNames} = \@testFunctionUserNames;
    $t{verbose} = 0;
    if (exists($ENV{'VERBOSE'}) and (1 == $ENV{'VERBOSE'})) {
        $t{verbose} = 1;
    }
    $t{tmpStderr} = 0;

    # Package Lists: hashrefs of hashrefs.
    my (%g_pkgLists,%g_pkgStates,%g_oldPkgStates);
    $t{g_PkgLists} = \%g_pkgLists;
    $t{g_PkgStates} = \%g_pkgStates;
    $t{g_PkgOldStates} = \%g_oldPkgStates;
    $t{haveFileLists} = 0;

    # Misc settings: sudo
    my $whoiam = `whoami`;
    chomp $whoiam;
    $t{tpsSudo} = 'sudo';
    $t{tpsSudo} = '' if ($whoiam eq 'root');

    # Arch info -- both family (uname -i) and true (uname -m)
    initArchInfo(\%t);

    # Package-specific stuff, can be filled in once we know what we are testing.
    $t{multiVersionOK} = 0;  # okay to install multiple versions?

    ## Kernel Handling
    $t{isKernel} = 0;        # is this the kernel?
    my $uname_r = `uname -r`;
    chomp $uname_r;
    $t{runningKernelRpm} = '';
    if (-f "/boot/vmlinuz-$uname_r") {
        $t{runningKernelRpm} = `rpm -q --qf '%{name}-%{version}-%{release}.%{arch}.rpm' -f /boot/vmlinuz-$uname_r`;
    } elsif (-f "/boot/vmlinux-$uname_r") {
        $t{runningKernelRpm} = `rpm -q --qf '%{name}-%{version}-%{release}.%{arch}.rpm' -f /boot/vmlinux-$uname_r`;
    }
    chomp($t{runningKernelRpm});
    # We will try only to install new kernels unless tps_upgrade_kernel is set.
    # If it is, we'll try to update/upgrade them instead.
    $t{useUpgradeOnKernel} = 0;
    if (exists($ENV{'TPS_UPGRADE_KERNEL'})) {
        $t{useUpgradeOnKernel} = 1 if ($ENV{'TPS_UPGRADE_KERNEL'} =~ m/true/i);
    }

    # Is this a new package release?
    $t{isNewPackage} = 0;
    if ((exists($ENV{'TPS_NEWPKGRELEASE'})) && ($ENV{'TPS_NEWPKGRELEASE'} eq 'true')) {
        $t{isNewPackage} = 1;
    }

    # Readelf stuff
    my $elf_cmd = `/usr/bin/which eu-readelf 2>/dev/null`;
    if ($? ne 0) {
        $elf_cmd = `/usr/bin/which readelf 2>/dev/null`;
        if ($? ne 0) {
            $elf_cmd = '';
        }
    }
    chomp($elf_cmd);
    $t{readelf} = $elf_cmd;

    # SELinux stuff
    $t{selinux_ok} = 0;
    $t{selinux_state} = 'not present';
    $t{restorecon_ok} = 0;
    my %selin_setup;
    my %selin_teardown;
    $t{selin_set_bools} = \%selin_setup;
    $t{selin_unset_bools} = \%selin_teardown;

    my $restorecon = `/usr/bin/which restorecon 2>/dev/null`;
    if ($? ne 0) {
        $restorecon = '/sbin/restorecon';
    }
    chomp($restorecon);
    $t{selinux_restorecon} = $restorecon;
    $t{restorecon_ok} = 1 if (($restorecon) && (-x $restorecon));

    $t{selin_setbool} = '';
    my $setbool = `/usr/bin/which setsebool 2>/dev/null`;
    if ($? == 0) {
        chomp($setbool);
        $t{selin_setbool} = $setbool;
    }
    $t{selin_getbool} = '';
    my $getbool = `/usr/bin/which getsebool 2>/dev/null`;
    if ($? == 0) {
        chomp($getbool);
        $t{selin_getbool} = $getbool;
    }

    $selinuxCmd = `/usr/bin/which selinuxenabled 2>/dev/null`;
    $selinuxCmd = $selinuxCmd_d if ($? ne 0);
    chomp($selinuxCmd);

    $selinuxEnfCmd = `/usr/bin/which getenforce 2>/dev/null`;
    $selinuxEnfCmd = $selinuxEnfCmd_d if ($? ne 0);
    chomp($selinuxEnfCmd);

    if (-x $selinuxCmd) {
        `$selinuxCmd >/dev/null 2>&1`;
        $se_rc = $?;
        if ($se_rc ne 0) {
            $t{selinux_state} = 'disabled';
        } else {
            $t{selinux_state} = 'enabled';
        }
    }
    my $selin_mode = "unknown\n";
    if (-x $selinuxEnfCmd) {
        $selin_mode = `$selinuxEnfCmd 2>&1`;
        chomp($selin_mode);
    }
    $t{selinux_mode} = $selin_mode;
    $t{selinux_ok} = 1 if ($t{selinux_state} eq 'enabled');

    # auditd stuff
    my $ok_ausearch = 0;
    my $ausearch = `/usr/bin/which ausearch 2>/dev/null`;
    if ($? ne 0) {
        if (-x '/sbin/ausearch') {
            $ausearch = '/sbin/ausearch';
            $ok_ausearch = 1;
        } else {
            $ausearch = '';
        }
    } else {
        $ok_ausearch = 1;
    }
    chomp($ausearch);
    $t{ausearch} = $ausearch;
    $t{ausearch_ok} = $ok_ausearch;
    $t{avc_time} = avc_timestamp();
    $t{perl_time} = time();

    $t{aud_state} = 'missing';
    if ( -f $aud_init ) {
        $aud_state = `/sbin/service auditd status 2>&1 | grep -sie stopped || echo running`;
        $aud_state = 'stopped' if ($aud_state =~ m/stopped/i);
    }
    # kludge for when modules include this library, in hopes of a global $globs.
    if (exists($t{globs})) {
        ${$t{globs}} = \%t;
        $globs = ${$t{globs}};
    }

    return \%t;
}
# Some items in $globs are highly useful whether you need everything
# in Init or not.  Thus the following...
sub initProductInfo {
    my ($t) = @_;
    if ((!exists($t->{'tpsProductVer'})) || !($t->{'tpsProductVer'})) {
        $t->{'tpsProductVer'} = `( rpm -q --provides --whatprovides redhat-release | grep '^system-release.releasever.' || rpm -q --qf '%{version}' --whatprovides redhat-release ) | awk '{ print \$NF }'`;
        chomp($t->{'tpsProductVer'});
        # FIXME: if anything ever expects something like redhat-release-server-6Server 
        # in tpsProductFrom, it needs to be updated like ProductVer for RHEL7+ compat.
        $t->{'tpsProductFrom'} = `rpm -q --qf '%{NAME}-%{VERSION}' --whatprovides redhat-release`;
        $t->{'tpsProductFam'} = 'RHEL';
        if ($t->{tpsProductVer} =~ m/^\s*\d+\s*$/) {
            if ($t->{'tpsProductFrom'} =~ m/fedora/i) {
                $t->{'tpsProductFam'} = 'Fedora';
            } elsif ($t->{'tpsProductFrom'} =~ m/rhgd-/i) {
                $t->{'tpsProductFam'} = 'RHGD';
            } else {
                $t->{'tpsProductFam'} = 'unknown';
            }
        }
    }
    if ($t->{tpsProductVer} =~ m/^\s*2\.1(\S+)$/) {
        $t->{tpsProductRel} = 2.1;
        $t->{tpsProductVariant} = $1;
        $t->{is21} = 1;
    } elsif ($t->{tpsProductVer} =~ m/^\s*(\d+)(\S+)$/) {
        $t->{tpsProductRel} = $1;
        $t->{tpsProductVariant} = $2;
    } elsif ($t->{tpsProductVer} =~ m/^\s*(\d+)$/) {
        $t->{tpsProductRel} = $1;
    }
    $t->{tpsNoSig} = ((1 == $t->{is21}) ? '' : '--nosignature');
    return $t;
}
sub initArchInfo {
    my ($t) = @_;
    # Architecture Family (uname -i)
    unless ((exists($t->{arch})) && ($t->{arch})) {
        if (exists($ENV{'ARCH'})) {
            $t->{arch} = $ENV{'ARCH'};
        } else {
            my $tpsarch = `uname -i 2>/dev/null || uname -m`;
            chomp $tpsarch;
            $tpsarch =~ s/i[3-6]86/i386/;
            unless (($tpsarch =~ m/le/i) || ($t->{tpsProductRel} >= 6)) {
                $tpsarch =~ s/ppc64/ppc/;
            }
            $t->{arch} = $tpsarch;
        }
    }

    # True arch (uname -m)
    unless ((exists($t->{trueArch})) && ($t->{trueArch})) {
        if (exists($ENV{'TRUE_ARCH'})) {
            $t->{trueArch} = $ENV{'TRUE_ARCH'};
        } else {
            my $ta = `uname -m`;
            chomp $ta;
            $t->{trueArch} = $ta;
        }
    }
    return $t;
}
sub initStreamInfo {
    my ($t) = @_;
    my $stream = `source /etc/sysconfig/oats.conf >/dev/null 2>&1 && echo \$STREAM`;
    my $streamExt = `source /etc/sysconfig/oats.conf >/dev/null 2>&1 && echo \$STREAMEXT`;
    chomp($stream);
    chomp($streamExt);
    $t->{tpsProductStream} = $stream;  # possibly '' or undef or "0"
    $t->{tpsProductStreamExt} = $streamExt || 'Z';
    if ((defined($stream)) && (length($stream) > 0)) {
        $t->{tpsETRelease} = $t->{tpsProductVer} .'-'. $t->{tpsProductRel} .'.'. $stream .".$t->{tpsProductStreamExt}";
    } else {
        $t->{tpsETRelease} = $t->{tpsProductVer};
    }

    # Tps-server settings, if not already present, and if available.
    # TPSD_TPSS_CONF: TPSD_stream TPSD_test_profile TPSD_stable TPSD_dedicated TPSD_dist_method_name
    unless ((exists($t->{tpsStream})) && ($t->{tpsStream})) {
        if (!exists($ENV{TPSD_stream})) {
            my $conf = ($ENV{TPSD_TPSS_CONF} || '/var/cache/tps/settings/tps_server.conf') . '.sh';
            if (-r $conf) {
                if (open(IN,"<$conf")) {
                    my ($ln, $varname, $val);
                    while (defined($ln = <IN>)) {
                        chomp $ln;
                        if ($ln =~ m#\s*([^=]+)="([^"]+)"#) {
                            $varname = $1;
                            $val = $2;
                            $ENV{$varname} = $val;
                        }
                    }
                    close(IN);
                }
            }
        }
        # TPSD_stream TPSD_test_profile TPSD_stable TPSD_dedicated TPSD_dist_method_name
        if (exists($ENV{TPSD_stream})) {
            $t->{tpsStream}      = ($ENV{TPSD_stream} || '');
            $t->{tpsTestProfile} = ($ENV{TPSD_test_profile} || ''); 
            $t->{tpsStable}      = ($ENV{TPSD_stable} || '');
            $t->{tpsDedicated}   = ($ENV{TPSD_dedicated} || '');
            $t->{tpsDistMethod}  = (lc($ENV{TPSD_dist_method_name}) || '');
        }
    }
    if (exists($ENV{TPS_DIST_METHOD}) && ($ENV{TPS_DIST_METHOD})) {
        if (!exists($t->{tpsDistMethod}) || !($t->{tpsDistMethod})) {
            $t->{tpsDistMethod} = lc($ENV{TPS_DIST_METHOD});
        }
    } else {
        if (exists($t->{tpsDistMethod}) || ($t->{tpsDistMethod})) {
            $ENV{TPS_DIST_METHOD} = $t->{tpsDistMethod};
        } else {
            # fix uninitialized variable msg that otherwise happens
            $t->{tpsDistMethod} = '';
        }
    }

    return $t;
}
# Some items in $globs are not filled out right away, since they
# may interfere with other work on a shared system.  This includes
# anything that checks repos via yum.  The following routine
# can handle any number of these critters...
# Use: either: ensureInit($globs) for all delayed values,
# or ensureInit($globs, ['item1', ... , 'itemN']) for specific
# items.
sub ensureInit {
    my ($globPtr,$delayListRef) = @_;
    $delayListRef = $globPtr->{delayInitItems} if (!defined($delayListRef));

    foreach my $varr (@$delayListRef) {
	if ($varr eq 'tpsReposLive') {
	    if ($globPtr->{tpsIsPreRelease}) {
		# use on-disk repos until RHN is populated...
		$globPtr->{tpsReposLive} = '--enablerepo=*';
	    } else {
		$globPtr->{tpsReposLive} = disableLocalRepoList();
	    }
	} elsif ($varr eq 'tpsReposQA') {
	    if ($globPtr->{tpsIsPreRelease}) {
		# Do not use repos...
		$globPtr->{tpsReposQA} = '--disablerepo=*';
	    } else {
		$globPtr->{tpsReposQA} = disableLocalRepoList();
	    }
	}
    }
}
sub initRepoChannelInfo {
    my ($t) = @_;
    my $def_repo_name = 'tps-profile.repo';

    $t->{tpsAllowLocalRepos} = 0;
    if (exists($ENV{TPS_ALLOW_LOCAL_REPOS}) && ($ENV{TPS_ALLOW_LOCAL_REPOS})) {
        $t->{tpsAllowLocalRepos} = 1 if ('true' eq $ENV{TPS_ALLOW_LOCAL_REPOS});
    }
    $t->{tpsProfileRepo} = '';
    if (exists($ENV{TPS_PROFILE_REPO}) && ($ENV{TPS_PROFILE_REPO})) {
        $t->{tpsProfileRepo} = $ENV{TPS_PROFILE_REPO};
    } else {
        # Current profile repo, can be live or qa...
        $t->{tpsProfileRepo} = "/etc/yum.repos.d/${def_repo_name}";
    }
    $t->{tpsRepoFileLive} = "/etc/sysconfig/rhn.live/${def_repo_name}";
    $t->{tpsRepoFileQA} = "/etc/sysconfig/rhn.live/${def_repo_name}";
    my @repo_files = glob('/etc/yum.repos.d/*.repo');
    # All current local repos
    $t->{tpsRepoChannels} = {};
    reposToHash($t->{tpsRepoChannels}, \@repo_files);
    # Profile repos for Live
    $t->{tpsRepoChannelsLive} = {};
    reposToHash($t->{tpsRepoChannelsLive}, [ $t->{tpsRepoFileLive} ]);
    # Profile repos for Current
    $t->{tpsRepoChannelsProfile} = {};
    reposToHash($t->{tpsRepoChannelsProfile}, [ $t->{tpsProfileRepo} ]);
    # Profile repos for QA
    $t->{tpsRepoChannelsQA} = {};
    reposToHash($t->{tpsRepoChannelsQA}, [ $t->{tpsRepoFileQA} ]);
    # Non-Profile repos
    $t->{tpsRepoChannelsOther} = {};
    my @local_files = grep(!/^\Q$t->{tpsProfileRepo}\E/,@repo_files);
    reposToHash($t->{tpsRepoChannelsOther}, \@local_files);
}
sub reposToHash {
    my ($hr, $repoList) = @_;
    my ($ln, $tmp, $latest);
    return unless (scalar(@$repoList) > 0);
    foreach my $f (@$repoList) {
        if (open(IN, "<$f")) {
            while (defined($ln = <IN>)) {
                chomp($ln);
                if ($ln =~ m/^\[(.*)\]\s*$/) {
                    $latest = $1;
                    $hr->{$latest} = {};
                } elsif ($ln =~ m/^name\s*=\s*(.*)$/) {
                    $tmp = $1;
                    $hr->{$latest}->{name} = $tmp;
                    # Only do the translation for pulp repos
                    $hr->{$latest}->{idname} = '';
                    if ($tmp =~ m|/|) {
                        $tmp =~ s/\./_DOT_/g;
                        $tmp =~ s|/|__|g;
                        $hr->{$latest}->{idname} = $tmp;
                    }
                } elsif ($ln =~ m/^enabled\s*=\s*(.*)$/) {
                    $hr->{$latest}->{enabled} = $1;
                } elsif ($ln =~ m/^gpgcheck\s*=\s*(.*)$/) {
                    $hr->{$latest}->{gpgcheck} = $1;
                }
            }
            close(IN);
        }
    }
}
sub getChannelIDName {
    my ($chName, $ghr) = @_;
    my $ret = '';
    my $t = $ghr->{tpsRepoChannels};
    if (exists($t->{$chName})) {
        return ($t->{$chName}->{idname});
    }
    return($ret);
}
sub standardTpsIntro {
    my ($scriptName,$tpsVer,$hostName,$timeStamp,$autoOrManual,$runID,$jobID);
    $scriptName = $globs->{progName};
    $tpsVer = $globs->{'tpsRpmVersion'};
    $hostName = $globs->{'hostInfo'};
    $timeStamp = `date`; chomp($timeStamp);
    $autoOrManual = 'Manual run';
    $runID = '';
    $jobID = '';
    if (1 == $globs->{'tpsAuto'}) {
        $runID = 'unknown';
        $jobID = 'unknown';
        $runID = $ENV{'TPSQ_RUNID'} if (exists($ENV{'TPSQ_RUNID'}));
        $jobID = $ENV{'TPSQ_JOBID'} if (exists($ENV{'TPSQ_JOBID'}));
        $autoOrManual = "Automated run (job: $jobID, run: $runID)";
    }
    doLog($TPSINFO,$TPSRPT,"$scriptName from $tpsVer -- $autoOrManual on $hostName on $timeStamp\n");
    doLog($TPSMISC,$TPSDEBUG,"Raw File Format: $globs->{tpsLoggingVersion}\n");
}

# Return true (1) if the provided string matches the form of
# a valid advisory number.  Optional second arg permits recognition
# of year-less format when set to 1.
sub isErrataString {
    my ($str, $yearless) = @_;
    return 1 if ($str =~ m/^\d\d\d\d:\d\d\d\d{1,2}$/);
    if (defined($yearless) && (1 == $yearless)) {
        # 4 or 5 digits
        return 1 if ($str =~ m/^\d\d\d\d{1,2}$/);
    }
    return 0;
}

# feed this thing a newPkgNamesListRef or an oldPkgNamesListRef and it'll
# check for known kernel-package names.  Sets multiVersionOK and isKernel globals
# and returns 1 if it's a kernel; does not set globals, and return 0, otherwise.
sub isKernel {
    my ($pkgListRef) = @_;
    my @kerns = qw( kernel kernel-smp kernel-hugemem kernel-pae kernel-xen rt-kernel kernel-rt cman-kernel cmirror-kernel dlm-kernel );

    foreach my $p (@$pkgListRef) {
        foreach my $k (@kerns) {
            if ($k eq $p) {
                $globs->{multiVersionOK} = 1;
                $globs->{isKernel} = 1;
                return 1;
            }
        }
    }

    return 0;
}

# Program that uses/requires us must provide a LOG and RPT filehandles
# for logs/reports.
#################################
# log#Print - print to logfile, and to stderr if debugging
sub logPrint {
    doLog($TPSMISC, $TPSLOG, @_);
    # print STDERR @_ if (exists($ENV{'VERBOSE'}) and (1 == $ENV{'VERBOSE'}));
}
#################################
# vlog#Print - print to logfile, and to stderr if debugging or requested
#  Inputs:  string(s), useStdErr
#  If useStdErr == 1, will print strings to STDERR as well as logfile.
sub vlogPrint {
    doLog($TPSTXT, $TPSLOG, @_);
    print STDERR @_ if ($globs->{isManual} != 0);
}
#######################
# rptPrint - print to report file, and to stdout
sub rptPrint {
    doLog($TPSMISC, $TPSRPT, @_);
    # print @_;
}

sub beginSubTest {
    my ($logStr) = @_;
    beginTest($logStr, 1);
}
sub beginTest {
    my ($logString,$isSubTest) = @_;
    my $stamp = avc_timestamp();
    my $hostInfo = $globs->{hostInfo};
    my $tType = $TPSBEGIN;
    my $globName = 'testName';
    my $s1 = '===';
    my $s2 = '=====================';
    my $tcount_glob = 1 + $globs->{'testCount'};
    $isSubTest = 0 if (!defined($isSubTest));

    $globs->{'testCount'} = $tcount_glob;
    if ($isSubTest) {
        my $cur_sub = 1 + $globs->{'curSubTestNumber'};
        $tType = $TPSSUBBEGIN;
        $globName = 'subName';
        $s1 =~ s/=/-/g;
        $s2 =~ s/=/-/g;
        $globs->{'inSubTest'} = 1;
        $globs->{'curSubTestNumber'} = $cur_sub;
    } else {
        my $cur_test = 1+ $globs->{'curTestNumber'};
        $globs->{'inTest'} = 1;
        # $globs->{'inSubTest'} = 0;  # should not be needed due to endTest manips.
        $globs->{'curTestNumber'} = $cur_test;
        $globs->{'curSubTestNumber'} = 0;
    }

    $tpsErrorText = '';
    $globs->{avc_time} = $stamp;
    $globs->{perl_time} = time();

    $globs->{$globName} = $logString;
    doLog($tType,$TPSLOG,"\n\n$s1 $logString $s2\n");
    doLog($TPSMISC,$TPSLOG,"begin at $stamp on $hostInfo\n\n");
}
sub endSubTest {
    my ($res,$logStr) = @_;
    endTest($res, $logStr, 1);
}
# endTest: run SELinux avc-check, report any failures, return results
sub endTest {
    my ($result, $logString, $isSubTest) = @_;
    my $stamp;
    my $hostInfo = $globs->{hostInfo};
    my $tType = $TPSEND;
    my $seBegin = $TPSSUBBEGIN;
    my $seEnd = $TPSSUBEND;
    my $globName = 'testName';
    my $s1 = '===';
    my $s2 = '=====================';

    if (!defined($isSubTest)) {
        $isSubTest = 0;
    }
    if ($isSubTest) {
        $tType = $TPSSUBEND;
        $seBegin = $TPSSUBBEGIN;
        $globName = 'subName';
        $s1 =~ s/=/-/g;
        $s2 =~ s/=/-/g;
    }

    # Restore any SELinux settings that the test changed.
    # Also clears said settings from tps's memory.
    selinux_RestoreAfterTest();

    $stamp = `date`;
    chomp($stamp);
    if (defined($result) && defined($logString)) {
        doLog($TPSMISC,$TPSLOG,"end test at $stamp on $hostInfo\n");
        doLog($tType,$TPSLOG,"TPSRESULT: ${logString} Returning: $result\n\n");
    }

    $globs->{'inSubTest'} = 0 if ($isSubTest);

    # Run selinux subtest if applicable
    $globs->{$globName} .= '-selinux';
    if (1 == $globs->{selinux_ok}) {
        my $tName = $globs->{$globName};
        my $resCnt = 0;

        my $cur_sub = 1 + $globs->{'curSubTestNumber'};
        $globs->{'inSubTest'} = 1;
        $globs->{'curSubTestNumber'} = $cur_sub;

        doLog($seBegin,$TPSLOG,"$s1 ${tName} Test $s2\n");
        my $se_res = avc_check();
        if ($se_res =~ m/(\S+)/) {
            $resCnt = length($1);
        }
        if (0 == $resCnt) {
            # endSubTest marker: PASS
            doLog($seEnd,$TPSLOG,"TPSRESULT: ${tName} Returning: PASS\n");
        } else {
            doLog($TPSFAILTXT,$TPSRPT,"SELinux Check: FAIL\n");
            doLog($TPSFAILTXT,$TPSLOG, "SELinux AVC messages found:\n${se_res}\n");
            doLog($TPSHINT,$TPSLOG,
                  ("TPSHINT: It is possible that other stable systems activity has caused this issue.\n" .
                   "If you are sure that this is the case, you may waive this failure.\n" .
                   "If you have any doubts, RE-RUN " . $globs->{progName} . " to be sure.\n")
                  );
            # endSubTest marker: FAIL
            doLog($seEnd,$TPSLOG,"TPSRESULT: ${tName} Returning: FAIL\n");
            $result = 'FAIL';
        }
        $globs->{subName} = '';
        $globs->{'inSubTest'} = 0;
    }
    # else... doLog($TPSINFO,$TPSDEBUG,"SKIPPED: Check-SELinux test / not available\n");

    $globs->{avc_time} = avc_timestamp();
    $globs->{perl_time} = time();

    if ($isSubTest) {
        $globs->{subName} = '';
    } else {
        $globs->{'inTest'} = 0;
        $globs->{'inSubTest'} = 0;
        $globs->{testName} = $globs->{progName};
    }
    return $result;
}

#########################
#  run_test / _subtest  #  Simplified wrappers for test & subtest invocations
#########################
#
# Return true on test success, false otherwise
#
sub run_test {
    my $coderef = shift;                # in: function to invoke
    my $blurb   = shift;                # in: one-liner test name
    my $tip     = shift;                # in: multi-line test descr. (optional)

    beginTest($blurb);
    doLog($TPSTIP, $TPSLOG, $tip)       if $tip;
    my $result = $coderef->();
    return (endTest($result, $blurb) eq 'PASS');
}

sub run_subtest {
    my $coderef = shift;                # in: function to invoke
    my $blurb   = shift;                # in: one-liner test name
    my $tip     = shift;                # in: multi-line test descr. (optional)

    beginSubTest($blurb);
    doLog($TPSTIP, $TPSLOG, $tip)       if $tip;
    my $result = $coderef->();
    return (endSubTest($result, $blurb) eq 'PASS');
}

#######################
# logTestFatal - ensure that fatal errors are presented in the context
# of a test.  In short, if we're in a test/subtest, print out the
# message and end the test (or subtest) normally; the caller is expected to
# exit.  If we are not in a test, create a 'Fatal Error' test, print
# out the message, and end the test without the usual SELinux subtest.
# Again, the caller is expected to close logs & exit after making this call.
# Inputs:
#   msg -  text that explains the fatal error.  Anything in tpsErrorText will
#          also be used.
#  mType - message type, default TPSFATAL.
#  mLevel- message level, default TPSCRIT.
sub logTestFatal {
    my ($msg,$mType,$mLevel) = @_;
    my $tcount_glob = $globs->{'testCount'};
    my $createNewTest = 1;
    my $tName = 'Fatal Error';
    my $endType = $TPSEND;
    my $isSubTest = 0;

    $mType  = $TPSFATAL if (!defined($mType));
    $mLevel = $TPSCRIT  if (!defined($mLevel));

    # detect/setup for existing test
    if ($globs->{inTest}) {
        $createNewTest = 0;
        $tName = $globs->{testName};
    } elsif ($globs->{inSubTest}) {
        $createNewTest = 0;
        $tName = $globs->{subName};
        $endType = $TPSSUBEND;
        $isSubTest = 1;
    }

    # proper bookkeeping for a new test
    if ($createNewTest) {
        $tcount_glob++;
        $globs->{testCount} = $tcount_glob;
        $globs->{inTest} = 1;
        $globs->{testName} = $tName;
        doLog($TPSBEGIN,$TPSLOG,"=== $tName =======\n");
    }

    # Output relevant messages
    if (defined($tpsErrorText) && (length($tpsErrorText) > 0)) {
        doLog($TPSTXT,$TPSLOG,$tpsErrorText);
    }
    doLog($mType,$mLevel,$msg);

    if ($createNewTest) {
        $stamp = `date`;
        chomp($stamp);
        doLog($TPSMISC,$TPSLOG,"end test at $stamp on $globs->{hostInfo}\n");
        doLog($endType,$TPSLOG,"TPSRESULT: Fatal Error: FAIL\n\n");
        $globs->{inTest} = 0;
        $globs->{testName} = ($globs->{progName});
    } else {
        endTest('FAIL',$tName,$isSubTest);
    }
    return 'FAIL';
}

#######################
# avc_timestamp - return timestamp in format suitable for ausearch
# Inputs: $thisStamp - epoch seconds such as from time(), or omit
#         to use the current localtime().
# Returns: formatted string with month day year hour minute second.
sub avc_timestamp {
    my ($thisStamp) = @_; # epoch number suitable for localtime()
    my ($sec,$min,$hour,$day,$mon,$year);

    # ausearch takes a DD/MM/YY HH:MM:SS time argument, so get localtime into that fmt.
    if (defined($thisStamp) && $thisStamp) {
        ($sec,$min,$hour,$day,$mon,$year,undef,undef,undef) = localtime($thisStamp);
    } else {
        ($sec,$min,$hour,$day,$mon,$year,undef,undef,undef) = localtime();
    }
    $mon++;
    $year += 1900;
    #$year %= 2000;
    my $avctime = sprintf("%02d/%02d/%d %02d:%02d:%02d", $mon,$day,$year,$hour,$min,$sec);
    return $avctime;
}
#######################
# avc_check - check for SELinux 'avc denied' messages since $lastTime
# Inputs: $lastTime - time such as obtained from avc_timestamp();
# Note: caller is presumed to have checked whether SELinux is present.
sub avc_check {
    my ($lastTime) = @_; # was error/log file, dmesg_file
    my $results = '';
    my $opts_ausearch = '-sv no -m AVC -ts';
    my $perlTime = $globs->{perl_time};
    if (!defined($lastTime) || !($lastTime)) {
        $lastTime = $globs->{avc_time};
        if (!defined($lastTime) || !($lastTime)) {
            $lastTime = avc_timestamp();
            $perlTime = time();
        }
    }
    my $ausearch = ($globs->{tpsSudo} ? "$globs->{tpsSudo} $globs->{ausearch}" : $globs->{ausearch});
    doLog($TPSMISC,$TPSDEBUG,"Really using $ausearch\n");
    # alternatively $mtime = ${stat(file)}[9]; (epoch seconds)
    if (($globs->{ausearch_ok}) && ($ausearch)) {
        doLog($TPSCMD,$TPSLOG,"Running: $ausearch  $opts_ausearch  $lastTime \n");

        # Note: ausearch limits you to a 2-digit year in LANG=C.  Use en_US just for this.
        $ENV{LANG} = 'en_US';
        $results .= `$ausearch  $opts_ausearch  $lastTime 2>&1`;
        $rc = $?; # ausearch returns non-zero in many non-error conditions. Ignore.
        $ENV{LANG} = 'C';

        # if ($rc ne 0) {
        #   print STDERR "$ausearch returned $rc : $result\n";
        # }
        # In theory, ausearch returns 0 if a match is found, else 0.
        # If a match is not found, it prints '<no matches>'.
        $results =~ s/<no matches>//;
    }

    # Looking for stuff like so:
    # Aug 14 15:02:54 s390x-4as kernel: audit(1155582172.307:211): avc:  denied  { read } for  \
    # pid=8036 comm="rndc" name="ypserv-2.13-14.s390x.rpm" dev=dm-0 ino=1895255 \
    # scontext=root:system_r:ndc_t tcontext=root:object_r:var_spool_t tclass=file

    # Check output of dmesg as well.
    my @dmResults = ();
    my $dm_res = `dmesg | /bin/grep avc | /bin/grep -v granted`;
    # $rc = $?;
    if ($dm_res =~ m/ avc/) {
        my @dm_resA = split("\n",$dm_res);
        # print STDERR "split got $#dm_res \n";
        my $n = 0;
        foreach my $l (grep('audit\(\d+\.\d+:\d+\):\s+avc:\s+denied',@dm_resA)) {
            if ($l =~ m|audit\((\d+)\.\d+:\d+\):\s+avc:\s+denied|) {
                push @dmResults, $l if ($1 >= $perlTime);
                $n++;
            }
        }
        # print STDERR "Found $n dmesg lines\n";
        if ($#dmResults >= 0) {
            $results .= join("\n",@dmResults);
            $results .= "\n";
        }
    }

    return $results;
}
###############################################
# seRpmCheck - given the name (or nvra) of an installed package, check it for selinux context errors
# Returns array:
#    0 if a clean run, 1 if restorecon produced output
#    output from restorecon (possibly voluminous)
sub seRpmCheck {
    my ($pkgname) = @_;
    my $returnVal = 1; # error value

    my $output = `rpm -ql "$pkgname" | restorecon -n -vv -f - 2>&1`;
    my $o_rc = $?;  # exit code of restorecon operation above
    my $o_err = $!; # any text message if $? != 0.

    chomp $output;
    @outputLines = split(/\n/,$output);
    my $lineCount = $#outputLines + 1;

    $returnVal = 0 if (0 == $lineCount);

    return($returnVal, $output);
}
###############################################
# fileToListRef - return reference to list of individual lines of a
#  file (or files) without trailing newlines .
#  Skips any blank lines or commented-out (#) ones.
sub fileToListRef {
    my @fileNames = @_;
    my @lst = ();
    my $ln;

    foreach my $filename (@fileNames) {
	next if ((!defined($filename)) || ($filename =~ m/^\s*$/));
	next if ((! -r $filename) || (-z $filename));

	open(_FTLR,"<$filename") || do {
	    doLog($TPSMISC,$TPSLOG,"fileToListRef: cannot open $filename for read\n");
	    next;
	};
	while (defined($ln = <_FTLR>)) {
	    chomp $ln;
	    # skip blank lines
	    next if ($ln =~ m/^\s*$/);
	    # skip lines that start with a hash (comment)
	    next if ($ln =~ m/^\s*\#/);
	    push @lst, $ln;
	}
	close(_FTLR);
    }
    return \@lst;
}
###################################
# hasOnlyDepFailure - given some rpmOutput that contains a failure, try to figure out
# whether the failure was due only to dependencies.  When deleting a package, such
# a failure is expected and okay.  Returns the number of dependencies found, or
# 0 if dependencies were not the (only) cause for the failure.
#
# Future: should check to see that the dependencies are kosher -- that
# is, not contained in the errata's packages, but caused by other legitimately installed packages.
# Could also return the names of the packages and requirements, if desired.  Right now
# that info is collected but not returned...
sub hasOnlyDepFailure {
    my ($rpmOut) = @_;
    my $ret = 0;
    # my %depPkgs;
    # my %reqItems;
    my $rpmCpy;

    if (($rpmOut =~ m/error:*\s+failed\s+dependencies:*/i) ||
        ($rpmOut =~ m/error:*\s+removing these packages would break dependencies:*/i)) {
        $rpmCpy = $rpmOut;
        $rpmCpy =~ s/error:*\s+failed\s+dependencies:*//i;
        $rpmCpy =~ s/error:*\s+removing these packages would break dependencies:*//i;
        # now figure out what unique things are required by which packages:
        while (($rpmCpy =~ s/(\S+)(\s+>=*\s+\S+)*\s+is needed by .installed. (\S+)//) ||
               ($rpmCpy =~ s/(\S+)(\s+>=*\s+\S+)*\s+is needed by\s+(\S+)//)) {
            # $reqItems{$1} = 1;
            # $depPkgs{$2} = 1;
            $ret++;
        }
        if ($rpmCpy =~ m/error:*\s+(.*)/i) {
            # For other errors, do NOT return 1,
            # since we're trying to guarantee only a dependency failure error.
            $ret = 0;
            doLog($TPSMISC,$TPSLOG,"RpmError: $1\n");
        }
    }
    return $ret;
}
##############################
# deleteExtraPackages -- on downgrade, delete any new packages that weren't in the old set.
# Inputs: newSet: (new packages) hashref of "name.arch" => NVR info
#         oldSet: (old packages) hashref of "name.arch" => NVR info
# Outputs: Output of rpm deletion command, or empty string if N/A.
#
sub deleteExtraPackages {
    my ($newSet,$oldSet,$hr) = @_;
    my @nukeThese;
    my ($hack21,undef) = handleAS21hack();
    my $h3;

    # First, locate any "name.arch" combos that are
    # in the new package set but weren't in the old.
    foreach my $nameArch (keys(%{$newSet})) {
        if (!exists($oldSet->{$nameArch})) {
            foreach my $k (keys(%$hr)) {
                $h3 = $hr->{$k};
                next unless (exists($h3->{na}) && ($h3->{na} eq $nameArch));
                if (exists($h3->{new}) && (exists($h3->{n})) && (exists($h3->{inst}))) {
                    if ((1 == $h3->{new}) && (1 == $h3->{inst})) {
                        push @nukeThese, ($hack21 ? $h3->{n} : $nameArch);
                    }
                }
            }
        }
    }
    my $rpmOut = '';
    if ($#nukeThese >= 0) {
        my $fileList = join(' ',@nukeThese);
        doLog($TPSINFO,$TPSDEBUG,"Deleting using nodeps: $fileList \n");
        $rpmOut = doRpmCommand("rpm -e --nodeps $fileList");
    }
    # else there was nothing to delete

    return $rpmOut;
}

############################################################
# makeArchList -- goes through a hashref and returns a unique listref of arches it found
#   Used on the output of pkgListToNVR(newfiles) to figure out what arches to try
#   to rebuild SRPMs for.  (see $rpm_arch in the Rebuild() routine)
#   Also used to figure out how to ask up2date to install multilib packages.
sub makeArchList {
    my ($nvrRef) = @_;
    my %nvrs = %{$nvrRef};
    my (%tmp, $a);
    my @arches = ();
    foreach my $i (keys(%nvrs)) {
        my (undef,undef,undef,$a,undef,undef,undef) = split /\n/, $nvrs{$i}, 7;
        $tmp{$a} = 1;
    }
    foreach my $i (keys(%tmp)) {
        # the arch is the keyname; the value is always 1.
        push @arches, $i;
    }
    return \@arches;
}


#############################################
# doRpmCommand - actually, sudo any command and return stderr/stdout in a scalar.
#  Note that multi-line returns are possible.
#  Inputs:
#     command  -- command to execute. Preferred form is a list of tokens,
#                 eg ('rpm', '-qp', ...) but we also accept a single string
#                 eg  'rpm -qp ...'.
#  Returns the combined stdout and stderr from the command. Also does
#  some logging.
#
sub doRpmCommand {
    my @command = @_;

    # We tend to use newlines in the query formats,
    # so make them nicer/more compact in the logfile:
    (my $command_string = "@command") =~ s/\n/\\n/g;

    # Query of packages is noise for most people.
    my $sevLevel = $TPSLOG;
    if ($command_string =~ m/\s+-qp*\s+/) {
        $sevLevel = $TPSNOISE;
    }

    # Almost everything needs sudo. 'rpmbuild --rebuild' does not.
    # Be careful when adding sudo: handle both list & shell-string forms
    unless ($command_string =~ /rpmbuild\s+--rebuild/) {
        if (my $sudo = $globs->{tpsSudo}) {
            # 'rpm -qp -foo -bar' becomes 'sudo rpm -qp -foo'
            if (@command == 1 && $command_string =~ /\s/) {
                $command[0] = "$sudo $command[0]";
            } else {
                # ('rpm', '-qp', '-foo')  -> ('sudo', 'rpm', '-qp', '-foo')
                unshift @command, $sudo;
            }
        }
    }

    doLog($TPSCMD,$sevLevel,"doRpmCommand: $command_string\n");

    # Run the command, and slurp in its output.
    my ($pid, $cmd_in, $cmd_output);
    eval { $pid = open3( $cmd_in, $cmd_output, undef, @command) };
    if ($@) {
        return "doRpmCommand Error: $@ \n";
    }

    close $cmd_in;
    my $result = do { local $/ = undef; <$cmd_output>; };
    waitpid( $pid, 0 );

    my $printMe = $result;
    $printMe =~ s/\n/ /g if $command_string =~ /\s+-qp*\s+/;

    # Set global variable so that test modules can further
    # diagnose any errors that come from rpm.
    if ($?) {
        $tpsErrorText .= $result;
    }

    doLog($TPSCMDOUT,$sevLevel,"doRpmCommand-result ($?): $printMe\n");
    return $result;
}

############################
# nvraConvert - go from newline-separated NVRA to dash/dot-separated + sigmd5
sub nvraConvert {
    my ($in) = @_;
    # last 2 items are Epoch and SourceRPM
    my ($name,$ver,$rel,$arch,$sum,undef,undef) = split /\n/, $in, 7;
    return ("${name}-${ver}-${rel}.${arch}", $sum);
}
sub nvrasepConvert {
    my ($in) = @_;
    # last 2 items are Epoch and SourceRPM
    my ($name,$ver,$rel,$arch,$sum,$e,$srpm) = split /\n/, $in, 7;
    chomp($srpm);
    return("${name}-${ver}-${rel}.${arch} $sum $e $srpm");
}
############################
# nvrToHRef - go from newline-separated NVRASEP to a hash ref.
sub nvrToHRef {
    my ($in) = @_;
    my ($name,$ver,$rel,$arch,$sum,$ep,$srpm) = split /\n/, $in, 7;
    chomp($srpm) if (defined($srpm));
    my %out = ( 'name' => $name,
                'ver'  => $ver,
                'rel'  => $rel,
                'arch' => $arch,
                'sum'  => $sum,
                'epoch' => (defined($ep) ? $ep : "0"),
                'srpm' => (defined($srpm) ? $srpm : ""),
                );
    # We use the :? for backwards compatibility...
    return \%out;
}
###########################
# pkgNamesToPkgNVRs
# Given:
#  nameString - yum/up2date-friendly string of package names for updating
#  nvrHashRef - typical newPkgHRef from FILES_OUT
# Do:
#  Generate a string of packageName-version-release for yum's use.
# Returns:
#    (string, nvraListRef, naListRef)
# Typical use: create a package list for yum installs; one that
# uses Name-Version-Release.Arch or Name-Version-Release.
#
sub pkgNamesToPkgNVRs {
    my ($nameString, $nvrRef) = @_;
    my @nvrs;
    my $ret = '';
    my @nvraList;
    my @naList;
    my %seen;
    foreach my $k (keys(%$nvrRef)) {
	push @nvrs, nvrToHRef($nvrRef->{$k});
    }
    foreach my $nm (split(/\s+/,$nameString)) {
	foreach $item (@nvrs) {
	    if ($nm eq $item->{name}) {
		$nameVerRel = "$item->{name}-$item->{ver}-$item->{rel}";
		$nameVerRelArch = "${nameVerRel}.$item->{arch}";
		$ret .= " $nameVerRel" unless (exists($seen{$nameVerRel}));
		$seen{$nameVerRel} = 1;
		push @naList, "$item->{name}.$item->{arch}";
		push @nvraList, $nameVerRelArch;
	    }
	}
    }
    return ($ret,\@nvraList,\@naList);
}

###########################
# pkgListByKey - create hashref ordered by given key
# Runs nvrToHRef on each package in $href, and creates a
# new hash.  The keys to this new hash are as specified by $keyname.
# Each hash value is a reference to an array of hashrefs of matching
# packages.  For instance, calling pkgListByKey on $newPkgNVRhref with
# a keyname of 'srpm' will yield a ref to a hash of all source rpms
# (keys: source rpm names).  The hash values are a reference to an array
# of nvrToHRef values, representing the info for all binary RPMs built
# from the Source RPM in question.
# Inputs:
#   href   = reference to package list
#  keyname = name of key to index by, as found in nvrToHRef.  Currently, one of:
#    name, ver, rel, arch, sum, epoch, srpm.
#  FIXME: Some error-checking code would make this function a lot more forgiving.
sub pkgListByKey {
    my ($href,$keyname) = @_;
    my ($hr, $newName, %foundRpms, $nn);
    foreach my $i (keys(%$href)) {
        $hr = nvrToHRef($href->{$i});
        $nn = ( $hr->{name} . '-' . $hr->{ver} . '-' .
                $hr->{rel} . '.' . $hr->{arch} . '.rpm' );
        $hr->{fullname} = $nn;
        $newName = $hr->{$keyname};
        if (!exists($foundRpms{"$newName"})) {
            my @arr = ();
            $foundRpms{"$newName"} = \@arr;
        }
        push @{$foundRpms{"$newName"}}, $hr;
    }
    return(\%foundRpms);
}
###################################################
# listInclude - list.include?(list,item)
# think of array.include?(item), but this is perl, not ruby,
# so listInclude(list,item) it is...
sub listInclude($$) {
    my ($lst,$what) = @_;
    foreach my $i (@$lst) {
	return 1 if ($i eq $what);
    }
    return 0;
}
###################################################
# exprListMatch
# Given a list of expressions, ask whether the 2nd arg matches
sub exprListMatch($$) {
    my ($lst,$what) = @_;
    foreach my $i (@$lst) {
	return 1 if ($what =~ m/$i/);
    }
    return 0;
}

###################################################
# getPkgHashKeyedByChannels
# Fetch list of old|new packages from ET as
# a hash (keyed by channels), with entries which are
# list references containing the /full/rpm/names.
# DEBUG FEATURES:
#   If TPSDEBUG_SAVE_ET_PKGS is set, the returns from ET will be saved.
#   If $useDebugFiles is non-zero, files will be used instead of ET queries.
#   Filenames are:  et-{new,old}-$ADVISORY.txt
sub getPkgHashKeyedByChannels($$;$) {
    my ($isOld,$advisory,$useDebugFiles) = @_;
    my %h_ash = ();
    my $ret = \%h_ash;
    my (@lines, $fetch_worked, $foundCh);
    my $me = 'getPkgHashKeyedByChannels';
    my $errataServer= ($ENV{ERRATA_XMLRPC} || "errata-xmlrpc.devel.redhat.com");
    my $ET_URL = "http://$errataServer";
    my $ET_func = ((0 == $isOld) ? 'get_channel_packages' : 'get_released_channel_packages');
    if ($globs->{tpsDistMethod} eq 'pulp') {
        $ET_func = ((0 == $isOld) ? 'get_pulp_packages' : 'get_released_pulp_packages');
    }
    my $fetchThis = "$ET_URL/errata/$ET_func/$advisory";

    # Enable reading or creation of files instead of fresh ET data
    # File format: plain text, one line per channel
    #   channel1Name,/full/path/to/file1,/full/path/to/file2,etc
    my $createDebugFiles = 1; # disabled later without ENV var
    $useDebugFiles = 0 unless (defined($useDebugFiles));
    $createDebugFiles = 0 unless (defined($ENV{'TPSDEBUG_SAVE_ET_PKGS'}));
    my $debugFileName = "et-new-${advisory}.txt";
    $debugFileName = "et-old-${advisory}.txt" if ($isOld);
    my $debugFH;

    if (($useDebugFiles) && (open $debugFH, '<', $debugFileName)) {
        doLog($TPSTXT,$TPSDEBUG,"READING: $debugFileName for advisory: $advisory\n");
        # more elegant, but gets munged later... problem with newlines?
        # @lines = do { local $/; <$debugFH> };
        my $l;
        while (defined($l = <$debugFH>)) {
            chomp($l);
            push @lines, $l unless ($l =~ m/^\s*$/);
        }
        close($debugFH);
    } else {
        # Do web query.  Do a single re-try if we hit a timeout.
        # (ET had issues where a quick re-try would sometimes succeed after a 
        # timeout; hopefully this will help if the issues re-occur.)
        doLog($TPSMISC,$TPSDEBUG,"Open of $debugFileName failed: $!\n") if ($useDebugFiles);
        doLog($TPSCMD,$TPSDEBUG,"Fetching: $fetchThis\n");
        ($fetch_worked, @lines) = fetchUrl("$fetchThis", 'text/plain');
        unless ($fetch_worked) {
            doLog($TPSFAILTXT,$TPSLOG,("$me: ERROR: " . $lines[0] . "\n"));
            doLog($TPSFAILTXT,$TPSLOG,"Error from URL: $fetchThis\n");
            if ($lines[0] =~ m/timeout/i) {
                doLog($TPSFAILTXT,$TPSLOG,"Re-trying URL: $fetchThis\n");
                ($fetch_worked, @lines) = fetchUrl("$fetchThis", 'text/plain');
                unless ($fetch_worked) {
                    doLog($TPSFAILTXT,$TPSLOG,("$me: ERROR: " . $lines[0] . "\n"));
                    doLog($TPSFAILTXT,$TPSLOG,"Error from URL: $fetchThis\n");
                    doLog($TPSFAILTXT,$TPSLOG,"Giving up on URL: $fetchThis\n");
                    return $ret;
                }
            } else {
                return $ret;
            }
        }
    }

    if ($createDebugFiles) {
        if (open $debugFH, '>', $debugFileName) {
            doLog($TPSMISC,$TPSDEBUG,"Writing list to $debugFileName\n");
            print { $debugFH } $_,"\n"    for @lines;
            close($debugFH);
        } else {
            doLog($TPSMISC,$TPSDEBUG,"Write to $debugFileName failed: $!\n");
        }
    }

    # Process query results...
    if ($lines[0] =~ m/^ERROR:/) {
        doLog($TPSFAILTXT,$TPSLOG,("$me: ERROR: " . join("\n",@lines) . "\n"));
        doLog($TPSFAILTXT,$TPSLOG,"Error from URL: $fetchThis\n");
        return $ret;
    }

    foreach my $el (@lines) {
        next if ($el =~ m/^\s*$/);
        my @savePkgs = reverse(split(/,/,$el));
        $foundCh = pop(@savePkgs);
        $h_ash{$foundCh} = \@savePkgs;
    }

    return $ret;
}

###################################################
# needDetailedPkgList
#  Determine whether a detailed (NVR) package list is
#  needed due to older-than-current-RHN packages being tested.
#  Also returns the output of pkgNamesToPkgNVRs().
# Inputs:
#  pkgNameStr - args to yum as found in rhnqa's doDownloadTest.
#  newPkgHRef - as found in envPkgCacheToRefs('FILES_OUT')
# Outputs:
#  needDetails - 0 for false, 1 for true
#  eStr, eListR, naList: as from pkgNamesToPkgNVRs
# Note:
#  caller is responsible for feeding this to yum|up2date|whatever
#  **as appropriate**.
#
sub needDetailedPkgList {
    my ($pkgNameStr,$newPkgHRef) = @_;
    my ($eStr, $eListR, $naList) = pkgNamesToPkgNVRs($pkgNameStr,$newPkgHRef);
    my @eList = @$eListR;
    my $needDetails = 0;

    my $i = 0;
    my $okay = 1;
    my ($s1,$s2,$rc1,$rc2,@nErr,@nvrErr);
    foreach my $n (@$naList) {
	$s1 = `tps-check-channels -n qa -f NA "$n"`;
	$rc1 = $?;
	$s2 = `tps-check-channels qa -f NVRA "$eList[$i]"`;
	$rc2 = $?;
	if (0 != $rc1) {
	    push @nErr, $n;
	    $okay = 0;
	}
	if (0 != $rc2) {
	    push @nvrErr, $eList[$i];
	    $okay = 0;
	}
	if ((1 == $okay) && ($s1 ne $s2)) {
	    doLog($TPSWARN,$TPSLOG,("WARNING: Non-current package under test!\n".
                  "  $s2 on RHN and under test, but latest found is:\n".
		  "  $s1\n"));
	    $needDetails = 1;
	}
	$okay = 1;
	$i++;
    }

    doLog($TPSNOISE,$TPSLOG,("Errors found querying tps-check-channels about: ". 
			     join(' ',@nErr) . "\n")) if ($#nErr >= 0);
    doLog($TPSNOISE,$TPSLOG,("Errors were found querying tps-check-channels about: ".
			     join(' ',@nvrErr) . "\n")) if ($#nvrErr >= 0);

    return ($needDetails, $eStr, $eListR, $naList);
}
###################################################
# instSumsToQueryList - go from a hashref with md5sum keys and \n-separated NVRAS lines
# to a ref to ("list-2.34-5.el4.i386", "of-1.0-2.el21", "rpm-queryable-1.0-1.noarch") rpms.
sub instSumsToQueryList {
    my ($href,$wrapChar) = @_;
    my ($tmp, @retList, $str);
    $wrapChar = '' if (!defined($wrapChar));
    foreach my $k (keys(%$href)) {
        $tmp = nvrToHRef($href->{$k});
        $str = ($tmp->{name} .'-'. $tmp->{ver} .'-'. $tmp->{rel});
        if (0 == $globs->{is21}) {
            $str .= ('.' . $tmp->{arch});
        }
        if ($wrapChar) {
            push @retList, "${wrapChar}${str}${wrapChar}";
        } else {
            push @retList, $str;
        }
    }
    return \@retList;
}

###################################################
# pkgListToNVR - grab name-version-release-arch-sigmd5 for each rpm in list
# returns a hashref with "name.arch" -> NVRAS-info (newline-separated)
# If there are multiple name.arch's, THE LAST ONE WINS.
sub pkgListToNVR {
    my ($packageref) = @_;
    my @packagelist = @{$packageref};
    my ($info, %pkghash);
    my ($n,$v,$r,$arch,$s,$e,$srpm,$is_src);
    my ($hack21,$rmArch);
    my $nosig = '';

    # Cannot use --nosignature rpm option under 2.1AS/2.1AW
    ($hack21, $rmArch) = handleAS21hack();
    $nosig = '--nosignature' if (!$hack21);

    foreach my $i (@packagelist) {
        # signature warnings cause parsing troubles, so skip them
        $info = doRpmCommand("rpm -qp $nosig --qf '%{NAME}\n%{VERSION}\n%{RELEASE}\n%{ARCH}\n%{SIGMD5}\n%{EPOCH}\n%{SOURCERPM}\n%{SOURCEPACKAGE}\n' $i");
        if ($info =~ m/^error:/) {
            # FIXME: IMPROVE ERROR HANDLING
            # print STDERR "pkgListToNVR: error on pkg $i: $info\n";
            doLog($TPSERROR,$TPSLOG,"pkgListToNVR: error on pkg $i: $info\n");
        } else {
            # ($name,undef,undef,$arch,undef,undef,undef) = split /\n/,$info,7;
            ($n,$v,$r,$arch,$s,$e,$srpm,$is_src) = split /\n/,$info,8;
            chomp($is_src);
	    chomp($srpm);
            $arch = 'src' if ($is_src eq '1');
            $pkghash{"${n}.${arch}"} = join("\n",$n,$v,$r,$arch,$s,$e,$srpm);
        }
    }
    return \%pkghash;
}
sub instPkgToNVR {
    my ($pkgName) = @_;
    my ($info, %pkghash);
    my ($n,$v,$r,$arch,$s,$e,$srpm,$is_src);
    my ($hack21,$rmArch);
    my $nosig = '';

    # Cannot use --nosignature rpm option under 2.1AS/2.1AW
    ($hack21, $rmArch) = handleAS21hack();
    $nosig = '--nosignature' if (!$hack21);

    # signature warnings cause parsing troubles, so skip them
    $info = doRpmCommand("rpm -q $nosig --qf '%{NAME}\t%{VERSION}\t%{RELEASE}\t%{ARCH}\t%{SIGMD5}\t%{EPOCH}\t%{SOURCERPM}\t%{SOURCEPACKAGE}\n' '${pkgName}' 2>&1 | grep -v 'not installed\$'");
    if ($info =~ m/^error:/) {
	# FIXME: IMPROVE ERROR HANDLING
	# print STDERR "pkgListToNVR: error on pkg $i: $info\n";
	doLog($TPSERROR,$TPSLOG,"pkgListToNVR: error on pkg $i: $info\n");
    } else {
	foreach my $ln (split(/\n/,$info)) {
	    ($n,$v,$r,$arch,$s,$e,$srpm,$is_src) = split /\t/,$ln,8;
	    chomp($is_src);
	    chomp($srpm);
	    $arch = 'src' if ($is_src eq '1');
	    $pkghash{"${n}.${arch}"} = join("\n",$n,$v,$r,$arch,$s,$e,$srpm);
	}
    }
    return \%pkghash;
}
############################
# appendToCacheRefs --
# This routine is for appending dep-errata items to new/old filelists
# Thus, do: 
#  (listRef,hashRef) = envPkgCacheToRefs(FILES_OUT) followed by 
#  appendToCacheRefs(DEP_FILES_OUT,listRef,hashRef)
# Returns number of items added to the hashref.
sub appendToCacheRefs {
    my ($envVar,$listRef,$hashRef) = @_;
    my $pkCount = 0;

    return(0) unless (exists($ENV{$envVar}));

    # REMOVE_DEBUG
    # print STDERR "appendToCacheRefs: using: $ENV{$envVar}\n";

    my ($lr,$hr) = envPkgCacheToRefs($envVar);
    push(@$listRef,@$lr);
    foreach my $k (sort(keys(%$hr))) {
	$hashRef->{$k} = $hr->{$k};
	$pkCount++;
    }
    return($pkCount);
}
##################################
# envPkgCacheToRefs --
# Takes the name of an environment variable that contains a the name of a file
# which contains the /full/names/of/packages.rpm involved in an errata -- for
# example, the newfiles or oldfiles.  Returns a listref of those package names
# and a pkgListToNVR-style hashref.  Uses and/or creates cache files so that
# subsequent tools/invocations need not wait for long rpm queries on slow networks.
#  Usage: ($filelistRef, $nvrHashRef) = envPkgCacheToRefs('FILES_OUT');
sub envPkgCacheToRefs {
    my @env_Names = @_;
    my $cacheFile;
    my ($fileName,@flist,$tmpListRef,$nvrRef);
    my $useCache;
    my $doRegen;
    my ($listRef,%nvr);


    # REMOVE_DEBUG
    # print STDERR "envPkgCacheToRefs: using $fileName and $cacheFile\n";

    $listRef = \@flist;
    foreach my $envName (@env_Names) {
	next unless (defined($envName) && $envName);
	next unless (exists($ENV{$envName}));
	$fileName = $ENV{$envName};
	next unless (defined($fileName) && $fileName && (-r $fileName));

	$cacheFile = $fileName . '.cache';
	$tmpListRef = fileToListRef($fileName);
	$useCache = 0; # try to use cache (look first, use later)
	$doRegen = 1;  # regen if error while loading cache

	push @flist,@$tmpListRef if ($#$tmpListRef >= 0);

	# See whether we can use the cache -
	# it must exist + be nonzero-sized & newer than fileName.
	if (-e $cacheFile && -s $cacheFile) {
	    # my ($dev,$ino,$mode,$nlink,$uid,$gid,$rdev,$size,
	    #    $atime,$mtime,$ctime,$blksize,$blocks)
	    my (undef,undef,undef,undef,undef,undef,undef,undef,
		undef,$cache_mtime,undef,undef,undef)
		= stat($cacheFile);
	    my (undef,undef,undef,undef,undef,undef,undef,undef,
		undef,$orig_mtime,undef,undef,undef)
		= stat($fileName);
	    if ($cache_mtime >= $orig_mtime) {
		$useCache = 1;
	    }
	}
	if ($useCache) {
	    if (open(__C,"<$cacheFile")) {
		my $ln;
	        CACHELOOP: while (defined($ln = <__C>)) {
		    chomp $ln;
		    next CACHELOOP if ($ln =~ /^\s*$/);
		    if ($ln =~ m/\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$/) {
			my ($n,$v,$r,$a,$s,$e,$srpm) = ($1,$2,$3,$4,$5,$6,$7);
			chomp($srpm);
			$nvr{"${n}.${a}"} = "${n}\n${v}\n${r}\n${a}\n${s}\n${e}\n${srpm}\n";
			$doRegen = 0;
		    } else {
			# misc: gets regenerated.
			doLog($TPSMISC,$TPSLOG,"Invalid Cache: $ln -- Regenerating Cache.\n"); 
			$doRegen = 1;
			last CACHELOOP;
		    }
		}
		close(__C);
	    } else {
		$doRegen = 1;
	    }
	}
	if (!$useCache || $doRegen) {
	    # Regenerate package info
	    if (!defined($tmpListRef) || ( ! -f $fileName)) {
		logTestFatal("Error reading file: $fileName -- please regenerate by running tps-make-lists\n");
		die "Error reading file: $fileName -- please regenerate by running tps-make-lists";
	    }
	    $nvrRef = pkgListToNVR($tmpListRef);
	    my $printed = 0;

	    # copy info to hash for return
	    foreach my $i (keys(%$nvrRef)) {
		$nvr{$i} = $nvrRef->{$i};
	    }

	    # Now save the info to cache
	    if (open(__C,">$cacheFile")) {
		foreach my $i (keys(%{$nvrRef})) {
		    my $ln = $nvrRef->{$i};
		    $ln =~ s/\n/ /g;
		    $printed = 1;
		    print __C "$ln\n";
		}
		close(__C);
		# Do not save an empty/invalid cache file
		unlink($cacheFile) unless (1 == $printed);
	    } else {
		doLog($TPSWARN,$TPSLOG,"warning: could not create cache file: $cacheFile\n");
	    }
	    # drop hashref to prevent accidental re-use.
	    $nvrRef = {};
	} 
	# else {
	     # Use the info that we gathered from cache
	#    $nvrRef = \%nvr;
	# }
    }

    # Return the package listref and nvr-hashref
    return ($listRef, \%nvr);
}
sub isFileInListRef {
    my ($fullname, $listRef) = @_;
    my @flist = @$listRef;
    my $rc = 0; # e.g., false/notFound
    my $shortName = basename($fullname);
    foreach my $f (@flist) {
        return(1) if ($shortName eq (basename($f)));
    }
    return $rc;
}

##################################
# Takes a hashref of "Name.arch"=>"NVRASEP" and the directory where the blacklist file may be found,
# and returns 0 for "not blacklisted" or 1 for "blacklisted".
sub blacklisted {
    my ($newInfo,$blPath) = @_;
    my $blacklistR = [];
    my $name;

    if (open(_BL,"<$blPath/tps-blacklist.txt")) {
        my $ln;
        while (defined($ln = <_BL>)) {
            chomp $ln;
            push @{$blacklistR}, $ln;
        }
        close(_BL);
    } else {
        doLog($TPSINFO,$TPSLOG,"cannot open $blPath/tps-blacklist.txt to check for blacklist -- using builtins\n");
        # print STDERR "cannot open $blPath/tps-blacklist.txt to check for blacklist -- using builtins\n";
        my @bl = qw(kernel glibc pam rpm krb5 bash perl);
        $blacklistR = \@bl;
    }
    foreach my $i (@{$blacklistR}) {
        foreach my $pNameArch (keys(%{$newInfo})) {
            ($name,undef,undef,undef,undef,undef,undef) = split /\n/,$newInfo->{$pNameArch};
            return 1 if ($name eq $i);
        }
    }

    return 0;
}
##################################
# findModules - locate additional testing modules, return ref to list of same.
sub findModules {
    my ($newInfo,$blPath) = @_;
    my $found = [];

    foreach my $pNameArch (keys(%{$newInfo})) {
        ($name,undef,undef,undef,undef,undef,undef) = split /\n/,$newInfo->{$pNameArch};
        if (-r "${blPath}/${pNameArch}.pl") {
            push @{$found}, "${blPath}/${pNameArch}.pl";
        } elsif (-r "${blPath}/${name}.pl") {
            push @{$found}, "${blPath}/${name}.pl";
        }
    }

    return $found;
}
#################################################
# detect RHEL2.1 use and specify an ARCH string to remove from rpm queries if using RHEL2.1.
sub handleAS21hack {
    my $hack21 = 0;
    my $rmArch = '';

    # A[S|W] 2.1 didn't grok "name.arch" for rpm queries, so hack around that if need be.
    if (exists($ENV{'RELEASE'}) && exists($ENV{'ARCH'})) {
        $hack21 = 1 if ($ENV{'RELEASE'} =~ m/2\.1/);
        $rmArch = $ENV{'ARCH'};
    }
    return ($hack21, $rmArch);
}
#######################################################
# determinePackageState - return one of: new | old | mixed | none
#   to reflect whether the 'new' or 'old' packages are currently installed;
#   or 'mixed' if some of each are present; or 'none' if packages
#   are missing or neither the old/new ones.
# 2 required inputs: reference to new and ref to old package lists (filenames)
# 2 optional inputs: reference to new & old hashes full of NVRAS info
# Returns one of the words above plus references to 2 hashes of installed pkgs:
# ($word, \%instsums, \%instpkgs, \%statesRef) -- instsums is NVRAS info keyed by sigmd5sum,
# instpkgs is the NVRAS info keyed by "name.arch".
# determinePackageState($newPkgListRef, $oldPkgListRef, $newPkgHRef, $oldPkgHRef);
sub determinePackageState {
    my ($newpackageref, $oldpackageref, $newpkghref, $oldpkghref) = @_;
    my @oldpackagelist = @{$oldpackageref};
    my @newpackagelist = @{$newpackageref};
    my ($newinfo, $installedinfo);
    my ($n, $v, $r, $a, $s, $e, $srpm); # name, version, release, arch, sigmd5, epoch, srpm
    my ($oldCnt, $newCnt, $oldInstCnt, $newInstCnt, $none, $dropCnt, $addCnt) = (0,0,0,0,0,0,0);
    my $strayCnt = 0;
    my (%oldpkgs,%newpkgs,%instpkgs,%instsums,@allpkgs);
    my @strayList = ();
    my %pksums;
    my %pkgStates;
    my $ret = 'none';
    my $hack21 = 0;
    my $rmArch = '';
    my $nosig = '';
    my $isManualRun = 0;
    my $beVerbose = 0;

    # Extra output to StdErr if we are running from 'tps-which'...
    $beVerbose = 1 if (exists($ENV{'VERBOSE'}) && (1 == $ENV{'VERBOSE'}));
    $isManualRun = 1 if (($FindBin::Script =~ m/tps-which/) || (!exists($ENV{'TPSAUTO'})));

    # helper routine used only here to print info about PackageState structures.
    # $pksums = hashref to pksums struct
    # pick = valid keyname for pksums (str, na, old, new, inst, stray)
    # instState = inst or missing (eg !inst)
    sub reportPkgs {
        my ($pksums, $pick, $instState) = @_;
        my $t;
        my $gotSome = 0;
        my $instTag = 'installed';
	return if ($globs->{silentReportPkgs});
        $instTag = 'missing' unless ($instState eq 'inst');

        my $introStr = "\n$pick packages that are $instTag:\n";

        foreach my $s (keys(%$pksums)) {
            $t = $pksums->{$s};
            if ($t->{$pick}) {
                if ( (($instState eq 'inst') && ($t->{inst})) ||
                     (($instState ne 'inst') && (0 == $t->{inst})) ) {
                    doLog($TPSTXT,$TPSLOG,$introStr) unless ($gotSome > 0);
                    doLog($TPSTXT,$TPSLOG," $pick : $instTag : " . $t->{str} . "\n");
                    $gotSome++;
                }
            }
        }
        # print STDERR " (none)\n" unless ($gotSome);
    }
    # Args:
    # pkSums = hashref for $pksums
    # new,oldPkgs: hashref  for $newpkgs or $oldpkgs
    # iCur = current $i for loop
    # allPkgs = array ref for @allpkgs
    # isNew, isOld: 1 for true, 0 for false. Both are used.
    # Returns: ourCnt.  Either addCnt or dropCnt, depending on 
    # whether you call it for new or old pkgs.
    sub pksumWorker {
	my ($pkSums,$newPkgs,$oldPkgs,$iCur,$hack21,$isNew,$isOld,$allPkgs) = @_;
	my ($thisPkgs,$otherPkgs);
	if ($isNew) {
	    ($thisPkgs,$otherPkgs) = ($newPkgs,$oldPkgs);
	} else {
	    ($thisPkgs,$otherPkgs) = ($oldPkgs,$newPkgs);
	}
	my $ourCnt = 0;
        my ($n,$v,$r,$a,$s,$e,$srpm) = split /\n/, $thisPkgs->{$iCur}, 7;
        chomp $s;
        chomp $n;
	chomp($srpm);
        if (exists($pkSums->{$s})) {
            # we've seen it before, which means that it's on both old & new lists: BADNESS.
            doLog($TPSERROR,$TPSCRIT,"TPSERROR: BUG: already have checksum for ${n}-${v}-${r}.${a} : $s\n");
            doLog($TPSERROR,$TPSCRIT,"TPSERROR: BUG: THIS IS BAD: Package is on both New and Old Lists, or Duplicated.\n");
            doLog($TPSERROR,$TPSCRIT,"TPSERROR: Your package list may not be sane, your TPS results are not likely to be.\n");
        }
        $pkSums->{$s} = {
            str  => "${n}-${v}-${r}.${a}",
            nvra => "${n}-${v}-${r}.${a}",
            nvr  => "${n}-${v}-${r}",
            na   => "${n}.${a}",
            n    => "${n}",
            inst => 0,
            new => $isNew,
            old => $isOld,
            stray => 0,
	    epoch => $e,
	    srpm => $srpm,
        };
        # if the package name.arch wasn't seen previously, it has been added.
        if (!defined($otherPkgs->{$iCur})) {
            $ourCnt++;
	}
        if (($isOld) || (!defined($otherPkgs->{$iCur}))) {
            # if isNew, only put on "check for install status" list if it's not already there.
            if ($hack21) {
                push @$allPkgs, $n; # cannot use '.arch' in RHEL2.1.
            } else {
                push @$allPkgs, $iCur; # 'name.arch' for other RHELs
            }
        }
	return($ourCnt);
    }

    ($hack21, $rmArch) = handleAS21hack();
    $nosig = '--nosignature' if (!$hack21);

    # Get the NVR+AS for new and old package lists
    # If caller provides refs, use 'em; they can take a while to build.
    unless (defined($newpkghref)) {
        doLog($TPSMISC,$TPSLOG,"=============== newpkghref not defined......\n");
        $newpkghref = pkgListToNVR($newpackageref);
    }
    %newpkgs = %{$newpkghref};

    unless (defined($oldpkghref)) {
        doLog($TPSMISC,$TPSLOG,"=============== oldpkghref not defined......\n");
        $oldpkghref = pkgListToNVR($oldpackageref);
    }
    %oldpkgs = %{$oldpkghref};

    # build unique list of old+new package names
    foreach my $i (keys(%oldpkgs)) {
        $oldCnt++;  # count of old pkgs for this update
	$dropCnt += pksumWorker(\%pksums,\%newpkgs,\%oldpkgs,$i,$hack21,0,1,\@allpkgs);
    }

    foreach my $i (keys(%newpkgs)) {
        $newCnt++;  # count of new packages for this update
	$addCnt += pksumWorker(\%pksums,\%newpkgs,\%oldpkgs,$i,$hack21,1,0,\@allpkgs);
    }

    # Go through all package names to see what is installed.
    # Save in two formats -- hash by name.arch, and hash by sigmd5.
    foreach my $i (@allpkgs) {
        # Okay, for all the old/new package "name.arch" pairs,
        # find out what's currently on the system, if anything...

        $info = doRpmCommand("rpm -q $nosig --qf '%{NAME}\n%{VERSION}\n%{RELEASE}\n%{ARCH}\n%{SIGMD5}\n%{EPOCH}\n%{SOURCERPM}\n' ${i}");

        if ($info =~ m/not installed/i) {
            # do *not* set %instpkgs or %instsums, so we easily know it's not installed later on...
            $none++;
        } elsif ($info =~ m/^error:/i) {
            # FIXME: IMPROVE ERROR HANDLING
            # print STDERR "RPM Error querying installed package $i\n";
            doLog($TPSERROR,$TPSLOG,"TPSERROR: RPM Error querying installed package $i\n");
        } else {
            # note that multiple "name.arch" can be installed -- e.g., kernel.
            # Thus we put a reference to a list into the corresponding hash entry.
            my @instList;
            while ($info) {
                ($n,$v,$r,$a,$s,$e,$srpm, $info) = split /\n/,$info,8;
                doLog($TPSMISC,$TPSNOISE,"InstalledState: ${e}: $n - $v - $r - $a / $srpm // $s\n");
                if (exists($pksums{$s})) {
                    my $t = $pksums{$s};
                    my $na = $t->{na};
                    $t->{inst} = 1;
                    if (($t->{new}) && ($t->{old})) {
                        doLog($TPSERROR,$TPSLOG,"TPSERROR: BUG: both new and old: " . $t->{str} . "\n");
                        doLog($TPSHINT,$TPSLOG,"This could be a bug in the filelist for this update.\n");
                    }
                    if ($t->{new}) {
                        $newInstCnt++;
                        # $addCnt++ if (!exists($oldpkgs{$na}));
                    }
                    if ($t->{old}) {
                        $oldInstCnt++;
                        # $dropCnt++ if (!exists($newpkgs{$na}));
                    }
                } else {
                    $pksums{$s} = {
                        str  => "${n}-${v}-${r}.${a}",
                        nvra => "${n}-${v}-${r}.${a}",
                        nvr  => "${n}-${v}-${r}",
                        na   => "${n}.${a}",
                        n    => "${n}",
                        inst => 1,
                        new => 0,
                        old => 0,
                        stray => 1,
			epoch => ((defined($e)) ? $e : ''),
			srpm => ((defined($srpm)) ? $srpm : ''),
                    };
                    push @strayList, "${n}-${v}-${r}.${a}";
                }

                push @instList, "${n}\n${v}\n${r}\n${a}\n${s}\n";
                $instsums{$s} = "${n}\n${v}\n${r}\n${a}\n${s}\n";
            }
            $instpkgs{"${n}.${a}"} = \@instList;
        }
    }
    # print STDERR "===================\n";
    # print STDERR "Debug: oldCnt $oldCnt ; oldInstCnt $oldInstCnt\n";
    # print STDERR "       newCnt $newCnt ; newInstCnt $newInstCnt\n";
    # print STDERR "       none = $none\n";
    # print STDERR "===================\n";
    $strayCnt = $#strayList + 1;

    ########################
    # Turn on STDERR output if we're being called from tps-which.
    # All log#Print() output => STDERR unless TPSAUTO is set in the environment.
    # $ENV{'VERBOSE'} = 1 if ($isManualRun);
    $globs->{verbose} = 1 if (($isManualRun) && !($globs->{quietStderr}));
    $globs->{tmpStderr} = 1 if ($globs->{progName} =~ /tps-which/);

    doLog($TPSNOISE,$TPSLOG,
          "PkgState: oldCnt $oldCnt ; oldInstCnt $oldInstCnt ; newCnt $newCnt ; newInstCnt $newInstCnt ; none = $none ; dropCnt $dropCnt ; addCnt $addCnt ; strayCnt $strayCnt\n");
    foreach my $p (qw(oldCnt oldInstCnt newCnt newInstCnt none dropCnt addCnt strayCnt)) {
        eval "\$pkgStates{$p} = \$$p;"
    }

    doLog($TPSINFO,$TPSLOG, sprintf(("\n %2d of %2d OLD, " .
                      "%2d of %2d NEW, "   .
                      "and %2d STRAY packages are installed\n"),
                     $oldInstCnt, $oldCnt, $newInstCnt, $newCnt, $strayCnt));

    $globs->{tmpStderr} = 0;
    # Now that we have old/new/installed info, figure out
    # if the installed packages are the old list, the new list, a mix, or absent ("none").
    if ($oldCnt && ($oldCnt == $oldInstCnt)) {
        # everything on the oldpackage-list is installed (and perhaps more stuff).
        if (0 == $newInstCnt) {
            # then we're good.
            $ret = "old";
        } else {
            # both new & old stuff installed
            $ret = "mixed";
        }
    } elsif ($newCnt && ($newCnt == $newInstCnt)) {
        # everything on the newpackage-list is installed (and perhaps more stuff).
        if (0 == $oldInstCnt) {
            # then we're good.
            $ret = "new";
        } else {
            # both new & old stuff installed
            $ret = "mixed";
        }
    } else {
        # none, or partial new/old.
        if ((0 == $newInstCnt) && (0 == $oldInstCnt)) {
            # no new pkgs installed.  no old pkgs installed.
            if (0 == $none) {
                doLog($TPSWARN,$TPSLOG,"\nTPSWARNING: check system integrity: you appear to have a version of one of the errata packages installed that is not on the list of old or new packages.  This could indicate the presence of test packages or configurations that might cause additional problems.\n\n");
            }
            $ret = "none";
        } else {
            if ($oldInstCnt && ($newInstCnt == 0)) {
               $ret = 'old';
               doLog($TPSINFO,$TPSLOG,"\nTPSINFO: PkgState: Warning: not all the 'old' packages are actually installed.\n");
            } elsif ($newInstCnt && ($oldInstCnt == 0)) {
               $ret = 'new';
               doLog($TPSINFO,$TPSLOG,"\nTPSINFO: PkgState: Warning: not all the 'new' packages are actually installed.\n");
            } else {
               # hmm, is this correct?  probably 'partial'
               $ret = "mixed";
            }
        }
    }

    # Additional Sanity Check
    # $globs->{tmpStderr} = 1 if ($globs->{progName} =~ /tps-which/);
    if ($ret eq 'mixed') {
        reportPkgs(\%pksums, 'new', 'inst');
        reportPkgs(\%pksums, 'new', 'missing');
        reportPkgs(\%pksums, 'old', 'inst');
        reportPkgs(\%pksums, 'old', 'missing');
        reportPkgs(\%pksums, 'stray', 'inst');
    } elsif ($ret eq 'none') {
        reportPkgs(\%pksums, 'stray', 'inst');
    } elsif ($ret eq 'new') {
        reportPkgs(\%pksums, 'new', 'missing');
    } else {
        # old
        reportPkgs(\%pksums, 'old', 'missing');
    }
    # $globs->{tmpStderr} = 0;

    ######################
    # Restore debug setting, and don't spew to STDERR unless
    # we were already doing so.
    if ($isManualRun) {
        # We are restoring, so do not create ENV{VERBOSE} if it
        # did not exist previously.  See BZ 1181743.
        $ENV{'VERBOSE'} = $beVerbose if (exists($ENV{'VERBOSE'}));
        $globs->{verbose} = $beVerbose;
    }

    $pkgStates{'ret'} = $ret;
    $pkgStates{'instsums'} = \%instsums;
    $pkgStates{'instpkgs'} = \%instpkgs;
    $pkgStates{oldCnt}     = $oldCnt;
    $pkgStates{oldInstCnt} = $oldInstCnt;
    $pkgStates{newCnt}     = $newCnt;
    $pkgStates{newInstCnt} = $newInstCnt;
    $pkgStates{none}       = $none;
    $pkgStates{dropCnt}    = $dropCnt;
    $pkgStates{addCnt}     = $addCnt;
    $pkgStates{strayCnt}   = $strayCnt;
    $pkgStates{pkSums}     = \%pksums;  # save for deletion commands, etc.

    return ($ret, \%instsums, \%instpkgs, \%pkgStates);
}
sub setGlobalLists {
    my ($newPkgListRef, $oldPkgListRef, $newPkgHRef, $oldPkgHRef) = @_;
    my $hr = $globs->{g_PkgLists};
    $hr->{newPkgListRef} = $newPkgListRef;
    $hr->{oldPkgListRef} = $oldPkgListRef;
    $hr->{newPkgHRef} = $newPkgHRef;
    $hr->{oldPkgHRef} = $oldPkgHRef;
    $globs->{haveFileLists} = 1;
}
sub getGlobalLists {
    my $hr = $globs->{g_PkgLists};
    return ($hr->{newPkgListRef}, $hr->{oldPkgListRef}, $hr->{newPkgHRef}, $hr->{oldPkgHRef});
}
sub fetchPackageState {
    my ($whichOne) = @_;
    my $refName = 'g_PkgStates';
    $whichOne = 'cur' if (!defined($whichOne));
    $refName = 'g_PkgOldStates' if ($whichOne eq 'old');
    my $hr = $globs->{$refName};
    return($hr);
}
sub fetchPackageStates {
    my ($whichOne) = @_;
    $whichOne = 'cur' if (!defined($whichOne));
    my $hr = fetchPackageState($whichOne);
    return($hr->{condition}, $hr->{instSumsRef}, $hr->{instPkgsRef}, $hr->{statesRef});
}
sub setPackageStates {
    my ($whichOnes,$condition, $instSumsRef, $instPkgsRef, $statesRef) = @_;
    my $hr = fetchPackageState($whichOnes);
    $hr->{condition} = $condition;
    $hr->{instSumsRef} = $instSumsRef;
    $hr->{instPkgsRef} = $instPkgsRef;
    $hr->{statesRef} = $statesRef;
}
sub updatePackageState {
    my ($old_hr, $new_hr);
    my ($newPkgListRef, $oldPkgListRef, $newPkgHRef, $oldPkgHRef) = getGlobalLists();

    $old_hr = fetchPackageState('old');
    $new_hr = fetchPackageState('cur');

    my ($condition, $instSumsRef, 
	$instPkgsRef, $statesRef) = determinePackageState($newPkgListRef, $oldPkgListRef, 
							  $newPkgHRef, $oldPkgHRef);
    foreach my $i (keys(%$new_hr)) {
	$old_hr->{$i} = $new_hr->{$i};
    }
    setPackageStates('cur',$condition, $instSumsRef, $instPkgsRef, $statesRef);
    return($condition, $instSumsRef, $instPkgsRef, $statesRef);
}

# return a string suitable for rpm installation/deletion commands
# href = hashref as in pkgStates{pkSums}.
# what: new, old, stray; whatForm: n, nvr.  (.a is added if not AS21).
# whatForm is needed because up2date (n) / rpm (nvr) accept different package specs.
sub selectFromPKSums {
    my ($href,$what,$whatForm) = @_;
    my ($hr2, @selList, $ret);
    my ($is21,undef) = handleAS21hack();

    $ret = '';
    foreach my $k (keys(%$href)) {
        $hr2 = $href->{$k};
        if (exists($hr2->{$what}) && (1 == $hr2->{$what})) {
            push @selList,$hr2;
        }
    }
    $whatForm .= 'a' if (!$is21);
    foreach my $n (@selList) {
        if (exists($n->{$whatForm})) {
            $ret .= " $n->{$whatForm}";
        }
    }
    return($ret);
}
sub selectPKSumData {
    my ($whatKey,$specsHR) = @_;
    my ($pkgHR, @selList, $ret);
    my ($is21,undef) = handleAS21hack();

    my ($gstate, $pksumHR, $specVal);

    $ret = '';

    $gstate = fetchPackageState('cur');
    return($ret) unless (defined($gstate) && ($gstate));

    my $statesRef = $gstate->{statesRef};
    return($ret) unless (defined($statesRef) && ($statesRef));

    $pksumHR = $statesRef->{pkSums};
    return($ret) unless (defined($pksumHR) && ($pksumHR));

    KLOOP: foreach my $k (keys(%$pksumHR)) {
        $pkgHR = $pksumHR->{$k};
        foreach my $specKey (keys(%$specsHR)) {
            $specVal = $specsHR->{$specKey};
            next KLOOP unless (exists($pkgHR->{$specKey}));
            next KLOOP unless ($specVal eq $pkgHR->{$specKey});
        }
        push @selList,$pkgHR;
    }
    $whatForm =~ s/a$//i if ($is21);
    foreach my $n (@selList) {
        if (exists($n->{$whatKey})) {
            $ret .= " $n->{$whatKey}";
        }
    }
    return($ret);
}

# selectNVRAfromStr
# inputs:
#  str: string of package names, or names.arch
#  stateRef: as returned by determinePackageState
#  newOld: either 'new' or 'old' packages
#  strFmt: 'n'(default) or 'na' for name.arch string format
# output: string of nvra-formatted packages
# returns original string upon any errors.
sub selectNVRAfromStr {
    my ($str,$stateRef,$newOld,$strFmt) = @_;
    my $pkSums = $stateRef->{pkSums};
    my @nvraList = ();
    my @hitList = split(/\s+/,$str);
    my $k;
    my $newStr = '';
    $strFmt = 'n' unless ($strFmt);

    foreach my $pk (sort keys(%$pkSums)) {
        $k = $pkSums->{$pk};
        if (1 == $k->{$newOld}) {
	    next unless (listInclude(\@hitList,$k->{$strFmt}));
            push @nvraList, $k->{nvra};
        }
    }
    $newStr = join(' ',@nvraList);
    return($newStr) if ($newStr !~ m/^\s*$/);
    return($str);
}
sub shellFileToEnv {
    my ($cacheFileName, $clobber) = @_;
    my ($ln,$varname,$val);
    my $ret = '';

    if (open(IN,"<$cacheFileName")) {
        while (defined($ln = <IN>)) {
            chomp $ln;
            next if ($ln =~ m/^\s*#/); # skip comments
            # expected format: FOO="BAR"
            if ($ln =~ m#\s*([^=]+)="([^"]+)"#) {
                $varname = $1;
                $val = $2;
                if ($clobber) {
                    $ENV{$varname} = $val;
                } else {
                    $ENV{$varname} = $val if (!exists($ENV{$varname}));
                }
            }
        }
        close(IN);
    } else {
        $ret = "cannot read $cacheFileName: $!";
    }
    return $ret;
}
sub cacheToEnv {
    my ($cacheFileName) = @_;
    my ($ln,$varname,$val);

    $cacheFileName = 'variable-names.sh' unless (defined($cacheFileName));
    my $errmsg = shellFileToEnv($cacheFileName,1);
    if ($errmsg) {
        die "TPSERROR: Are you in a tps working directory?\n$err\n";
    }

    if (!defined($globs)) {
        # some callers might not use/care about the global pointer.
        my %globalHash;
        $globs = \%globalHash;
    }
    if ((!defined($globs->{tpsErratum})) || (!exists($globs->{tpsErratum}))
        || (!($globs->{tpsErratum})) || ('unknown' eq $globs->{tpsErratum})) {
        if ((defined($ENV{ERRATA})) && (exists($ENV{ERRATA})) &&
            ($ENV{ERRATA})) {
            $globs->{tpsErratum} = $ENV{ERRATA};
        } elsif ((defined($ENV{TPSQ_ERRATA})) && (exists($ENV{TPSQ_ERRATA})) &&
            ($ENV{TPSQ_ERRATA})) {
            $globs->{tpsErratum} = $ENV{TPSQ_ERRATA};
        }
    }
    if (exists($globs->{forbidDepErrata}) && (1 == $globs->{forbidDepErrata})) {
	my $depR = $globs->{depErrataVars};
	foreach my $d (@$depR) {
	    delete($ENV{$d});
	}
    }
}
## shellExportsToEnv
# let perl source the variables exported from a shell script
# inputs: shFile: shell file to be sourced
#       doOverride: whether to override an existing ENV
#                   var with values from shFile.
# returns: 1 if shFile couldn't be read, or nothing was set.
#          0 if any ENV variables were set.
#
sub shellExportsToEnv {
    my ($shFile,$doOverride) = @_;
    my $rc = 1;
    return($rc) unless (-r $shFile);

    my $f = `grep export \"$shFile\" | grep -v ' *#' | sed -e 's/=.*//g; s/export //g'`;
    my @varList = split(/\s+/,$f);
    my $shellOut = `source \"$shFile\" && printenv`;
    my @shellLines = split(/\n/,$shellOut);
    my @grepOut;

    VLP: foreach my $v (@varList) {
        foreach my $sl (@shellLines) {
            if ($sl =~ m|^$v=(.*)|) {
                if ($doOverride){
                    $ENV{$v} = $1;
                    $rc = 0;
                } else {
                    if (!exists($ENV{$v})) {
                        $ENV{$v} = $1;
                        $rc = 0;
                    }
                }
                next VLP;
            }
        }
    }
    return $rc;
}
## fetchUrl
#  similar to wget, but all done in perl.
#  Inputs:
#    url -- url to fetch
#  accept -- format to accept, default: text/plain
#  last_mod_ref -- reference to scalar to hold the 'last_modified'
#    filed of the http response.  This is only filled in if the
#    request is successful.  Default: undef.
#  Outputs:
#    rc = success or failure
#   array = array of lines -- either output lines or error message(s).
sub fetchUrl {
    my ($url,$accept,$last_mod_ref) = @_;
    $accept = 'text/plain' if (!defined($accept) || !$accept);
    my @ret = ();
    my $rc;

    my $hdr = HTTP::Headers->new;
    $hdr->header('Accept' => $accept);
    my $req = HTTP::Request->new(GET => $url, $hdr);
    my $ua = LWP::UserAgent->new;
    # the agent string contains a version number.  Must be >= 5.821 
    # for working decoded_content; else use plain 'content'.
    my $ua_ver = $ua->agent;
    $ua_ver =~ s|^.*/||g;
    $ua_ver =~ s|[^.\d]||g; 
    my $resp = $ua->request($req);
    $rc = $resp->is_success;
    if ($resp->is_success) {
        $$last_mod_ref = $resp->last_modified if (ref($last_mod_ref));
        return ($resp->is_success, split(/\n/,$resp->decoded_content)) if ($ua_ver >= 5.821);
        return ($resp->is_success, split(/\n/,$resp->content));
    }
    push @ret, $resp->status_line;
    return ($rc, @ret);
}

sub printSumsHashRef {
    my ($sumsRef) = @_;
    my $k;

    foreach my $i (keys(%$sumsRef)) {
        $k = nvrasepConvert($sumsRef->{$i});
        doLog($TPSMISC,$TPSLOG,"$i: $k\n");
    }
}
sub printNamesHashRef {
    my ($logLev,$pkgsRef) = @_;
    my ($lr, $k);

    # We might be given key->string or key->arrayRef.
    foreach my $i (keys(%{$pkgsRef})) {
        doLog($TPSMISC,$TPSDEBUG,"PackageName $i : ");
        $lr = $pkgsRef->{$i};
        if (ref($lr)) {
            foreach my $j (@$lr) {
                ($k,undef) = nvraConvert("$j");
                chomp($k);
                doLog($logLev,$TPSLOG,"\t${k}\n");
            }
        } else {
            ($k,undef) = nvraConvert("$lr");
            chomp($k);
            doLog($logLev,$TPSLOG," ${k}");
        }
        doLog($logLev,$TPSLOG,"\n");
    }
}
##########################
# printKeyRpt - print out output from pkgListByKey for debugging
# Useful since ListByKey is a reference to a hash whose values
# are references to arrays which consist of references to hashes
# that contain a package's N-V-R-A-Sum-Epoch-Srpm information.
# One could use Data::Dumper for a visualization, too.
# Inputs:
#  $hr     - reference to hash to print
# $logLev  - (optional) log level, default TPSTXT.
# $logType - (optional) log type, default TPSRPT.
#   (default values chosen for debug purposes)
sub printKeyRpt {
    my ($hr,$logLev,$logType) = @_;
    my $ln;
    $logLev = $TPSTXT if (!defined($logLev));
    $logType = $TPSRPT if (!defined($logType));
    foreach my $i (keys(%$hr)) {
        doLog($logLev,$logType,"KeyName $i : \n");
        # Value is a reference to an array.
        my $arrRef = $hr->{$i};
        foreach my $j (@$arrRef) {
            # each of these is a hashref from nvrToHRef
            $ln = "\t";
            foreach my $k (keys(%$j)) {
                $ln .= " $k: \"$j->{$k}\";";
            }
            doLog($logLev,$logType,"$ln\n");
        }
    }
}
######################################################################################
# specialCaseLoader - return a ref to array of hashrefs that contain special case info
#   that is relevant to a separate special-case checking routine.
# Inputs: filename to load, testTag to search for.
#   appendTo is an optional array reference, available in case you want to
#   append the contents of another file to an existing ruleset.
# Outputs: ref to (possibly empty) array of hashrefs
#          with $hr->{$key}==$value and $hr->{action}==$action.
# The format of the file *must* be:
#   <testTag>\t<action>\t<key>\t<value>[\t<key>\t<value>]+
# In short, you must have at least 4 items; you may have additional key/value pairs.
# Lines beginning with '#' or which are malformed will be silently ignored.
#
sub specialCaseLoader {
    my ($fname,$tagName,$appendTo) = @_;
    my @retArr = ();
    my $ret;

    $ret = ((defined($appendTo)) ? $appendTo : \@retArr);

    if (open(__SC,"<$fname")) {
        my $ln;
        while (defined($ln = <__SC>)) {
            chomp($ln);
            next if ($ln =~ m/^\s*#/);  # skip comments
            next if ($ln =~ m/^\s*$/);  # skip blank lines
            # separators == one or more tabs (allow for 'pretty' formatting in file).
            if ($ln =~ m/([^\t]+)\t+([^\t]+)\t+([^\t]+)\t+([^\t]+)/) {
                my @lnArr = split(/\t+/,$ln);
                my ($ttag,$taction) = @lnArr[0,1];
                if ($ttag =~ m/$tagName/i) {
                    my (%h, $dx);
                    $h{action} = $taction;
                    for ($dx = 2; $dx <= $#lnArr; $dx += 2) {
                        # an odd number of array elements should yield 'undef'.
                        $h{$lnArr[$dx]} = $lnArr[$dx+1];
                    }
                    push @$ret, \%h;
                }
            }
        }
        close(__SC);
    }
    return $ret;
}
#######################################################################
# specialCaseMultiLoader - read multiple keys from multiple files
# Inputs:
#   includeLocal: whether to use local special-case file (if present) 
#   scKeyName: see globs->{*_scFile}, this is the asterisk part.
#  lookupKeys: variable number of tags to locate in the file(s).
# Output: 
#   list of references; each is a return from specialCaseLoader
# Usage:
#   my ($a,$b,$c) = specialCaseMultiLoader(1,'rpm','a','b','c');
#   => reads $globs->{rpm_scFile} and $globs->{rpm_lscFile}
#   => looks for tags a, b, and c; returns list of refs, one per tag.
#######################################################################
sub specialCaseMultiLoader {
    my $includeLocal = shift;
    my $scKeyName = shift;
    my @lookupKeys = @_;
    my @ret = ();
    my @infiles = ();
    my $main_fileKey = "${scKeyName}_scFile";
    my $local_fileKey = "${scKeyName}_lscFile";
    my $localOkay = 0;

    if (($includeLocal) && (-r $globs->{$local_fileKey})) {
        doLog($TPSINFO,$TPSLOG,"Using additional local special-cases from: $globs->{$local_fileKey}\n");
        $localOkay = 1;
    }
    foreach my $lk (@lookupKeys) {
        my $tmp = specialCaseLoader($globs->{$main_fileKey}, $lk);
        $tmp = specialCaseLoader($globs->{$local_fileKey}, $lk, $tmp) if ($localOkay);
        push @ret, $tmp;
    }

    return @ret;
}
#######################################################################
# ensureNoStrayMix
# Note: caller should run updatePackageState() on non-nil return.
#######################################################################
sub ensureNoStrayMix {
    my ($condition, $instSumsRef, $instPkgsRef, $statesRef) = fetchPackageStates();
    my ($newPkgListRef, $oldPkgListRef, $newPkgHRef, $oldPkgHRef) = getGlobalLists();
    my $res = '';
    if (($condition eq 'mixed') || ($statesRef->{strayCnt} != 0)) {
        doLog($TPSTXT,$TPSLOG,"EnsureNoStrayMix:  Downgrading to avoid mixed/stray packages\n");
        $res = DowngradeTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                             $newPkgListRef,$oldPkgHRef,$newPkgHRef);
        doLog($TPSTXT,$TPSLOG,"EnsureNoStrayMix:  Downgrade returned: $res\n");
        if ($res ne 'PASS') {
            doLog($TPSINFO,$TPSLOG,
                  "If this test run does not pass, try to ensure that only ".
                  "Old packages are installed, and then re-run.\n");
        }
    }
    return $res;
}
#######################################################################
# VerifyTest
#######################################################################
sub VerifyTest {
    my ($instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef,$funcOptsRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # All of the @_ arguments are optional; fill them in below if anything's missing.
    my ($condition, $funcPkgStates);
    my ($hack21, $rmArch);
    my $multiLogMsg = '';
    my $multilibFail = 0;
    my $vt_debug = 0;
    my $reportFunc = 0;
    $tpsErrorText = ''; # Replace eventually with beginTest()
    beginTest('VerifyTest');

    $vt_debug = 1 if ((defined($debug) && $debug) || (exists($ENV{'VERBOSE'}) && (1 == $ENV{'VERBOSE'})));
    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT','DEP_OLDFILES_OUT');
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT');
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);
    # end of "fill in missing args" section

    # Until we do something to pass, well:
    $result = 'FAIL';

    my $isManual = 1;
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));

    # Already done by beginTest().
    # vlog#Print("\nVerifyTest =====================================\n");

    ($hack21, $rmArch) = handleAS21hack();

    # Find out what's installed
    ($condition, $instSumsRef, $instPkgsRef,$funcPkgStates) = updatePackageState();

    doLog($TPSINFO,$TPSLOG,"\n\nTPSINFO: VerifyTest: package state is: $condition\n");
    if (('none' eq $condition) || (('mixed' eq $condition) && (0 == $globs->{multiVersionOK}))) {
        # um, we don't have a consistent package set to verify --
        # thus we can't PASS it.
        doLog($TPSERROR,$TPSLOG,"ERROR: cannot test packages without a consistent state.  Current package set is: $condition\n");
        # log#Print "VerifyTest Returning: $result\n";
        $result = endTest($result, 'VerifyTest');
        return $result;
    }

    # Verify the unique packages on the list
    my @nativePkgs = ();       # exact `uname -m` match
    my @nearNativePkgs = ();   # related match; eg, i686/i386
    my @multilibPkgs = ();     # i386 on ia64, etc.
    my %longResults;           # detailed results hash.

    # $ENV{'ARCH'} contains the simplified version of "uname -m"
    # (that is, ARCH=i386 if `uname -m` = i686).  So don't use that.
    my $realArch = '';
    if (exists($ENV{'TRUE_ARCH'})) {
        $realArch = $ENV{'TRUE_ARCH'};
    } else {
        $realArch = `uname -m`;
        chomp $realArch;
    }

    # longResults (n=name,v=version,r=revision,a=arch); rpmOut=list of 'rpm -V' output lines
    # nvra { n v r a result error %rpmOut }

    # create/populate data structures...
    foreach my $msum (keys(%{$instSumsRef})) {
        my ($n,$v,$r,$a,$s,$e,$srpm) = split m/\n/m, $instSumsRef->{$msum};
        my $pkgNameArch = "${n}.${a}";
        my $fullName = "${n}-${v}-${r}.${a}";
        $longResults{$fullName} = {
                                   n => $n, v => $v, r => $r, a => $a,
                                   e => $e, srpm => $srpm,
                                   na => $pkgNameArch,
                                   nvr => "${n}-${v}-${r}",
                                   result => 'FAIL',
                                   error => 0,
                                   rpmOut => {},
                                   files => {},
                                   };
    }

    # Sanity Check: do we have multiple versions of the same package
    # installed?  Unless you're the kernel, it's probably NOT what you want,
    # so print a TPSHINT for analysis help.
    my $haveMultilib = 0;  # need more analysis later
    my $haveMultiples = 0; # possible error
    foreach my $P (keys(%longResults)) {
        my @seen = ();
        my $p = $longResults{$P};
        # Note that @seen should always gain at least 1 entry (pkg sees itself).
        foreach my $D (keys(%longResults)) {
            my $d = $longResults{$D};
            if ($p->{n} eq $d->{n}) {
                # same package name
                if ($p->{a} eq $d->{a}) {
                    # same arch
                    push @seen, $D;
                } else {
                    $haveMultilib = 1;
                }
            }
        }
        if ($#seen > 0) {
            $haveMultiples = 1;
            $seen[0] = ' '; # hide duplicate entry from user
            doLog($TPSHINT,$TPSLOG,"TPSHINT: possible problem, multiple copies of pkg present: " . join("\n",@seen) . "\n");
        }
    }

    # rpm -V returns:
    # 0 - success
    # 1 - verify errs: list of "...... w /path/file" on stdout
    # 1/other - error, with message (on stdout afaict).
    # foreach my $L (\@nativePkgs, \@nearNativePkgs, \@multilibPkgs) {
    foreach my $L (keys(%longResults)) {
        my $H = $longResults{$L};
        my $n = $H->{n};
        my $pn = $H->{nvr};
        my $i = $H->{na};
        my $na = $H->{na};

        ($childErr, $osErr, $evalErr) = (0,0,0);
        my $rpmOutput;
        my $verifyCommand = 'rpm -V ';

        if ($hack21) {
            # No multilib on AS2.1, thus $arch is disallowed in query
            $verifyCommand .= $pn; # n-v-r
        } else {
            $verifyCommand .= $L; # n-v-r.a
        }

        $rpmOutput = doRpmCommand($verifyCommand);
        $childerr = $? || 0;
        $osErr = $!;
        $evalErr = $@ || 0;
        $H->{error} = $childerr;

        if ((0 == $childerr) && (!$rpmOutput)) {
            # This one PASSes.
            $H->{result} = 'PASS';
        } else {
            # FIXME: Note that having rpmOutput can cause a failure: Explain It.
            # Stash each output line from rpm into a hashref (key by filename).
            my $R = $H->{rpmOut};
            if (($rpmOutput =~ m@/@) and (! ($rpmOutput =~ m/not installed/i))) {
                # we should have a list of X...X... c /path/file entries to parse
                foreach my $l (split m|\n|m, $rpmOutput) {
                    chomp($l);
                    my @chunks = split m|\s+|s, $l;
                    if ($#chunks > 0) {
                        my $fqFile = pop @chunks;
                        my $rest = join(' ',@chunks);
                        chomp($fqFile);
                        $R->{$fqFile} = $rest;
                    }
                }
            } elsif ($rpmOutput) {
                $R->{error} = $rpmOutput;
            }
        }
        print STDERR "==============================\n\n" if $vt_debug;
        # Hmm, if osErr is not 9, rpm had errors.  (9 means that the filehandle was fully read)
        # 9 == 'Bad file descriptor' fwiw.
        # Other error numbers should apparently be 0 under normal circumstances.
        # print STDERR "childErr = $childErr ; osErr = $osErr; evalErr = $evalErr;\n";
        printf STDERR "childErr = %d ; osErr = %s; evalErr = %d;\n", $childErr, $osErr, $evalErr if $vt_debug;
    }
    my $failCount = 0;
    # use smart approach for analysis
    # compare last key to each preceding key in list, looking for identical n-v-r
    # with differing a, with errors in one or the other.  Go through the rpmOut of any
    # pair thus identified.  Only flag errors that appear in both lists, or
    # non-native binaries.
    my @klist = (sort(keys(%longResults)));
    while ($#klist >= 0) {
        my $k = pop(@klist);
        my $A = $longResults{$k};
        # some updates contain multiple rpms, some of which are
        # single-arch, others of which are multilib.
        # So if we don't find multilib, use single-pkg pass/fail.
        my $foundMultilib = 0;
        # foreach my $i (@klist) {
        foreach my $i (sort(keys(%longResults))) {
            my $B = $longResults{$i};
            if (($A->{n} eq $B->{n}) && ($A->{v} eq $B->{v}) && ($A->{r} eq $B->{r}) && ($A->{a} ne $B->{a})) {
                # MULTILIB:  e.g., foo-1.0-1.i386.rpm and foo-1.0-1.x86_64.rpm.
                # Check for real failure...
                $foundMultilib = 1;
                # log#Print("codepath: haveMultilib: " . $A->{na} . "\n") if ($vt_debug);
                if (($A->{error} != 0) || ($B->{error} != 0)) {
                    # figure out whether it's really a failure
                    # log#Print("\n\ndoFailCmp OF " . $A->{na} . " and " . $B->{na} . "\n") if ($vt_debug);
                    my ($gotFail,$failText) = tpsDoFailCmp($realArch, $A, $B);
                    if ($gotFail != 0) {
                        $result = 'FAIL';
                        $multiLogMsg .= $failText;
                        $multilibFail = 1;
                        $failCount++;
                    } else {
                        if ($A->{error} != 0) {
                            doLog($TPSINFO,$TPSLOG,"TPSINFO: multilib compare returned okay despite verify issues with ". $A->{na} . "\n");
                        }
                    }
                } else {
                    # We wind up here for foo.arch1+foo.arch2 when both have a clean 'rpm -V'.
                    # well, hopefully both are marked PASS.  if not, report it.
                    doLog($TPSINFO,$TPSLOG,"TPSINFO: pass: " . $A->{na} . " and " . $B->{na} . "\n\n") if ($vt_debug);
                }
            } else {
                # non-multilib or mismatched package names/versions.
                doLog($TPSMISC,$TPSLOG,"SKIP: " . $A->{na} . " and " . $B->{na} . "\n\n") if ($vt_debug);
            }
        }
        if ((0 == $foundMultilib) && (0 != $A->{error})) {
            # A non-multilib package.
            my $x = $A->{rpmOut};
            my $x_na = $A->{na};
            # log#Print("DEBUG: foundMultilib 0 but error for: $x_na \n") if ($vt_debug);
            foreach my $fileName (keys(%$x)) {
                my ($xletters,$xtypes) = split m|\s+|s, $x->{$fileName};
                $xtypes = '' if (!defined($xtypes));
                $failCount++;
                $multiLogMsg .= ($x_na . ': ' . $fileName . ' ' . $xletters . ' ' . $xtypes . " [tps:B]\n");
            }
        } else {
            doLog($TPSMISC,$TPSDEBUG,"DEBUG: foundMultilib 0, PASS for: ". $A->{na} . "\n") if ($vt_debug);
        }
    }
    if ($failCount > 0) {
        my $keyText = "TPS verify test analysis tags:\n";
        $keyText .= "  tps:a -- verify errors on both arches\n";
        $keyText .= "  tps:b -- verify error on file not present in alternative arch\n";
        $keyText .= "  tps:c -- verify error on preferred binary/ELF file\n";
        $keyText .= "  tps:d -- significant type of verify error\n";
        $multiLogMsg .= "\n${keyText}\n";
        doLog($TPSFAILTXT,$TPSLOG,"result: verify test: FAIL:\n${multiLogMsg}\n");
    }
    $result = 'PASS' if (0 == $failCount);
    doLog($TPSINFO,$TPSLOG,"TPSINFO: built-in verifyTest result: $result\n");

    if ((defined($funcOptsRef)) && exists($funcOptsRef->{'passFail'}) && defined($funcOptsRef->{'passFail'})) {
        my $pfArgs = undef;
        if (exists($funcOptsRef->{'passFailArgs'}) && defined($funcOptsRef->{'passFail'})) {
            $pfArgs = $funcOptsRef->{'passFailArgs'};
        }
        $result = &{$funcOptsRef->{'passFail'}}($pfArgs,$funcPkgStates);
    }

    # vlog#Print("VerifyTest Returning: $result\n\n");
    $result = endTest($result, 'VerifyTest');
    return $result;
}

############################
# tpsMatchArch - find best arch match
#  (for tpsDoFailCmp)
# inputs: string, hashref, hashref: same as tpsDoFailCmp
# outputs: best-match hashref, or undef on error/unknown.
sub tpsMatchArch {
    my ($realArch, $A, $B) = @_;
    my $bestMatch = '';
    my ($ftReal, $ftA, $ftB);  # ft = FamilyType
    my ($archA, $archB);

    sub getFT {
        my ($rName) = @_;
        if ($rName =~ m/i[3-6]86/) {
            return 'i386';
        } elsif ($rName =~ m/ppc/i) {
            if ($rName =~ m/le/i) {
                return 'ppc64le';
            } elsif ($rName =~ m/64/) {
                return 'ppc64';
            } else {
                return 'ppc32';
            }
        } else {
            return $rName;
            # one of: ia64, x86_64, s390, s390x, we hope.
        }
    }
    $archA = $A->{a};
    $archB = $B->{a};
    $ftReal = getFT($realArch);
    $ftA = getFT($archA);
    $ftB = getFT($archB);

    if ($ftA ne $ftB) {
        return $A if ($ftReal eq $ftA);
        return $B if ($ftReal eq $ftB);
        # else... real arch is neither A nor B.  Ouch.
        doLog($TPSBUG,$TPSLOG,"TPSBUG: Got type $ftReal on this box, packages for $ftA and $ftB but cannot figure out what to do with $realArch / $archA / $archB");
        return undef;
    } else {
        # growl.  Looks like they're all the same.
        if ($ftA eq 'i386') {
            my ($v1, $v2, $v3) = ('','','');
            if ($realArch =~ m/i(.)86/) { $v1 = $1; }
            if ($archA =~ m/i(.)86/) { $v2 = $1; }
            if ($archB =~ m/i(.)86/) { $v3 = $1; }
            if ($v2 eq $v3) {
                doLog($TPSBUG,$TPSLOG,"TPSBUG: Got type $ftReal on this box, packages for $ftA == $ftB; or $realArch and $v2");
                return undef;
            }
            # now as numbers rather than strings
            if ($v2 > $v3) {
                return $A if ($v1 >= $v2);
                return $B;
            } else {
                return $B if ($v1 >= $v3);
                return $A;
            }
        } else {
            doLog($TPSBUG,$TPSLOG,"TPSBUG: Got type $ftReal on this box, packages for $ftA == $ftB but cannot figure out what to do");
            return undef;
        }
    }
}
############################
# tpsDoFailCmp
# realArch - real ("native") architecture such as i386
# A = %longResults hash pointer for a single package
# B = %longResults hash pointer for another single package
# Modifies A and B to reflect PASS/FAIL, writes to log, and
# returns 1 if it found a failure, 0 if everything PASSED.
sub tpsDoFailCmp {
    my ($realArch, $A, $B) = @_;
    my ($native,$compat);
    my $gotFail = 1;
    my $failText = '';
    my $R1 = $A->{rpmOut};
    my $R2 = $B->{rpmOut};
    my $invA = $A->{files};
    my $invB = $B->{files};
    my ($nameA,$nameB);
    my ($aCnt, $bCnt) = (0, 0);

    sub isELF {
        my ($fn) = @_;
        my $res = `file $fn 2>&1 `;
        return 1 if ($res =~ m/ELF/);
        return 0;
    }

    if ($A->{a} eq $B->{a}) {
        # Erm. A and B should really be different.  What kind of error should we throw?
        return($gotFail,"TPSERROR: internal error, got two identical pkgs in tpsDoFailCmp");
    }
    if ($A->{n} ne $B->{n}) {
        return($gotFail,"TPSERROR: internal error, got two unrelated pkgs in tpsDoFailCmp");
    }

    if (!$realArch) {
        $realArch = `uname -m`;
        chomp($realArch);
    }

    my $pref = tpsMatchArch($realArch, $A, $B);
    return($gotFail,"TPSERROR: tpsMatchArch failed") unless (defined($pref));

    # If we have 2 different arches installed, we're *not* on RHEL2.1, hooray.
    # Get list of files present in each RPM, stash into inv{A,B}.
    $nameA = ($A->{n} . '-' . $A->{v} . '-' . $A->{r} . '.' . $A->{a});
    $nameB = ($B->{n} . '-' . $B->{v} . '-' . $B->{r} . '.' . $B->{a});

    doLog($TPSMISC,$TPSDEBUG,"\n\n=======\nnew cmp: $nameA versus $nameB \n") if ($vt_debug);
    foreach my $l (split m|\n|m,`rpm -ql $nameA`) {
        chomp($l);
        $invA->{"$l"} = $l;
    }

    foreach my $l (split m|\n|m,`rpm -ql $nameB`) {
        chomp($l);
        $invB->{"$l"} = $l;
    }

    # how many verify failures do we have, and where are they?
    foreach my $i (keys(%$R1)) {
        $aCnt++;
    }
    foreach my $i (keys(%$R2)) {
        $bCnt++;
    }

    ### Here are the things that RHEL4-rpm can report.
    ### Anything marked with '*' is something we'll still
    ### consider to be an error.  (easily done with the hash below).
    ### * = error; + = always error
    #  *S file Size differs
    #  *M Mode differs (includes permissions and file type)
    #  *5 MD5 sum differs
    # +*D Device major/minor number mismatch
    #  *L readLink(2) path mismatch
    # +*U User ownership differs
    # +*G Group ownership differs
    #   T mTime differs
    # +*C selinux Context differs

    # Here's a list of types that could be encountered:
    #  c %config configuration file.
    #  d %doc documentation file.
    #  g %ghost file (i.e. the file contents are not included in the package payload).
    #  l %license license file.
    #  r %readme readme file.
    #  [this is why we ignore $xtypes below...]

    my @errLetters = qw( S M 5 D L U G C );
    my @failLetters = qw( M D U G C );
    my @noErrLetters = qw( T );

    # we use $p as the preferred-arch list (but as ref to rhnOutput).
    my ($x,$y,$xi,$yi,$p);
    if ($pref == $A) {
        $p = $R1;
    } else {
        $p = $R2;
    }

    my $x_na = '';
    my $failCount = 0;
    # Hmm, probably don't need to check B->A as well, but
    # the loop is here should we need to.
    for (my $loopCount = 0; $loopCount < 1; $loopCount++) {
        # if ($aCnt > $bCnt) {
        if (0 == $loopCount) {
            ($x,$y,$xi,$yi) = ($R1,$R2,$invA,$invB);
            $x_na = $A->{na};
        } else {
            ($x,$y,$xi,$yi) = ($R2,$R1,$invB,$invA);
            $x_na = $B->{na};
        }

        foreach my $fileName (keys(%$x)) {
            # log#Print("Checking: $fileName in " . $x_na . "\n") if ($vt_debug);
            my ($xletters,$xtypes) = split m|\s+|s, $x->{$fileName};
            $xtypes = '' if (!defined($xtypes));
            # we now have stuff like:
            # xletters   xtypes     fileName
            # ........C  c          /etc/X11/fs/config
            # SM5......             /etc/X11/xorg.conf
            # missing               /etc/redhat-release-rhel2.1as
            if (exists($y->{$fileName})) {
                # failed on both arches, so it instantly fails.
                $failCount++;
                $failText .= ($x_na . ': ' . $fileName . ' ' . $xletters . ' ' . $xtypes . " [tps:a]\n");
            } else {
                # only failed on current arch
                # so it's only a failure if:
                # altArch doesn't have it, or: isBinary but NotPreferred, or: has a $failLetter.
                if (!exists($yi->{$fileName})) {
                    # altArch doesn't have it, and we have an error here.
                    $failCount++;
                    $failText .= ($x_na . ': ' . $fileName . ' ' . $xletters . ' ' . $xtypes . " [tps:b]\n");
                } elsif (($fileName =~ m|/bin/|) or (isELF($fileName))) {
                    # if binary, we're preferred, and have an errLetter error == FAIL.
                    # NB: stuff in /bin/ can be a script with a different timestamp...
                    if ($x == $p) {
                        my $subCount = 0;
                        foreach my $ltr (@failLetters) {
                            if ($xletters =~ m/$ltr/) {
                                $subCount++;
                            }
                        }
                        $subCount++ if ($xletters =~ m/missing/i);
                        if ($subCount > 0) {
                            $failCount++;
                            $failText .= ($x_na . ': ' . $fileName . ' ' . $xletters . ' ' . $xtypes . " [tps:c]\n");
                        }
                    }
                    # if we're not preferred and $y had no error, that's fine:
                    # for instance, this is the 32-bit package and we have a 64-bit binary.
                } else {
                    # for certain types of rpm errors, we should always generate a failure.
                    my $subCount = 0;
                    foreach my $ltr (@failLetters) {
                        if ($xletters =~ m/$ltr/) {
                            $subCount++;
                        }
                    }
                    $subCount++ if ($xletters =~ m/missing/i);
                    if ($subCount != 0) {
                        $failCount++;
                        $failText .= ($x_na . ': ' . $fileName . ' ' . $xletters . ' ' . $xtypes . " [tps:d]\n");
                    }
                }
            }
        }
    }
    if ($failCount > 0) {
        # we found real errors
        $gotFail = 1;
    } else {
        # PASS
        $gotFail = 0;
    }

    doLog($TPSMISC,$TPSDEBUG,"\n\n:::: VERIFY: RET $gotFail cmp: $nameA versus $nameB \n") if ($vt_debug);
    return ($gotFail,$failText);
}

# sorry, tmp function for sanity; will clean up later.
sub nvrlistFromPkgHref {
    my ($oldP, $instSumsRef, $newP) = @_;
    my (@delPkgs, %tmp, $pspec);
    my ($n,$v,$r,$a,$s,$e,$srpm);
    my ($hack21, $rmArch) = handleAS21hack();
    @delPkgs = ();

    foreach my $k (keys(%{$oldP})) {
        my $i = $oldP->{$k};
        while ($i) {
            ($n,$v,$r,$a,$s,$e,$srpm,$i) = split /\n/, $i, 8;
            if ($hack21) {
                $pspec = "${n}-${v}-${r}";
            } else {
                $pspec = "${n}-${v}-${r}.${a}";
            }
            if (exists($instSumsRef->{$s})) {
                push @delPkgs, $pspec;
                $tmp{$pspec} = 1;
            }
        }
    }
    if (defined($newP)) {
        foreach my $k (keys(%{$newP})) {
            my $i = $newP->{$k};
            while ($i) {
                ($n,$v,$r,$a,$s,$e,$srpm,$i) = split /\n/, $i, 8;
                $pspec = "${n}-${v}-${r}.${a}";
                $pspec = "${n}-${v}-${r}" if ($hack21);
                if ((!exists($tmp{$pspec})) && exists($instSumsRef->{$s})) {
                    push @delPkgs, $pspec;
                    $tmp{$pspec} = 1;
                }
            }
        }
    }
    return \@delPkgs;
}
sub keyCount {
    my ($ref) = @_;
    my @keylist = keys(%$ref);
    return ($#keylist + 1);

}

sub is_x86 {
    my ($s) = @_;
    return 1 if ($s  =~ m/i[3-6]86/);
    return 1 if ($s  =~ m/ia32e*/);
    return 1 if ($s  =~ m/athlon/);
    return 0;
}
sub rpmNameInPkgList {
    my ($rName,$pList) = @_;
    foreach my $f (@$pList) {
	return $f if ($rName eq basename($f));
    }
    return '';
}
###################
# selectPkgListByState
#   Allow selection of installed or uninstalled packages 
# from the new* or old* filelists.  Highly useful since RPM
# will toss errors (like cookies!) when you ask it to install
# a pkg which is already installed; or delete one that is not present.
# Inputs:
#  StatePtr (as obtained from determinePackageSet's last return)
#  'new' or 'old': which filelist to use
#  'installed' or 'uninstalled': which to select
#  ListPtr: list of old|new /full/paths/to/rpms
# Outputs:
#  list of packages (possibly empty) which match the search
# Notes:
#  - This function does NOT refresh state info; do that before calling it.
#  - This function only works for new|old lists, not src lists.
#  - If you typo "installed" or "old", you will get 
#    "uninstalled" or "new", respectively.
#
sub selectPkgListByState {
    my ($stateRef,$newOldArg,$instUn,$listRef) = @_;
    my $pkSums = $stateRef->{pkSums};
    my $wantInst = (($instUn eq 'installed') ? 1 : 0);
    my $newOld = (($newOldArg eq 'old') ? 'old' : 'new');
    my @nvraList = ();
    my @hitList = ();
    my $k;

    foreach my $pk (keys(%$pkSums)) {
	$k = $pkSums->{$pk};
	if ((1 == $k->{$newOld}) && ($wantInst == $k->{inst})) {
	    push @nvraList, $k->{nvra};
	}
    }
    foreach my $p (@nvraList) {
	$pp = "/${p}.rpm";
	my @ret = grep(m|\Q$pp\E$|,@$listRef);
	if ($#ret >= 0) {
	    push @hitList, @ret;
	}
    }
    return(@hitList);
}
###################
# weedMLDebug - Weed the MultiLib Debuginfo packages from lists.
#  When both native arch and multilib -debuginfo are present, use only one.
#  Return both a (possibly modified) pkgList and nvrHref containing only the
#  preferred-arch packages -- eg, the ones expected to install if both are supplied to rpm.
sub weedMLDebug {
    my ($pkgList,$nvrHref) = @_;
    my ($n,$t,$t2,$rpmfrag,$rpmName,@goodList,%goodHash);
    my $trueArch = $globs->{trueArch};
    foreach my $na (keys(%{$nvrHref})) {
        $t = nvrToHRef($nvrHref->{$na});
        $n = $t->{'name'};
	$prefer_na = "${n}.${trueArch}";
	($rpmfrag,undef) = nvraConvert($nvrHref->{$na});
	$rpmName = $rpmfrag . ".rpm";
	if ($n =~ m/-debuginfo/) {
	    if ($na ne $prefer_na) {
		if (exists($nvrHref->{$prefer_na})) {
		    #### DROP THIS ONE
		    doLog($TPSINFO,$TPSLOG,"Discarding: $rpmName to avoid unsupported conflicts with $na\n");
		    next;
		}; # else save it (done below)
	    };     # else save it (as below)
	}
	# save the rpm to the "good" list and proceed.
	$t2 = rpmNameInPkgList($rpmName,$pkgList);
	push @goodList, $t2 if ($t2);
	$goodHash{$na} = $nvrHref->{$na};
    }
    return (\@goodList,\%goodHash);
}
###################
# weedOut86 - when both i386 and higher ia32 arches are specified, use only one.
#  Return both a (possibly modified) pkgList and nvrHref containing only the
#  preferred-arch packages -- eg, the ones expected to install if both are supplied to rpm.
#  (hmm, this routine is ugly, and there ought to be a better way to deal with it.)
sub weedOut86 {
    my ($pkgList,$nvrHref) = @_;
    my $trueArch = $globs->{trueArch};
    my (%native,%nativeN,%foreign,%foreignN,$t,$t2,$n,$n2);
    my $useArch = $trueArch;
    my @nogood = ();
    my @newList = ();

    # print STDERR "working with truearch: $trueArch\n";
    # we are x86-specific... but, alas, multilib, too.
    unless (($trueArch =~ m/^i.86$/) || 
	    ($trueArch =~ m/^ia32e*$/i) ||
	    ($trueArch =~ m/x86_64/i)) {
	return ($pkgList,$nvrHref);
    }
    if ($trueArch =~ m/x86_64/i) {
	# use a "native" arch of i686 for multilib.
	$useArch = 'i686';
    }

    foreach my $na (keys(%{$nvrHref})) {
        # each $na is "name.arch", and $nvrHref->{$na} is "nameVerRevArchMd5Sum" separated by "\n".
        $t = nvrToHRef($nvrHref->{$na});
        $n = $t->{'name'};
        if ($t->{'arch'} eq $useArch) {
	    # example: foo.i686
            $native{$na} = $nvrHref->{$na};
            $nativeN{$n} = $nvrHref->{$na};
        } else {
	    # example: foo.i386
            $foreign{$na} = $nvrHref->{$na};
            $foreignN{$n} = $nvrHref->{$na};
        }
    }

    # Debugging:
    # my $natCnt = keyCount(\%native);
    # my $frnCnt = keyCount(\%foreign);
    # print STDERR "keyCounts: n $natCnt ; f $frnCnt\n";

    # if we only had one arch, we're done.
    return ($pkgList,$nvrHref) if (0 >= (keyCount(\%native)));
    return ($pkgList,$nvrHref) if (0 >= (keyCount(\%foreign)));

    # if we have both native and foreign with both arches being x86, discard foreign.
    foreach $n (keys(%nativeN)) {
        if (exists($foreignN{$n})) {
            $t  = nvrToHRef($nativeN{$n});
            $t2 = nvrToHRef($foreignN{$n});
            if (is_x86($t->{'arch'}) && is_x86($t2->{'arch'})) {
                my $x = $t2->{'arch'};
                my ($rpmfrag,undef) = nvraConvert($foreign{"${n}.${x}"});
                push @nogood, ($rpmfrag . '.rpm');
                # Hmm: print debug message here?
                doLog($TPSINFO,$TPSLOG,"weedOut86: ignoring extra package: ${n}.${x}\n");
                delete $foreign{"${n}.${x}"};
                delete $foreignN{$n};
            }
        }
    }
    # reassemble.
    foreach my $na (keys(%foreign)) {
        $native{$na} = $foreign{$na};
    }
    # process package list.
    foreach $n (@{$pkgList}) {
        my $bad = 0;
        $t = basename($n);
        foreach $t2 (@nogood) {
            $bad = 1 if ($t2 eq $t);
        }
        push @newList, $n unless ($bad);
    }

    return (\@newList,\%native);
}

####################################
# weedOutDebug - modify pkgNameList and nvrHash
# in place to get rid of -debuginfo packages
# (used by tps-rhnqa)
sub weedOutDebug {
    my ($listRef,$hashRef) = @_;
    my $t;
    my @badPkgs = ();

    foreach my $k (keys(%$hashRef)) {
        $t = nvrToHRef($hashRef->{$k});
        if ($t->{'name'} =~ m/debuginfo/) {
            # got a debuginfo package here...
            push @badPkgs, ($t->{'name'} .'-'. $t->{'ver'} .'-'. $t->{'rel'} .'.'. $t->{'arch'} . '.rpm');
            delete $hashRef->{$k};
        }
    }
    my $i = -1;
    my $foundOne = 1;
    my $bn = '';
    my @lst = @$listRef;
    foreach my $pkg (@lst) {
        $i++;
        $foundOne = 0;
        $bn = basename($pkg);
        foreach my $p (@badPkgs) {
            if ($bn eq $p) {
                $foundOne = 1;
                doLog($TPSINFO,$TPSLOG,"INFO: ignoring debuginfo: $p\n");
            }
        }
        if ($foundOne) {
            splice(@$listRef,$i,1);
            $i--;
        }
    }
    # done.  mods done in place.
}
####################################
# warnOfExtraOutput
sub warnOfExtraOutput {
    my ($what,$regularOut) = @_;
    my $doMsg = 0;
    my @extraOut = split(/\n/,$regularOut);
    
    if (($#extraOut > 0) || ($regularOut =~ m/warn/i)) {
	$doMsg = 1;
    } elsif (0 == $#extraOut) {
	my $ln = $extraOut[0];
	if (($ln !~ /^\s*$/) || (length($ln) > 4)) {
	    $doMsg = 1;
	}
    }
    if (1 == $doMsg) {
	doLog($TPSWARN,$TPSLOG, 
	      "$what produced extra output or warning text, see log above.\n");
    }
}
sub checkErrAfterFilter {
    my ($suspectOutput,$newStateRef) = @_;
    # package names are: $newStateRef->{pkSums}->{eachKey}->{n}
    # 'pkSums' => {
    #       '24e331747676546973baa552d0dee4fe' => {
    #                                              'epoch' => '(none)',
    #                                              'n' => 'libgpg-error-debuginfo',
    my @falsePositives = ( '(platform error handling) daemon:' );
    my ($pkSumRef,$pRef,$tmp,$tmpRef,@theNames,%pkgNames);
    $pkSumRef = $newStateRef->{pkSums};
    foreach my $k (keys(%$pkSumRef)) {
	$tmpRef = $pkSumRef->{$k};
	$tmp = $tmpRef->{n};
	$pkgNames{$tmp} = 1;
    }
    @theNames = keys(%pkgNames);
    foreach my $name (@theNames) {
	$suspectOutput =~ s/\Q$name\E//gm;
    }
    foreach my $fp (@falsePositives) {
	$suspectOutput =~ s/\Q$fp\E//gm;
    }
    return($suspectOutput =~ m/(^|\W)(error|fail(ed)*)(\W|$)/i);
}
###############################################################
# DeleteTest
###############################################################
sub DeleteTest {
    my ($condition, $instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # my ($delPkgsListRef);
    my ($oldCondition, $curCondition, $pkgStateRef);
    my ($hack21, $rmArch);
    my $testType = 'Performed';
    my $isManual = 1;
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));

    $tpsErrorText = ''; # Replace eventually with beginTest()
    beginTest('DeleteTest');

    # All of the @_ arguments are optional; fill them in below if anything's missing.
    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT','DEP_OLDFILES_OUT');
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT');
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);
    # end of "fill in missing args" section

    # vlog#Print("\nDeleteTest =====================================\n");

    ($hack21, $rmArch) = handleAS21hack();

    # Find out what we're supposed to delete
    $oldCondition = $condition;
    ($curCondition, $instSumsRef,
     $instPkgsRef, $pkgStateRef) = updatePackageState();
    $condition = $curCondition;

    # Set up string of packages to be deleted; ensure that only
    # installed packages are selected (BZ 1012248).
    my $deleteThese = '';
    if ('new' eq $condition) {
        # $delPkgsListRef = nvrlistFromPkgHref($newPkgHRef,$instSumsRef);
        # $deleteThese = selectFromPKSums($pkgStateRef->{pkSums},'new','nvr');
        $deleteThese = selectPKSumData('nvra', {'new' => 1, 'inst' => 1});
    } elsif ('old' eq $condition) {
        # $delPkgsListRef = nvrlistFromPkgHref($oldPkgHRef,$instSumsRef);
        # $deleteThese = selectFromPKSums($pkgStateRef->{pkSums},'old','nvr');
        $deleteThese = selectPKSumData('nvra', {'old' => 1, 'inst' => 1});
    } elsif ('mixed' eq $condition) {
        # $delPkgsListRef = nvrlistFromPkgHref($oldPkgHRef,$instSumsRef,$newPkgHRef);
        # $deleteThese = selectFromPKSums($pkgStateRef->{pkSums},'old','nvr');
        $deleteThese = selectPKSumData('nvra', {'old' => 1, 'inst' => 1});
        # $deleteThese .= selectFromPKSums($pkgStateRef->{pkSums},'new','nvr');
        $deleteThese .= selectPKSumData('nvra', {'new' => 1, 'inst' => 1});
        # $deleteThese .= selectFromPKSums($pkgStateRef->{pkSums},'stray','nvr');
        $deleteThese .= selectPKSumData('nvra', {'stray' => 1, 'inst' => 1});
    } else {
        # none.  so what are we deleting?
        # maybe stray?
        # $deleteThese = selectFromPKSums($pkgStateRef->{pkSums},'stray','nvr');
        $deleteThese = selectPKSumData('nvra', {'stray' => 1, 'inst' => 1});
        # kill whitespace...
        $deleteThese =~ s/^\s+//; $deleteThese =~ s/\s+$//;
        if ($deleteThese) {
            doLog($TPSTXT,$TPSRPT,"Delete Test: Deleting STRAY packages.\n");
        }
    }
    # kill whitespace...
    $deleteThese =~ s/^\s+//; $deleteThese =~ s/\s+$//;
    if (!$deleteThese) {
        # If there's nothing to delete, we're done now, so return.
        $result = 'PASS';
        doLog($TPSTXT,$TPSRPT,"Delete Test: none of the packages for this errata are installed.  Result is N/A:PASS.\n");
        $result = endTest($result, "DeleteTest (N/A:PASS)");
        return $result;
    } 

    # Do the deletion work...
    $result = 'FAIL';
    ($childErr, $osErr, $evalErr) = (0,0,0);
    my $rpmOutput;
    my $deleteCommand;
    # $deleteCommand = 'rpm -e ' . join(' ',@{$delPkgsListRef});
    $deleteCommand = "rpm -e $deleteThese";
    $rpmOutput = doRpmCommand($deleteCommand);
    $childerr = $? ;
    $osErr = $!;
    $evalErr = $@;
    # print STDERR "==============================\n\n";
    # Hmm, if osErr is not 9, rpm had errors.  (9 means that the filehandle was fully read)
    # 9 == 'Bad file descriptor' fwiw.
    # Other error numbers should apparently be 0 under normal circumstances.
    # print STDERR "childErr = $childErr ; osErr = $osErr; evalErr = $evalErr;\n";
    # printf STDERR "childErr = %d ; osErr = %d; evalErr = %d;\n", $childErr, $osErr, $evalErr;
    # print STDERR "rpmOutput: $rpmOutput\n";

    my (%sums,%pkgs,@l, $lr, $k);
    # print "got $condition packages installed\n";
    %sums = %{$instSumsRef};
    %pkgs = %{$instPkgsRef};
    ######### verify contents of %sums
    ## printSumsHashRef($instSumsRef);
    ######### verify contents of %pkgs
    ## printNamesHashRef($instPkgsRef);

    my ($newCondition,
        $newInstSumsRef,
        $newInstPkgsRef,$newStateRef) = updatePackageState();

    my $hasOutputErr = 0;
    if ($rpmOutput =~ m/(^|\W)(error|fail(ed)*)(\W|$)/i) {
	$hasOutputErr = checkErrAfterFilter($rpmOutput,$newStateRef);
    }
    if (('none' eq $newCondition) && !$hasOutputErr) {
	warnOfExtraOutput('Deletion',$rpmOutput);
        $result = 'PASS';
    } else {
        my $depFails = hasOnlyDepFailure($rpmOutput);
        if ($depFails > 0) {
            $testType = 'Prevented';
            $result = 'PASS';
            doLog($TPSTXT,$TPSLOG,"Delete test: deletion correctly prevented by $depFails dependencies.\n");
        } else {
            if ($hasOutputErr && ('none' eq $newCondition)) {
                # rpmOutput with error/fail in it causes a failure -- alert user in case some file/rpm matches.
                doLog($TPSFAILTXT,$TPSLOG,"Error|Fail string detected in rpmOutput, although package state is 'none'.\n");
            }
            doLog($TPSFAILTXT,$TPSLOG,  "Delete test FAILED\n");
            doLog($TPSFAILTXT,$TPSLOG,  "Output from RPM Command:\n");
            doLog($TPSFAILTXT,$TPSLOG,  "$rpmOutput\n");
            doLog($TPSFAILTXT,$TPSLOG,  ("Old packages: " . join(' ',@{$oldPkgListRef}) . "\n"));
            doLog($TPSFAILTXT,$TPSLOG,  ("New packages: " . join(' ',@{$newPkgListRef}) . "\n"));
            doLog($TPSFAILTXT,$TPSLOG,  "Packages on system after delete attempt - $newCondition -\n");
            printNamesHashRef($TPSFAILTXT, $newInstPkgsRef);
            $result = 'FAIL';
        }
    }
    # vlog#Print("DeleteTest (${testType}) Returning: $result\n\n");
    $result = endTest($result, "DeleteTest (${testType})");
    return $result;
}
#############################################################
# InstallTest
#############################################################
sub InstallTest {
    my ($instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef,$funcOptsRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # All of the @_ arguments are optional; fill them in below if anything's missing.
    my ($condition);
    my $isManual = 1;
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));

    $tpsErrorText = ''; # Replace eventually with beginTest()
    beginTest('InstallTest');

    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT','DEP_OLDFILES_OUT');
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT');
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);

    ($condition, $instSumsRef, $instPkgsRef,$statesRef) = updatePackageState();

    # end of "fill in missing args" section

    # vlog#Print("\nInstallTest =====================================\n");

    # Do the install work...
    $result = 'FAIL';
    ($childErr, $osErr, $evalErr) = (0,0,0);
    my $rpmOutput;
    my $installCommand = 'rpm -i ' . join(' ',@{$newPkgListRef});
    $rpmOutput = doRpmCommand($installCommand);
    $childerr = $? ;
    $osErr = $!;
    $evalErr = $@;
    # print STDERR "==============================\n\n";
    # Hmm, if osErr is not 9, rpm had errors.  (9 means that the filehandle was fully read)
    # 9 == 'Bad file descriptor' fwiw.
    # Other error numbers should apparently be 0 under normal circumstances.
    # print STDERR "childErr = $childErr ; osErr = $osErr; evalErr = $evalErr;\n";
    # printf STDERR "childErr = %d ; osErr = %d; evalErr = %d;\n", $childErr, $osErr, $evalErr;
    # print STDERR "rpmOutput: $rpmOutput\n";

    my (%sums,%pkgs,@l, $lr, $k);
    # print "got $condition packages installed\n";
    %sums = %{$instSumsRef};
    %pkgs = %{$instPkgsRef};
    ######### verify contents of %sums
    ## printSumsHashRef($instSumsRef);
    ######### verify contents of %pkgs
    ## printNamesHashRef($instPkgsRef);

    # print STDERR "determinePackageState from InstallTest\n";
    my ($newCondition,
        $newInstSumsRef,
        $newInstPkgsRef,$funcPkgStates) = updatePackageState();

    if ((defined($funcOptsRef)) && exists($funcOptsRef->{'passFail'}) && defined($funcOptsRef->{'passFail'})) {
        my $pfArgs = undef;
        if (exists($funcOptsRef->{'passFailArgs'}) && defined($funcOptsRef->{'passFail'})) {
            $pfArgs = $funcOptsRef->{'passFailArgs'};
        }
        $result = &{$funcOptsRef->{'passFail'}}($pfArgs, $funcPkgStates);
    } else {
        my $hasOutputErr = 0;
	if ($rpmOutput =~ m/(^|\W)(error|fail(ed)*)(\W|$)/i) {
	    $hasOutputErr = checkErrAfterFilter($rpmOutput,$funcPkgStates);
	}
        if (('new' eq $newCondition) && !$hasOutputErr) {
	    warnOfExtraOutput('Install',$rpmOutput);
            $result = 'PASS';
        } else {
            if ($hasOutputErr && ('new' eq $newCondition)) {
                # rpmOutput with error/fail in it causes a failure -- alert user in case some file/rpm matches.
                doLog($TPSFAILTXT,$TPSLOG,"Error|Fail string detected in rpmOutput, although new packages are present.\n");
            }
            doLog($TPSFAILTXT,$TPSLOG, "Install test FAILED\n");
            doLog($TPSFAILTXT,$TPSLOG, "Output from RPM Command:\n");
            doLog($TPSFAILTXT,$TPSLOG, "$rpmOutput\n");
            doLog($TPSFAILTXT,$TPSLOG, ("Old packages: " . join(' ',@{$oldPkgListRef}) . "\n"));
            doLog($TPSFAILTXT,$TPSLOG, ("New packages: " . join(' ',@{$newPkgListRef}) . "\n"));
            doLog($TPSFAILTXT,$TPSLOG, "Packages on system after install attempt - $newCondition -\n");
            printNamesHashRef($TPSFAILTXT, $newInstPkgsRef);
            $result = 'FAIL';
        }
    }
    # vlog#Print("InstallTest Returning: $result\n\n");
    $result = endTest($result, 'InstallTest');
    return $result;
}
######################################################################
# DowngradeTest
######################################################################
sub DowngradeTest {
    my ($instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # All of the @_ arguments are optional; fill them in below if anything's missing.
    my ($condition,$pkgStateRef);
    my $isManual = 1;
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));

    $tpsErrorText = ''; # Replace eventually with beginTest()
    beginTest('DowngradeTest');

    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT','DEP_OLDFILES_OUT');
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT');
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);

    # Unconditionally get latest package info so that deleteExtraPackages() can work.
    ($condition, $instSumsRef,
     $instPkgsRef,$pkgStateRef) = updatePackageState();

    # Do the downgrade work...
    # First delete any new packages that weren't in the old set...
    deleteExtraPackages($newPkgHRef,$oldPkgHRef,$pkgStateRef->{pkSums});
    # Update info after any extra pkgs have been nuked
    ($condition, $instSumsRef,
     $instPkgsRef,$pkgStateRef) = updatePackageState();
    my $rpmOutput;
    my $skippedActualDowngrade = 0;
    my @oldUnPkgList = selectPkgListByState($pkgStateRef,'old','uninstalled',$oldPkgListRef);
    if (scalar(@oldUnPkgList) <= 0) {
        # There are no old packages to downgrade *to*...
        $rpmOutput = 'rpm command skipped, there are no old, uninstalled packages to downgrade to.';
        doLog($TPSWARN,$TPSLOG,"No old, uninstalled packages found.  Skipping downgrade command.\n");
        $skippedActualDowngrade = 1;
    } else {
        # Now try a downgrade...
        $result = 'FAIL';
        ($childErr, $osErr, $evalErr) = (0,0,0);
	# Note: using only Uninstalled OldPkgs
        my $downgradeCommand = 'rpm -U --oldpackage ' . join(' ',@oldUnPkgList);
        $rpmOutput = doRpmCommand($downgradeCommand);
        $childerr = $? ;
        $osErr = $!;
        $evalErr = $@;
        doLog($TPSMISC,$TPSLOG,"==============================\n\n");
        # Hmm, if osErr is not 9, rpm had errors.  (9 means that the filehandle was fully read)
        # 9 == 'Bad file descriptor' fwiw.
        # Other error numbers should apparently be 0 under normal circumstances.
        doLog($TPSCMDOUT,$TPSLOG,"childErr = $childErr ; osErr = $osErr; evalErr = $evalErr;\n");
        # printf STDERR "childErr = %d ; osErr = %d; evalErr = %d;\n", $childErr, $osErr, $evalErr;
        doLog($TPSCMDOUT,$TPSLOG,"rpmOutput: $rpmOutput\n");
    }
    my (%sums,%pkgs,@l, $lr, $k);
    # print "got $condition packages installed\n";
    %sums = %{$instSumsRef};
    %pkgs = %{$instPkgsRef};
    ######### verify contents of %sums
    ## printSumsHashRef($instSumsRef);
    ######### verify contents of %pkgs
    ## printNamesHashRef($instPkgsRef);

    # print STDERR "determinePackageState from DowngradeTest\n";
    my ($newCondition,
        $newInstSumsRef,
        $newInstPkgsRef,$newStateRef) = updatePackageState();

    my $hasOutputErr = 0;
    if ($rpmOutput =~ m/(^|\W)(error|fail(ed)*)(\W|$)/i) {
        $hasOutputErr = checkErrAfterFilter($rpmOutput,$newStateRef);
    }

    if (('old' eq $newCondition) && !$hasOutputErr) {
	warnOfExtraOutput('Downgrade',$rpmOutput);
        $result = 'PASS';
    } elsif (('none' eq $newCondition) && ($skippedActualDowngrade)) {
        $result = 'PASS';
    } else {
        if ($hasOutputErr && ('old' eq $newCondition)) {
            # rpmOutput with error/fail in it causes a failure -- alert user in case some file/rpm matches.
            doLog($TPSFAILTXT,$TPSLOG,"Error|Fail string detected in rpmOutput, although old packages are present.\n");
        }
        doLog($TPSFAILTXT,$TPSLOG,"Downgrade test FAILED\n");
        doLog($TPSFAILTXT,$TPSLOG,"Output from RPM Command:\n");
        doLog($TPSFAILTXT,$TPSLOG,"$rpmOutput\n");
        doLog($TPSFAILTXT,$TPSLOG,("Old packages: " . join(' ',@{$oldPkgListRef}) . "\n"));
        doLog($TPSFAILTXT,$TPSLOG,("New packages: " . join(' ',@{$newPkgListRef}) . "\n"));
        doLog($TPSFAILTXT,$TPSLOG,"Packages on system after downgrade attempt - $newCondition -\n");
        printNamesHashRef($TPSFAILTXT, $newInstPkgsRef);
        $result = 'FAIL';
    }

    $result = endTest($result, 'DowngradeTest');
    return $result;
}
#################################################################
# UpgradeTest
#################################################################
sub UpgradeTest {
    my ($instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # All of the @_ arguments are optional; fill them in below if anything's missing.
    my ($condition);
    my $isManual = 1;
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));

    $tpsErrorText = ''; # Replace eventually with beginTest()
    beginTest('UpgradeTest');

    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT', 'DEP_OLDFILES_OUT'); 
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT'); 
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);

    ($condition, $instSumsRef,
     $instPkgsRef,$statesRef) = updatePackageState();

    # end of "fill in missing args" section

    # vlog#Print("\nUpgradeTest =====================================\n");

    # Do the upgrade work...
    $result = 'FAIL';
    ($childErr, $osErr, $evalErr) = (0,0,0);
    my $rpmOutput;
    my $upgradeCommand = 'rpm -U ' . join(' ',@{$newPkgListRef});
    $rpmOutput = doRpmCommand($upgradeCommand);
    $childerr = $? ;
    $osErr = $!;
    $evalErr = $@;
    # print STDERR "==============================\n\n";
    # Hmm, if osErr is not 9, rpm had errors.  (9 means that the filehandle was fully read)
    # 9 == 'Bad file descriptor' fwiw.
    # Other error numbers should apparently be 0 under normal circumstances.
    # print STDERR "childErr = $childErr ; osErr = $osErr; evalErr = $evalErr;\n";
    # printf STDERR "childErr = %d ; osErr = %d; evalErr = %d;\n", $childErr, $osErr, $evalErr;
    # print STDERR "rpmOutput: $rpmOutput\n";

    my (%sums,%pkgs,@l, $lr, $k);
    # print "got $condition packages installed\n";
    %sums = %{$instSumsRef};
    %pkgs = %{$instPkgsRef};
    ######### verify contents of %sums
    ## printSumsHashRef($instSumsRef);
    ######### verify contents of %pkgs
    ## printNamesHashRef($instPkgsRef);

    # print STDERR "determinePackageState from UpgradeTest\n";
    my ($newCondition,
        $newInstSumsRef,
        $newInstPkgsRef,$newStatesRef) = updatePackageState();

    my $hasOutputErr = 0;
    if ($rpmOutput =~ m/(^|\W)(error|fail(ed)*)(\W|$)/i) {
        $hasOutputErr = checkErrAfterFilter($rpmOutput,$newStatesRef);
    }

    if (('new' eq $newCondition) && !$hasOutputErr) {
	warnOfExtraOutput('Upgrade',$rpmOutput);
        $result = 'PASS';
    } else {
        if ($hasOutputErr && ('new' eq $newCondition)) {
            # rpmOutput with error/fail in it causes a failure -- alert user in case some file/rpm matches.
            doLog($TPSFAILTXT,$TPSLOG,"Error|Fail string detected in rpmOutput, although new packages are present.\n");
        }
        doLog($TPSFAILTXT,$TPSLOG,  "Upgrade test FAILED\n");
        doLog($TPSFAILTXT,$TPSLOG,  "Output from RPM Command:\n");
        doLog($TPSFAILTXT,$TPSLOG,  "$rpmOutput\n");
        doLog($TPSFAILTXT,$TPSLOG,  ("Old packages: " . join(' ',@{$oldPkgListRef}) . "\n"));
        doLog($TPSFAILTXT,$TPSLOG,  ("New packages: " . join(' ',@{$newPkgListRef}) . "\n"));
        doLog($TPSFAILTXT,$TPSLOG,  "Packages on system after upgrade attempt - $newCondition -\n");
        printNamesHashRef($TPSFAILTXT, $newInstPkgsRef);
        $result = 'FAIL';
    }
    # vlog#Print("UpgradeTest Returning: $result\n\n");
    $result = endTest($result, 'UpgradeTest');
    return $result;
}

# Routine for use by the SharedLibTest -- takes output from 'file' and standardizes it.
# Calls readelf/eu-readelf, if available, on anything that 'file' does not recognize.
# Returns arch name or 'UNKNOWN' if it couldn't figure it out.
sub fixBinFileArch {
    # my ($oarch,$bits,$rpmArch,$binName) = @_;
    my ($fcmdHR,$rpmArch) = @_;
    # fcmdHR is the hashref resulting from parsing the output from the 'file' command.

    my $oarch = $fcmdHR->{oarch};
    my $bits = $fcmdHR->{bits};
    my $binName = $fcmdHR->{name};
    my $sigBits = $fcmdHR->{sigBits};  # typically, LSB or MSB.  Atypically, ''.

    # Sample forms of 'file' output --
    # ./aarch64/bin/foo: ELF 64-bit LSB executable, ARM aarch64, version 1 (SYSV), dynamically linked (uses shared libs), for GNU/Linux 3.7.0, BuildID[sha1]=0xec3b787a71c4beba653f8397fc9a2fcfcd374532, stripped
    # ./i386/bin/tracepath: ELF 32-bit LSB shared object, Intel 80386, version 1 (SYSV), stripped
    # ./ia64/bin/tracepath: ELF 64-bit LSB shared object, IA-64, version 1 (SYSV), for GNU/Linux 2.6.9, stripped
    # ./ppc64/bin/tracepath: ELF 64-bit MSB shared object, cisco 7500, version 1 (SYSV), for GNU/Linux 2.6.9, stripped
    # ./ppc64/bin/tracepath: ELF 64-bit MSB shared object, PowerPC or cisco 7500, version 1 (SYSV), stripped
    # ./ppc/bin/tracepath:  ELF 32-bit MSB shared object, PowerPC or cisco 4500, version 1 (SYSV), stripped
    # ./s390/bin/tracepath: ELF 32-bit MSB shared object, IBM S/390, version 1 (SYSV), for GNU/Linux 2.6.9, stripped
    # ./s390/bin/tracepath: ELF 32-bit MSB shared object, version 1 (SYSV), stripped
    # ./s390x/bin/tracepath: ELF 64-bit MSB shared object, IBM S/390, version 1 (SYSV), for GNU/Linux 2.6.9, stripped
    # ./s390x/bin/tracepath: ELF 64-bit MSB shared object, version 1 (SYSV), stripped
    # ./x86_64/bin/tracepath: ELF 64-bit LSB shared object, AMD x86-64, version 1 (SYSV), for GNU/Linux 2.6.9, stripped
    # ./x86_64/bin/tracepath: ELF 64-bit LSB shared object, AMD x86-64, version 1 (SYSV), stripped

    # Sample weirdnesses:
    # /usr/X11R6/lib/modules/v10002d.uc: ELF 32-bit MSB executable, version 1 MathCoPro/FPU/MAU Required (SYSV),
    #                                    statically linked, not stripped
    # /usr/X11R6/lib/modules/v20002d.uc: ELF 32-bit MSB executable, version 1 (SYSV), statically linked, not stripped


    sub _do_readelf {
        my ($fileName) = @_;
        my %ret;
        $ret{valid} = 0;
        $ret{name} = $fileName;
        # print STDERR "_do_readelf called on $fileName\n";
        if (exists($globs->{readelf}) && ($globs->{readelf})) {
            if (-r $fileName) {
                my $elfCmd = "$globs->{readelf} -h \"$fileName\" 2>&1 | egrep -e '(Class|Machine|Data):'";
                my $elfOut = `$elfCmd`;
                if ($elfOut =~ m/^\s*Class:\s+(.*)$/m) {
                    my $cl = $1;
                    $ret{eclass} = $cl;
                    if ($cl =~ m/ELF(\d+)/) {
                        $ret{ebits} = $1;
                    }
                }
                if ($elfOut =~ m/^\s*Machine:\s+(.*)$/m) {
                    $ret{emachine} = $1;
                }
                if ($elfOut =~ m/^\s*Data:\s+(.*)$/m) {
                    my $bitstring = $1;
                    if ($bitstring =~ m/little end/i) {
                        $ret{eSigBits} = 'LSB';
                    } else {
                        $ret{eSigBits} = 'MSB';
                    }
                }
            }
        }
        if (exists($ret{eclass}) && exists($ret{ebits}) && exists($ret{emachine})) {
            $ret{valid} = 1;
        }
        return(\%ret);
    }
   # Alternatively, with readelf:
   #  Class:                             ELF32
   #  Class:                             ELF64
   #  Machine:                           Advanced Micro Devices X86-64
   #  Machine:                           IBM S/390
   #  Machine:                           Intel 80386
   #  Machine:                           Intel IA-64
   #  Machine:                           PowerPC
   #  Machine:                           PowerPC64
   #  Machine:                           AArch64
   #  Data:                              2's complement, little endian
   #  Data:                              2's complement, big endian
   # on RHEL2.1:
   # File: ./ppc64/bin/tracepath
   #   Class:                             ELF64
   #   Machine:                           <unknown>: 15

# my ($isValidReturn, $retArch) = _findBinArchLabel($oarch,$bits,$rpmArch,$binName);
#    ($isValidReturn, $retArch) = _findBinArchLabel($href, $href->{emachine},$href->{ebits},$rpmArch,$binName);
  sub _findBinArchLabel {
    my ($dataSource, $dsHR,$rpmArch) = @_;
    # my ($oarch,$bits,$rpmArch,$binName) = @_;
    my ($bits,$sigbits,$binName,$oarch);
    if ('readelf' eq $dataSource) {
        # output from the 'file' command
        ($bits,$sigbits,$binName,$oarch) = ($dsHR->{ebits},$dsHR->{eSigBits},$dsHR->{name},$dsHR->{emachine});
    } else {
        # output from the 'readelf' command
        ($bits,$sigbits,$binName,$oarch) = ($dsHR->{bits},$dsHR->{sigBits},$dsHR->{name},$dsHR->{oarch});
    }
    ## bits => 31, 32, 64
    ## sigbits => LSB, MSB (least/most significant bit)
    ## binName => /path/to/whatever.so
    ## oarch => original string with arch info from data source, see file/readelf output for examples.
    my $do_readelf = 0;  # We will consult readelf if we have questions
    my $is_valid = 0;
    my $x86ret = 'i386';
    if ($rpmArch =~ m/i([456])86/) {
        # Currently we cannot easily distinguish between i386-686 binaries.
        # This is a kludge designed to turn off a flood of incorrect messages.
        $x86ret = "i${1}86";
    }

    if ($bits =~ m/3[12]/) {
        ($oarch =~ m/Intel\s+80386/i) && return (1,$x86ret);
        ($oarch =~ m/cisco\s+4500/i) && return (1,'ppc');
        ($oarch =~ m|IBM\s+S/390|i) && return (1,'s390');
        if ($oarch !~ m/64/) {
            ($oarch =~ m/powerpc/i) && return (1,'ppc');
        }
        # RHEL3 bug in s390 identification
        ($oarch =~ m|version\s+1\s+.SYSV.|i) && return (1,'s390');

        # print STDERR "Match bug with 32 bits: $bits and oarch: $oarch\n";
        $do_readelf = 1;
    } elsif ($bits =~ m/64/) {
        ($oarch =~ m/x86-64/i) && return (1,'x86_64');
        ($oarch =~ m/IA-64/i) && return (1,'ia64');
        ($oarch =~ m/cisco\s+7500/i) && return (1,'ppc64');
        ($oarch =~ m|IBM\s+S/390|i) && return (1,'s390x');
        ($oarch =~ m/powerpc/i) && ($sigbits eq 'MSB') && return (1,'ppc64');
        ($oarch =~ m/powerpc/i) && ($sigbits eq 'LSB') && return (1,'ppc64le');
        ($oarch =~ m/aarch64/i) && return (1,'aarch64');
        # RHEL3 bug in s390 identification
        # ./s390/bin/tracepath: ELF 32-bit MSB shared object, version 1 (SYSV), stripped
        ($oarch =~ m|version\s+1\s+.SYSV.|i) && ($sigbits eq 'MSB') && return (1,'s390x');
        ($oarch =~ m|<unknown>: 15|i) && return(1,'ppc64');  # RHEL2.1 bug for ppc64

        # print STDERR "Match bug with 64 bits: $bits and oarch: $oarch\n";
        $do_readelf = 1;
    } # else {
    #    print STDERR "Non-matching bits: $bits\n";
    #    $do_readelf = 1;
    # }

    return ($is_valid,$oarch);
  }

  # Do a lookup using provided info.
    my ($isValidReturn, $retArch) = _findBinArchLabel('file', $fcmdHR, $rpmArch);
    # my ($isValidReturn, $retArch) = _findBinArchLabel($oarch,$bits,$rpmArch,$binName);

  # If that failed, go look at the file using readelf/eu-readelf.
    if (0 == $isValidReturn) {
        my $href = _do_readelf($binName);
        if (exists($href->{valid}) && (1 == $href->{valid})) {
            # Do a lookup based on whatever readelf found...
            ($isValidReturn, $retArch) = _findBinArchLabel('readelf', $href, $rpmArch);
            # $href, $href->{emachine},$href->{ebits},$rpmArch,$binName);
            if (1 == $isValidReturn) {
                # Success...
                return $retArch;
            } else {
                # provide more info than just 'ERROR', since we have it at hand.
                return "ERROR: '$href->{emachine}, $href->{ebits}-bit'";
            }
        }
    } else {
        # Success.
        return $retArch;
    }
    return 'UNKNOWN';
}


# Selinux Boolean Manipulation System
# The setup for a test is done with selinux_SetupForTest,
# which lets you invoke it multiple times to set various selinux booleans.
# Use selinux_ModifyForTest to set the (temporary, -P isn't used) changes.
# Use selinux_ClearTestSetup to force tps to forget about the SetupForTest
# data.
# Use selinux_RestoreAfterTest to do just that: put on whatever data
# was current when ModifyForTest was called.  This will be auto-invoked
# by endTest(), so no worries if you forget.
# Note that ClearTestSetup is not called by other routines.  This means
# you can accumulate commands if desired, but should likely clear
# the setup if you wonder whether someone else has been using it :)
sub selinux_SetupForTest {
    my ($vname, $val) = @_;
    my $href = $globs->{selin_set_bools};
    $href->{$vname} = $val;
}
sub selinux_ClearTestSetup {
    my %newBools;
    $globs->{selin_set_bools} = \%newBools;
}
sub selinux_ModifyForTest {
    my $oldvals = $globs->{selin_unset_bools};
    my $newvals = $globs->{selin_set_bools};
    my $haveErr;
    if (($globs->{selin_setbool}) && ($globs->{selin_getbool})) {
        foreach my $k (keys(%$newvals)) {
            my $curVal;
            my $ln = `$globs->{selin_getbool} $k 2>&1`;
            if (($? == 0) && ($ln !~ m/^Error get/i)) {
                chomp($ln);
                # typical selinux output:
                #   foo_bar_some_name --> active (or on; or inactive, or off)
                if ($ln =~ m/^\s*\S+\s+-->\s+(.*)$/) {
                    my $t = $1;
                    if (($t =~ m/inactive/i) || ($t =~ m/off/i)) {
                        $curVal = 0;
                    } else {
                        $curVal = 1;
                    }
                    $oldvals->{$k} = $curVal;
                    my $ln2 = `$globs->{selin_setbool} $k $newvals->{$k} 2>&1`;
                    $haveErr = $?;
                    chomp($ln2) if (0 != $haveErr);
                    doLog($TPSTXT,$TPSLOG,
                          ("SELinux Boolean $k was " . (($haveErr != 0) ? 'NOT ' : '') . "set to $newvals->{$k}" .
                           (($haveErr != 0) ? ": $ln2\n" : "\n")));
                }
            }
        }
    }
}
sub selinux_RestoreAfterTest {
    my $oldvals = $globs->{selin_unset_bools};
    my $haveErr;
    if ($globs->{selin_setbool}) {
        foreach my $k (keys(%$oldvals)) {
            my $ln2 = `$globs->{selin_setbool} $k $oldvals->{$k} 2>&1`;
            $haveErr = $?;
            chomp($ln2) if (0 != $haveErr);
            doLog($TPSTXT,$TPSLOG,
                  ("SELinux Boolean $k was " . (($haveErr != 0) ? 'NOT ' : '') . "restored to $oldvals->{$k}" .
                   (($haveErr != 0) ? ": $ln2\n" : "\n")));
            if (0 == $haveErr) {
                delete $oldvals->{$k};
            }
        }
    }
}

# This routine asks ldconf what files it has cached, and creates a comma-separated
# list of the unique directory names of those files, suitable for use as LD_LIBRARY_PATH.
sub getLDLibBase {
    my %dirsFound;
    my $ldconfOut = `ldconfig -p 2>&1 | grep '=>'`;
    map { if (m|\s*=>\s+(.*)$|) { $dirsFound{(dirname($1))} = 1; }; } (split(/\n/,$ldconfOut));
    return(join(':',sort(keys(%dirsFound))));
}

# Given a current file that would otherwise get a 'mismatched rpm arch' error,
# check to see whether there's a multilib version available that *does* match
# the arch.  Return 0 if not found, 1 if found.
# inputs: ref to hash of individual file, ref to array that contains all hashrefs under test.
sub shlib_haveMultilibVer {
    my ($href,$hrefList) = @_;
    my $ret = 0;
    my $okArches = { $globs->{arch} => 1, $globs->{trueArch} => 1, };
    my ($iArch, $curArch, $curRpmArch);
    foreach my $i (@$hrefList) {
        if ($i->{name} eq $href->{name}) {
            $curArch = $href->{arch};
            $curRpmArch = $href->{rpm_arch};
            $iArch = $i->{arch};
            if (($iArch ne $curRpmArch) && ($iArch eq $curArch) && (exists($okArches->{$iArch}))) {
                return 1;
            }
        }
    }
    return $ret;
}
#### SharedLib Special Case Testers
# Returns: Empty string (no exception found), PASS, FAIL, or WARN for
# relevant special cases / exceptions to each of these rules.
# inputs: itemRef is an href from the main SharedLibTest routine;
#         rules is an array ref (of hash refs) from specialCaseLoader.
# Match if: all rules{key}s exist as itemRef{key}, and the
#           contents are string-equal.  Tempting to use regexps, but
#           that would likely be slower and more error-prone.
# Actual return: uppercased version of whatever is defined
# as 'action' in the rules file.  Recall that the rules file
# is: '<testTag> <action> (<key> <value>)+'.  Only the action,
# keys, and values get picked up.  Thus the max array index
# of the list of keys is the number of rule matches we need
# to consider that a rule applies to the item we are fed.
sub shlib_sc_check_Generic {
    my ($itemRef,$rules) = @_;
    my ($act, $ret, @klist, $matches);
    $ret = '';
    HRLOOP: foreach my $href (@$rules) {
        @klist = keys(%$href);
        $matches = 0;
        foreach my $k (@klist) {
            if ($k eq 'action') {
                $act = $href->{$k};
            } else {
                if ((exists($itemRef->{$k})) &&
                    ($href->{$k} eq $itemRef->{$k})) {
                    $matches++;
                } else {
                    next HRLOOP;
                }
            }
        }
        if ($#klist == $matches) {
            $ret = uc($act) if (defined($act) && ($act));
            return $ret;
        }
    }
    return $ret;
}
# Handler for special cases
sub shlib_sc_handler {
    my ($spCase) = @_;
    my ($applies,$lev,$typ,$txt) = (0,-1,-1,'');
    if ($spCase eq 'WARN') {
        # user-visible warning
        $applies = 1;
        $lev = $TPSLOG;
        $typ = $TPSWARN;
        $txt= '[SpecialCase] ';
    } elsif ($spCase) {
        # debug log only, with name of triggering action
        $applies = 1;
        $lev = $TPSDEBUG;
        $typ = $TPSMISC;
        $txt = ('['."SpecialCase: $spCase".'] ');
    }
    return($applies,$lev,$typ,$txt);
}

### shlib_handle_fail:
# ($errorText,$notableText) = shlib_handle_fail($msgTxt,$specialCase_Unknown,\$hasError,\$hasNotable);
sub shlib_handle_fail {
    my ($msgTxt,$itemRef,$specialCase_Ref,$errorText,$notableText,
        $hasErrorRef,$hasNotableRef,$noteLevelRef,$noteTypeRef) = @_;
    my $noteLevel = -1;
    my $noteType = -1;
    my $hasNotable = $$hasNotableRef;
    my $hasError = $$hasErrorRef;

    my $specCase = shlib_sc_check_Generic($itemRef,$specialCase_Ref);
    my ($hasSpecCase,$scLev,$scTyp,$scTxt) = shlib_sc_handler($specCase);

    if (1 == $hasSpecCase) {
        $notableText .= "\n$itemRef->{rpm_nvra}: " if ($hasNotable);
        $hasNotable = 1;
        $$noteLevelRef = $scLev;
        $$noteTypeRef = $scTyp;
        $notableText .= ($scTxt . $msgTxt);
    } else {
        # No special cases applied.
        # user-visible error
        $errorText .= "\n$itemRef->{rpm_nvra}: " if ($hasError);
        $printTip_UnknownError = 1;
        $hasError = 1;
        $errorText .= $msgTxt;
    }
    $$hasNotableRef = $hasNotable;
    $$hasErrorRef = $hasError;

    return ($errorText,$notableText);
}

###################################################################
#                      SharedLibTest
###################################################################
#### This is the LDD test, which checks the following IF it starts with 'new' packages installed:
# 1. All symbols must resolve if the package was successfully installed.
# 2. binaries in /bin or /sbin can only be linked against things in /lib (no /usr/whatnot).
# 3. binaries must be for the correct architecture (no i386 in an .ia64 rpm)
sub SharedLibTest {
    my ($instSumsRef, $instPkgsRef, $oldPkgListRef, $newPkgListRef,$oldPkgHRef,$newPkgHRef) = @_;
    my ($result, $childErr, $osErr, $evalErr);
    # All of the @_ arguments are optional; fill them in below if anything's missing.
    my ($condition);
    my $isManual = $globs->{isManual};
    $isManual = 0 if (exists($ENV{'TPSAUTO'}) && (1 == $ENV{'TPSAUTO'}));
    my $testName = 'SharedLibTest';
    my $queryListRef;
    my %libPaths;
    # provide one valid default:
    $libPaths{'/lib'} = 1;

    $tpsErrorText = '';
    beginTest('SharedLibTest');

    # RHEL5.3 ia64 has a bug with ia32emul and selinux.  (BZ 474152)
    # Work around it here.
    if ((($globs->{trueArch} =~ m/ia64/i) || ($globs->{arch} =~ m/ia64/i)) &&
        (($globs->{tpsProductFam} eq 'RHEL') && ($globs->{tpsProductRel} >= 5))) {
        selinux_SetupForTest('allow_unconfined_execmem_dyntrans',1);
        selinux_SetupForTest('allow_execmem',1);
        selinux_ModifyForTest(); # this will be auto-reverted in endTest().
    }

    cacheToEnv() if (!exists($ENV{'OLDFILES_OUT'}));
    if ((!defined($oldPkgListRef)) || (!defined($oldPkgHRef))) {
	($oldPkgListRef,$oldPkgHRef) = envPkgCacheToRefs('OLDFILES_OUT','DEP_OLDFILES_OUT');
    }
    if ((!defined($newPkgListRef)) || (!defined($newPkgHRef))) {
	($newPkgListRef,$newPkgHRef) = envPkgCacheToRefs('FILES_OUT','DEP_FILES_OUT');
    }
    setGlobalLists($newPkgListRef,$oldPkgListRef,$newPkgHRef,$oldPkgHRef) if ($globs->{haveFileLists} != 1);

    ($condition, $instSumsRef,
     $instPkgsRef,$statesRef) = updatePackageState();

    if ($condition ne 'new') {
        doLog($TPSINFO,$TPSLOG,"Starting state for this test must be NEW, but was ${condition}.  Skipping it.\n");
        my $res = endTest('PASS-skipped', $testName);
        return $res;
    }

    $queryListRef = instSumsToQueryList($instSumsRef,'"');

    $result = 'FAIL';
    my $errataTmp = 'unknown';
    if (exists($ENV{ERRATA})) {
      $errataTmp = $ENV{ERRATA};
      $errataTmp =~ s/:/-/g;
    }
    my $manTmp = "/tmp/manifest-${errataTmp}-$$.txt";
    # my $manifestCmd = 'rpm -ql --qf "=::=>RPM=%{SIGMD5} %{NAME} %{VERSION} %{RELEASE} %{EPOCH} %{ARCH}\n%{FILENAMES}\n" ' .
    #    join(' ',@{$queryListRef}) . ' | uniq | while read ln ; do echo \"$ln\" ; done';
    my $manifestCmd = 'rpm -ql --qf "=::=>RPM=%{SIGMD5} %{NAME} %{VERSION} %{RELEASE} %{EPOCH} %{ARCH}\n%{FILENAMES}\n" ' .
        join(' ',@{$queryListRef}) . ' | uniq';

    # Do not use doRpmCommand here: manifests can get Very Long and would wind up in the logfiles.
    # Possible enhancement: save to alternative file if desired for debugging.
    doLog($TPSMISC,$TPSDEBUG,"Running manifestCmd: $manifestCmd\n");
    my $manifestOutput = `$manifestCmd > $manTmp`;
    if ($? != 0) {
        # handle error
        doLog($TPSFAILTXT,$TPSLOG,"Cannot get manifest list for packages\n");
        my $res = endTest('FAIL', $testName);
        return $res;
    }
    # lose the newlines
    $manifestOutput =~ s/\n/ /g;

    doLog($TPSMISC,$TPSDEBUG,"Running file cmd: file -f $manTmp\n");
    my $fileTypeOutput = `file -f $manTmp`;
    my $tmpRc = $?; my $tmpErr = $!;
    if (($tmpRc != 0) && (1 <= scalar(grep {/ERROR:/} (grep {!/=::=>RPM=/} (split(/\n/,$fileTypeOutput)))))) {
        # handle error
        doLog($TPSFAILTXT,$TPSLOG,"Cannot run 'file' command on $manTmp: $tmpRc $tmpErr\n");
        my $res = endTest('FAIL', $testName);
        return $res;
    } else {
        unlink($manTmp) unless ($debug);
    }

    # At this point, manifestOutput looks something like:
    # =::=>RPM=1b87416ffa667465922862a9715f0d8f binutils 2.17.50.0.18 1 (none) x86_64: ERROR: cannot open ...
    # /usr/bin/addr2line:  ELF 64-bit LSB executable, x86-64, ...
    # and so on...

    # Below, we need to treat debugFiles differently, as they can crash LDD.  Make sure they're last.
    my @binFileOut = grep { (m/\sELF\s/) || (m/^=::=>RPM=/) } (split(/\n/,$fileTypeOutput));
    my @binFileNames = ();
    my @binFileHashList;
    my @debugFileNames = ();
    my @debugFileHashList;
    my ($binFileCount, $debugFileCount);
    my $tmp;
    my $filesToCheck = 0;
    # info about current rpm:
    my ($r_5, $r_name, $r_ver, $r_rev, $r_epoch, $r_arch) = (0,'','','','','');
    foreach my $i (@binFileOut) {
        # collect filename and info from 'file' and 'ldd'
        if ($i =~ m/^([^:]+):\s/) {
            $tmp = $1;
            my %h;
            $h{name} = $tmp;
            $h{basename} = basename($tmp);
            $h{is_debug} = 0;
            if (($tmp =~ m|^/usr/lib/debug/|) || ($tmp =~ m|^/emul/ia32-linux/usr/lib/debug/|)) {
                $h{is_debug} = 1;
                push @debugFileNames,$tmp;
            } elsif ((defined($r_name)) && ($r_name) && ($r_name =~ m|-debuginfo$|)) {
                # Consider this a debug file due to its rpm name.  Possibly not entirely safe,
                # so log a tpsdebug message in case it breaks.
                doLog($TPSMISC,$TPSDEBUG,"Marking $tmp as is_debug due to rpm name $r_name\n");
                $h{is_debug} = 1;
                push @debugFileNames,$tmp;
            } else {
                push @binFileNames,$tmp;
            }
            $h{arch} = '';
            $h{useShared} = 0;
            $h{sigBits} = 'unknown';
            if ($i =~ m/uses shared libs/) {
                $h{useShared} = 1;
            } elsif ($i =~ m/(LSB|MSB) shared object/) {
                $h{useShared} = 1;
                $h{sigBits} = $1;
            }
            if (($tmp =~ m/\.so$/) || ($tmp =~ m/\.so\./)) {
                # Save path of .so for ld_lib_path use later
                $libPaths{(dirname($tmp))} = 1;
            }
            if ($i =~ m/ELF\s(\S+)\sexecutable/) {
                $h{bits} = $1;
            } elsif ($i =~ m/ELF\s(\d+)-bit\s+(LSB|MSB)*\sexecutable/) {
                $h{bits} = $1;
                $h{sigBits} = $2;
            } elsif ($i =~ m/ELF\s(\d+)-bit\s+(LSB|MSB)*\sshared/) {
                $h{bits} = $1;
                $h{sigBits} = $2;
            } elsif ($i =~ m/ELF\s(\d+)-bit\s+(LSB|MSB)*\srelocatable/) {
                # for RHEL3 .o files, see BZ 497993
                $h{bits} = $1;
                $h{sigBits} = $2;
            }
            $h{rpm_md5} = $r_5;
            $h{rpm_nvra} = "${r_name}-${r_ver}-${r_rev}.${r_arch}";
            $h{rpm_nvr} = "${r_name}-${r_ver}-${r_rev}";
            $h{rpm_nv} = "${r_name}-${r_ver}";
            $h{rpm_name} = "${r_name}";
            $h{rpm_arch} = "${r_arch}";

            if ($i =~ m/,\s([^,]+),\s/) {
                # $h{arch} = fixBinFileArch($1,$h{bits},$r_arch,$h{name});
                $h{oarch} = $1;
                $h{arch} = fixBinFileArch(\%h,$r_arch);
            }
            $h{result} = 'NOT TESTED';
            if (1 == $h{is_debug}) {
                push @debugFileHashList,\%h;
            } else {
                push @binFileHashList,\%h;
            }
            $filesToCheck++;
        # } elsif ($i =~ m/^=::=>RPM=(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)/) {
        } elsif ($i =~ m/^=::=>RPM=(\S+)\s(\S+)\s(\S+)\s(\S+)\s(\S+)\s([^: ]+)/) {
            # =::=>RPM=1b87416ffa667465922862a9715f0d8f binutils 2.17.50.0.18 1 (none) x86_64
            ($r_5, $r_name, $r_ver, $r_rev, $r_epoch, $r_arch) = ($1,$2,$3,$4,$5,$6);
        }
    }
    if (0 == $filesToCheck) {
        doLog($TPSTXT,$TPSLOG,"$testName: no ELF executables found to analyze\n");
        my $res = endTest('PASS', $testName);
        return $res;
    } else {
        doLog($TPSMISC,$TPSDEBUG,"$testName: found $filesToCheck ELF objects to analyze\n");
    }

    # Assemble the two lists, ensuring that debug files are at the end (in case ldd crashes on one).
    $binFileCount = $#binFileNames;
    $debugFileCount = $#debugFileNames;
    push @binFileNames, @debugFileNames;
    push @binFileHashList, @debugFileHashList;

    # More variables for the actual testing...
    my @binFileArches = ();
    my $binFileNamesStr = join(" ",@binFileNames);
    $tmp = 0;
    my ($href,$errorText,$notableText,$msgText,$hasError,$hasNotable,$specCase);
    my ($noteLevel,$noteType);
    my ($hasSpecCase,$scLev,$scTyp,$scTxt);
    my $errorsFound = 0;
    my $trueArch = $globs->{trueArch};
    my $printTip_DynExe = 0;
    my $printTip_Usr = 0;
    my $printTip_RpmArch = 0;
    my $printTip_Unresolved = 0;
    my $printTip_UnknownError = 0;
    my $printTip_Notable = 0;
    my $newln_cnt = 0;  # how many lines of output in each ldd chunk
    my $specialCase_RpmArch = specialCaseLoader($globs->{shlib_scFile},'rpmarch');
    my $specialCase_Unresolved = specialCaseLoader($globs->{shlib_scFile},'unresolved');
    my $specialCase_Unknown = specialCaseLoader($globs->{shlib_scFile},'unknown');
    my $specialCase_Usr = specialCaseLoader($globs->{shlib_scFile},'usr');
    my $specialCase_DynExe = specialCaseLoader($globs->{shlib_scFile},'dynexe');

    # Use LD_LIBRARY_PATH to prevent false "unresolved symbols" messages
    # due to odd paths for an erratum's .so files.
    my $ldLibPath = '';
    my $oldLDLibPath = '';
    if (exists($ENV{LD_LIBRARY_PATH})) {
        $ldLibPath = "$ENV{LD_LIBRARY_PATH}:";
        $oldLDLibPath = $ENV{LD_LIBRARY_PATH};
    }
    $ldLibPath .= getLDLibBase();
    $ldLibPath .= (':' . (join(':',(sort(keys(%libPaths))))));
    doLog($TPSMISC,$TPSDEBUG,"SharedLibTest: using LD_LIBRARY_PATH=$ldLibPath\n");
    $ENV{LD_LIBRARY_PATH} = $ldLibPath;

    # Invoke ldd once for the whole lot.
    # Syntax is a bit byzantine, but should be better performance.
    # We append perl to the binFileNamesStr in case there's only one binary on the list.
    # Otherwise, ldd would change its output format.
    # Since it won't have an entry in binFileHashList, it will be ignored otherwise.
    # Note: ldd returns non-zero for non-executables, binary not found, etc.
    # It returns 0 for successful analysis, even if unresolved .so files are found.
    foreach my $ln (split(/^(?=\S)/m,`ldd $binFileNamesStr /usr/bin/perl 2>/dev/null`)) {
        $href = $binFileHashList[$tmp];
        next if (!defined($href)); # something went wrong with ldd?
        $href->{ldd} = $ln;
        $errorText = "$href->{rpm_nvra}: ";
        $notableText = "$href->{rpm_nvra}: ";
        $hasError = 0;
        $hasNotable = 0;
        # Note that $ln contains newlines, so all regexps that use
        # begin/end of line *must* use the 'm' option here to work as expected.

        # if ldd gave us only 1 newline, there was a problem with it.
        # thus, count the newlines.
        $newln_cnt = grep(m/\n/,(split(m//,$ln)));

        chomp($ln);

        if (($newln_cnt <= 1) && (0 == $href->{is_debug})) {
            my $ldd_error_txt = `ldd $href->{name} 2>&1 1>/dev/null`;
            chomp($ldd_error_txt);
            $ldd_error_txt =~ s/\x04/^D/g;
            $msgText = "$href->{name}: ldd error:  $ln $ldd_error_txt\n";

            ($errorText,$notableText) = shlib_handle_fail($msgText,$href,$specialCase_Unknown,
                                                          $errorText,$notableText,
                                                          \$hasError,\$hasNotable,\$noteLevel,\$noteType);
        }

        # Check for unresolved symbols.
        if ($ln =~ m/^\s+(.*)\s+=>\s+not\s+found/m) {
            # libstdc++-libc6.2-2.so.3 => not found
            # check specialCase_Unresolved
            $msgText = "$href->{name}: unresolved symbols found:  ";
            $msgText .= join("\n",grep(/\snot\s+found/,split(/\n/,$ln)));

            ($errorText,$notableText) = shlib_handle_fail($msgText,$href,$specialCase_Unresolved,
                                                          $errorText,$notableText,
                                                          \$hasError,\$hasNotable,\$noteLevel,\$noteType);
        }
        # Check for "recognized by 'file' as 'shared' but not by 'ldd'"
        # Note: this is not an error for debug files; this can be examined in
        # detail, if desired, by running 'eu-readelf -S' on the file and checking
        # the .dynamic section -- if NOBITS is listed, ldd will fail with either
        # 'not a dynamic executable' or '^D bad ELF interpreter'.
        if ((1 == $href->{useShared}) && ($ln =~ m/not a dynamic executable/)) {
            $msgText = "$href->{name}: not a dynamic executable\n";
            ($errorText,$notableText) = shlib_handle_fail($msgText,$href,$specialCase_DynExe,
                                                          $errorText,$notableText,
                                                          \$hasError,\$hasNotable,\$noteLevel,\$noteType);
        }
        # Check paths for /bin,/sbin not relying on /usr.
        if ($href->{name} =~ m|^/*s*bin/|) {
            if ($ln =~ m|^\s+\S+\s+=>\s+/usr|m) {
                # Display only some of the /usr libraries; 1 is enough to
                # matter, the rest seem to be considered noise by testers.
                # The lines can either get very long, or wrap into an ugly mess.
                my @whichLibs = grep({ m|\s=>\s+/usr|m } split(/\n\s*/m,$ln));
                my $spewLimit = 2; # max index to print... 2 means 0,1,2 -- aka 3. :)
                my $libCnt = $#whichLibs;
                my $prCnt = $libCnt;
                my $truncMsg = '';
                if ($libCnt > $spewLimit) {
                    $prCnt = $spewLimit;
                    $truncMsg .= ( '('.($prCnt+1)." of $libCnt libs shown)" );
                }
                $msgText = ( "$href->{name} relies on libs in /usr: " .
                                join(" ",@whichLibs[(0 .. $prCnt)]) .
                                " $truncMsg\n");
                ($errorText,$notableText) = shlib_handle_fail($msgText,$href,$specialCase_Usr,
                                                              $errorText,$notableText,
                                                              \$hasError,\$hasNotable,\$noteLevel,\$noteType);

            }
        }
        # Check for correct arches and bits.
        if (($href->{arch} ne $href->{rpm_arch}) && (!shlib_haveMultilibVer($href,\@binFileHashList))) {
            # check specialCase_RpmArch
            $msgText = "$href->{name}: Arch differs from that of its rpm: $href->{arch} versus $href->{rpm_arch}\n";
            ($errorText,$notableText) = shlib_handle_fail($msgText,$href,$specialCase_RpmArch,
                                                          $errorText,$notableText,
                                                          \$hasError,\$hasNotable,\$noteLevel,\$noteType);
        }

        if (1 == $hasError) {
            doLog($TPSFAILTXT,$TPSLOG,$errorText);
        }
        if (1 == $hasNotable) {
            doLog($noteType,$noteLevel,$notableText);
            $printTip_Notable = 1 if ($noteLevel > $TPSDEBUG);
        }
        $errorsFound += $hasError;
        $href->{result} = ((1 == $hasError) ? 'FAIL' : 'PASS');
        $tmp++;
    }
    if ($oldLDLibPath) {
        $ENV{LD_LIBRARY_PATH} = $oldLDLibPath;
    } else {
        delete($ENV{LD_LIBRARY_PATH});
    }
    if ($tmp <= $binFileCount) {
        $errorsFound++;
        $hasError = 1;
        $printTip_UnknownError = 1;
        doLog($TPSFAILTXT,$TPSLOG,"Only $tmp of the detected $binFileCount regular binaries had results from ldd. List of tested binaries follows.\n");
        foreach my $skipped (@binFileHashList) {
            doLog($TPSTXT,$TPSLOG,"$skipped->{basename} : $skipped->{result}\n");
        }
    }

    if ($printTip_UnknownError) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: Unknown ldd error:  This should not happen; depending on the\n".
                               "output, you should investigate as to whether the binaries work, and then\n".
                               "probably file a bug against TPS, glibc, or consider re-spinning the package\n".
                               "if there is a linkage problem.  You may also see this message for\n".
                               "packages such as acroread, which use shell tricks to load binaries creatively.\n".
                               "Please investigate and explain; do not let it go unreported.\n"));
    }
    if ($printTip_DynExe) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: Dynamic Executable Error: the 'file' command has identified files which\n" .
                               "it believes are dynamic executables; however, the 'ldd' command\n" .
                               "(and possibly 'readelf') disagrees.  The files should be examined --\n".
                               "try using them in an appropriate way -- to make sure that there is not\n" .
                               "a problem hiding here.  If they work as intended, you can waive this failure.\n".
                               "You can also run 'eu-readelf -S' on the file, and check the .dynamic section\n".
                               "If it does not say NOBITS, there is a problem which bears investigation.  If\n".
                               "it does say NOBITS, use your judgement whether the linker could/should have\n".
                               "included the info needed to examine linkages and waive if appropriate.\n"));
    }
    if ($printTip_Usr) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: Error: Relies on /usr:  Most programs in /bin and /sbin should not assume\n".
                               "that /usr is mounted, since they can be called at runlevel 1 as the system\n".
                               "is starting up.  Depending on your package, this may be a problem.  Investigate\n".
                               "and put the results of your investigation into the QA Comments section of the\n".
                               "Errata Tool.  Either Re-spin the package, or Waive, as appropriate.\n"));
    }
    if ($printTip_RpmArch) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: Error: Wrong Arch:  A binary from an architecture different from that\n".
                               "of its RPM was detected.  This is usually an error that requires Re-spin,\n".
                               "but which may be okay for a compatible architecture in limited circumstances --\n".
                               "for instance, an i386-compatible bootloader on an x86_64 machine.  Investigate,\n".
                               "report in the Errata Tool, and either re-spin or waive, as appropriate.\n"));
    }
    if ($printTip_Unresolved) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: Error: Unresolved symbols found.  This typically means that the package needs\n".
                               "to be re-spun.  A package should either contain objects with the correct symbols,\n".
                               "or declare a dependency upon the package that *does* contain the symbols.\n".
                               "Note that this may not be a bug if the package makes odd use of LD_LIBRARY_PATH\n".
                               "or loads itself in a non-standard way.  Investigate and explain.\n".
                               "Do NOT waive this error without a Very Good Reason, explained prominently\n".
                               "in the Errata Tool.\n"));
    }
    if ($printTip_Notable) {
        doLog($TPSTIP,$TPSLOG,("\nTPSTIP: The [SpecialCase] markers indicate items which would ordinarily\n".
                               "cause failures.  The failure has been marked as Pass or Warn and is presented for\n".
                               "your information.  There may be help available on the TPS Help page if\n".
                               "you would like addtional explanation.\n"));
    }

    # The binFileCount and debugFileCounts are actually array indices.
    # For human consumption, add 1 to each here.
    $binFileCount++;
    $debugFileCount++;

    if ($errorsFound == 0) {
        doLog($TPSTXT,$TPSLOG,("$testName: $binFileCount regular binaries and $debugFileCount debug files were found.\n".
                               "Checked $tmp of these $filesToCheck ELF objects, and no problems were found.\n".
                               "Unless otherwise reported, any unchecked objects are part of debuginfo and may be ignored.\n"));
        $result = 'PASS';
    } else {
        doLog($TPSTXT,$TPSLOG,
              ("$testName: $binFileCount regular binaries and $debugFileCount debug files were found.\n".
               "Checked $tmp of these $filesToCheck ELF objects, and $errorsFound error" .
               ((1 == $errorsFound) ? " was" : "s were") . " found.\n".
               "Unless otherwise reported, any unchecked objects are part of debuginfo and may be ignored.\n"));
        $result = 'FAIL';
    }

    $result = endTest($result, $testName);
    return $result;
}

1;
