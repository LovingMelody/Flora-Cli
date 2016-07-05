#!/usr/bin/python3
import re
import os
import time
import math
import urllib
import psutil
from subprocess import PIPE
import subprocess
import traceback
import sys
import zipfile
from urllib.request import urlretrieve
from shutil import rmtree
core = psutil.Process()
home = os.path.expanduser("~")
options = {'debug': False, 'First Start': False, 'edit config': False}
list_of_commands = ['Edit Config', 'Test Python', 'Update PIP Dependencies', 'network speed test', 'start bot',
                    'kill pid', 'bash', 'update', 'task manager', 'android adb installer']
da_folder = '{0}/Flora_Command-Line/'.format(home)
if os.name == 'nt':
    da_folder = da_folder.replace('/','\\')
list_of_commands += ['Exit']
running_pid = {'list': []}
val = {}


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
        except Exception:
            pass


def get_values(fresh=False):
    path_to_config = '{0}/Flora_Command-Line/'.format(home)
    if not os.path.exists(path_to_config):
        os.mkdir(path_to_config)
        f = open('{0}/values.txt'.format(path_to_config), 'w')
        f.close()
        fresh = True
    if fresh:
        val['name'] = str(input('What Should I call you?\nName: ')).strip()
        text = '{0}\n'.format(val['name'])
        prompt = 'Do You Have any libraries that cannot be updated through pip -U {name} [like a git repo]\nYes/No: '
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
        text += '{0}\n'.format(val['pip list'])
        f = open('{0}/values.txt'.format(path_to_config), 'w')
        f.write(text)
        f.close()
    else:
        with open('{0}/values.txt'.format(path_to_config), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('[') and line.endswith(']'):
                    line.strip('[').strip(']')
                    line.split('\', \'')
                    for entry in line:
                        line[line.index(entry)] = entry.strip('\'').strip()
                    val['pip list'] = line
                elif lines.index(line) == 0:
                    val['name'] = line.strip()


def command_handler(command):
    if command:
        if command != 'Exit':
            try:
                command_dictionary[command]()
            except:
                print('Command Failed')
            input('press Enter to continue')
            if len(running_pid['list']) > 0:
                print('running PID:', running_pid['list'])
            main()
        else:
            exiter()
    else:
        main()


def edit_config():
    pass  # "Add something here


def bot_starter():
    process = None
    path_to_bot = '{0}/Flora_Command-Line/'.format(home)
    print(path_to_bot)
    print(os.listdir(path_to_bot))
    try:
        with open('{0}bot.txt'.format(path_to_bot), 'r') as f:
            x = f.readlines()
            name, bot_command = x
            f.close()
            print('Would you like to start', name, 'with the command:\n', bot_command)
            if not yes_or_no():
                if not yes_or_no('Would you like to start the bot at all?'):
                    return
                while True:
                    name = input('Bots Name\n>>> ')
                    bot_command = input('Bot Start Command\n>>> ')
                    if yes_or_no('Would you like to start {} with the command:\n{1}'.format(name, bot_command)):
                        f = open('{0}/bot.txt'.format(path_to_bot), 'w')
                        text = '{0}\n{1}'.format(name, bot_command)
                        f.write(text)
                        f.close()
                        break

            print('Starting Bot...')
            try:
                process = psutil.Popen(bot_command.split(), stdout=PIPE)
            except Exception as error:
                the_error = '\n'.join(traceback.format_exception(type(error), error, error.__traceback__))
                print(the_error)

    except:
        try:
            print(os.listdir(path_to_bot))
            f = open('{0}bot.txt'.format(path_to_bot), 'w')
            name = input('Bots Name: ')
            print('Please input command needed to start bot from root directory')
            command_need = input('Command: ')
            text = '{0}\n{1}'.format(name, command_need)
            f.write(text)
            f.close()
            print('Starting Bot')
            process = psutil.Popen(command_need.split(), stdout=PIPE)
            # process = psutil.Popen(['python3.5', '/home/fuzen/Flora/flora.py'], stdout=PIPE)
        except Exception as e:
            print(e)
    if process:
        print('Bot Started on ID:', process.pid)
        running_pid['list'] += [process]
    else:
        print('Could not start bot')


def on_terminate(proc):
    print("process {} terminated with exit code {}".format(proc, proc.returncode))


def process_killer():
    for p in running_pid['list']:
        p.terminate()
        try:
            p.kill()
        except:
            print('failed to kill {0}'.format(p))


def speed_test():
    share = None
    print('Running Speedtest')
    a = os.popen('speedtest-cli --share').readlines()
    try:
        a, share = speed_test_formatter(a)
    except Exception as e:
        print(e)
        print('required dependency not installed')
        if yes_or_no('Would you like for me to install speedtest-cli?'):
            if os.name != 'nt':
                a = os.popen('sudo pip install speedtest-cli -U')
            else:
                a = os.popen('pip install speedtest-cli -U')
            a = os.popen('speedtest-cli --share')
            cheker = ''.join(a)
            print(cheker)
            cheker = len(cheker.split('speedtest-cli')) == 2
            if cheker:
                a = 'Failed To Install speedtest-cli\n Lacking root permissions?'
            else:
                try:
                    a,share = speed_test_formatter(a)
                except:
                    share = None
        else:
            a = 'Missing Dependency speedtest-cli'
    finally:
        if share:
            if yes_or_no('Would you like for me to open this in a browser?'):
                if os.name == 'nt':
                    os.popen('start {0}'.format(share))
                elif os.name == 'posix':
                    os.popen('open {0}'.format(share))
                else:
                    os.popen('xdg-open {0}'.format(share))
            else:
                print(a)
                print(share)


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
    x = os.popen('pip freeze --local >> {0}its_pip'.format(da_folder))
    len(x.readlines())
    if os.name != 'nt':
        if not yes_or_no('Do you need sudo?'):
            pip_update_command = 'pip install -r {0}its_pip -U '.format(da_folder)
        else:
            pip_update_command = 'sudo pip install -r {0}its_pip -U '.format(da_folder)
    else:
        pip_update_command = 'pip install -r {0}its_pip -U '.format(da_folder)
    if yes_or_no('Do you want to install pre releases?'):
        pip_update_command += ' --pre '
    x = os.popen(pip_update_command)
    print('Updating pip please wait...')
    len(x.readlines())
    os.remove('{0}its_pip'.format(da_folder))
    print('Done')



def run_bash_commands():
    while True:
        print('Entering Bash Mode....')
        x = input('Command >>')
        if x.lower() in ['exit', 'done', 'quit']:
            return
        x = os.popen(x)
        print(x.read())


def test_python():
    print('enter \n for multi-lined code')
    while True:
        try:
            x = str(input('>>> ')).strip().replace('\\n','\n')
            while x.endswith('\n'):
                x += str(input('>>> ')).strip().replace('\\n', '\n')
            if not x.startswith('exit'):
                exec(x, globals(), locals())
            else:
                break
        except Exception as e:
            print(e)


def exiter():
    print('Exiting...')
    process_killer()
    exit('Exited')


def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = "\r%5.1f%% %*d / %d" % (
            percent, len(str(totalsize)), readsofar, totalsize)
        sys.stderr.write(s)
        if readsofar >= totalsize: # near the end
            sys.stderr.write("\n")
    else:  # total size is unknown
        sys.stderr.write("read %d\n" % (readsofar,))


def program_update():
    try:
        if os.name != 'posix':
            print('Only working on linux systems')
            return
        x = [os.getcwd(), 0]
        while os.path.exists('temp{0}'.format(x[1])):
            x[1] += 1
        temp_path = 'temp{}'.format(x[1])
        print('Downloading...')
        urlretrieve('https://github.com/NekoKitty/Flora-Cli/archive/master.zip', 'master.zip', reporthook)
        print('Extracting...')
        unzip('master.zip', temp_path)
        print('installing....')
        command = 'cd {0}/Flora-Cli-master/ && sudo sh setup.sh'.format(temp_path)
        len(os.popen(command).readlines())
        print('Removing junk')
        rmtree(temp_path)
        print('Done')
    except Exception as e:
        print(e)


def unzip(source_filename: str, path: str, remove_zip: bool=True):
    with zipfile.ZipFile(source_filename) as zf:
        if not os.path.exists(path):
            os.mkdir(path)
        zf.extractall(path=path)
    if remove_zip:
        os.remove(source_filename)


def task_manager(loop=False):
    processes = psutil.pids()
    display = '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format('PID', 'Name', 'CPU%', 'MEMORY%', 'Current Working Directory')
    for p in processes:
        try:
            p = psutil.Process(p)
            display += '{0:<10} | {1:>40} | {2:>8} | {3:<22}| {4:>60} |\n'.format(p.pid, p.name(), str(p.cpu_percent()) + '%', str(p.memory_percent()) + '%', p.cwd())
        except:
            pass
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
                except Exception:
                    pass
            p = 'list'
        if p.lower() != 'list':
            try:
                p = psutil.Process(int(p))
                if os.name != 'nt':
                    os.popen('kill {0}'.format(p.pid))
                else:
                    p.kill()
                    p.terminate()
                psutil.pids()
                p = int(psutil.pid)
                if p in psutil.pids():
                    print('Failed')
                else:
                    print('Exited')
            except:
                print('Sorry, I cannot terminate that process')
                time.sleep(2)
        task_manager(True)


def get_android_adb():
    if os.path.exists('{0}adb'.format(da_folder)):
        rmtree('{0}/adb'.format(da_folder))
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
            urlretrieve(downloadlink, da_folder+'latest.zip',reporthook)
        if not zipfile.is_zipfile('{0}/latest.zip'.format(da_folder)):
            print('Something went wrong\nFile downloaded is not a zip')
            return
        print('Extracting...')
        unzip('{0}/latest.zip'.format(da_folder), '{0}'.format(da_folder))
        print('Renaming Folder..')
        os.rename('{0}/platform-tools'.format(da_folder), '{0}/adb'.format(da_folder))
        print('Done')


def main():
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
    except:
        command = None
    command_handler(command)
command_dictionary = {'Edit Config': edit_config, 'Test Python': test_python, 'Update PIP Dependencies': pip_updater,
                      'network speed test': speed_test, 'start bot': bot_starter, 'kill pid': process_killer,
                      'bash': run_bash_commands, 'update': program_update, 'task manager': task_manager,
                      'android adb installer': get_android_adb}
if __name__ == '__main__':
    try:
        # print(sys.argv)
        error = 'Not Given'
        move_forward = True
        if '-d' in sys.argv or '--debug' in sys.argv:
            options['debug'] = True
        if '--refresh' in sys.argv:
            options['First Start'] = True
        if '--config' in sys.argv:
            options['edit config'] = True
        get_values(options['First Start'])
        if '--help' in sys.argv:
            move_forward = False
            print('Flora Command Line Utility\n--debug || prints out erros\n--config || edit config\n--refresh || resets configuration\n--help || outputs this screen')
        if move_forward:
            print('Hello', val['name'])
            main()
        else:
            print('Something went wrong\nError:', error)
    except:
        exiter()
