#!/usr/bin/env python
"""
The kertPR script generates a LaTeX project report based on templates.  
"""

# Defaults
__dirTemplates__ = "../src/templates/kert"
__appname__ = "kertPR"
__author__ = "Timothy C. Burt"
__email__ = "rketburt@gmail.com"
__version__ = 1.0

# ==========================================================
# Module-level imports
# ----------------------------------------------------------
# Operating system interaction
import os
# System calls
import sys
# Logging mechanism
import logging
# Date and time
import datetime as dt
# Regular expressions
import re
# Shell utilities
import shutil
# Login information
import getpass
# Filename filtering
import fnmatch
# XML capabilities in ElementTree (with C accelerator if possible)
import xml.etree.cElementTree as ET
# Keyboard input
from builtins import input


# ==========================================================
# Class
# ----------------------------------------------------------
class kertPRfam:
    def __init__(self):
        self.fam = {}
        

# ==========================================================
# Module methods
# ----------------------------------------------------------

# ---- buildTemplateDirs
def buildTemplateDirs(inDirTemplates):
    """
    Build a list of directories from the comma-separated list 
    input (inDirTemplates) and add the default directory 
    (__dirTemplates__) unless the input includes the exclusion 
    character (#).
    """
    if inDirTemplates == __dirTemplates__:
        dirList = [__dirTemplates__]
    else:
        # Separate the (possible) list of directories
        dirList = [x.strip() for x in inDirTemplates.split(',')]
        # Determine if the exclusion character is one of the directories 
        if '#' not in dirList:
            dirList.append(__dirTemplates__)
    # The outermost list() accommodates Python 3 behavior of filter as a generator
    dirList = list(filter(lambda x:x!='#', dirList))
    
    msg = 'Template directories: ' + ', '.join(dirList)
    lgr.log(logging.DEBUG, msg)
    return dirList

# ----- getFiles
def getTranslators(dirs):
    """
    Put all files found under dirs into a fileList.  If 
    """
    translators = []
    for dir in templateDirs:
        msg = ''
        msg = 'Path ' + dir + ' '
        if os.path.isdir(dir):
            msg = msg + 'is a directory'
            lgr.log(logging.DEBUG, msg)
            # Determine if the directory contains subdirectories with valid
            # translator files
            for root, subFolders, files in os.walk(dir):
                fileList = []
                for file in files:
                    fullName = os.path.join(root,file)
                    fileList.append(fullName)
                    # Find all files that are valid translators - Currently
                    # 'valid' means success of extraction, not up-front
                    # validation against a descriptione (e.g. DTD or
                    # Schema)
                    if fnmatch.fnmatch(file, '*-translator.xml'):
                        thisTr = extractTranslator(fullName)
                        if thisTr == 0:
                            msg = "WARNING: " + fullName
                            msg = msg + " is not a proper translator file"
                            lgr.log(logging.WARNING, msg)
                        else:
                            thisTr['sourceFile'] = fullName
                            if thisTr != 0:
                                thisTr['fsFileList'] = fileList
                                translators.append(thisTr)
        else:
            msg = 'WARNING: ' + msg + 'is not a directory'
            lgr.log(logging.WARNING, msg)
    
    return translators
    

# ----- extractTranslator
def extractTranslator(infile):
    """
    Extract translator information from the input infile.  
    """
    
    msg = "Extracting translator elements in " + infile
    lgr.log(logging.DEBUG, msg)
    # Read and parse the data file
    tree = ET.parse(infile)

    # Ensure the 'translator' tag exists
    rootElem = tree.getroot()
    xlator = kertPRfam()
    xlator.fam['tree'] = rootElem
    tName = rootElem.tag
    if tName != 'translator':
        msg = tName + " not found in " + infile
        lgr.log(logging.WARNING, msg)
        return 0

    # ---- Populate the template information for this family
    fam = {}
    # Get the family name
    tName = 'family'
    aName = 'name'
    family = rootElem.find(tName)
    if family == None:
        msg = "WARNING: Element " + tName 
        msg += " not found in " + infile
        lgr.log(logging.WARNING, msg)
        return 0

    famName = family.attrib.get(aName)
    if famName == None:
        msg = "WARNING: Attribute " + aName
        msg += " not found in " 
        msg += tName + " element from " + infile
        lgr.log(logging.WARNING, msg)
        return 0

    msg = "Family name = " + famName
    lgr.log(logging.DEBUG, msg)
    fam[aName] = famName

    # Get the short description of the family 
    sDesc = tree.findtext('family/description/short').strip()
    fam['sDesc'] = sDesc
    msg = "Short description = " + sDesc
    lgr.log(logging.DEBUG, msg)

    memberList = tree.findall("family/members/member")
    fam['members'] = {}
    for m in memberList:
        # Get the member name
        mName = m.get("name")
        lgr.log(logging.DEBUG, "Member name = " + mName)
        fam['members'][mName] = {}
        mmbr = fam['members'][mName]
        # Get the member description            
        sDesc = m.findtext("description/short")
        if sDesc == None:
            sDesc = "(No description provided.)"
        mmbr['sDesc'] = sDesc.strip()
        lgr.log(logging.DEBUG, "Member desc (short) = " + mmbr['sDesc'])

        # Get member replacements
        mmbr['replacements'] = {}
        mrep = mmbr['replacements']
        replList = m.findall("replacements/replacement")
        for r in replList:
            rtag = r.get("elemtag")
            mrep[rtag] = r.text.strip()
            msg = "Member replacement <" + rtag
            msg += "> = " + mrep[rtag]
            lgr.log(logging.DEBUG, msg)
    
    return fam

# **********************************************************
# **********************************************************
# Main script
# ----------------------------------------------------------
# ----------------------------------------------------------
if __name__ == '__main__':
    # ======================================================
    # Script-level imports
    # ------------------------------------------------------
    # Command-line parsing
    from optparse import OptionParser

    # Setup and parse command-line
    # -----
    usageMsg = "%prog [--dirTemplates dir1[,dir2,...][,#]] [--help] [--verbose] [--version]"
    parser = OptionParser(
        description=__doc__, 
        version="%%prog v%s" % __version__,
        usage=usageMsg
        )
    # Options
    #  --quiet
    #  --verbose
    parser.add_option(
        '-d', '--dirTemplates', 
        action="store", type="string", dest="dirTemplates",
        default=__dirTemplates__, 
        help="Comma-separated list of additional template directories. If one of the list is the character #, then the default template directory is not used.")
    parser.add_option(
            '-q', '--quiet', 
            action="count", dest="quiet",
            default=0, 
            help="Decrease the verbosity. Can be used twice for extra effect.")
    parser.add_option(
        '-v', '--verbose', 
        action="count", dest="verbose",
        default=2, 
        help="Increase the verbosity. Can be used twice for extra effect.")
    # opts are the values that have been successfully parsed.
    # args are the leftover arguments from the command-line
    opts, args  = parser.parse_args()

    # Setup logging
    # -----
    # Message levels: Critical, Error, Warning, Info, Debug
    log_levels = [logging.CRITICAL, logging.ERROR, logging.WARNING,
                  logging.INFO, logging.DEBUG]
    # Derive the verbosity level from command-line arguments
    opts.verbose = min(opts.verbose - opts.quiet, len(log_levels) - 1)
    opts.verbose = max(opts.verbose, 0)
    # Define format for logging: <Datetime> <message>
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=log_levels[opts.verbose],
                        format=FORMAT)
    lgr = logging.getLogger(__name__)
    
    # ======================================================
    # Ensure the template directories are available
    # ------------------------------------------------------
    msg = 'Build template directory list ...'
    lgr.log(logging.DEBUG, msg)
    templateDirs = buildTemplateDirs(opts.dirTemplates)
    lgr.log(logging.DEBUG, "Template directories = {}".format(templateDirs))
    translators = getTranslators(templateDirs)
    sortedTranslators = sorted(translators,
                               key=lambda x:x['name'].lower())

    


    # Select a destination directory
    destDir = input("[Enter destination directory] ")
    destDir = os.path.expanduser(destDir)
    if os.path.exists(destDir):
        msg = "Using the existing directory " + destDir
        lgr.log(logging.DEBUG, msg)
    else:
        msg = "Creating new directory " + destDir
        os.makedirs(destDir)

    # Obtain project basename
    projBasename = input("[Enter project basename] ")
    lgr.log(logging.DEBUG, "Project basename is " + projBasename)
    
    

    # Display the candidate translators
    for (i,n) in enumerate(sortedTranslators):
        disp = '  '.join([str(i),n['name']])
        disp += ': ' + n['sDesc']
        print(disp)

    # Select the template
    templateType = input("[Enter template family #] ")
    thisTmpl = sortedTranslators[int(templateType)]
    tmplName = thisTmpl['name']
    # Log the name entered by the user.
    msg = ''
    msg += "Template type is " + tmplName
    lgr.log(logging.DEBUG, msg)

    # Show the members of this template
    tmplMembers = thisTmpl['members']
    sortedTmplMemberKeys = sorted(iter(tmplMembers.keys()))
    while True:
        try:
            print("Members of " + tmplName + " family of templates")
            for (i,m) in enumerate(sortedTmplMemberKeys):
                if m == 'ALL':
                    print("{}   (INFO ONLY) {}: {}".format(i, m, tmplMembers[m]['sDesc']))
                else: 
                    print("{}   {}: {}".format(i, m, tmplMembers[m]['sDesc']))
                
            # Select the member 
            memberType  = input("[Enter " + tmplName + " member #] ")
            if memberType == '0':
                raise ValueError
        except ValueError:
            m = "-"*10
            m+= os.linesep
            m+="Note: The ALL member type should not be selected. Please reenter."
            m+= os.linesep
            m+= "-"*10
            print(m)
        else:
            break
    memName = sortedTmplMemberKeys[int(memberType)]
    thisMember = tmplMembers[memName]

    
    # Capture the replacements
    # NOTE: Begin with the ALL replacements, then the update() call will
    #       *change* any overlap replacements.
    replaceList = tmplMembers['ALL']['replacements']
    if memName != "ALL":
        replaceList.update(thisMember['replacements'])
    
    msg = "Generating project " +projBasename 
    msg += " from " +tmplName +" " +memName +" ..."
    print(msg)
    lgr.log(logging.DEBUG, msg)

    # Log the file list for this template
    tmplFiles = thisTmpl['fsFileList']
    lgr.log(logging.DEBUG,  "File list from directory")
    [lgr.log(logging.DEBUG, "   "+f) for f in tmplFiles]
    # Copy the files for this template to the destination directory
    for f in tmplFiles:
        # Copy templates to project files
        newFname = re.sub(tmplName, projBasename, os.path.basename(f))
        newFnameFull = destDir + os.path.sep + newFname
        msg = 'Copying to ' + newFnameFull
        if lgr.getEffectiveLevel() == logging.DEBUG:
            msg += ' from ' + f
        lgr.log(logging.INFO, msg)
        shutil.copy(f, newFnameFull)
        # Read the file for subsequent substitutions
        try:
            with open(newFnameFull, 'r') as fHandle:
                strForSubst = fHandle.read()
        except UnicodeDecodeError:
            msg = 'Binary file: No substitutions needed'
            lgr.log(logging.WARN, msg)
            continue
        
        
        # Perform template replacements 
        for repl in iter(replaceList.keys()):
            msg = "-->Replacing {} ".format(repl)
            msg+= "with {}".format(replaceList[repl])
            lgr.log(logging.DEBUG, msg)
            blkOld = r"<" +repl +r">.*</" +repl +">"
            blkNew = "<" +repl +">" + os.linesep
            blkNew += replaceList[repl]
            preSubStr = strForSubst
            strForSubst = re.sub(re.compile(blkOld, re.DOTALL),
                                 blkNew.replace('\\', r'\\'),
                                 preSubStr)

                
        # Perform entity replacements
        replEntities = {'tmplBasename':projBasename, 
                        'tmplCreationDate':dt.date.today().strftime("%d/%m/%y"), 
                        'tmplAuthor':getpass.getuser()}
        for r in iter(replEntities.keys()):
            preSubStr = strForSubst
            strForSubst = strForSubst.replace(r, replEntities[r])
           

        # Write the new contents    
        fHandle = open(newFnameFull, 'w')
        fHandle.write(strForSubst)
        fHandle.close()


    

