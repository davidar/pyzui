## genapidoc.py - Generate LaTeX documentation for a Python package
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""
USAGE:
  genapidoc.py package_location/package
e.g.:
  genapidoc.py ../pyzui > apidoc.tex
"""

import __future__
import sys
import os
import inspect
import re

member_doc = {
    "run": "Note: for threading to be enabled this method should not "
        "be called directly, call the `start()` method instead.",
}

def str_function(func):
    s = func.__name__

    args, varargs, varkw, defaults = inspect.getargspec(func)
    if 'self' in args:
        args.remove('self')

    s += inspect.formatargspec(args, varargs, varkw, defaults)

    return s


def str_class(cls):
    module = inspect.getmodule(cls)
    return "%s.%s" % (module.__name__, cls.__name__)


def repl_url(matchobj):
    url = matchobj.group(1)
    url = url.replace('\\_','_')
    return "\\url{%s}" % url


def print_tex(*args):
    for s in map(str, args):
        s = s.replace('_', '\\_')
        s = s.replace('->', '$\\rightarrow$')
        s = s.replace('~', '$\\sim$')
        s = s.replace('...', '$\\ldots$')
        s = s.replace('<=', '$\\leq$')
        s = s.replace('>=', '$\\geq$')

        s = re.sub(r'`(.*?)`', r'\\texttt{\1}', s)
        s = re.sub(r'<(http://[^ ]*)>', r'\\url{\1}', s)
        s = re.sub(r'\\url{(.*?)}', repl_url, s)
        s = re.sub(r'\n([^\s\\]*:)', r'\n\n\\textbf{\1}', s)
        s = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', s)

        print s,
    print


def print_heading(level, title):
    heading_cmd = [
        "chapter",
        "section",
        "subsection",
        "subsubsection",
    ]
    print_tex("\\%s{%s}" % (heading_cmd[level], title))


def print_items(items):
    if not items: return
    print_tex("\\begin{itemize}")
    for item in items:
        print_tex("\\item", item)
    print_tex("\\end{itemize}")


def print_desc(d):
    if not d: return
    keys = d.keys()
    keys.sort()
    print_tex("\\begin{description}")
    for k in keys:
        print_tex("\\item[%s]" % k)
        if d[k]: print_tex(d[k])
    print_tex("\\end{description}")


def get_inheritance(superclasses, member_name, member):
    for superclass in reversed(superclasses):
        if hasattr(superclass, member_name) and \
           getattr(superclass, member_name) == member:
            return superclass


def get_doc_member(cls, superclasses, member_name, member, toplevel=True):
    if superclasses:
        baseclass = superclasses[0]
    else:
        baseclass = None

    doc = inspect.getdoc(member) or ''
    if doc:
        if member_name in member_doc:
            doc += "\n\n%s" % member_doc[member_name]
        if not toplevel:
            doc += "\n\\textit{(Docstring inherited " \
                "from %s)}" % cls.__name__
    else:
        if baseclass and hasattr(baseclass, member_name):
            doc = get_doc_member(baseclass,
                superclasses[1:], member_name,
                getattr(baseclass, member_name), False)

    if toplevel and member_name != "__init__" and \
       baseclass and hasattr(baseclass, member_name):
        overrides_cls = get_inheritance(
            superclasses[1:], member_name,
            getattr(baseclass, member_name))
        if overrides_cls:
            doc += "\n\n\\textit{Overrides %s.%s}" % \
                (str_class(overrides_cls), member_name)
        else:
            doc += "\n\n\\textit{Overrides %s.%s}" % \
                (str_class(baseclass), member_name)

    return doc


def handle_class(cls):
    try:
        superclasses = list(cls.__mro__)
        superclasses.remove(object)
        superclasses.remove(cls)
    except Exception:
        superclasses = []

    print_heading(2, "Class %s" % cls.__name__)
    print_tex(inspect.getdoc(cls))
    if superclasses:
        print_tex("\n\\textbf{Derived from:}",
            ', '.join(
                ["\\url{%s}" % str_class(c)
                for c in superclasses]))

    methods = {}
    data = {}
    attrs = {}

    inherits = dict([(c, []) for c in superclasses])

    for member_name, member in inspect.getmembers(cls):
        if (member_name.startswith('_') and \
            member_name != "__init__") or \
           member_name == "staticMetaObject":
            continue

        inherited_from = get_inheritance(
            superclasses, member_name, member)
        if inherited_from:
            if inspect.ismethod(member):
                inherits[inherited_from].append(
                    str_function(member))
            else:
                inherits[inherited_from].append(member_name)
            continue

        if inspect.ismethod(member):
            s = str_function(member)
            s = s.replace("__init__", cls.__name__)
            methods[s] = get_doc_member(
                cls, superclasses, member_name, member)
        elif inspect.isdatadescriptor(member):
            data[member_name] = get_doc_member(
                cls, superclasses, member_name, member)
        else:
            doc = "`%s`" % repr(member)
            doc = doc.replace('{','\\{')
            doc = doc.replace('}','\\}')
            attrs[member_name] = doc

    print_desc(methods)
    print_desc(data)
    print_desc(attrs)

    for c in superclasses:
        members = inherits[c]
        if members:
            members.sort()
            num_members = len(members)
            if num_members > 20:
                members = members[:20]
                members.append(
                    "... \\textit{%d more}" % num_members)
            print_tex("\n\\textbf{Inherited from %s:}" % \
                str_class(c), ', '.join(members))


def handle_module(module):
    print_tex("\\pagebreak")
    print_heading(1, "Module %s" % module.__name__)
    print_tex(inspect.getdoc(module))

    functions = {}
    data = {}

    for obj_name in dir(module):
        obj = getattr(module, obj_name)

        if inspect.ismodule(obj) or inspect.isbuiltin(obj) or \
           (inspect.isclass(obj) and \
            inspect.getmodule(obj) != module) or \
           (inspect.isfunction(obj) and \
            inspect.getmodule(obj) != module) or \
           isinstance(obj, __future__._Feature) or \
           obj_name.startswith('_'):
            continue

        if obj_name.startswith('__') and obj_name.endswith('__'):
            pass
        elif inspect.isclass(obj):
            handle_class(obj)
        elif inspect.isfunction(obj):
            functions[str_function(obj)] = inspect.getdoc(obj)
        else:
            data[obj_name] = str(obj)

    if functions:
        print_heading(2, "Functions")
        print_desc(functions)
    if data:
        print_heading(2, "Data")
        print_desc(data)


def handle_package(package_name):
    package = __import__(package_name)
    module_names = package.__all__
    package = __import__(package_name, fromlist=module_names)

    for module_name in module_names:
        module = getattr(package, module_name)
        handle_module(module)


if __name__ == '__main__':
    package_path = sys.argv[1]
    sys.path.append(os.path.abspath(os.path.dirname(package_path)))
    handle_package(os.path.basename(package_path))
