#!/usr/bin/env python3
# Git Repo https://github.com/Fuzen-py/Flora-Cli
import json
import os
import sys
import platform
try:
    import psutil
except:
    print('Psutil is not installed')
    quit(-1)
import re
import time
import traceback
import urllib
import zipfile
import tarfile
from shutil import rmtree
from subprocess import PIPE
from urllib.request import urlretrieve
import subprocess
try:
    from logbook import Logger, FileHandler, StreamHandler
except:
    print('Logbook is not installed')
    quit(-1)

log = Logger('Flora-Cli Log')


print('Use at your own risk, I am not responsible for anything caused by this program!')
print('If an problem arises please create submit an issue at https://github.com/Fuzen-py/Flora-Cli/issues')
home = os.path.expanduser("~")
options = {'debug': False, 'First Start': False, 'edit config': False}
list_of_commands = ['Edit Config', 'Test Python', 'Update PIP Dependencies', 'network speed test', 'custom command',
                    'kill pid', 'bash', 'update', 'task manager', 'android adb installer', 'aria2 installer',
                    'Edit Hosts']
da_folder = os.path.join(home, '.Flora_Command-Line')
list_of_commands += ['Exit']
running_pid = {'list': []}
join = os.path.join
exist_check = os.path.exists
sudo_command = 'sudo '
if os.name == 'nt':
    sudo_command = 'runas.exe /savecred /user:{} '.format(input('Administrator user name\n>>>'))


class Utilities:
    def exiter(self):
        print('Exiting...')
        self.process_killer()
        exit()

    def reporthook(self, blocknum, blocksize, totalsize):
        readsofar = blocknum * blocksize
        if totalsize > 0:
            percent = readsofar * 1e2 / totalsize
            s = "\r%5.1f%% %*d / %d" % (
                percent, len(str(totalsize)), readsofar, totalsize)
            sys.stderr.write(s)
            if readsofar >= totalsize:  # near the end
                sys.stderr.write("\n")
        else:  # total size is unknown
            sys.stderr.write("read %d\n" % (readsofar,))

    def unzip(self, source_filename: str, path: str, remove_zip: bool = True):
        try:
            with zipfile.ZipFile(source_filename) as zf:
                if not exist_check(path):
                    os.mkdir(path)
                zf.extractall(path=path)
            if remove_zip:
                os.remove(source_filename)
        except Exception as error:
            self.error_handler(error)

    def process_killer(self, p=None):
        if p is None:
            for p in running_pid['list']:
                p.terminate()
                try:
                    p.kill()
                except Exception as error:
                    self.error_handler(error)
                    print('failed to kill {0}'.format(p))
            return
        p = psutil.Process(int(p))
        if os.name != 'nt':
            subprocess.Popen(['kill', p.pid], shell=True).communicate()
        else:
            p.kill()
            p.terminate()
        psutil.pids()
        p = int(p.pid)
        if p in psutil.pids():
            print('Failed to kill')
        else:
            print('Exited')

    def get_values(self, fresh=False):
        val = {}
        path_to_config = da_folder
        if not exist_check(path_to_config):
            print('I am not responsible for anything that goes wrong while using this')
            if not self.yes_or_no('Would you like to continue?'):
                return
            os.mkdir(path_to_config)
            with open(join(path_to_config, 'values.json'), mode='w', encoding='utf-8', errors='backslashreplace') as f:
                json.dump(obj={}, fp=f, sort_keys=True, indent=4)
            fresh = True
        if fresh or not exist_check(join(path_to_config, 'values.json')):
            val['name'] = str(input('What Should I call you?\nName: ')).strip()
            print('Hello', val['name'])
            prompt = 'Do You Have any libraries that cannot be updated through pip -U {name} [like a git repo]\n'
            if self.yes_or_no(prompt):
                pip_list = [True]
                adding_entries = True
                print('Please Press Enter After each command.\nType "Done" when done.')
                while adding_entries:
                    entry = str(input('Command: ')).strip()
                    if entry.lower() != 'done':
                        pip_list += [entry]
                    else:
                        adding_entries = False
                if len(pip_list) == 1:
                    pip_list = [False]
            else:
                pip_list = [False]
            val['pip list'] = pip_list
            with open(join(path_to_config, 'values.json'), 'w') as f:
                json.dump(val, f, sort_keys=True, indent=4)
        else:
            with open(os.path.join(path_to_config, 'values.json'), 'r') as f:
                del val
                val = json.load(f)
        return val

    def yes_or_no(self, question=None):
        while True:
            try:
                if question:
                    prompt = question + 'Yes or No\n>>> '
                else:
                    prompt = 'Yes or No\n>>> '
                x = input(prompt).lower()
                if x in ['yes', 'ye', 'y', 'no', 'n']:
                    if x.startswith('y'):
                        return True
                    if x.startswith('n'):
                        return False
            except Exception as error:
                self.error_handler(error)

    def error_handler(self, error, bypass: bool = False):
        log.error('\n'.join(traceback.format_exception(type(error), error, error.__traceback__)))
        if options['debug'] is not True or not bypass:
            return


class SystemManagement(Utilities):
    def host_file_editor(self):
        print('This requires the script to be run as root/admin')
        if not self.yes_or_no('Would you like to continue?'):
            print('Returning to menu..')
            return
        path_to_hosts = str(input('Path to hosts file: '))
        if not exist_check(join(da_folder, 'hosts')):
            os.mkdir(join(da_folder, 'hosts'))
        print('Making a host file backup')
        with open(path_to_hosts, 'r') as backup:
            b = backup.read()
            files = os.listdir(join(da_folder, 'hosts'))
            backup_name = 'host.backup'
            if 'host.backup' in files:
                x = 1
                while 'host.backup{0}'.format(x) in files:
                    x += 1
                backup_name = 'host.backup{0}'.format(x)
                backup_path = os.path.join(da_folder, 'hosts', backup_name)
            else:
                print('Failed to make a backup')
                raise Exception('Host File backup Failed')
            with open(join(backup_path, 'w')) as x:
                x.write(b)
        print('Done:', backup_path)
        host_config = os.path.join(da_folder, 'host_sources.json')
        if exist_check(host_config):
            with open(host_config, 'r') as hosts:
                host_sources = json.load(hosts)
        else:
            with open(host_config, 'w') as hosts:
                host_sources = {}
                json.dump(host_sources, hosts)
        sources = []
        for key in host_sources.keys():
            sources += [key]
        sources += ['Add your own']
        sources += ['Cancel']
        msg = 'Host Sources:\n'
        for option in sources:
            msg += '\n{0}. {1}'.format(sources.index(option), option)
        print(msg)
        try:
            choice = sources[int(input('Option: '))]
            if choice == 'Cancel':
                return
            if choice == 'Add your own':
                name = str(input('Name:'))
                link = str(input('DL link to Host file (ZIP NOT SUPPORTED):'))
                host_sources[name] = link
                f = open(join(da_folder, 'host_sources.json'), 'w')
                json.dump(host_sources, f, indent=4)
            else:
                link = host_sources[choice]
            if link:
                print('Downloading host file...')
                # may have to use url retrieve
                urlretrieve(link, da_folder + 'dl_host', reporthook=self.reporthook)
                with open(join(da_folder, 'dl_host')) as new_host:
                    if self.yes_or_no('Would you like to append to current hosts?\n'):
                        print('Append hosts...')
                        f = open(path_to_hosts, 'a')
                    else:
                        print('Overwriting hosts...')
                        f = open(path_to_hosts, 'w')
                    f.write('\n# Added By Flora-CLI\n')
                    f.write(new_host.read())
                    f.write('\n#End')
                    f.close()
                print('Done')
        except Exception as e:
            self.error_handler(e)
            print('Invallid option')

    def task_manager(self, loop=False):
        processes = psutil.pids()
        display = '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format('PID', 'Name', 'CPU%', 'MEMORY%',
                                                                             'Current Working Directory')
        for p in processes:
            try:
                p = psutil.Process(p)
                display += '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format(p.pid, p.name(),
                                                                                      str(p.cpu_percent()) + '%',
                                                                                      str(p.memory_percent()) + '%',
                                                                                      p.cwd())
            except Exception as e:
                self.error_handler(e)
        print(display)
        if loop or self.yes_or_no('Would You like me to terminate a process?\n'):
            print('Enter Done, when you are done')
            p = input('PID:\n>>> ')
            print(p)
            if p.lower() == 'done':
                return
            if p.lower() == 'list':
                processes = psutil.pids()
                display = '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format('PID', 'Name', 'CPU%',
                                                                                     'MEMORY%',
                                                                                     'Current Working Directory')
                for p in processes:
                    try:
                        p = psutil.Process(p)
                        display += '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format(p.pid, p.name(), str(
                            p.cpu_percent()) + '%', str(p.memory_percent()) + '%', p.cwd())
                    except Exception as e:
                        self.error_handler(e)
                p = 'list'
            if p.lower() != 'list':
                try:
                    p = psutil.Process(int(p))
                    if os.name != 'nt':
                        subprocess.Popen(['kill', p.pid]).communicate()
                    else:
                        p.kill()
                        p.terminate()
                    psutil.pids()
                    p = int(p.pid)
                    if p in psutil.pids():
                        print('Failed to kill')
                    else:
                        print('Exited')
                except Exception as e:
                    self.error_handler(e)
                    print('Sorry, I cannot terminate that process')
                    time.sleep(2)
            self.task_manager(True)

    def speed_test(self):
        share = None
        print('Running Speedtest')
        a = [i.decode('utf-8') for i in subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
        try:
            a, share = self.speed_test_formatter(a)
        except Exception as e:
            self.error_handler(e)
            print('required dependency not installed')
            if self.yes_or_no('Would you like for me to install speedtest-cli?'):
                if os.name != 'nt':
                    subprocess.Popen('sudo pip install speedtest-cli -U'.split()).communicate()
                else:
                    subprocess.Popen('pip install speedtest-cli -U'.split()).communicate()
                a = [i.decode('utf-8') for i in subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
                cheker = ''.join(a)
                print(cheker)
                cheker = len(cheker.split('speedtest-cli')) == 2
                if cheker:
                    a = 'Failed To Install speedtest-cli\n Lacking root permissions?'
                else:
                    try:
                        a, share = self.speed_test_formatter(a)
                    except Exception as e:
                        self.error_handler(e)
                        share = None
            else:
                a = 'Missing Dependency speedtest-cli'
        finally:
            if share:
                print(a)
                print(share)
                if self.yes_or_no('Would you like for me to open this in a browser?'):
                    if os.name == 'nt':
                        subprocess.Popen('start {0}'.format(share).split())
                    elif os.name == 'posix':
                        subprocess.Popen('open {0}'.format(share).split())
                    else:
                        subprocess.Popen('xdg-open {0}'.format(share).split())

    def speed_test_formatter(self, a):
        b = ['', '', '']
        b[0] = a[4].split(':')[-1].strip().strip('\'')
        b[1] = a[6].strip()
        b[2] = a[8].strip()
        share = a[-1]
        a = '\n'.join(b)
        share = share.split('results: ')[-1].strip()
        return a, share

    def pip_updater(self):
        print('Please Note, this has to be run as root or in a venv')
        if not self.yes_or_no('would you like to continue?'):
            return
        p = subprocess.Popen('pip freeze --local'.split(), cwd=da_folder, stdout=subprocess.PIPE).stdout.read().decode('utf-8', errors='backslashreplace').replace('\n', ' ').replace('==', '>=').strip()
        if os.name != 'nt':
            if not self.yes_or_no('Do you need sudo?'):
                pip_update_command = 'pip install -U {}'.format(p)
            else:
                pip_update_command = 'sudo -H pip install -U {}'.format(p)
        else:
            pip_update_command = 'pip install -U {}'.format(p)
        if self.yes_or_no('Do you want to install pre releases?'):
            pip_update_command += ' --pre '
        x = subprocess.Popen(pip_update_command.split(), cwd=da_folder)
        print('Updating pip please wait...')
        x.communicate()
        print('Done')


class Debugging(Utilities):
    def test_python(self):
        print('enter \n for multi-lined code')
        while True:
            try:
                x = str(input('>>> ')).strip().replace('\\n', '\n')
                while x.endswith('\n'):
                    x += str(input('>>> ')).strip().replace('\\n', '\n')
                if not x.startswith('exit'):
                    exec(x, globals(), locals())
                else:
                    return
            except Exception as e:
                self.error_handler(e, True)

    def run_bash_commands(self):
        print('Entering Bash Mode....')
        while True:
            try:
                x = input('Command >>').strip()
                if x.lower() in ['exit', 'done', 'quit']:
                    return
                x = x.split()
                print(subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE).stdout.read())
            except Exception as error:
                self.error_handler(error)




class Downloading(Utilities):
    def get_android_adb(self):
        if exist_check(join(da_folder, 'adb')):
            rmtree(join(da_folder, 'adb'))
        url = 'https://dl.google.com/android/repository/repository-12.xml'
        #
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        respData = resp.read()
        latest = re.findall('<sdk:url>platform-tools_r(.*?)</sdk:url>', str(respData))
        osname = sys.platform
        if osname == 'win32':
            osname = 'windows'
        elif osname == 'cygwin':
            osname = 'windows'
        elif osname == 'darwin':
            osname = 'macosx'
        else:
            osname = 'linux'
        if len(latest) > 0:
            latest = str(latest[0])
            latest = latest.split('-')
            if len(latest) > 1:
                latest = str(latest[0])
                latest = ('platform-tools_r' + latest + '-' + osname + '.zip')
                downloadlink = 'https://dl.google.com/android/repository/' + latest
                print('Downloading...')
                urlretrieve(downloadlink, join(da_folder, 'latest.zip'), self.reporthook)
            if not zipfile.is_zipfile(join(da_folder, 'latest.zip')):
                print('Something went wrong\nFile downloaded is not a zip')
                return
            print('Extracting...')
            self.unzip(join(da_folder, 'latest.zip'), da_folder)
            print('Renaming Folder..')
            os.rename(join(da_folder, 'platform-tools'), join(da_folder, 'adb'))
            print('Done')

    def get_aria2(self):
        if sys.platform == 'cygwin':
            print('Please install using your package manager')
            return
        link = 'https://github.com/aria2/aria2/releases/latest'
        resp = urllib.request.urlopen(urllib.request.Request(link)).read()
        resp = resp.decode('utf-8')
        version = re.findall('<span class="css-truncate-target">(.*?)</span>', resp)
        if len(version) < 1:
            return
        version = version[0]
        version_num = version[8:]
        if not self.yes_or_no('Would you like to install aria2 {0}\n'.format(version)):
            return
        if sys.platform == 'darwin':
            dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-osx-darwin.tar.bz2'
        elif sys.platform == 'linux' or sys.platform == 'linux2':
            dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}.tar.bz2'
        elif sys.platform == 'win32':
            if exist_check(join(da_folder, 'aria2')):
                rmtree(join(da_folder, 'aria2'))
            if platform.uname()[-1] == 'x86_64':
                dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-win-64bit-build1.zip'
            else:
                dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-win-32bit-build1.zip'
            dl = dl.format(version, version_num)
            path_to_zip = os.path.join(da_folder, 'aria2.zip')
            urlretrieve(dl, path_to_zip, reporthook=self.reporthook)
            self.unzip(path_to_zip, da_folder)
            name = None
            for names in os.listdir(da_folder):
                if names.startswith('aria2'):
                    name = names
                    break
            if name is None:
                return
            os.rename(os.path.join(da_folder, name), os.path.join(da_folder, 'aria2'))
            return
        else:
            print('Your system isn\'t supported.\nCheck - https://github.com/aria2/aria2/releases/latest to install')
            return
        print('Downlading...')
        dl = dl.format(version, version_num)
        print(dl)
        path_to_tar = join(da_folder, 'aria2.tar.bz2')
        urlretrieve(dl, path_to_tar, reporthook = self.reporthook)
        import tarfile
        if not tarfile.is_tarfile(path_to_tar):
            print('Something went wrong! File isnt a tar')
            if exist_check(path_to_tar):
                pass
                os.remove(join(da_folder, 'aria2.tar.bz2'))
            return
        print('Extracting..')
        file = tarfile.open(path_to_tar, 'r:bz2')
        file.extractall(da_folder)
        file.close()
        os.remove(path_to_tar)
        for file in os.listdir(da_folder):
            if file.startswith('aria2'):
                file = file
                break
        configureflags = ''
        makeflags = ''
        makeinstallflags = ''
        if self.yes_or_no('[Advanced]Do you wish to input flags?\n'):
            print('press enter if no flags for that option (be sure to input (-- or -)')
            configureflags = input('Configure Flags\n>>> ')
            makeflags = input('Make Flags\n>>> ')
            makeinstallflags = 'Make install Flags\n>>> '
        if_sudo = ''
        if self.yes_or_no('Do you need sudo?\n'):
            if_sudo = 'sudo '
        print('Configuring...')
        subprocess.Popen('./configure {}'.format(configureflags).split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=join(da_folder, file)).communicate()
        print('make....')
        subprocess.Popen('make {}'.format(makeflags).split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=join(da_folder, file)).communicate()
        print('Installing...')
        subprocess.Popen('{}make install {}'.format(if_sudo, makeinstallflags).split(), cwd=join(da_folder, file), stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        print('Cleaning up...')
        subprocess.Popen('make distclean'.split(), cwd=join(da_folder, file), stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        try:
            rmtree(join(da_folder, file))
        except Exception as error:
            self.error_handler(error)
            pass
        print('Done')

    def program_update(self):
        try:
            print('updating..')
            update_path = join(da_folder, 'Flora-Update')
            if not exist_check(update_path):
                os.mkdir(update_path)
            x = 'Flora-Cli'
            print('downloading...')
            urlretrieve('https://github.com/Fuzen-py/Flora-Cli/archive/master.zip', join(update_path, 'master.zip'), reporthook=self.reporthook)
            print('Extracting...')
            self.unzip(join(update_path,'master.zip'), join(update_path))
            if os.name == 'win32':
                cmd = 'py {} install'.format(join(update_path,'Flora-Cli-master','setup.py'))
            else:
                sudo = ''
                if self.yes_or_no('do you need sudo for setup.py?\n'):
                    sudo = 'sudo '
                cmd = '{}python3 setup.py install'.format(sudo)
            print('Executing "{}"...'.format(cmd))
            subprocess.Popen(cmd.split(), cwd=join(update_path, 'Flora-Cli-master')).communicate()
            print('Update Complete')
        except Exception as e:
            self.error_handler(e)

class Core(Downloading, Debugging, SystemManagement):
    def __init__(self):
        self.core = psutil.Process()
        self.command_dictionary = {'Edit Config': self.edit_config, 'Test Python': self.test_python,
                                   'Update PIP Dependencies': self.pip_updater, 'network speed test': self.speed_test,
                                   'custom command': self.scripts_handler, 'kill pid': self.process_killer,
                                   'bash': self.run_bash_commands, 'update': self.program_update,
                                   'task manager': self.task_manager, 'android adb installer': self.get_android_adb,
                                   'aria2 installer': self.get_aria2, 'Edit Hosts': self.host_file_editor}

    def command_handler(self, command):
        if command:
            if command != 'Exit':
                try:
                    self.command_dictionary[command]()
                except Exception as error:
                    the_error = '\n'.join(traceback.format_exception(type(error), error, error.__traceback__))
                    print(the_error)
                    print('Command Failed')
                input('press Enter to continue')
                if len(running_pid['list']) > 0:
                    print('running PID:', running_pid['list'])
                self.main_menu()
            else:
                self.exiter()
        else:
            self.main_menu()

    def edit_config(self):
        print('Edit ', join(da_folder, 'values.json'))


    def scripts_handler(self):
        if not exist_check(join(da_folder, 'scripts')):
            os.mkdir(join(da_folder, 'scripts'))
        print('All custom scripts go in', join(da_folder, 'scripts'))
        while True:
            msg = 'Please chose an option\nDone to finish\nreload to reload'
            scripts = os.listdir(join(da_folder, 'scripts'))
            counter = 0
            for script in scripts:
                if script.endswith('.bat') or script.endswith('.sh') or script.endswith('.exe'):
                    if sys.platform != 'win32' and script.endswith('.exe'):
                        scripts.remove(script)
                        return
                    if sys.platform != 'win32' and script.endswith('.bat'):
                        scripts.remove(script)
                        return
                    if sys.platform == 'win32' and script.endswith('.sh'):
                        scripts.remove(script)
                        return
                else:
                    scripts.remove(script)
                if script in scripts:
                    msg += '\n{}. {}'.format(counter, script)
                    counter += 1
            del counter
            try:
                print(msg)
                inc = input('>>> ')
                if inc.lower() == 'done':
                    return
                if inc.lower() != 'reload':
                    script = scripts[int(inc)]
                    if script.endswith('.sh'):
                        c = subprocess.Popen(['sh', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=join(da_folder, 'scripts'))
                    if script.endswith('.bat') or script.endswith('.exe'):
                        c = subprocess.Popen([script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=join(da_folder, 'scripts'))
                    print('\aExecuting...')

                    print(c.stdout.read().decode('utf-8'))
                    del c
            except Exception as error:
                self.error_handler(error, bypass=True)
                print('Failed')
                del script
                del scripts
                del msg

    def main_menu(self):
        print('Please Select an option')
        for command in list_of_commands:
            msg = '{0}. {1}'.format(list_of_commands.index(command), command)
            print(msg)
        try:
            x = input('Option:')
            if not x.isdigit():
                command = list_of_commands.index(x)
            else:
                command = list_of_commands[int(x)]
        except Exception as e:
            self.error_handler(e)
            command = None
        if command is not None:
            log.info('Command "{}" selected'.format(command))
        self.command_handler(command)

    def main(self):
        val = self.get_values()
        try:
            # print(sys.argv)
            error = 'Not Given'
            move_forward = True
            if '-UP' in sys.argv or '--update-pip' in sys.argv:
                self.pip_updater()
                quit('PIP Update complete')
            if '-U' in sys.argv or '--update' in sys.argv:
                Core().program_update()
                quit('Update complete')
            if '-d' in sys.argv or '--debug' in sys.argv:
                options['debug'] = True
                StreamHandler(sys.stdout).push_application()
            if '--refresh' in sys.argv:
                options['First Start'] = True
            if '--config' in sys.argv:
                options['edit config'] = True
            Core().get_values(options['First Start'])
            if '-ADB' in sys.argv:
                self.get_android_adb()
                quit('Exiting...')
            elif '-Aria2' in sys.argv:
                self.get_aria2()
                quit('Exiting...')
            elif '--speedtest' in sys.argv:
                self.speed_test()
                quit('Exiting...')
            if '--help' in sys.argv:
                move_forward = False
                help_message = ("Flora Command Line Utility\n"
                                "--debug      || prints out errors when they occur\n"
                                "--config     || edit config [DISABLED]\n"
                                "--refresh    || resets configuration (No idea if this works or not to be changed)\n"
                                "--update     || updates script\n"
                                "--update-pip || updates pip\n"
                                "--Aria2      || Installs Aria2\n"
                                "--speedtest  || Performs a network speedtest\n"
                                "--help       || Shows this message")
                print(help_message)
            if move_forward:
                del move_forward
                del error
                print('Hello', val['name'])
                log_folder = join(da_folder,'logs')
                if exist_check(log_folder):
                    if not os.path.isdir(log_folder):
                        os.remove(log_folder)
                        os.mkdir(log_folder)
                else:
                    os.mkdir(log_folder)
                log_path = join(log_folder, 'flora.log')
                del log_folder
                log_handler = FileHandler(log_path)
                log_handler.push_application()
                self.main_menu()
            exit(0)
        except Exception as error:
            self.error_handler(error)
            self.exiter()
if __name__ == '__main__':
    Core().main()
