#!/usr/bin/perl -w

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# User Documentation

=pod

=head1 NAME

kertBundle.pl

=head1 SYNOPSIS

kertBundle.pl

=over 4

Let the computer do the grunt work ...

=back

kertBundle.pl [-Help <helpLevel>]

=over 4

Display help messages at a certain I<helpLevel>: 0 (this
SYNOPSIS), 1 (SYNOPSIS and OPTIONS), 2 (complete documentation), or no
value which defaults to 0.

=back


kertBundle.pl [-inFile <inFilename>] [-outFile <outFilename>]

=over 4

Allow I<inFilename> for input and I<outFilename> for output.

=back


=head1 OPTIONS

Options are case-sensitive.  Any option can be abbreviated to the
shortest string that remains unambiguous with all other options.  For
example B<-H> is the same as B<-Help> as long as no other option
starts with B<H>.

=over 2

=item B<-inFile> I<inFilename>

The input file I<inFilename> is specified with this switch.


=item B<-outFile> I<outFilename>

The output file I<outFilename> is specified with this switch.


=item B<-Help> I<helpLevel>

Help messages are tuned for a specific I<helpLevel>.  Default is 0
which displays a brief usage message (the SYNOPSIS section).
I<helpLevel> 1 presents the usage together with detailed information
about the options (SYNOPSIS and OPTIONS sections).  Any value for
I<helpLevel> of 2 or greater will display all the documentation
available.  

The display for I<helpLevel>=1 can get long due to description of
the OPTIONS, therefore it is recommended to pipe the output to a
pager.  For example,

  kertBundle.pl -H 1 | less


Take note that for I<helpLevel>>=2, the documentation is prepared
and displayed through the program perldoc allowing for easy navigation
so there is no need for the pager as described for I<helpLevel>=1.


=back


=head1 DESCRIPTION

=head1 AUTHOR

=head1 BUGS

=head1 SEE ALSO

=head1 COPYRIGHT



=cut



# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# Code
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

use Env;
use strict;
use Getopt::Long;
$Getopt::Long::ignorecase = 0; # Options are case-sensitive
$Getopt::Long::autoabbrev = 1; # Options can be abbreviated
use Pod::Text;
use POSIX;
use English;
use File::Basename;
use File::Copy;
use File::Find;
use DirHandle;
use Term::ReadLine;
use FileHandle;
use Text::Balanced ':ALL';
use Pod::Usage;
use Cwd 'abs_path';

STDOUT->autoflush;


# Parse the command line
my %cmdLine = parseCmdLine();
my $BIN_tar = 'gtar';

my $archiveFile = $cmdLine{archive};
my $manifestFile = $cmdLine{manifest};
my $archiveDir = $cmdLine{archiveDir};
$archiveDir =~ s+[/]*$++;
my $pathToManifest = $archiveDir . '/' . $manifestFile;

#* Read the manifest file
#** Prep
my $extractManifestCmd = "$BIN_tar xvzf $archiveFile $pathToManifest";
my $rc = system($extractManifestCmd);
die "Error extracting <$pathToManifest> from <$archiveFile>" 
    if $rc;
#** Open and slurp contents
open IN, "< $pathToManifest" 
    or die "Cannot open <$pathToManifest> for reading";
my $manifestContents;
{
    local $/;
    $manifestContents = <IN>;
}
#** Close manifest filehandle and delete archive and manifest files
close IN;
unlink $archiveFile;
unlink $pathToManifest;

#* Directory setup
my $bundleDir = abs_path($archiveDir) . "/" . "bundledSys"; 
mkdir $bundleDir; 
my $currentDir = abs_path('.'); # Full path to current directory 
#-debug-#print "DIR = $currentDir\n";

#* Copy system files to  $bundleDir
my @manifestContentLines = split(/\n/, $manifestContents);
foreach my $file (@manifestContentLines){
    #-debug-#print "AA = $file\n";
    my ($name, $path) = fileparse($file);
    my $bPath = "$bundleDir/$path";
    #** Do not copy files in current directory
    unless ($file =~ m/^\Q$currentDir\E/){
	#*** Create directory and copy system file
	system("mkdir -p $bPath") unless -e $bPath; 
	copy ($file, $bPath);
    }
}

#* Copy project files to $archiveDir
my $tarCmd = '';
$tarCmd .= "$BIN_tar cf temp.tar";
$tarCmd .= " --exclude=$archiveDir";
$tarCmd .= " --exclude=temp.tar";
$tarCmd .= " .";
print "TC = $tarCmd\n";
$rc = system($tarCmd);
die "Error gathering project files\n" if $rc;
chdir($archiveDir);
$tarCmd = '';
$tarCmd .= "$BIN_tar xf $currentDir/temp.tar";
print "TC = $tarCmd\n";
$rc = system($tarCmd);
die "Error copying project files\n" if $rc;
chdir($currentDir);
unlink('temp.tar');

#* Create tarball
$tarCmd = '';
$tarCmd .= "$BIN_tar cvzf";
$tarCmd .= " $archiveDir" . ".tar.gz";
$tarCmd .= " $archiveDir";
$rc = system($tarCmd);
die "Failed to make archive" if $rc;

#--???--#my $dh = DirHandle->new($currentDir);
#--???--#my $dirList = $dh->read();#    sort map {"$currentDir/$_"} $dh->read(); 
#--???--#
#--???--#print "DIRLIST = $dirList\n";
#--???--#
#--???--#exit(0);
#--???--#my @dirsToDescend = qw(.);
#--???--#find(\&processFile, $currentDir);
#--???--#    
#--???--#
#--???--#exit(0);
#--???--#
#--???--#
#--???--#sub processFile {
#--???--#    my $ffName = $File::Find::name;
#--???--#    mkdir $ffName if -d _;
#--???--#    unless ( ($ffName eq '.') or
#--???--#    	     ($ffName eq '..') or
#--???--#    	     ($ffName =~ m/\.tar\.gz/) or
#--???--#    	     ($ffName eq $archiveDir)
#--???--#    	){
#--???--#    	print "FILE = $ffName\n";
#--???--#    	copy ($ffName, $archiveDir);
#--???--#    	
#--???--#    }
#--???--#}

exit(0);
######################################################################
sub parseCmdLine {

  my $infoFlag = 0; # Flag for informational messages
  my %P; # Hash to be populated and returned
  my $clHelp = -1; # Default before setting options

  # DEVELOPERS ......................
  # NOTE: All valid arguments (except Help) *must* be put in @clArgs.
  my @clArgs = 
    qw(
inFile
outFile
archive
manifest
archiveDir
     );

  # Parse the command-line
  if (&GetOptions(# Option formats
		  # ====================================================
		  # Format
		  # ----------------------------------------------------
		  # optName           option
		  # optName!          negatable option
		  # optName:argType   argument optional
		  # optName=argType   argument required
		  # ====================================================
		  # argType = {s=>string, i=>integer, f=>float}
		  'Help:i' => \$clHelp,
		  "inFile=s",
		  "archive=s",
		  "manifest=s",
		  "archiveDir=s",
		  "outFile=s"
		 )){

    no strict 'refs'; # Turn off strict for the moment
    if ($clHelp > -1){
	$P{Help} = $clHelp;
	$infoFlag = 1;
    }
    # Load all options into %P
    foreach my $a (@clArgs){
      my $option = "opt_" . $a;
      if ($$option){
	$P{$a} = $$option;
	print "cmdLine -$a = $P{$a}\n";
      }
    }
  }# End of if (&GetOptions(...))
  else {
    my $msg = "Error while processing options. Check usage.\n";
    pod2usage(-verbose => 0, 
	      -exitval => 1,
	      -message => $msg);
  }
  use strict; # Turn strict back on

  if ($infoFlag){
    SWITCH: {
	if ($P{Help} == 0){
	    pod2usage(-verbose => 0,
		      -exitval => 'NOEXIT'
		);
	    last SWITCH;
	}
	if ($P{Help} == 1){
	    pod2usage(-verbose => 1,
		      -exitval => 'NOEXIT'
		);
	    last SWITCH;
	}
	if ($P{Help} > 1){
	    pod2usage(-verbose => 98,
		      -exitval => 'NOEXIT'
		);
	    last SWITCH;
	}
      }
      exit (0);
  }
  return %P;
}



__END__

