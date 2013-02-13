# This module provides the function getopt_afs.getopt()

# Written by Justin Sheehy
# Further modified by Jeff Blaine

# getopt_afs, version 0.2

# Clearly, it is modeled after the standard module 'getopt', but
# it attempts to add argument processing logic similar to that found
# in the suite of commands used for administering the Andrew File System.

# No use of AFS code occured in the writing of this module.  In fact,
# since the argument processing interface in AFS is not clearly 
# documented anywhere, I do not know that this will actually behave in
# the same manner.  I have merely imitated the interface as well as
# possible.

# Perhaps at some point I will use this space to try to describe this
# method of argument processing.  For now, I will assume that you know
# what you want if you are using this module.

# It has two required arguments:
#  The first should be argv[1:]
#  The second should be a list of allowable argument strings.  If the
#   name ends '=', the argument requires an argument.  If the name ends
#   '+', the argument is required.  Obviously, required arguments
#   implicitly require an argument.  (Have fun parsing that sentence.)
#   If for some reason you decide to be redundant and specify both, do
#   it in this order: '=+'.  The reverse ('+=') will not work.  All 
#   required args should precede all non-required args.

# It raises the exception getopt_afs with a string argument 
# if it detects an error.

# It returns two values:
# (1) a list of pairs (option, option_argument) giving the options in
#     the order in which they were specified.  Boolean options 
#     have '' as option_argument.
# (2) the list of remaining arguments (may be empty).

import string, sys

# return tuple:
#  0 -> valid_opt? (None, 0, 1)
#        None  -> no such option
#        0     -> ambiguous prefix
#        1     -> option is valid
#  1 -> this opt is required? (0 or 1)
#  2 -> requires_arg?  (0 or 1)
#  3 -> full option name (without '=', if present)
# all returned values after the first are only meaningful if the first is 1
def _opt_info(opt, opts):
    opts = opts[:]
    opts.sort()
    optlen = len(opt)
    required = 0
    requires_arg = 0
    for i in range(len(opts)):  
        fullopt = opts[i]
        x = fullopt[:optlen]
        if opt != x:
            continue
        if len(opts) > i+1:
            if x == opts[i+1][:optlen]:
                return 0, 0, 0, 0
        if fullopt[-1:] == '+':
            required = 1
            requires_arg = 1
            fullopt = fullopt[:-1]
        if fullopt[-1:] == '=':
            requires_arg = 1
            fullopt = fullopt[:-1]
        return 1, required, requires_arg, fullopt
    return None, 0, 0, 0

def _strip_opt_mung(optname):
    while optname[-1] == '=' or optname[-1] == '+':
        optname = optname[:-1]
    return optname

def _delete_opt(opt, opts):
    if not opts:
        return []
    topopt = [opts[0]]
    if _strip_opt_mung(topopt) == opt:
        return opts[1:]
    else:
        return topopt + _delete_opt(opt, opts[1:])

# return a tuple:
# 0 -> remaining unparsed args
# 1 -> remaining unmatched opts
# 2 -> list of pairs of (option, option_argument)
def _parse_positional(args, opts, pairs=[]):
    if not opts:
        return args, [], pairs
    if not args:
        return [], opts, pairs
    arg = args[0]
    if arg[0] == '-':
        return args, opts, pairs
    opt = _strip_opt_mung(opts[0])
    return _parse_positional(args[1:],
                             opts[1:],
                             pairs + [(opt, arg)])

# return a tuple:
# 0 -> list of pairs of (option, option_argument)
# 1 -> list of unmatched args
# all args not destined to be matched must be at the end of the arglist
def _parse_keyed(args, opts):
    parsed = _parse_keyed_1(args, opts)
    try:
        sep = parsed.index(' ')
    except ValueError:
        return parsed, []
    matches = parsed[:sep]
    unmatched = parsed[sep+1:]
    return matches, unmatched

def _parse_keyed_1(args, opts):  
    if not opts:
        return [' '] + args 
    if not args:
        return []
    if args[0][0] != '-':
        return [' '] + args
    arg = args[0][1:]
    valid, required, requires_arg, argname = _opt_info(arg, opts)
    if not valid:
        raise Exception('getopt_afs', 'invalid option name: %s' % arg)
    argval = '' 
    if len(args) > 1:
        argval = args[1]
    if argval != '' and argval[0] == '-': argval = ''
    if requires_arg and not argval:
        raise Exception('getops_afs', 'option %s requires an argument' % argname)
    curlist = [(argname, argval)]
    if argval:
        return curlist + _parse_keyed_1(args[2:], opts)
    else:
        return curlist + _parse_keyed_1(args[1:], opts)

def _required_opts(opts):
    r_opts = []
    for opt in opts:
        valid, required, requires_arg, argname = _opt_info(opt, opts)
        if required:
            r_opts.append(argname)
    return r_opts

def _all_required_matched(matches, opts):
    matched_opts = map(lambda a: a[0], matches)
    for r_opt in _required_opts(opts):
        if r_opt not in matched_opts:
            return 0
    return 1

def getopt(args, opts_1):
    list = []
    opts = opts_1[:]
    args, opts, frontlist = _parse_positional(args, opts)
    restlist, remainder = _parse_keyed(args, opts)
    biglist = frontlist + restlist
    if not _all_required_matched(biglist, opts_1):
        raise Exception('getopt_afs', 'not all required options were supplied')
    biglist = map(lambda a: ('-' + a[0], a[1]), biglist)
    return biglist, remainder

if __name__ == '__main__':
    # test by acting as though we take the same args as AFS 'vos create'
    cropts = string.split('server+ partition+ name+ maxquota= cell= noauth '+
                          'localauth verbose help')
    print getopt(sys.argv[1:], cropts)
