# -*- coding: utf-8 -*-

from __future__ import print_function
from PyQt5.QtWidgets import QApplication
import sys

# Note that importing QApplication sets up the PyOS_InputHook
# which is used by interactive python and ipython basic consoles but not ipython remote kernel.


# This startup code handles running the application in these ways:
# - python myapp.py, or python -i myapp.py
# - ipython -i myapp.py, or ipython myapp.py
# - within a basic python shell using: execfile('myapp.py')
#     or for python3: exec(open('myapp.py').read())
# - within an ipython shell using: execfile('myapp.py')
# - within an ipython shell using: "%run -i myapp", or "%run myapp"
# - within a remote kernel shell (qtconsole, spyder console ...): using run or execfile like above
#    Note that it works for anaconda 5.1 and above but failed with ipykernel version 4.6.0
#     ("%gui qt5" would not properly start the gui loop)
# Note that under IPython, the magic "%gui qt5" is automatically called if needed.


TEST = True
def printif(*args, **kwargs):
    if TEST:
        print(*args, **kwargs)

# This prevents loosing the Application object in case of reload (because of delete)
try:
    qApp
except NameError:
    qApp = None

_start_qt_loop = False
_interactive = False
_ipython_remote = False
_spyder_kernel_orig_stderr = None

def check_interactive():
    global _interactive, _start_qt_loop, _ipython_remote
    shell = None
    try:
        # check if under ipython
        import IPython
        import IPython.lib.guisupport
        shell = IPython.get_ipython()
        if shell:
            printif('Running under ipython')
            _interactive = True
            # check if gui is already started (by "%gui qt5"; can be disabled again with "%gui")
            if IPython.lib.guisupport.is_event_loop_running_qt4():
                _start_qt_loop = False
            else: # never started or disabled.
                _start_qt_loop = 'ipython'
            # check if we are under a remote kernel (qtconsole, spyder console...)
            import ipykernel.zmqshell
            if isinstance(shell, ipykernel.zmqshell.ZMQInteractiveShell):
                printif('Running under ipython remote kernel')
                _ipython_remote = True
            else:
                if shell.parent.file_to_run and not shell.parent.force_interact:
                    printif('Running under non interactive ipython')
                    # user called the file like: ipython file.py
                    # This immediately returns unless we run the loop
                    _start_qt_loop = True
                    _interactive = False
                printif('Running under interactive ipython')
    except ImportError:
        printif('IPython is not (fully) installed')
    #printif('sys has ps1 attr: ', hasattr(sys,'ps1'))
    if not shell: # under regular python executable
        # sys.flags.interactive represent the use of -i on the command line.
        if hasattr(sys,'ps1') or sys.flags.interactive:
            printif('Running under interactive python')
            _interactive = True
            # PyOS_InputHook is used.
            _start_qt_loop = False
        else:
            printif('Running under non-interactive python')
            _interactive = False
            _start_qt_loop = True

def load_qapp(argv=[' ']):
    global qApp
    if QApplication.startingUp():
        printif('setting qApp')
        qApp = QApplication(argv)
    if qApp is None:
        printif('resetting qApp')
        qApp = QApplication.instance()

def spyder_stdout_redirect():
    # spyder redirects stderr to a file in the temp directory
    #  (ipython qtconsole leaves it to the calling console, not inside the qtconsole)
    #  under windows it is %TMP%/spyder/kernel-*.stderr
    #    where %TMP% is often %USERPROFILE%/AppData/Local/Temp
    #  under linux it is /tmp/spyder-lupien/kernel-*.stderr
    # This prevents exception from the gui loop from showing up in the
    #  console window.
    # Redirect it (the kernel uses sys.__stderr__ for those erors) to
    # the kernel usual stderr
    global _spyder_kernel_orig_stderr
    if not _ipython_remote:
        return
    if sys.__stderr__ is not sys.stderr:
        printif('Redirecting __stderr__ for spyder')
        if _spyder_kernel_orig_stderr == None:
            _spyder_kernel_orig_stderr = sys.__stderr__
        sys.__stderr__ = sys.stderr

def start_qt_loop_if_needed(redirect_stderr=True):
    if redirect_stderr:
        spyder_stdout_redirect()
    if _start_qt_loop == 'ipython':
        printif('Enabling qt5 gui loop handling in ipython')
        import IPython
        ip = IPython.get_ipython()
        ip.run_line_magic('gui', 'qt5')
    elif _start_qt_loop:
        printif('Starting qApp loop')
        ret = qApp.exec_()
        if _interactive:
            return ret
        else:
            sys.exit(ret)
    else:
        printif('Qt loop already working')

def prepare_qt(argv=[' ']):
    check_interactive()
    load_qapp(argv)
    return qApp

if __name__ == "__main__":
    from PyQt5.QtWidgets import QPushButton
    # import matplotlib enables the gui
    #import matplotlib.pyplot as plt
    qApp_copy = prepare_qt()
    q = QPushButton('Test button')
    q.show()
    start_qt_loop_if_needed()

