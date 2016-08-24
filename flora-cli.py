#!/usr/bin/env python3
# Git Repo https://github.com/Fuzen-py/Flora-Cli
import json
import os
import sys
import platform

try:
    # noinspection PyUnresolvedReferences
    import psutil
except ImportError:
    print('Psutil is not installed')
    sys.exit(-1)
import re
import time
import traceback
import urllib
import zipfile
import tarfile
from shutil import rmtree
from urllib.request import urlretrieve
import subprocess

try:
    # noinspection PyUnresolvedReferences
    from logbook import Logger, FileHandler, StreamHandler
except ImportError:
    print('Logbook is not installed')
    sys.exit(-1)

log = Logger('Flora-Cli Log')

print('Use at your own risk, I am not responsible for anything caused by this program!')
print('If an problem arises please create submit an issue at https://github.com/Fuzen-py/Flora-Cli/issues')
home = os.path.expanduser("~")
options = {'debug': False, 'First Start': False, 'edit config': False}
da_folder = os.path.join(home, '.Flora_Command-Line')
running_pid = {'list': []}
join = os.path.join
exist_check = os.path.exists
sudo_command = 'sudo '
if os.name == 'nt':
    sudo_command = 'runas.exe /savecred /user:{} '.format(input('Administrator user name\n>>>'))


def exiter():
    print('Exiting...')
    process_killer()
    exit()


def reporthook(block_number, block_size, total_size):
    readsofar = block_number * block_size
    if total_size > 0:
        percent = readsofar * 1e2 / total_size
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(total_size)), readsofar, total_size)
        sys.stderr.write(s)
        if readsofar >= total_size:  # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


def unzip(source_filename: str, path: str, remove_zip: bool = True):
    try:
        with zipfile.ZipFile(source_filename) as zf:
            if not exist_check(path):
                os.mkdir(path)
            zf.extractall(path=path)
        if remove_zip:
            os.remove(source_filename)
    except Exception as error:
        error_handler(error)


def process_killer(p=None):
    if p is None:
        for p in running_pid['list']:
            p.terminate()
            try:
                p.kill()
            except Exception as error:
                error_handler(error)
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


def get_values(fresh=False):
    val = {}
    path_to_config = da_folder
    if not exist_check(path_to_config):
        print('I am not responsible for anything that goes wrong while using this')
        if not yes_or_no('Would you like to continue?'):
            return
        os.mkdir(path_to_config)
        with open(join(path_to_config, 'values.json'), mode='w', encoding='utf-8', errors='backslashreplace') as f:
            json.dump(obj={}, fp=f, sort_keys=True, indent=4)
        fresh = True
    if fresh or not exist_check(join(path_to_config, 'values.json')):
        val['name'] = str(input('What Should I call you?\nName: ')).strip()
        print('Hello', val['name'])
        prompt = 'Do You Have any libraries that cannot be updated through pip -U {name} [like a git repo]\n'
        if yes_or_no(prompt):
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


def yes_or_no(question=None):
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
            error_handler(error)


def error_handler(error, bypass: bool = False):
    log.error('\n'.join(traceback.format_exception(type(error), error, error.__traceback__)))
    if options['debug'] is not True or not bypass:
        return


def speed_test_formatter(a):
    b = ['', '', '']
    b[0] = a[4].split(':')[-1].strip().strip('\'')
    b[1] = a[6].strip()
    b[2] = a[8].strip()
    share = a[-1]
    a = '\n'.join(b)
    share = share.split('results: ')[-1].strip()
    return a, share


def pip_updater():
    print('Please Note, this has to be run as root or in a venv')
    if not yes_or_no('would you like to continue?'):
        return
    p = subprocess.Popen('pip freeze --local'.split(), cwd=da_folder, stdout=subprocess.PIPE).stdout.read().decode(
        'utf-8', errors='backslashreplace').replace('\n', ' ').replace('==', '>=').strip()
    if os.name != 'nt':
        if not yes_or_no('Do you need sudo?'):
            pip_update_command = 'pip install -U {}'.format(p)
        else:
            pip_update_command = 'sudo -H pip install -U {}'.format(p)
    else:
        pip_update_command = 'pip install -U {}'.format(p)
    if yes_or_no('Do you want to install pre releases?'):
        pip_update_command += ' --pre '
    x = subprocess.Popen(pip_update_command.split(), cwd=da_folder)
    print('Updating pip please wait...')
    x.communicate()
    print('Done')


def speed_test():
    share = None
    print('Running Speedtest')
    a = [i.decode('utf-8') for i in
         subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
    try:
        a, share = speed_test_formatter(a)
    except Exception as e:
        error_handler(e)
        print('required dependency not installed')
        if yes_or_no('Would you like for me to install speedtest-cli?'):
            if os.name != 'nt':
                subprocess.Popen('sudo pip install speedtest-cli -U'.split()).communicate()
            else:
                subprocess.Popen('pip install speedtest-cli -U'.split()).communicate()
            a = [i.decode('utf-8') for i in
                 subprocess.Popen('speedtest-cli --share'.split(), stdout=subprocess.PIPE).stdout.readlines()]
            cheker = ''.join(a)
            print(cheker)
            cheker = len(cheker.split('speedtest-cli')) == 2
            if cheker:
                a = 'Failed To Install speedtest-cli\n Lacking root permissions?'
            else:
                try:
                    a, share = speed_test_formatter(a)
                except Exception as e:
                    error_handler(e)
                    share = None
        else:
            a = 'Missing Dependency speedtest-cli'
    finally:
        if share:
            print(a)
            print(share)
            if yes_or_no('Would you like for me to open this in a browser?'):
                if os.name == 'nt':
                    subprocess.Popen('start {0}'.format(share).split())
                elif os.name == 'posix':
                    subprocess.Popen('open {0}'.format(share).split())
                else:
                    subprocess.Popen('xdg-open {0}'.format(share).split())


def host_file_editor():
    print('This requires the script to be run as root/admin')
    if not yes_or_no('Would you like to continue?'):
        print('Returning to menu..')
        return
    path_to_hosts = str(input('Path to hosts file: '))
    if not exist_check(join(da_folder, 'hosts')):
        os.mkdir(join(da_folder, 'hosts'))
    print('Making a host file backup')
    with open(path_to_hosts, 'r') as backup:
        b = backup.read()
        files = os.listdir(join(da_folder, 'hosts'))
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
            urlretrieve(link, da_folder + 'dl_host', reporthook=reporthook)
            with open(join(da_folder, 'dl_host')) as new_host:
                if yes_or_no('Would you like to append to current hosts?\n'):
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
        error_handler(e)
        print('Invalid option')


class SystemManagement:
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
                error_handler(e)
        print(display)
        if loop or yes_or_no('Would You like me to terminate a process?\n'):
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
                        error_handler(e)
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
                    error_handler(e)
                    print('Sorry, I cannot terminate that process')
                    time.sleep(2)
            self.task_manager(True)


def test_python():
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
            error_handler(e, True)


def run_bash_commands():
    print('Entering Bash Mode....')
    while True:
        try:
            x = input('Command >>').strip()
            if x.lower() in ['exit', 'done', 'quit']:
                return
            x = x.split()
            print(subprocess.Popen(x, stderr=subprocess.PIPE, stdout=subprocess.PIPE).stdout.read())
        except Exception as error:
            error_handler(error)


def program_update():
    try:
        print('updating..')
        if os.name == 'win32':
            subprocess.Popen('py -m pip install -U git+https://github.com/Fuzen-py/Flora-Cli.git'.split()).communicate()
        else:
            sudo = ''
            if yes_or_no('do you need sudo for setup.py?\n'):
                sudo = 'sudo '
            cmd = '{}python3 -m pip install -U git+https://github.com/Fuzen-py/Flora-Cli.git'.format(sudo)
        subprocess.Popen(cmd.split(), cwd=join(update_path, 'Flora-Cli-master')).communicate()
        print('Update Complete')
    except Exception as e:
        error_handler(e)


def get_aria2():
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
    if not yes_or_no('Would you like to install aria2 {0}\n'.format(version)):
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
        urlretrieve(dl, path_to_zip, reporthook=reporthook)
        unzip(path_to_zip, da_folder)
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
    print('Downloading...')
    dl = dl.format(version, version_num)
    print(dl)
    path_to_tar = join(da_folder, 'aria2.tar.bz2')
    urlretrieve(dl, path_to_tar, reporthook=reporthook)
    if not tarfile.is_tarfile(path_to_tar):
        print('Something went wrong! File isn\'t a tar')
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
    configure_flags = ''
    make_flags = ''
    make_install_flags = ''
    if yes_or_no('[Advanced]Do you wish to input flags?\n'):
        print('press enter if no flags for that option (be sure to input (-- or -)')
        configure_flags = input('Configure Flags\n>>> ')
        make_flags = input('Make Flags\n>>> ')
        make_install_flags = 'Make install Flags\n>>> '
    if_sudo = ''
    if yes_or_no('Do you need sudo?\n'):
        if_sudo = 'sudo '
    print('Configuring...')
    subprocess.Popen('./configure {}'.format(configure_flags).split(), stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE, cwd=join(da_folder, file)).communicate()
    print('make....')
    subprocess.Popen('make {}'.format(make_flags).split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                     cwd=join(da_folder, file)).communicate()
    print('Installing...')
    subprocess.Popen('{}make install {}'.format(if_sudo, make_install_flags).split(), cwd=join(da_folder, file),
                     stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    print('Cleaning up...')
    subprocess.Popen('make distclean'.split(), cwd=join(da_folder, file), stderr=subprocess.PIPE,
                     stdout=subprocess.PIPE).communicate()
    try:
        rmtree(join(da_folder, file))
    except Exception as error:
        error_handler(error)
        pass
    print('Done')


def get_android_adb():
    if exist_check(join(da_folder, 'adb')):
        rmtree(join(da_folder, 'adb'))
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
            urlretrieve(download_link, join(da_folder, 'latest.zip'), reporthook)
        if not zipfile.is_zipfile(join(da_folder, 'latest.zip')):
            print('Something went wrong\nFile downloaded is not a zip')
            return
        print('Extracting...')
        unzip(join(da_folder, 'latest.zip'), da_folder)
        print('Renaming Folder..')
        os.rename(join(da_folder, 'platform-tools'), join(da_folder, 'adb'))
        print('Done')


def edit_config():
    print('Edit ', join(da_folder, 'values.json'))


def scripts_handler():
    script = None
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
                    c = subprocess.Popen(['sh', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         cwd=join(da_folder, 'scripts'))
                if script.endswith('.bat') or script.endswith('.exe'):
                    c = subprocess.Popen([script], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         cwd=join(da_folder, 'scripts'))
                print('\aExecuting...')

                print(c.stdout.read().decode('utf-8'))
                del c
        except Exception as error:
            error_handler(error, bypass=True)
            print('Failed')
            del script, scripts, msg


class Core(SystemManagement):
    def __init__(self):
        self.core = psutil.Process()
        self.command_dictionary = {'Edit Config': edit_config, 'Test Python': test_python,
                                   'Update PIP Dependencies': pip_updater, 'network speed test': speed_test,
                                   'custom command': scripts_handler, 'kill pid': process_killer,
                                   'bash': run_bash_commands, 'update': program_update,
                                   'task manager': self.task_manager, 'android adb installer': get_android_adb,
                                   'aria2 installer': get_aria2, 'Edit Hosts': host_file_editor,
                                   'Exit': exiter}

    def command_handler(self, command):
        if command:
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
            error_handler(e)
            command = None
        if command is not None:
            log.info('Command "{}" selected'.format(command))
        self.command_handler(command)

    def main(self):
        val = get_values()
        try:
            # print(sys.argv)
            error = 'Not Given'
            move_forward = True
            if '-UP' in sys.argv or '--update-pip' in sys.argv:
                pip_updater()
                sys.exit('pip Update complete')
            if '-U' in sys.argv or '--update' in sys.argv:
                program_update()
                sys.exit('Update complete')
            if '-d' in sys.argv or '--debug' in sys.argv:
                options['debug'] = True
                StreamHandler(sys.stdout).push_application()
            if '--refresh' in sys.argv:
                options['First Start'] = True
            if '--config' in sys.argv:
                options['edit config'] = True
            get_values(options['First Start'])
            if '-ADB' in sys.argv:
                get_android_adb()
                sys.exit('Exiting...')
            elif '-Aria2' in sys.argv:
                get_aria2()
                sys.exit('Exiting...')
            elif '--speedtest' in sys.argv:
                speed_test()
                sys.exit('Exiting...')
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
                log_folder = join(da_folder, 'logs')
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
            error_handler(error)
            exiter()


if __name__ == '__main__':
    Core().main()
