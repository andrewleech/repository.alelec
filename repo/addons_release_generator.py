#!/usr/bin/env python3
# *
# *  Copyright (C) 2014-2015 Andrew Leech
# *  Copyright (C) 2012-2013 Garrett Brown
# *  Copyright (C) 2010      j48antialias
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# *  Based on code by j48antialias:
# *  https://anarchintosh-projects.googlecode.com/files/addons_xml_generator.py
 
""" addons.xml generator """
from __future__ import print_function
import os
import sys
import zipfile
from glob import glob
import xml.etree.ElementTree as ET

def zipdir(dirPath=None, zipFilePath=None, includeDirInZip=True, excludeDotFiles=True):
    """Create a zip archive from a directory.
    
    Note that this function is designed to put files in the zip archive with
    either no parent directory or just one parent directory, so it will trim any
    leading directories in the filesystem paths and not include them inside the
    zip archive paths. This is generally the case when you want to just take a
    directory and make it into a zip file that can be extracted in different
    locations. 
    
    Keyword arguments:
    
    dirPath -- string path to the directory to archive. This is the only
    required argument. It can be absolute or relative, but only one or zero
    leading directories will be included in the zip archive.

    zipFilePath -- string path to the output zip file. This can be an absolute
    or relative path. If the zip file already exists, it will be updated. If
    not, it will be created. If you want to replace it from scratch, delete it
    prior to calling this function. (default is computed as dirPath + ".zip")

    includeDirInZip -- boolean indicating whether the top level directory should
    be included in the archive or omitted. (default True)

"""
    if not zipFilePath:
        zipFilePath = dirPath + ".zip"
    if not os.path.isdir(dirPath):
        raise OSError("dirPath argument must point to a directory. "
            "'%s' does not." % dirPath)
    parentDir, dirToZip = os.path.split(dirPath)
    #Little nested function to prepare the proper archive path
    def trimPath(path):
        archivePath = path.replace(parentDir, "", 1)
        if parentDir:
            archivePath = archivePath.replace(os.path.sep, "", 1)
        if not includeDirInZip:
            archivePath = archivePath.replace(dirToZip + os.path.sep, "", 1)
        return os.path.normcase(archivePath)
        
    outFile = zipfile.ZipFile(zipFilePath, "w",
        compression=zipfile.ZIP_DEFLATED)
    for (archiveDirPath, dirNames, fileNames) in os.walk(dirPath):
        if excludeDotFiles:
            fileNames = [f for f in fileNames if not f[0] == '.']
            dirNames[:] = [d for d in dirNames if not d[0] == '.']
        for fileName in fileNames:
            filePath = os.path.join(archiveDirPath, fileName)
            outFile.write(filePath, trimPath(filePath))
        #Make sure we get empty directories as well
        if not fileNames and not dirNames:
            zipInfo = zipfile.ZipInfo(trimPath(archiveDirPath) + "/")
            #some web sites suggest doing
            #zipInfo.external_attr = 16
            #or
            #zipInfo.external_attr = 48
            #Here to allow for inserting an empty directory.  Still TBD/TODO.
            outFile.writestr(zipInfo, "")
    outFile.close()

# Compatibility with 3.0, 3.1 and 3.2 not supporting u"" literals
if sys.version < '3':
    import codecs
    def u(x):
        return codecs.unicode_escape_decode(x)[0]
else:
    def u(x):
        return x
 
class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from the root of
        the checked-out repo. Only handles single depth folder structure.
    """
    def __init__( self, repo_folder=None ):
        if repo_folder is None:
            self._repo_folder = 'repository'
        # generate files
        self._generate_addons_file()
        self._generate_md5_file()
        # notify user
        print("Finished updating addons xml and md5 files")
 
    def _generate_addons_file( self ):
        # addon list
        addons = os.listdir( "." )
        # final addons text
        addons_xml = u("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<addons>\n")

        # loop thru and add each addons addon.xml file
        for addon in addons:
            try:
                # skip any file or .svn folder or .git folder
                if ( not os.path.isdir( addon ) or addon == ".svn" or addon == ".git" ): continue
                # create path
                _path = os.path.join( addon, "addon.xml" )
                if os.path.exists(_path):
                    # split lines for stripping
                    xml_lines = open( _path, "r" , encoding="UTF-8").read().splitlines()
                    # new addon
                    addon_xml = ""
                    # loop thru cleaning each line
                    version = None
                    for line in xml_lines:
                        # skip encoding format line
                        if ( line.find( "<?xml" ) >= 0 ): continue
                        # add line
                        if sys.version < '3':
                            addon_xml += unicode( line.rstrip() + "\n", "UTF-8" )
                        else:
                            addon_xml += line.rstrip() + "\n"
                        # Find version
                        xml = ET.parse(_path).getroot()
                        version = xml.attrib['version']
                    # we succeeded so add to our final addons.xml text
                    addons_xml += addon_xml.rstrip() + "\n\n"

                    # report progress
                    status = "* %s-%s"%(addon, version)
                    print(status + " "*max(0,60-len(status)), end="")

                    # create zip release
                    zipfilename = "%s-%s.zip"%(addon, version)
                    if not os.path.exists(os.path.join(self._repo_folder,addon,zipfilename)):
                        print(": Creating zip release")
                        for oldzip in glob(os.path.join(self._repo_folder,addon,"%s-*.zip"%(addon))):
                            os.unlink(oldzip)
                        zipdir(addon, zipfilename)
                        if not os.path.exists(os.path.join(self._repo_folder,addon)):
                            os.makedirs(os.path.join(self._repo_folder,addon))
                        os.rename(zipfilename, os.path.join(self._repo_folder,addon, zipfilename))
                    else:
                        print(": Up-to-date")

            except Exception as e:
                # missing or poorly formatted addon.xml
                print("Excluding %s for %s" % ( _path, e ))
        # clean and add closing tag
        addons_xml = addons_xml.strip() + u("\n</addons>\n")
        # save file
        if not os.path.exists(self._repo_folder):
            os.makedirs(self._repo_folder)
        self._save_file( addons_xml.encode( "UTF-8" ), file=os.path.join(self._repo_folder,"addons.xml") )
            
        
 
    def _generate_md5_file( self ):
        # create a new md5 hash
        try:
            import md5
            m = md5.new( open( os.path.join(self._repo_folder,"addons.xml"), "r" ).read() ).hexdigest()
        except ImportError:
            import hashlib
            m = hashlib.md5( open( os.path.join(self._repo_folder,"addons.xml"), "r", encoding="UTF-8" ).read().encode( "UTF-8" ) ).hexdigest()
 
        # save file
        try:
            self._save_file( m.encode( "UTF-8" ), file=os.path.join(self._repo_folder,"addons.xml.md5") )
        except Exception as e:
            # oops
            print("An error occurred creating addons.xml.md5 file!\n%s" % e)
 
    def _save_file( self, data, file ):
        try:
            # write data to the file (use b for Python 3)
            open( file, "wb" ).write( data )
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % ( file, e ))
 
 
if ( __name__ == "__main__" ):
    # start
    Generator()
