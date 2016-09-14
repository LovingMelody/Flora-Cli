#!/usr/bin/env python3
# Git Repo https://github.com/Fuzen-py/Flora-Cli
import inspect
import json
import platform
import re
import subprocess
import sys
import tarfile
import time
import traceback
import urllib
import zipfile
from os import mkdir, listdir, remove, name as os_name, execv, rename
from os.path import join, exists, expanduser, isdir
from shutil import rmtree
from urllib.request import urlretrieve

import psutil
from logbook import Logger, FileHandler, StreamHandler


class Config:
    """
    Configuration Object

    :param self.__dict__: returns Configuration dict
    """

    def __init__(self, path):
        self.path = join(path, 'config.json')
        config = {}
        if not exists(path):
            mkdir(path)
        if exists(self.path):
            try:
                with open(self.path) as f:
                    config.update(json.load(f))
            except json.decoder.JSONDecodeError:
                remove(self.path)
        else:
            print('I\'m not responsible for damages caused by this software')
            assert Flora.yes_or_no('Would you like to continue?')

        if not isinstance(config.get('debug'), bool):
            config['debug'] = False
        if not isinstance(config.get('First Start'), bool):
            config['First Start'] = False
        if not isinstance(config.get('edit config'), bool):
            config['edit config'] = False

        config.setdefault(
            'sudo', config.get('sudo'
                               ) or 'sudo ' if sys.platform != 'win32' else 'runas.exe /savecred /user:{} '.format(
                input('Administrator user name\n>>>')))
        print(config.get('Name'))
        if not isinstance(config.get('Name'), str):
            print('Hi, What should I call you?')
            config['Name'] = input('>>> ')

        self.__config = config
        self.get = self.__config.get
        self.pop = self.__config.pop
        self.save()

    @property
    def __dict__(self) -> dict:
        return self.__config

    def __del__(self):
        self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.__config, f, indent=True, sort_keys=True)

    def update(self, *kv: dict, **kwargs):
        self.__config.update(**kwargs)
        for adding in kv:
            assert isinstance(adding, dict)
            self.__config.update(adding)

    def refresh(self):
        if exists(self.path):
            with open(self.path) as f:
                self.update(json.load(f))

    def rm(self, *key):
        for k in key:
            try:
                self.pop(k)
            except KeyError:
                continue

    def mget(self, *key) -> list:
        response = []
        for k in key:
            response.append(self.get(k))
        return response

    def mpop(self, *key):
        response = []
        for k in key:
            try:
                response.append(self.pop(k))
            except KeyError:
                response.append(None)
        return response


class Flora:
    def __init__(self, log=None):
        """"Flora Cli Creation"""
        self.log = log or Logger('Flora-Cli Log')
        print('Use at your own risk, I am not responsible for anything caused by this program!\n',
              'If an problem arises please create submit an issue at https://github.com/Fuzen-py/Flora-Cli/issues')
        self.path = join(expanduser("~"), '.Flora_Command-Line')
        self.config = None
        self.__get_config()
        self.running_pid = []
        self.core = psutil.Process()
        self.command_dictionary = {'Edit Config': self.edit_config, 'Test Python': self.test_python,
                                   'Update PIP Dependencies': self.pip_updater, 'network speed test': self.speed_test,
                                   'custom command': self.scripts_handler,
                                   'bash': self.run_bash_commands, 'update': self.program_update,
                                   'task manager': self.task_manager, 'android adb installer': self.get_android_adb,
                                   'aria2 installer': self.get_aria2, 'Edit Hosts': self.host_file_editor,
                                   'Exit': sys.exit}

    def __get_config(self):
        self.config = Config(self.path)
        return self.config.__dict__

    # UTILITIES
    @staticmethod
    def reporthook(block_number, block_size, total_size):
        read_so_far = block_number * block_size
        if total_size > 0:
            percent = read_so_far * 1e2 / total_size
            s = "\r%5.1f%% %*d / %d" % (
                percent, len(str(total_size)), read_so_far, total_size)
            sys.stderr.write(s)
            if read_so_far >= total_size:  # near the end
                sys.stderr.write("\n")
        else:  # total size is unknown
            sys.stderr.write("read %d\n" % (read_so_far,))

    def error_handler(self, error, bypass: bool = False):
        if inspect.istraceback(error):
            error = '\n'.join(traceback.format_exception(type(error), error, error.__traceback__))
        self.log.error(error)
        if self.config.get('debug') is not True or not bypass:
            return
        print(error)

    def unzip(self, source_filename: str, path: str, remove_zip: bool = True):
        try:
            with zipfile.ZipFile(source_filename) as zf:
                if not exists(path):
                    mkdir(path)
                zf.extractall(path=path)
            if remove_zip:
                remove(source_filename)
        except Exception as error:
            self.error_handler(error)

    @staticmethod
    def yes_or_no(question=None):
        while True:
            try:
                if question:
                    prompt = question + ' Y/N\n>>> '
                else:
                    prompt = 'Yes or No\n>>> '
                x = input(prompt).lower()
                if x in ['yes', 'ye', 'y', 'no', 'n']:
                    if x.startswith('y'):
                        return True
                    if x.startswith('n'):
                        return False
            except KeyboardInterrupt:
                return False

    @staticmethod
    def speed_test_formatter(a):
        b = ['', '', '']
        b[0] = a[4].split(':')[-1].strip().strip('\'')
        b[1] = a[6].strip()
        b[2] = a[8].strip()
        share = a[-1]
        a = '\n'.join(b)
        share = share.split('results: ')[-1].strip()
        return a, share

    def speed_test(self):
        share = None
        print('Running Speedtest')
        a = [i.decode('utf-8') for i in
             subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
        try:
            a, share = self.speed_test_formatter(a)
        except Exception as e:
            self.error_handler(e)
            print('required dependency not installed')
            if self.yes_or_no('Would you like for me to install speedtest-cli?'):
                if os_name != 'nt':
                    subprocess.Popen('sudo pip install speedtest-cli -U'.split()).communicate()
                else:
                    subprocess.Popen('pip install speedtest-cli -U'.split()).communicate()
                a = [i.decode('utf-8') for i in
                     subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
                checker = ''.join(a)
                print(checker)
                checker = len(checker.split('speedtest-cli')) == 2
                if checker:
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
                print('Ping:', a)
                print(share)
                if self.yes_or_no('Would you like for me to open this in a browser?'):
                    if os_name == 'nt':
                        subprocess.Popen('start {0}'.format(share))
                    elif os_name == 'posix':
                        subprocess.Popen('open {0}'.format(share))
                    else:
                        subprocess.Popen('xdg-open {0}'.format(share))

    def edit_config(self):
        print('Edit ', join(self.path, 'values.json'))

    # SYSTEM TOOLS
    def pip_updater(self):
        cmd = [sys.executable, ' -m', ' pip', ' install', ' -U ']
        freeze = [sys.executable + ' -m', ' pip', ' freeze', ' --local']
        if os_name != 'win32':
            print('Please Note, this has to be run as root or in a venv')
            if not self.yes_or_no('would you like to continue?'):
                return
        p = subprocess.Popen(freeze, cwd=self.path, stdout=subprocess.PIPE).stdout.read().decode(
            'utf-8', errors='backslashreplace').replace('==', '>=').strip()
        cmd += p.split('\n')
        if os_name != 'nt':
            if self.yes_or_no('Do you need sudo?'):
                cmd.insert(0, self.config.get('sudo') or 'sudo')
        if self.yes_or_no('Do you want to install pre releases?'):
            cmd.append(' --pre ')
        x = subprocess.Popen(cmd, cwd=self.path)
        print('Updating pip please wait...')
        x.communicate()
        print('Done')

    def host_file_editor(self):
        host_dir = join(self.path, 'hosts')
        print('This requires the script to be run as root/admin')
        if not self.yes_or_no('Would you like to continue?'):
            print('Returning to menu..')
            return
        path_to_hosts = str(input('Path to hosts file: '))
        if not exists(host_dir):
            mkdir(host_dir)
        print('Making a host file backup')
        with open(path_to_hosts, 'r') as backup:
            b = backup.read()
            files = listdir(host_dir)
            if 'host.backup' in files:
                x = 1
                while 'host.backup{0}'.format(x) in files:
                    x += 1
                backup_name = 'host.backup{0}'.format(x)
                backup_path = join(host_dir, backup_name)
            else:
                print('Failed to make a backup')
                raise Exception('Host File backup Failed')
            with open(join(backup_path, 'w')) as x:
                x.write(b)
                print('Done:', backup_path)
        host_config = join(self.path, 'host_sources.json')
        if exists(host_config):
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
                f = open(host_config, 'w')
                json.dump(host_sources, f, indent=4)
            else:
                link = host_sources[choice]
            if link:
                print('Downloading host file...')
                # may have to use url retrieve
                urlretrieve(link, join(self.path, 'dl_host'), reporthook=self.reporthook)
                with open(join(self.path, 'dl_host')) as new_host:
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
            print('Invalid option')

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
                    if os_name != 'nt':
                        subprocess.Popen('kill {}'.format(p.pid)).communicate()
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

    # DEVELOP
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
                x = x
                print(subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE).stdout.read())
            except Exception as error:
                self.error_handler(error)

    # Downloads
    def program_update(self):
        try:
            print('updating..')
            if os_name == 'win32':
                subprocess.Popen(
                    'py -m pip install -U git+https://github.com/Fuzen-py/Flora-Cli.git').communicate()
            else:
                sudo = ''
                if self.yes_or_no('do you need sudo for setup.py?\n'):
                    sudo = 'sudo '
                cmd = '{}python3 -m pip install -U git+https://github.com/Fuzen-py/Flora-Cli.git'.format(sudo)
                subprocess.Popen(cmd).communicate()
            print('Update Complete')
            print('Restarting')
            self.config.save()
            execv('flora-cli', sys.argv)
            return
        except Exception as e:
            self.error_handler(e)
            print('Failed to update')

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
        if not self.yes_or_no('Would you like to install aria2 {0}'.format(version)):
            return
        if sys.platform == 'darwin':
            dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-osx-darwin.tar.bz2'
        elif sys.platform == 'linux' or sys.platform == 'linux2':
            dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}.tar.bz2'
        elif sys.platform == 'win32':
            if exists(join(self.path, 'aria2')):
                rmtree(join(self.path, 'aria2'))
            if platform.uname()[-1] == 'x86_64':
                dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-win-64bit-build1.zip'
            else:
                dl = 'https://github.com/aria2/aria2/releases/download/{0}/aria2-{1}-win-32bit-build1.zip'
            dl = dl.format(version, version_num)
            path_to_zip = join(self.path, 'aria2.zip')
            urlretrieve(dl, path_to_zip, reporthook=self.reporthook)
            self.unzip(path_to_zip, self.path)
            name = None
            for names in listdir(self.path):
                if names.startswith('aria2'):
                    name = names
                    break
            if name is None:
                return
            rename(join(self.path, name), join(self.path, 'aria2'))
            return
        else:
            print('Your system isn\'t supported.\nCheck - https://github.com/aria2/aria2/releases/latest to install')
            return
        print('Downloading...')
        dl = dl.format(version, version_num)
        print(dl)
        path_to_tar = join(self.path, 'aria2.tar.bz2')
        urlretrieve(dl, path_to_tar, reporthook=self.reporthook)
        if not tarfile.is_tarfile(path_to_tar):
            print('Something went wrong! File isn\'t a tar')
            if exists(path_to_tar):
                pass
                remove(join(self.path, 'aria2.tar.bz2'))
            return
        print('Extracting..')
        file = tarfile.open(path_to_tar, 'r:bz2')
        file.extractall(self.path)
        file.close()
        remove(path_to_tar)
        for file in listdir(self.path):
            if file.startswith('aria2'):
                file = file
                break
        configure_flags = ''
        make_flags = ''
        make_install_flags = ''
        if self.yes_or_no('[Advanced]Do you wish to input flags?\n'):
            print('press enter if no flags for that option (be sure to input (-- or -)')
            configure_flags = input('Configure Flags\n>>> ')
            make_flags = input('Make Flags\n>>> ')
            make_install_flags = 'Make install Flags\n>>> '
        if_sudo = ''
        if self.yes_or_no('Do you need sudo?\n'):
            if_sudo = 'sudo '
        print('Configuring...')
        subprocess.Popen('./configure {}'.format(configure_flags), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, cwd=join(self.path, file)).communicate()
        print('make....')
        subprocess.Popen('make {}'.format(make_flags), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         cwd=join(self.path, file)).communicate()
        print('Installing...')
        subprocess.Popen('{}make install {}'.format(if_sudo, make_install_flags), cwd=join(self.path, file),
                         stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
        print('Cleaning up...')
        subprocess.Popen('make distclean', cwd=join(self.path, file), stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE).communicate()
        try:
            rmtree(join(self.path, file))
        except Exception as error:
            self.error_handler(error)
            pass
        print('Done')

    def get_android_adb(self):
        if exists(join(self.path, 'adb')):
            rmtree(join(self.path, 'adb'))
        url = 'https://dl.google.com/android/repository/repository-12.xml'
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req)
        resp_data = resp.read()
        latest = re.findall('<sdk:url>platform-tools_r(.*?)</sdk:url>', str(resp_data))
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
                download_link = 'https://dl.google.com/android/repository/' + latest
                print('Downloading...')
                urlretrieve(download_link, join(self.path, 'latest.zip'), self.reporthook)
            if not zipfile.is_zipfile(join(self.path, 'latest.zip')):
                print('Something went wrong\nFile downloaded is not a zip')
                return
            print('Extracting...')
            self.unzip(join(self.path, 'latest.zip'), self.path)
            print('Renaming Folder..')
            rename(join(self.path, 'platform-tools'), join(self.path, 'adb'))
            print('Done')

    def scripts_handler(self):
        if not exists(join(self.path, 'scripts')):
            mkdir(join(self.path, 'scripts'))
        print('All custom scripts go in', join(self.path, 'scripts'))
        while True:
            msg = 'Please chose an option\nDone to finish\nreload to reload'
            scripts = listdir(join(self.path, 'scripts'))
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
            try:
                print(msg)
                inc = input('>>> ')
                if inc.lower() == 'done':
                    return
                if inc.lower() != 'reload':
                    script = scripts[int(inc)]
                    if script.endswith('.sh'):
                        c = subprocess.Popen('sh {}'.format(script), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             cwd=join(self.path, 'scripts'))
                    elif script.endswith('.bat') or script.endswith('.exe'):
                        c = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                             cwd=join(self.path, 'scripts'))
                    else:
                        return
                    print('\aExecuting...')

                    print(c.stdout.read().decode('utf-8'))
            except Exception as error:
                self.error_handler(error, bypass=True)
                print('Failed')

    # MAIN MENU STUFF
    def command_handler(self, command):
        if command:
            try:
                self.command_dictionary[command]()
            except Exception as error:
                self.error_handler(error, bypass=True)
                print('Command Failed')
            input('press Enter to continue')
            if len(self.running_pid) > 0:
                print('running PID:', self.running_pid)
            self.main_menu()
        self.main_menu()

    def main_menu(self):
        print('Please Select an option')
        list_of_commands = sorted(list(self.command_dictionary.keys()))
        list_of_commands.remove('Exit')
        list_of_commands.append('Exit')
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
            self.log.info('Command "{}" selected'.format(command))
        self.command_handler(command)

    def main(self):
        try:
            move_forward = True
            if '-UP' in sys.argv or '--update-pip' in sys.argv:
                self.pip_updater()
                sys.exit('pip Update complete')
            if '-U' in sys.argv or '--update' in sys.argv:
                self.program_update()
                sys.exit('Update complete')
            if '-d' in sys.argv or '--debug' in sys.argv:
                self.config.update(debug=True)
                StreamHandler(sys.stdout).push_application()
            if '--refresh' in sys.argv:
                self.config.update({'First Start': True})
                sys.argv.pop('--refresh')
                self.config.__config = {}
                self.config.save()
                self.config = Config(self.path)
            if '-ADB' in sys.argv:
                self.get_android_adb()
                sys.exit('Exiting...')
            elif '-Aria2' in sys.argv:
                self.get_aria2()
                sys.exit('Exiting...')
            elif '--speedtest' in sys.argv:
                self.speed_test()
                sys.exit('Exiting...')
            if '--help' in sys.argv:
                help_message = ("Flora Command Line Utility\n"
                                "--debug      || prints out errors when they occur\n"
                                "--config     || edit config [DISABLED]\n"
                                "--refresh    || resets configuration "
                                "(No idea if this works or not. to be changed)\n"
                                "--update     || updates script\n"
                                "--update-pip || updates pip\n"
                                "--Aria2      || Installs Aria2\n"
                                "--speedtest  || Performs a network speedtest\n"
                                "--help       || Shows this message")
                print(help_message)
                return
            if move_forward:
                print('Hello', self.config.get('Name'))
                log_folder = join(self.path, 'logs')
                if exists(log_folder):
                    if not isdir(log_folder):
                        remove(log_folder)
                        mkdir(log_folder)
                else:
                    mkdir(log_folder)
                log_path = join(log_folder, 'flora.log')
                log_handler = FileHandler(log_path)
                log_handler.push_application()
                self.main_menu()
            exit(0)
        except Exception as error:
            self.error_handler(error)
            return


def main():
    Flora().main()


if __name__ == '__main__':
    main()
