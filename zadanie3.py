# Author: Roland Körtvely

import re

fs = {}

user = 'user'
prompt = '% '
path = '/'


def require_arguments(args, count):
    if len(args) != count:
        raise Exception('expected {} arguments'.format(count))


def file_factory():
    global user
    return {
        'type': 'file',
        'owner': user,
        'perm': 'rwx'
    }


def directory_factory():
    global user
    return {
        'type': 'dir',
        'owner': user,
        'perm': 'rwx',
        'child': {}
    }


def filesystem_factory():
    global user
    return {
        '/': {
            'type': 'dir',
            'perm': 'rwx',
            'owner': 'user',
            'child': {}
        }
    }


def is_dir(record):
    return record['type'] == 'dir'


def is_file(record):
    return record['type'] == 'file'


def can(record, perm):
    return perm in record['perm']


def mine(record):
    return user == record['owner']


def pwd(args):
    require_arguments(args, 0)
    print(path)


def __current():
    pointer = fs['/']

    for child in path.split('/'):
        if len(child) == 0:
            continue
        pointer = pointer['child'][child]

    return pointer


def __parent():
    _path = re.sub(r'(/[\w]+)$', '', path)
    if not _path:
        _path = '/'
    return _path


def exists(name):
    return name in __current()['child']


def get(name):
    return __current()['child'][name]


def create(name, template):
    __current()['child'][name] = template


def run_quit(args):
    global prompt, user, path

    require_arguments(args, 0)

    if user == 'user':
        print('Bye')
        quit()

    user = 'user'
    prompt = '# '
    path = '/'


def run_sudo(args):
    global prompt, user

    if len(args) > 0:
        user = args[0]
        prompt = '% '
    else:
        user = 'root'
        prompt = '# '


def run_ls(args):
    if len(args) > 1:
        print('expected one argument')
        return

    pointer = __current()

    if len(args) == 1:
        if args[0] == '/':
            pointer = fs['/']
        else:
            name = args[0]
            if not exists(name):
                raise Exception('directory not found')
            pointer = get(name)
            if not is_dir(pointer):
                raise Exception('expected directory')

    if len(pointer['child']) == 0:
        print('no files')
    for f in pointer['child']:
        print('{}\t{}\t{}'.format(f, pointer['child'][f]['owner'], pointer['child'][f]['perm']))


def run_touch(args):
    require_arguments(args, 1)

    name = args[0]

    if exists(name):
        raise Exception('file or directory already exists')

    create(name, file_factory())


def run_mkdir(args):
    require_arguments(args, 1)

    name = args[0]

    if exists(name):
        raise Exception('file or directory already exists')

    create(name, directory_factory())


def run_rm(args):
    require_arguments(args, 1)

    name = args[0]

    if not exists(name):
        raise Exception('file or directory not found')

    record = get(name)
    if not mine(record):
        raise Exception('insufficient permissions, file belongs to {}'.format(record['owner']))

    del __current()['child'][name]


def run_vypis(args):
    require_arguments(args, 1)

    name = args[0]

    if not exists(name):
        raise Exception('file not found')

    record = get(name)

    if is_dir(record):
        raise Exception('expected file')

    if not can(record, 'r'):
        raise Exception('insufficient permissions to read file')

    print('ok')


def run_spusti(args):
    require_arguments(args, 1)

    name = args[0]

    if not exists(name):
        raise Exception('file not found')

    record = get(name)

    if is_dir(record):
        raise Exception('expected file')

    if not can(record, 'x'):
        raise Exception('insufficient permissions to read file')

    print('ok')


def run_zapis(args):
    require_arguments(args, 1)

    name = args[0]

    if not exists(name):
        raise Exception('file not found')

    record = get(name)

    if is_dir(record):
        raise Exception('expected file')

    if not can(record, 'w'):
        raise Exception('insufficient permissions to read file')

    print('ok')


def run_chmod(args):
    require_arguments(args, 2)

    perms = int(args[0])
    name = args[1]

    if not exists(name):
        raise Exception('file or directory not found')

    record = get(name)
    permissions = 'r' if perms >= 4 else '-'
    permissions += 'w' if perms in [2, 3, 6, 7] else '-'
    permissions += 'x' if perms % 2 == 1 else '-'
    record['perm'] = permissions


def run_chown(args):
    require_arguments(args, 2)

    owner = args[0]
    name = args[1]

    if not exists(name):
        raise Exception('file or directory not found')

    record = get(name)
    record['owner'] = owner


def run_cd(args):
    global path

    require_arguments(args, 1)

    if args[0] == '.':
        return

    if args[0] == '..':
        path = __parent()
        return

    if args[0] == '/':
        path = '/'
        return

    name = args[0]
    if not exists(name):
        raise Exception('directory not found')

    record = get(name)
    if not is_dir(record):
        raise Exception('expected directory')

    if not can(record, 'x'):
        raise Exception('insufficient permissions to read directory content')

    path = path + '/' + name
    path = re.sub(r'//', '/', path)


def run(command, args):
    commands = {
        'quit': run_quit,
        'sudo': run_sudo,
        'ls': run_ls,
        'touch': run_touch,
        'mkdir': run_mkdir,
        'rm': run_rm,
        'chmod': run_chmod,
        'chown': run_chown,
        'cd': run_cd,
        'vypis': run_vypis,
        'spusti': run_spusti,
        'zapis': run_zapis,
        'pwd': pwd,
    }

    if command not in commands:
        raise Exception('unknown command [{}]'.format(command))

    commands[command](args)


def command_parser():
    _input = input('{} {} {}'.format(user, path, prompt))
    _input = re.sub(r'[ ]+', ' ', _input).strip()
    [command, *args] = _input.split(' ')
    return command, args


def boot():
    global fs

    fs = filesystem_factory()

    while True:
        command, args = command_parser()
        try:
            run(command, args)
        except Exception as e:
            print(e)


boot()
