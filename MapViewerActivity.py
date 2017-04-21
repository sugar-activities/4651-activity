import os, shutil, stat
import gtk, gobject
import popen2
from os import path as Path

import logging
import sugar.activity.activity as activity
from sugar.activity.activity import Activity
from sugar.datastore import datastore

"""
Alternative paths to locate JRE
"""
JAVA_HOME_PATHS=(
#"/usr/lib/jvm/jre", # gcj path DOESN'T WORK!!!
str(Path.join(Path.expanduser("~"),"Activities/Java.activity/jre")), # Java activity path
    )

# LOG level config
logging.basicConfig(level=logging.DEBUG)
#logging.basicConfig(level=logging.INFO)


"""
gvSIG batovi MapViewer activity

Requires:

* Sugar builds > 706

* A java installed or the Java activity installed

  For more information see: http://www.mediagala.com/rap/foro/viewtopic.php?f=8&t=166

On first _run_ executes son post-install actions.

"""
class MapViewerActivity(Activity):
    # viewer activity path (where is gvSIG activity)
    viewer_activity=None

    # viewer Home path (where is gvSIG installation)
    viewer_home=None


    #Java Home
    java_home=None


    def __init__(self, handle):
      logging.debug('Creating MapViewer handler.')
      
      Activity.__init__(self, handle)
      self.handle = handle

      # Register run() to run from gtk_main_loop
      # as soon as it gets idle.
      # Which is kludge to make it run after the loop has begun
      self.idleFunc = gobject.idle_add(self.run)

    def run(self):
      # Remove run() because we want it to run only once
      gobject.source_remove(self.idleFunc)

      # locate and check jre
      if not self.initializeJavaHome():
        # Exiting with a error  
        self.showMessageError("Can't found any JRE to run MapViewer:\nSee http://www.mediagala.com/rap/foro/viewtopic.php?f=8&t=166\nfor more information")
        logging.error("No JRE found!!!")
        logging.debug("Closing activity");
        self.close(True)
        return

      # setup environ properties
      self.viewer_activity=activity.get_bundle_path()
      self.viewer_home=Path.join(self.viewer_activity, 'viewer')

      os.environ['VIEWER_HOME']=self.viewer_home
      os.environ['VIEWER_ACTIVITY']=self.viewer_activity
      os.environ['JAVA_HOME']=self.java_home

      # do post-install actions
      self.postInstall()

      # identify gvSIG launcher
      viewer_sh = Path.join(self.viewer_home, 'mapViewer.sh')

      if not Path.exists(viewer_sh):
        raise Exception("Missing launcher: %s" % viewer_sh)

      # check execution permission
      self.fixExcecutionFilePermission(viewer_sh)
      
      try:
        logging.info("Executing '%s'" % viewer_sh);

        # execute gvSIG.sh
        gvSIG_process = popen2.Popen4('%s' % viewer_sh, 16)

        # writing stout in log file
        logging.info(gvSIG_process.fromchild.read())

        # wait until gvSIG exit
        rcode = gvSIG_process.wait()

        logging.info('mapViewer.sh returned with code=%d' % rcode)

      finally:
        logging.debug("Closing activity");
        self.close(True)

    def showMessageError(self, message):
        md = gtk.MessageDialog(self, 
              gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, 
              gtk.BUTTONS_CLOSE, message)
        md.run()
        md.destroy()

    """
    Initialize property ``java_home``

    Try to locate a valid java in ``JAVA_HOME_PATHS`` list

    Check that existe a *bin/java* executable file inside of it.

    If not JRE found returns False. Otherwise returns True
    """
    def initializeJavaHome(self):
      for jhome in JAVA_HOME_PATHS:
        logging.debug("check jre in %s" % jhome)
        if not Path.exists(jhome):
          logging.debug("%s not found" % jhome)
          continue
        if self.checkJavaExecutable(jhome):
          self.java_home=jhome
          logging.debug("ussing '%s' for JAVA_HOME" % jhome)
          return True
      else:
        logging.debug("No Java available in register paths: %s" % repr(JAVA_HOME_PATHS))
        return False




    """
    Check ``javaHome`` folder: check that exist a *bin/java* executable file

    Returns True/False
    """
    def checkJavaExecutable(self, javaHome):
      javaExe=Path.join(javaHome,"bin","java")
      if not Path.exists(javaExe):
        return False
      return os.access(javaExe, os.X_OK)

    """
    Run post install actions.

    This actions usually will be execute just once, in first activity run
    """
    def postInstall(self):
      self.installInGvSIGUserHome()
      self.installInUserHome()
      self.execScripts()

    """
    *Post Intall process:* Excecutes install scripts

    This actions usually will be execute just once, in first activity run.
    """
    def execScripts(self):
      # check if ther is any file to copy to 
      sourceFolder = Path.join(activity.get_bundle_path(), 'post-install', 'scripts')

      if not Path.exists(sourceFolder):
        # No files to execute
        return

      everyScriptOk = True

      # for all file/dir in souceFolder
      scriptFiles = os.listdir(sourceFolder)

      for aFile in scriptFiles:
        fext = Path.splitext(aFile)[1]
        aFilePath = Path.join(sourceFolder,aFile)
        if fext == "py":
          # Exec python script
          execOk = self.execPython(aFilePath)
          if execOk:
            shutil.move(aFilePath,aFilePath+".done")
          else:
             everyScriptOk=False


        elif fext == "sh":
          # Exec Shell script
          execOk = self.execShell(aFilePath)
          if execOk:
            shutil.move(aFilePath,aFilePath+".done")
          else:
             everyScriptOk=False

        elif fext == "done":
          # Nothing to do
          pass

        else:
          # Ignoring file
          logging.debug("Ignoring post-install script: " + aFilePath)


      if everyScriptOk:
        # rename folder to avoid execution on next application open
        shutil.move(sourceFolder, sourceFolder+".done")

    """
    Excecutes a python script file
    """
    def execPython(self,aFile):
      logging.debug("Executing python script '%s'" % aFile);
      try:
        # open file in read-only mode
        f = file(aFile,"r")

        # exec script
        try:
          exec f
        finally:
          f.close()

        return True
      except Exception, exc:
        logging.error("Excecuting file %s: %s" % (aFile,exc));
        return False
      
    """
    Fix (set) execution permission of a file
    """
    def fixExcecutionFilePermission(self, aFile):
      # check execution permission
      if not os.access(aFile, os.X_OK):
        # set excecution permission
        os.chmod(aFile,os.stat(aFile)+stat.S_IEXEC)

    """
    Excecutes a shell script file
    """
    def execShell(self,aFile):
      logging.debug("Executing '%s'" % aFile);
      try:
        mProcess = popen2.Popen4('%s' % aFile, 16)
        logging.debug(mProcess.fromchild.read())
        rcode = mProcess.wait()
        return rcode == 0
      except Exception, exc:
        logging.error("Excecuting file %s: %s" % (aFile,exc));
        return False


    """
    *Post Intall process:* Install files in user home

    Move files from ``{activity_folder}/post-install/user-home`` to ``$HOME``

    **NOTE**: if a file/dir already exist **will be ignored** (Keeping untouched original files)
    """
    def installInUserHome(self):
      # check if ther is any file to copy to 
      sourceFolder = Path.join(activity.get_bundle_path(), 'post-install', 'user-home')

      if not Path.exists(sourceFolder):
        # No files to copy
        return

      homeUserFolder = Path.expanduser("~")

      #merge folder
      self.mergeFolder(sourceFolder,homeUserFolder)

      #rename source folder to prevent rerun of this step
      os.rename(sourceFolder,sourceFolder+".done")

      #done
      return

    """
    *Post Intall process:* Install files in the gvSIG user home folder

    Move files from ``{activity_folder}/post-install/user-gvsig-home`` to ``$HOME/gvSIG``
    """
    def installInGvSIGUserHome(self):
      # check if ther is any file to copy to 
      sourceFolder = Path.join(activity.get_bundle_path(), 'post-install', 'user-gvsig-home')

      if not Path.exists(sourceFolder):
        # No files to copy
        return

      homeGvsigUserFolder = Path.expanduser("~/gvSIG")

      if not Path.exists(homeGvsigUserFolder):
        # Create gvSIG user home folder
        os.mkdir(homeGvsigUserFolder)


      #move files
      self.mergeFolder(sourceFolder,homeGvsigUserFolder)

      #rename source folder to prevent rerun of this step
      os.rename(sourceFolder,sourceFolder+".done")

      #done
      return

    """
    Move files from ``sourceFolder`` into ``targetFolder``

    ``sourceFolder`` must be a folder
    ``targetFolder`` must be a folder or not exists (so it will be created)
    ``overrideTarget`` if it's ``False`` raise an exception when target already contains the file/dir to move. if ``ignoreExisting``
    ``ignoreExisting`` modifies ``overrideTarget`` option (when it's ``False``) to don't raise an exception, just skip file/folder
    """
    def moveFiles(self,sourceFolder,targetFolder,overrideTarget=True,ignoreExisting=True):
      if not Path.exists(targetFolder):
        # Create target folder
        os.makedirs(targetFolder)
        # set overrideTarget to True because target is new
        overrideTarget=True
      elif not Path.isdir(targetFolder):
        raise Exception("%s must be a dir" % targetFolder)

      # for all file/dir in souceFolder
      toMoveList = os.listdir(sourceFolder)
      for toMove in toMoveList:

        target = Path.join(targetFolder,toMove)
        # check if exists target
        if Path.exists(target):
          if overrideTarget:
            if ignoreExisting:
              continue
            
          else:
            if ignoreExisting:
              continue
            else:
              raise Exception("%s alredy exists in target folder %s" % (toMove, targetFolder))


        # move file/dir
        shutil.move(Path.join(sourceFolder, toMove), targetFolder)

   
    """
    Merge folder content: Copy all missing folders and files from
    ``sourceFolder`` to ``targetFolder``.

    Process doesn't override existing files in ``targetFolder``
    """
    def mergeFolder(self,sourceFolder,targetFolder):
      # get folder contents
      names = os.listdir(sourceFolder)

      if not Path.exists(targetFolder):
        # Create target folder if not exists
        os.makedirs(targetFolder)

      for name in names:
        srcname = Path.join(sourceFolder, name)
        dstname = Path.join(targetFolder, name)
        if Path.isdir(srcname):
          # Recursive call to mergeFolder
          self.mergeFolder(srcname,dstname)
        else:
          if not Path.exists(dstname):
            # Copy new file
            shutil.copy(srcname,dstname)
          else:
            # skip existing file
            continue





