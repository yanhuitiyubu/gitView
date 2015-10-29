#!/usr/bin/perl -w

# TPS module for RPM package sanity testing
# ---------------------------------------------------------------
# Purpose is to save functional rpm package for non-rpm installation
# and to backup the actual rpm database

# temp dir for backuping the database
my $rpmBackupDb;
# temp file for backuping the old rpm package in cpio
my $rpmBackupPkg;
# the old rpm package
my $oldRpmPkg;

sub rpmBackup {
    my ($oldPkgListRef) = @_;
    my $tName = "RpmMod:RPM Backup";

    beginTest($tName);
    my $result = 'PASS';
    my $command;
    my $pkg;

    # backup the actual rpm database
    $rpmBackupDb = `mktemp -d /tmp/tps-rpm.XXXXXX`;
    $rpmBackupDb =~ s/\s+$//;
    $command = "cp -rf /var/lib/rpm/* $rpmBackupDb";
    logPrint "$command \n";
    system($command) == 0
        or $result = 'FAIL';

    # search for the base rpm package (as in /usr/bin/rpm itself).
    ($oldRpmPkg) = grep { m!(^|/)rpm-\d! } @{$oldPkgListRef};

    if ($oldRpmPkg) {
        # save the old functional rpm pkg to cpio archive
        $rpmBackupPkg = `mktemp /tmp/tps-rpm.cpio.XXXXXX`;
        $rpmBackupPkg =~ s/\s+$//;
        $command = "rpm2cpio $oldRpmPkg > $rpmBackupPkg";
        logPrint "$command \n";
        system($command) == 0
            or $result = 'FAIL';
    } else {
        # No old RPM package! This should never happen, but it does: bz1219552
        logPrint("WEIRD! No 'rpm' package found on system!");
        $result = 'FAIL';
    }


    logPrint("rpm backup produced: $result\n");
    endTest($tName);
    return $result;
}

# If the functionality testing of the new package doesn't succeed
# this function restores the previous functional configuration
sub rpmRestore {
   logPrint "\nRPM Restore ==============================================\n";
   my $result = 'PASS';

   if ($rpmBackupDb) {
       my $command = "cp -rf $rpmBackupDb /var/lib/rpm/ ";
       logPrint "$command \n";
       system($command) == 0
           or $result = 'FAIL';
   } else {
       logPrint("Cannot restore rpmdb: no backup!");
       $result = 'FAIL';
   }

   if ($rpmBackupPkg) {
       my $command = "cpio -ivu < $rpmBackupPkg";
       logPrint "$command \n";
       system($command) == 0
           or $result = 'FAIL';
   } else {
       logPrint("Cannot restore rpm executable: no rpm backup found");
       $result = 'FAIL';
   }

   logPrint("rpm restore produced: $result\n");
   return $result;
}

# Rpm functionality test
sub rpmFunctionalityTest {
   logPrint "\nRPM FunctionalityTest =====================================\n";

   my $result = 'PASS';

   if ($oldRpmPkg) {
       # not sure if this is a good way how to easily test functionality of rpm
       my $command = "rpm -Uh --test --oldpackage --nodeps $oldRpmPkg ";
       logPrint "$command \n";
       system("$command &> /dev/null") == 0
           or $result = 'FAIL';
   } else {
       # No old RPM package! This cannot happen with correct data.  Trouble!
       logPrint("rpm functionality test skipped: no old rpm package found\n");
       $result = 'FAIL';
   }
   logPrint("rpm functionality produced: $result\n");
   return $result;
}

# Delete backup files 
sub delBackup {
    my $result = 'SKIPPED';
    logPrint "\nRPM DeleteBackup ==========================================\n";
    my $command = "rm -rf $rpmBackupDb $rpmBackupPkg";
    if ($rpmBackupDb || $rpmBackupPkg) {
        $result = 'PASS';
        logPrint "$command \n";
        system("$command 2>&1") == 0
            or $result = 'FAIL';
    }
    logPrint("rpm delete backup produced: $result\n");
    return $result;
}

# The name of this file should be %{NAME}.pl
# where %{NAME} is whatever RPM would print when queried for the 
# name of the package you want to test.
# If it's arch-specific, you can use %{NAME}.%{ARCH}.pl.

# These are variables that tps-rpmtest declares and uses
# to figure out what functions to call.
use vars qw{ @testFunctionUserNames @testFunctionList $globs  };

# First, provide a string that the user will see that
# can be used to say "Running test: YOURTESTNAME"
push @testFunctionUserNames, "RpmTest";

# Now define a closure -- eg, stuff a function into a scalar.
local $rpmSanityTest = sub {
    my ($condition,$instSumsRef, $instPkgsRef, $oldPkgListRef,
        $newPkgListRef,$oldPkgHRef,$newPkgHRef) = @_;

    logPrint("Starting with packages: $condition\n");

    my $exitStatus = "PASS";

    if ($condition  eq "old") {
        # Sanity for the condition: old packages

        # Backup the database and save the old package to cpio
        my $backupResult = rpmBackup($oldPkgListRef);
        rptPrint("rpm backup produced: $backupResult\n");
        if ($backupResult ne "PASS") {
            rptPrint("Actual rpm configuration cannot be saved.");
            rptPrint("Sorry, it's too risky to test it, do it manually.\n");
            $exitStatus = "FAIL";
        }

        unless ($exitStatus eq 'FAIL') {
            # Upgrade test
            my $upResult = UpgradeTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                       $newPkgListRef,$oldPkgHRef,$newPkgHRef);
            rptPrint("rpm upgrade produced: $upResult\n");
            $exitStatus = "FAIL" if ($upResult ne "PASS");

            # Verify test
            my $vResult = VerifyTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                     $newPkgListRef,$oldPkgHRef,$newPkgHRef);
            rptPrint("rpm verification produced: $vResult\n");
            $exitStatus = "FAIL" if ($vResult ne "PASS");

            # Functionality test
            my $funcResult = rpmFunctionalityTest;
            rptPrint("rpm functionality produced: $funcResult\n");
            if ($funcResult ne "PASS") {
                # Restore old condition
                my $restoreResult = rpmRestore;
                rptPrint("rpm restore produced: $restoreResult\n");
                $exitStatus = "FAIL" if ($restoreResult ne "PASS");
            }
        }

        # Delete the [possibly partial] backup files
        my $delBackupResult = delBackup;

        unless ($exitStatus eq 'FAIL') {
            # Downgrade test
            my $dnResult = DowngradeTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                         $newPkgListRef,$oldPkgHRef,$newPkgHRef);
            rptPrint("rpm downgrade produced: $dnResult\n");
            $exitStatus = "FAIL" if ($dnResult ne "PASS");
        }
    } else {
        # Sanity for condition: new or mixed packages
        # backup and restore would be hopefully not needed
        my $dnResult = DowngradeTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                     $newPkgListRef,$oldPkgHRef,$newPkgHRef);
        rptPrint("rpm downgrade produced: $dnResult\n");
        $exitStatus = "FAIL" if ($dnResult ne "PASS");

        my $upResult = UpgradeTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                   $newPkgListRef,$oldPkgHRef,$newPkgHRef);
        rptPrint("rpm upgrade produced: $upResult\n");
        $exitStatus = "FAIL" if ($upResult ne "PASS");

        my $vResult = VerifyTest($instSumsRef, $instPkgsRef, $oldPkgListRef,
                                 $newPkgListRef,$oldPkgHRef,$newPkgHRef);
        rptPrint("rpm verification produced: $vResult\n");
        $exitStatus = "FAIL" if ($vResult ne "PASS");
    }
    return $exitStatus;
};

# Now push that closure onto the list of function names that Main will run.
push @testFunctionList, $rpmSanityTest;

# And do something True to finish loading.
1;

